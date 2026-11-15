"""Offline News regressions; no Steam/Decky installation is required.
Run: python scripts/runtime_regression.py
"""
import asyncio
import builtins
from concurrent.futures import ThreadPoolExecutor
import http.client
import importlib.util
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TEMP = tempfile.TemporaryDirectory(prefix="news-runtime-tests-")
BASE = Path(TEMP.name)
LOGS = []
stub = types.ModuleType("decky_plugin")
stub.SETTINGS_DIR = str(BASE / "settings")
stub.RUNTIME_DIR = str(BASE / "runtime")
stub.logger = types.SimpleNamespace(info=lambda text, *args, **kwargs: LOGS.append(text))
sys.modules["decky_plugin"] = stub

# Reproduce the logged frozen-runtime import failure, including optional modules
# that used to be imported immediately after http.server.
real_import = builtins.__import__
def restricted_import(name, *args, **kwargs):
    if name in {"http.server", "socketserver", "mimetypes", "webbrowser"}:
        raise ModuleNotFoundError(f"No module named '{name}'", name=name)
    return real_import(name, *args, **kwargs)

with patch("builtins.__import__", restricted_import):
    spec = importlib.util.spec_from_file_location("news_runtime_test", ROOT / "main.py")
    news = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(news)

class ImageServerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=BASE)
        self.root = Path(self.directory.name)
        self.logs = []
        self.server = news.NewsImageCacheServer(self.root, self.logs.append)
        self.name = "a" * 40 + ".png"
        self.payload = b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 1500
        (self.root / self.name).write_bytes(self.payload)
        self.server.start()
        self.path = f"/{self.server.token}/image/{self.name}"

    def tearDown(self):
        self.server.stop()
        self.directory.cleanup()

    def request(self, path=None, method="GET"):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=3)
        try:
            conn.request(method, path or self.path)
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def raw(self, payload):
        with socket.create_connection(("127.0.0.1", self.server.port), timeout=2) as client:
            client.sendall(payload)
            result = bytearray()
            while True:
                try:
                    chunk = client.recv(65536)
                except ConnectionResetError:
                    # Rejected oversized requests can leave unread client bytes;
                    # require an actual HTTP response even if close sends a RST.
                    if not result:
                        raise
                    break
                if not chunk:
                    break
                result.extend(chunk)
            return bytes(result)

    def test_01_import_without_http_server(self):
        self.assertNotIn("import http.server", (ROOT / "main.py").read_text(encoding="utf-8"))
        self.assertGreater(self.server.port, 0)
        self.assertEqual(self.server._server.getsockname()[0], "127.0.0.1")

    def test_02_get_preserves_binary_and_headers(self):
        status, headers, body = self.request()
        self.assertEqual((status, body), (200, self.payload))
        self.assertEqual(headers["Content-Type"], "image/png")
        self.assertEqual(int(headers["Content-Length"]), len(body))
        self.assertEqual(headers["Access-Control-Allow-Origin"], "*")
        self.assertEqual(headers["Cross-Origin-Resource-Policy"], "cross-origin")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("immutable", headers["Cache-Control"])

    def test_03_head_does_not_send_body(self):
        status, headers, body = self.request(method="HEAD")
        self.assertEqual((status, body), (200, b""))
        self.assertEqual(int(headers["Content-Length"]), len(self.payload))

    def test_04_options_preflight(self):
        status, headers, body = self.request(method="OPTIONS")
        self.assertEqual((status, body), (204, b""))
        self.assertIn("HEAD", headers["Access-Control-Allow-Methods"])

    def test_05_all_mime_types(self):
        for suffix, mime in self.server.MIME_TYPES.items():
            with self.subTest(suffix=suffix):
                name = "b" * 40 + "." + suffix
                (self.root / name).write_bytes(b"image-bytes")
                status, headers, body = self.request(f"/{self.server.token}/image/{name}")
                self.assertEqual((status, body), (200, b"image-bytes"))
                self.assertEqual(headers["Content-Type"], mime)

    def test_06_bundled_favicon_and_query(self):
        (self.root / "asset-test-example.png").write_bytes(b"favicon")
        self.assertEqual(self.request(f"/{self.server.token}/image/asset-test-example.png?rev=1")[2], b"favicon")

    def test_07_wrong_token_and_missing_images(self):
        self.assertEqual(self.request(self.path.replace(self.server.token, "invalid"))[0], 404)
        self.assertEqual(self.request(f"/{self.server.token}/image/{'c'*40}.jpg")[0], 404)

    def test_08_no_path_traversal_or_directory_listing(self):
        for value in ("../main.py", "%2e%2e%2fmain.py", "..%5cmain.py", "", "a.png", "/etc/passwd", self.name+"%00"):
            with self.subTest(value=value):
                status, headers, _ = self.request(f"/{self.server.token}/image/{value}")
                self.assertEqual(status, 404)
                self.assertEqual(headers["Cache-Control"], "no-store")

    def test_09_symlink_cannot_escape(self):
        target = BASE / "outside.png"
        target.write_bytes(b"private")
        link = self.root / ("e" * 40 + ".png")
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable on this platform")
        self.assertEqual(self.request(f"/{self.server.token}/image/{link.name}")[0], 404)

    def test_10_rejects_post_and_malformed_request(self):
        self.assertEqual(self.request(method="POST")[0], 405)
        self.assertTrue(self.raw(b"BROKEN\r\n\r\n").startswith(b"HTTP/1.1 400"))
        self.assertTrue(self.raw(b"GET /\xff HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 400"))

    def test_11_headers_have_a_size_limit(self):
        self.assertTrue(self.raw(b"GET / HTTP/1.1\r\nX: " + b"a" * self.server.MAX_HEADERS).startswith(b"HTTP/1.1 431"))

    def test_12_parallel_requests(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(lambda _: self.request(), range(32)))
        self.assertTrue(all(status == 200 and body == self.payload for status, _, body in responses))

    def test_13_disconnects_do_not_break_server(self):
        for _ in range(10):
            with socket.create_connection(("127.0.0.1", self.server.port)) as client:
                client.sendall(f"GET {self.path} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode())
        time.sleep(0.05)
        self.assertEqual(self.request()[0], 200)
        self.assertFalse(any("error" in line for line in self.logs))

    def test_14_stop_closes_active_clients_and_can_restart(self):
        port = self.server.port
        client = socket.create_connection(("127.0.0.1", port), timeout=2)
        client.sendall(b"GET / HTTP/1.1\r\n")
        time.sleep(0.02)
        self.server.stop()
        self.assertEqual(self.server.port, 0)
        self.assertEqual(self.server.image_url(self.name), "")
        self.assertEqual(client.recv(1), b"")
        client.close()
        self.server.stop()
        self.server.start()
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.server._slots._value, self.server.MAX_CLIENTS)

    def test_15_request_deadline_and_bounded_workers(self):
        self.server.CLIENT_TIMEOUT = 0.2
        clients = [socket.create_connection(("127.0.0.1", self.server.port), timeout=2) for _ in range(16)]
        time.sleep(0.04)
        with self.server._clients_lock:
            self.assertLessEqual(len(self.server._clients), self.server.MAX_CLIENTS)
        time.sleep(0.35)
        for client in clients:
            client.close()
        self.assertEqual(self.request()[0], 200)

    def test_16_oversized_image_not_served(self):
        with (self.root / self.name).open("wb") as handle:
            handle.truncate(news.MAX_IMAGE_BYTES + 1)
        self.assertEqual(self.request()[0], 404)

class LifecycleTests(unittest.TestCase):
    def test_17_bootstrap_starts_without_optional_modules(self):
        async def exercise():
            plugin = news.Plugin()
            try:
                with patch("builtins.__import__", restricted_import):
                    await plugin._main()
                    result = await plugin.get_bootstrap()
                self.assertTrue(result["ok"])
                self.assertTrue(result["countries"])
                self.assertTrue(plugin._image_server.port)
                version = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
                self.assertTrue(any(f"News {version} loaded" in line for line in LOGS))
            finally:
                await plugin._unload()
        asyncio.run(exercise())

    def test_18_unload_cancels_delayed_image_and_prefetch_tasks(self):
        async def exercise():
            plugin = news.Plugin()
            calls = []
            plugin._schedule_background(0.15, lambda: calls.append("unexpected"))
            plugin._schedule_image_cache_warm("https://example.invalid/test.jpg", "", "test", 0.15)
            self.assertEqual(len(plugin._background_timers), 2)
            await plugin._unload()
            await asyncio.sleep(0.2)
            self.assertEqual(calls, [])
            self.assertFalse(plugin._background_timers)
            plugin._schedule_background(0, lambda: calls.append("unexpected"))
            self.assertFalse(plugin._background_timers)
            await plugin._unload()
        asyncio.run(exercise())

    def test_19_current_config_is_not_reset_on_upgrade(self):
        news.SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        config = news._default_config()
        config.update(onboardingComplete=True, country="DE", language="de-DE", refreshMinutes=30,
                      activeTabId="custom-one", tabs=[{"id":"custom-one", "name":"My stories", "category":"", "sourceIds":[]}])
        news.CONFIG_PATH.write_text(json.dumps(config))
        before = news.CONFIG_PATH.read_bytes()
        async def exercise():
            plugin = news.Plugin()
            try:
                await plugin._main()
                self.assertEqual(plugin._config, config)
            finally:
                await plugin._unload()
        asyncio.run(exercise())
        self.assertEqual(before, news.CONFIG_PATH.read_bytes())

if __name__ == "__main__":
    try:
        unittest.main(verbosity=2)
    finally:
        TEMP.cleanup()

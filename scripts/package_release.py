"""Create matching News Installer/Project ZIPs; excludes caches and dependencies."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {"node_modules", "__pycache__", ".git", ".settings", ".runtime", ".test-settings", ".test-runtime", "releases"}
RUNTIME = ("main.py", "package.json", "plugin.json", "dist/index.js", "countries.json", "source_catalog.json", "source_assets_manifest.json", "LICENSE", "README.md", "CHANGELOG_1.0.2.md")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "releases")
    args = parser.parse_args()
    version = json.loads((ROOT / "package.json").read_text())["version"]
    args.output.mkdir(parents=True, exist_ok=True)
    installer_files = [ROOT / entry for entry in RUNTIME] + sorted((ROOT / "assets").rglob("*.png"))
    for entry in installer_files:
        if not entry.is_file():
            raise FileNotFoundError(entry)
    installer = args.output / f"News-decky_Installer-{version}.zip"
    project = args.output / f"News-project-{version}.zip"
    excluded_output = args.output.resolve()
    exclude_output_tree = excluded_output != ROOT.resolve() and ROOT.resolve() in excluded_output.parents
    project_files = sorted(file for file in ROOT.rglob("*") if file.is_file()
        and not set(file.relative_to(ROOT).parts).intersection(IGNORED)
        and not file.name.endswith((".pyc", ".pyo", ".zip", ".log", ".map", ".tsbuildinfo"))
        and file.resolve() != installer.resolve() and file.resolve() != project.resolve()
        and not (exclude_output_tree and excluded_output in file.resolve().parents))
    for archive, prefix, files in [(installer, "News", installer_files), (project, f"News-project-{version}", project_files)]:
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for file in files:
                z.write(file, str(Path(prefix) / file.relative_to(ROOT)))
        with zipfile.ZipFile(archive) as z:
            bad = z.testzip()
            if bad:
                raise RuntimeError(f"ZIP integrity failed: {archive}: {bad}")
    with zipfile.ZipFile(installer) as i, zipfile.ZipFile(project) as p:
        for name in i.namelist():
            other = f"News-project-{version}/" + name.removeprefix("News/")
            if i.read(name) != p.read(other):
                raise RuntimeError(f"Installer/project mismatch: {name}")
    for archive in (installer, project):
        print(f"{archive}: {archive.stat().st_size} bytes; SHA-256 {hashlib.sha256(archive.read_bytes()).hexdigest()}")
    print("Archive integrity and all shared runtime files: OK")

if __name__ == "__main__":
    main()

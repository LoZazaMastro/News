import asyncio
import base64
import hashlib
import html
import http.cookiejar
import json
import os
import re
import secrets
import shutil
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import decky_plugin

PLUGIN_DIR = Path(__file__).resolve().parent
SETTINGS_DIR = Path(getattr(decky_plugin, "SETTINGS_DIR", PLUGIN_DIR / ".settings"))
CACHE_DIR = Path(getattr(decky_plugin, "RUNTIME_DIR", PLUGIN_DIR / ".runtime")) / "news-cache"
CONFIG_PATH = SETTINGS_DIR / "news.json"
CATALOG_PATH = PLUGIN_DIR / "source_catalog.json"
COUNTRIES_PATH = PLUGIN_DIR / "countries.json"
FAVICON_ASSETS_DIR = PLUGIN_DIR / "assets" / "favicons"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
MAX_FEED_BYTES = 4 * 1024 * 1024
MAX_ARTICLE_BYTES = 6 * 1024 * 1024
MAX_IMAGE_BYTES = 8 * 1024 * 1024
IMAGE_CACHE_DIR = CACHE_DIR / "images"
ARTICLE_CACHE_SECONDS = 6 * 60 * 60
IMAGE_CACHE_SECONDS = 30 * 24 * 60 * 60
FEED_CACHE_VERSION = 14
ARTICLE_CACHE_VERSION = 17
IMAGE_CACHE_VERSION = 14
JINA_READER_BASE = "https://r.jina.ai/"
JINA_READER_TIMEOUT = 6.0
JINA_COVER_TIMEOUT = 5.0
GOOGLE_RESOLVE_CACHE_SECONDS = 30 * 24 * 60 * 60
RESOLVE_CACHE_VERSION = 12

COUNTRY_LANGUAGE = {
    "IT": "it", "FR": "fr", "DE": "de", "ES": "es", "PT": "pt", "BR": "pt",
    "GB": "en", "US": "en", "CA": "en", "AU": "en", "NZ": "en", "IE": "en",
    "JP": "ja", "KR": "ko", "CN": "zh-CN", "TW": "zh-TW", "HK": "zh-TW",
    "NL": "nl", "BE": "nl", "SE": "sv", "NO": "no", "DK": "da", "FI": "fi",
    "PL": "pl", "CZ": "cs", "SK": "sk", "HU": "hu", "RO": "ro", "GR": "el",
    "TR": "tr", "RU": "ru", "UA": "uk", "IL": "he", "IN": "en", "ID": "id",
    "MX": "es", "AR": "es", "CL": "es", "CO": "es", "PE": "es", "ZA": "en",
}

PRESET_CATEGORY_ALIASES = {
    "all": "all", "tutte": "all",
    "politics": "politics", "politica": "politics",
    "sports": "sports", "sport": "sports",
    "economy": "economy", "economia": "economy", "business": "economy",
    "games": "games", "videogiochi": "games", "gaming": "games",
    "music": "music", "musica": "music",
    "cinema": "cinema", "film": "cinema", "cinema e serie tv": "cinema", "cinema e serie": "cinema", "serie tv": "cinema",
    "fashion": "fashion", "moda": "fashion", "style": "fashion",
    "science": "science", "scienza": "science",
    "health": "health", "salute": "health", "healthcare": "health",
    "comics": "comics", "fumetti": "comics",
    "tech": "tech", "tecnologia": "tech",
    "art": "art", "arte": "art",
    "travel": "travel", "viaggi": "travel",
    "food": "food", "cucina": "food",
    "culture": "culture", "cultura": "culture",
}


CATEGORY_STRONG_KEYWORDS = {
    "politics": [
        "governo", "government", "parlamento", "parliament", "senato", "senate", "camera dei deputati",
        "elezioni", "elezione", "election", "referendum", "prime minister",
        "white house", "casa bianca", "congresso", "congress", "commissione europea", "european commission",
        "diplomazia", "diplomacy", "sanzioni", "sanctions", "ceasefire", "tregua", "nato summit", "alleanza atlantica", "kremlin", "cremlino",
        "gaza", "hamas", "kim jong", "north korea", "corea del nord", "ukraine", "ucraina",
    ],
    "economy": [
        "economia", "economy", "business", "borsa", "stock market", "mercati", "market", "inflazione", "inflation", "pil", "gdp", "banca", "bank", "banche",
        "fisco", "tax", "tassi", "interest rate", "rates", "lavoro", "occupazione", "disoccupazione", "wall street", "nasdaq", "ftse mib", "utili", "earnings", "quarterly",
        "risultati finanziari", "startup", "impresa", "azienda", "aziende", "retail sales", "vendite", "recession", "recessione",
    ],
    "sports": [
        "calcio", "serie a", "serie b", "champions league", "europa league", "conference league", "coppa italia",
        "football", "soccer", "nba", "nfl", "nhl", "mlb", "formula 1", "formula one", "motogp", "tennis",
        "wimbledon", "roland garros", "us open", "olimpi", "olympic", "world cup", "mondiali", "golf", "pga",
        "liv golf", "rugby", "basket", "basketball", "pallavolo", "volley", "ciclismo", "cycling", "tour de france",
        "giro d'italia", "motorsport", "rally", "juventus", "inter milan", "ac milan", "napoli", "lazio", "as roma",
        "atalanta", "fiorentina", "premier league", "la liga", "bundesliga", "gattuso", "tifosi", "liv ", "pga",
        "calciatore", "footballer", "allenatore", "coach", "tournament", "torneo", "championship", "motorsport", "rally", "pilota",
    ],
    "games": [
        "videogioc", "video game", "videogame", "gaming", "playstation", "ps5", "ps6", "xbox", "nintendo", "switch 2",
        "steam deck", "game pass", "epic games", "ubisoft", "capcom", "square enix", "resident evil", "final fantasy",
        "pokemon", "zelda", "gameplay", "dlc", "gamescom", "the game awards", "console", "jrpg", "rpg a turni",
    ],
    "music": [
        "album", "singolo", "single", "cantante", "singer", "rapper", "concerto", "concert", "grammy", "billboard",
        "spotify", "taylor swift", "hip hop", "jazz", "music festival", "festival musicale",
    ],
    "cinema": [
        "cinema", "film", "movie", "box office", "hollywood", "netflix", "disney+", "prime video", "hbo", "serie tv",
        "tv series", "attore", "attrice", "actor", "actress", "regista", "director", "oscar", "emmy", "marvel studios",
    ],
    "fashion": ["moda", "fashion", "style", "runway", "sfilata", "couture", "luxury", "lusso", "designer", "fashion week", "beauty"],
    "science": ["scienza", "science", "scientific", "ricerca", "research", "nasa", "spazio", "space", "astronomia", "astronomy", "fisica", "physics", "biologia", "biology"],
    "health": ["salute", "health", "sanità", "healthcare", "medicina", "medicine", "ospedale", "hospital", "farmaco", "vaccine", "vaccino", "wellness"],
    "comics": ["fumett", "comic book", "comics", "manga", "anime", "graphic novel", "marvel comics", "dc comics", "bonelli"],
    "tech": [
        "tecnologia", "technology", "smartphone", "android", "iphone", "pixel", "windows", "linux", "intelligenza artificiale",
        "artificial intelligence", "openai", "chatgpt", "semiconductor", "nvidia", "amd", "intel", "cybersecurity",
        "sicurezza informatica", "hardware", "software", "robot", "satellite",
    ],
    "art": ["museo", "museum", "mostra", "exhibition", "galleria", "gallery", "pittura", "painting", "scultura", "sculpture", "biennale", "architettura"],
    "travel": ["viaggio", "travel", "turismo", "tourism", "vacanza", "hotel", "aeroporto", "airport", "destinazione", "lonely planet", "itinerario"],
    "food": ["cucina", "ristorante", "restaurant", "chef", "ricetta", "recipe", "vino", "wine", "gastronomia", "pizza", "michelin"],
    "culture": ["letteratura", "literature", "libro", "book", "teatro", "theatre", "archeolog", "archaeolog", "università", "university"],
}

BROAD_FEED_TOPIC_LABELS = {
    "business", "technology", "tech", "entertainment", "movies", "tv",
}

# City/team names such as Napoli, Lazio and Roma are inherently ambiguous. Weather
# headlines frequently contain them as geography, not sport. When a title is
# clearly meteorological, those location/team tokens cannot by themselves file
# the story under Sport; an actual sports term must also be present.
WEATHER_TITLE_KEYWORDS = (
    "meteo", "previsioni del tempo", "previsioni meteo", "temperature", "temperatura",
    "caldo", "afa", "pioggia", "temporali", "temporale", "maltempo", "neve",
    "vento", "allerta meteo", "ondata di calore",
)
SPORTS_CONTEXT_KEYWORDS = (
    "calcio", "serie a", "serie b", "champions league", "europa league", "conference league",
    "coppa italia", "football", "soccer", "formula 1", "formula one", "motogp", "tennis",
    "wimbledon", "roland garros", "us open", "nba", "nfl", "nhl", "mlb", "golf", "rugby",
    "basket", "pallavolo", "volley", "ciclismo", "cycling", "motorsport", "rally",
    "calciatore", "allenatore", "coach", "tifosi", "tournament", "torneo", "championship",
)

CATEGORY_LABEL_ALIASES = {
    **PRESET_CATEGORY_ALIASES,
    "politica": "politics", "politics": "politics", "government": "politics",
    "economia": "economy", "business": "economy", "finance": "economy", "mercati": "economy", "sport": "sports", "calcio": "sports",
    "games": "games", "gaming": "games", "game": "games", "videogames": "games",
    "technology": "tech", "tecnologia": "tech", "tech": "tech", "scienza": "science", "science": "science", "salute": "health", "health": "health", "fashion": "fashion", "moda": "fashion",
    "spettacoli": "cinema", "entertainment": "cinema", "movies": "cinema", "tv": "cinema",
}

CATEGORY_KEYWORDS = {
    "politics": [
        "governo", "govern", "politic", "parlamento", "parliament", "senato", "senate", "camera dei deputati",
        "elezion", "election", "referendum", "prime minister", "premier", "ministero", "minister",
        "trump", "biden", "meloni", "macron", "starmer", "putin", "zelensky", "cremlino", "kremlin", "nato", "ue ",
        "european union", "commissione europea", "white house", "casa bianca", "congresso", "congress", "diplomazia", "diplomacy",
        "sanzioni", "sanctions", "guerra", "war ", "ceasefire", "tregua", "confine", "border policy", "immigraz", "migration",
    ],
    "economy": [
        "economia", "economy", "business", "borsa", "stock market", "mercati", "market", "inflazione", "inflation", "pil", "gdp", "banca", "bank", "banche",
        "fisco", "tax", "tassi", "interest rate", "rates", "lavoro", "occupazione", "disoccupazione", "wall street", "nasdaq", "ftse mib", "utili", "earnings", "quarterly",
        "risultati finanziari", "startup", "impresa", "azienda", "aziende", "retail sales", "vendite", "recession", "recessione",
    ],
    "sports": [

        "calcio", "serie a", "serie b", "champions league", "europa league", "conference league", "coppa italia", "football", "soccer",
        "nba", "nfl", "nhl", "mlb", "formula 1", "formula one", "f1 ", "motogp", "tennis", "wimbledon", "roland garros", "us open",
        "olimpi", "olympic", "mondiali", "world cup", "allenatore", "coach",
        "gattuso", "milan", "inter ", "juventus", "napoli", "roma ", "lazio", "atalanta", "fiorentina", "premier league", "la liga", "bundesliga",
        "ciclismo", "cycling", "giro d'italia", "tour de france", "rugby", "basket", "pallavolo", "volley", "sci ", "ski ", "atleta", "athlete",
        "golf", "liv golf", "liv ", "pga", "formula e", "rally", "motorsport", "pilota", "driver", "tournament", "torneo", "championship", "campionato",
        "squadra", "transfer", "calciomercato", "semifinal", "quarter-final", "record sport",
    ],
    "games": [
        "videogioc", "video game", "videogame", "gaming", "playstation", "ps5", "ps6", "xbox", "nintendo", "switch", "steam deck",
        "game pass", "epic games", "ubisoft", "capcom", "square enix", "resident evil", "final fantasy", "pokemon", "zelda", "mario", "wolverine",
        "console", "dlc", "gameplay", "game awards", "the game awards", "gamescom", "trailer di gioco", "esports", "e-sport",
    ],
    "music": [
        "musica", "music", "album", "singolo", "single", "cantante", "singer", "rapper", "band ", "concerto", "concert", "tour ", "festival musicale",
        "grammy", "billboard", "spotify", "taylor swift", "tupac", "rock ", "pop ", "hip hop", "rap ", "jazz", "indie", "disco ", "track ", "brano",
    ],
    "cinema": [
        "cinema", "film ", "movie", "box office", "hollywood", "netflix", "disney+", "prime video", "hbo", "serie tv", "tv series", "telefilm",
        "attore", "attrice", "actor", "actress", "regista", "director", "oscar", "emmy", "trailer", "marvel studios", "dc studios",
    ],
    "fashion": [
        "moda", "fashion", "style", "runway", "sfilata", "fashion week", "couture", "designer", "lusso", "luxury", "beauty", "make-up", "makeup",
    ],
    "science": [
        "scienza", "science", "ricerca", "research", "studio scientifico", "scientist", "astronomia", "astronomy", "nasa", "space", "spazio", "fisica", "physics", "biologia", "biology", "climate research",
    ],
    "health": [
        "salute", "health", "sanità", "healthcare", "medicina", "medicine", "ospedale", "hospital", "farmaco", "drug", "vaccino", "vaccine", "wellness", "nutrizione", "nutrition",
    ],
    "comics": [
        "fumett", "comics", "comic book", "manga", "anime", "graphic novel", "marvel comics", "dc comics", "bonelli", "panini comics",
    ],
    "tech": [
        "tecnologia", "technology", "tech ", "smartphone", "android", "iphone", "pixel ", "apple ", "google ", "microsoft", "windows", "linux",
        "intelligenza artificiale", "artificial intelligence", " ai ", "openai", "chatgpt", "chip ", "semiconductor", "nvidia", "amd ", "intel ",
        "cyber", "sicurezza informatica", "software", "hardware", "app ", "robot", "space tech", "tesla", "satellite",
    ],
    "art": [
        "arte", " art ", "artista", "artist", "museo", "museum", "mostra", "exhibition", "galleria", "gallery", "pittura", "painting", "scultura", "sculpture",
        "biennale", "architettura", "architecture", "design ", "quadro", "quadri", "dipinto", "paintings",
    ],
    "travel": [
        "viaggio", "viaggi", "travel", "turismo", "tourism", "vacanza", "holiday", "hotel", "aeroporto", "airport", "volo ", "flight ", "destinazione",
        "lonely planet", "itinerario", "città da visitare", "isola ", "beach", "spiaggia",
    ],
    "food": [
        "cucina", "food", "ristorante", "restaurant", "chef ", "ricetta", "recipe", "vino ", "wine ", "birra", "beer ", "gastronomia", "cibo",
        "pizza", "pasta", "michelin", "gambero rosso", "dissapore",
    ],
    "culture": [
        "cultura", "culture", "libro", "book ", "letteratura", "literature", "teatro", "theatre", "storia", "history", "società", "society",
        "università", "university", "archeolog", "archaeolog", "religion", "religione",
    ],
}

WORLD_SOURCE_RECOMMENDATIONS = [
    {"name": "BBC News", "country": "GB", "siteUrl": "https://www.bbc.com/news", "feedUrl": "https://feeds.bbci.co.uk/news/rss.xml", "tags": ["politics", "all"]},
    {"name": "CNN", "country": "US", "siteUrl": "https://edition.cnn.com/", "feedUrl": "", "tags": ["politics", "all"]},
    {"name": "Euronews", "country": "FR", "siteUrl": "https://www.euronews.com/", "feedUrl": "https://www.euronews.com/rss", "tags": ["politics", "culture", "all"]},
    {"name": "The Verge", "country": "US", "siteUrl": "https://www.theverge.com/", "feedUrl": "https://www.theverge.com/rss/index.xml", "tags": ["tech", "games"]},
    {"name": "IGN", "country": "US", "siteUrl": "https://www.ign.com/", "feedUrl": "https://feeds.feedburner.com/ign/all", "tags": ["games", "cinema"]},
    {"name": "Reuters", "country": "US", "siteUrl": "https://www.reuters.com/", "feedUrl": "", "tags": ["politics", "all"]},
    {"name": "Eurogamer", "country": "GB", "siteUrl": "https://www.eurogamer.net/", "feedUrl": "https://www.eurogamer.net/feed", "tags": ["games"]},
    {"name": "Variety", "country": "US", "siteUrl": "https://variety.com/", "feedUrl": "https://variety.com/feed/", "tags": ["cinema"]},
    {"name": "Rolling Stone", "country": "US", "siteUrl": "https://www.rollingstone.com/", "feedUrl": "https://www.rollingstone.com/music/music-news/feed/", "tags": ["music", "culture"]},
]


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha1(value.encode('utf-8', 'ignore')).hexdigest()[:14]}"


def _load_json(path: Path, fallback: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return fallback


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _clean_text(value: Any) -> str:
    """Decode HTML/JSON-escaped publisher text before stripping markup.

    Google News RSS descriptions frequently contain escaped <a> tags; older
    builds stripped tags *before* html.unescape, which turned those anchors into
    visible raw HTML. Some Next/JSON publishers also expose \\uXXXX and \\r\\n
    sequences inside article-body strings. Keep this dependency-free for the
    minimal Decky Windows Python runtime.
    """
    raw = str(value or "")
    for _ in range(3):
        decoded = html.unescape(raw)
        if decoded == raw:
            break
        raw = decoded
    raw = raw.replace("\\/", "/").replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", " ").replace('\\"', '"').replace("\\'", "'")
    raw = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), raw)
    # Surrogate pairs are rare in prose; strip any unresolved escaped control.
    raw = re.sub(r"\\[rnt]", " ", raw)
    raw = re.sub(r"<script\b[^>]*>.*?</script\s*>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style\b[^>]*>.*?</style\s*>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    return re.sub(r"\s+", " ", raw).strip()


def _absolute(base: str, value: str) -> str:
    if not value:
        return ""
    return urllib.parse.urljoin(base, html.unescape(value.strip()))


def _parse_date(value: str) -> int:
    raw = str(value or "").strip()
    if not raw:
        return 0
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        pass
    normalized = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return 0


def _local_name(tag: str) -> str:
    value = str(tag or "")
    value = value.rsplit("}", 1)[-1]
    return value.rsplit(":", 1)[-1].lower()


def _parse_attrs(raw: str) -> Dict[str, str]:
    """Parse the small attribute subset needed by RSS/Atom/HTML.

    Kept deliberately self-contained because Decky's Windows Python runtime can
    omit parts of the stdlib package tree (notably html.parser/xml.etree).
    """
    attrs: Dict[str, str] = {}
    pattern = re.compile(r"([A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))", re.S)
    for match in pattern.finditer(raw or ""):
        value = match.group(2) if match.group(2) is not None else match.group(3) if match.group(3) is not None else match.group(4) or ""
        attrs[match.group(1).lower()] = html.unescape(value)
    return attrs


def _strip_cdata(value: str) -> str:
    raw = str(value or "").strip()
    if raw.startswith("<![CDATA[") and raw.endswith("]]>"):
        raw = raw[9:-3]
    return raw


def _tag_values(fragment: str, name: str) -> List[str]:
    escaped = re.escape(name)
    pattern = re.compile(
        rf"<(?:[A-Za-z0-9_.-]+:)?{escaped}\b[^>]*>(.*?)</(?:[A-Za-z0-9_.-]+:)?{escaped}\s*>",
        re.I | re.S,
    )
    return [_strip_cdata(match.group(1)) for match in pattern.finditer(fragment or "")]


def _first_tag_value(fragment: str, names: Iterable[str]) -> str:
    for name in names:
        values = _tag_values(fragment, str(name))
        if values:
            return values[0]
    return ""


class _FeedXmlParser:
    """Small RSS/Atom parser with no xml.etree/html.parser dependency."""

    TEXT_FIELDS = {
        "title", "description", "summary", "content", "encoded",
        "pubdate", "published", "updated", "date", "guid", "id",
        "link", "source", "category", "subject",
    }

    def __init__(self) -> None:
        self.items: List[Dict[str, Any]] = []
        self.feed_title = ""
        self.feed_link = ""
        self.publisher_sources: List[Dict[str, str]] = []

    def feed(self, text: str) -> None:
        raw = str(text or "")
        item_matches = list(re.finditer(r"<(?:[A-Za-z0-9_.-]+:)?(?:item|entry)\b[^>]*>(.*?)</(?:[A-Za-z0-9_.-]+:)?(?:item|entry)\s*>", raw, re.I | re.S))
        item_spans: List[Tuple[int, int]] = []
        for match in item_matches:
            item_spans.append(match.span())
            body = match.group(1)
            fields: Dict[str, List[str]] = {}
            for field in self.TEXT_FIELDS:
                values = _tag_values(body, field)
                if values:
                    fields[field] = values

            links: List[Dict[str, str]] = []
            for link_match in re.finditer(r"<(?:[A-Za-z0-9_.-]+:)?link\b([^>]*)/?>", body, re.I | re.S):
                attrs = _parse_attrs(link_match.group(1))
                href = attrs.get("href", "")
                if href:
                    links.append({"href": href, "rel": attrs.get("rel", "alternate")})

            media: List[Dict[str, str]] = []
            for media_match in re.finditer(r"<(?:[A-Za-z0-9_.-]+:)?(enclosure|content|thumbnail)\b([^>]*)/?>", body, re.I | re.S):
                attrs = _parse_attrs(media_match.group(2))
                url = attrs.get("url") or attrs.get("href") or ""
                if not url:
                    continue
                media.append({
                    "tag": media_match.group(1).lower(),
                    "url": url,
                    "type": attrs.get("type", ""),
                    "medium": attrs.get("medium", ""),
                    "width": attrs.get("width", ""),
                    "height": attrs.get("height", ""),
                })

            source_name = _clean_text(_first_tag_value(body, ["source"]))
            source_url = ""
            source_open = re.search(r"<(?:[A-Za-z0-9_.-]+:)?source\b([^>]*)>", body, re.I | re.S)
            if source_open:
                source_url = _parse_attrs(source_open.group(1)).get("url", "")
            item = {
                "fields": fields,
                "links": links,
                "media": media,
                "sourceName": source_name,
                "sourceUrl": source_url,
            }
            self.items.append(item)
            if source_name and source_url:
                self.publisher_sources.append({"name": source_name, "url": source_url})

        outside_parts: List[str] = []
        cursor = 0
        for lo, hi in item_spans:
            outside_parts.append(raw[cursor:lo])
            cursor = hi
        outside_parts.append(raw[cursor:])
        outside = "".join(outside_parts)
        self.feed_title = _clean_text(_first_tag_value(outside, ["title"]))

        for link_match in re.finditer(r"<(?:[A-Za-z0-9_.-]+:)?link\b([^>]*)/?>", outside, re.I | re.S):
            attrs = _parse_attrs(link_match.group(1))
            href = attrs.get("href", "")
            rel = attrs.get("rel", "alternate").lower()
            if href and rel in {"alternate", ""}:
                self.feed_link = href
                break
        if not self.feed_link:
            self.feed_link = _clean_text(_first_tag_value(outside, ["link"]))

    def close(self) -> None:
        return None


def _parse_feed_document(data: bytes) -> _FeedXmlParser:
    text = data.decode("utf-8", "replace")
    parser = _FeedXmlParser()
    parser.feed(text)
    parser.close()
    return parser


def _item_text(item: Dict[str, Any], names: Iterable[str]) -> str:
    fields = item.get("fields") or {}
    for name in names:
        parts = fields.get(str(name).lower()) or []
        value = " ".join(str(part) for part in parts).strip()
        if value:
            return value
    return ""


BAD_IMAGE_TERMS = (
    "avatar", "author", "authors", "profile", "portrait", "headshot", "gravatar",
    "logo", "favicon", "icon", "sprite", "badge", "emoji", "social", "facebook",
    "twitter", "x-logo", "instagram", "linkedin", "whatsapp", "telegram",
    "tracking", "pixel", "spacer", "advert", "banner-ad", "cookie",
)


def _int_attr(value: Any) -> int:
    try:
        match = re.search(r"\d+", str(value or ""))
        return int(match.group(0)) if match else 0
    except Exception:
        return 0


def _image_candidate_ok(url: str, width: int = 0, height: int = 0, alt: str = "") -> bool:
    value = html.unescape(str(url or "").strip())
    if not value or value.startswith(("data:", "blob:", "javascript:")):
        return False
    low = f"{value} {alt or ''}".lower()
    if any(term in low for term in BAD_IMAGE_TERMS):
        return False
    path = urllib.parse.urlparse(value).path.lower()
    if path.endswith((".svg", ".ico")):
        return False
    width = max(0, int(width or 0))
    height = max(0, int(height or 0))
    if width and height:
        if width < 300 or height < 150 or width * height < 60000:
            return False
    elif width and width < 300:
        return False
    elif height and height < 150:
        return False
    return True


def _srcset_best(value: str) -> str:
    candidates: List[Tuple[float, str]] = []
    for chunk in str(value or "").split(","):
        bit = chunk.strip()
        if not bit:
            continue
        parts = bit.split()
        url = parts[0]
        score = 1.0
        if len(parts) > 1:
            descriptor = parts[-1].lower()
            try:
                if descriptor.endswith("w"):
                    score = float(descriptor[:-1])
                elif descriptor.endswith("x"):
                    score = float(descriptor[:-1]) * 1000.0
            except Exception:
                pass
        candidates.append((score, url))
    return max(candidates, default=(0.0, ""))[1]


def _srcset_best_with_width(value: str) -> Tuple[str, int]:
    candidates: List[Tuple[float, str, int]] = []
    for chunk in str(value or "").split(","):
        bit = chunk.strip()
        if not bit:
            continue
        parts = bit.split()
        url = parts[0]
        score = 1.0
        width = 0
        if len(parts) > 1:
            descriptor = parts[-1].lower()
            try:
                if descriptor.endswith("w"):
                    width = int(float(descriptor[:-1]))
                    score = float(width)
                elif descriptor.endswith("x"):
                    score = float(descriptor[:-1]) * 1000.0
                    width = int(score)
            except Exception:
                pass
        candidates.append((score, url, width))
    _score, url, width = max(candidates, default=(0.0, "", 0), key=lambda row: row[0])
    return url, width


def _image_url_dimensions(url: str) -> Tuple[int, int]:
    value = html.unescape(str(url or ""))
    width = height = 0
    try:
        parsed = urllib.parse.urlparse(value)
        query = urllib.parse.parse_qs(parsed.query)
        for key in ("w", "width", "image_width", "maxwidth", "mw"):
            if query.get(key):
                width = max(width, _int_attr(query[key][-1]))
        for key in ("h", "height", "image_height", "maxheight", "mh"):
            if query.get(key):
                height = max(height, _int_attr(query[key][-1]))
        combined = f"{parsed.path} {parsed.query}"
        for match in re.finditer(r"(?<!\d)(\d{3,5})[xX](\d{3,5})(?!\d)", combined):
            width = max(width, int(match.group(1)))
            height = max(height, int(match.group(2)))
        # Common publisher/CDN suffixes: image.640.jpg, image.1536.webp, image.h720.jpg.
        for match in re.finditer(r"\.(\d{3,5})(?=\.(?:jpe?g|png|webp|avif)(?:$|[?#]))", parsed.path, re.I):
            width = max(width, int(match.group(1)))
        for match in re.finditer(r"\.h(\d{3,5})(?=\.(?:jpe?g|png|webp|avif)(?:$|[?#]))", parsed.path, re.I):
            height = max(height, int(match.group(1)))
    except Exception:
        pass
    return width, height


def _prefer_highres_image_url(url: str, target_width: int = 1920) -> str:
    """Upgrade only CDN transformations that have a safe, predictable original/high-res form.

    Never blindly rewrite signed CDN URLs. The IGN transform is especially important:
    its /t/ paths and .640/.960/.1200 suffixes are thumbnails while the same asset
    without the transform is the publisher original.
    """
    value = html.unescape(str(url or "").strip())
    if not value.startswith(("http://", "https://")):
        return value
    try:
        parsed = urllib.parse.urlparse(value)
        host = parsed.netloc.lower().split(":", 1)[0]
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        if host == "sm.ign.com":
            path = re.sub(r"^/t/", "/", path, flags=re.I)
            path = re.sub(r"\.(?:320|360|480|540|640|720|768|800|900|960|1024|1080|1200|1280|1440|1536|1600|1920)(?=\.(?:jpe?g|png|webp|avif)$)", "", path, flags=re.I)
            return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment))
        if host in {"i0.wp.com", "i1.wp.com", "i2.wp.com", "images.unsplash.com"}:
            current = _int_attr((query.get("w") or [""])[-1])
            if current and current < target_width:
                query["w"] = [str(target_width)]
                return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, urllib.parse.urlencode(query, doseq=True), parsed.fragment))

        # A large number of publishers use plain, unsigned width/height query
        # transforms (w=640, width=1200, etc.). Upgrade these conservatively and
        # preserve aspect ratio when a matching height is present. Signed URLs are
        # intentionally excluded because changing their query invalidates them.
        signed_terms = {"signature", "sig", "token", "expires", "policy", "key-pair-id", "x-amz-signature", "x-amz-credential"}
        if not any(str(key).lower() in signed_terms for key in query):
            width_key = next((key for key in ("w", "width", "image_width", "maxwidth", "mw") if query.get(key) and _int_attr(query[key][-1])), "")
            height_key = next((key for key in ("h", "height", "image_height", "maxheight", "mh") if query.get(key) and _int_attr(query[key][-1])), "")
            current_width = _int_attr(query[width_key][-1]) if width_key else 0
            current_height = _int_attr(query[height_key][-1]) if height_key else 0
            changed = False
            if current_width and 120 <= current_width < target_width:
                if current_height:
                    query[height_key] = [str(max(current_height, int(round(current_height * target_width / current_width))))]
                query[width_key] = [str(target_width)]
                changed = True
            resize_key = next((key for key in ("resize", "size", "dimensions") if query.get(key)), "")
            if resize_key:
                resize_value = str(query[resize_key][-1])
                match = re.fullmatch(r"(\d{2,5})[xX,](\d{2,5})", resize_value.strip())
                if match:
                    rw, rh = int(match.group(1)), int(match.group(2))
                    if 120 <= rw < target_width:
                        query[resize_key] = [f"{target_width}x{max(rh, int(round(rh * target_width / rw)))}"]
                        changed = True
            if changed:
                return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, urllib.parse.urlencode(query, doseq=True), parsed.fragment))

        # Common WordPress/generated thumbnail filename: photo-640x360.jpg. The
        # unsuffixed asset is the original upload on standard WordPress media paths.
        upgraded_path = re.sub(r"-(\d{3,5})x(\d{3,5})(?=\.(?:jpe?g|png|webp|avif)$)", "", path, flags=re.I)
        if target_width >= 1600 and upgraded_path != path and ("/uploads/" in path.lower() or "wp-content" in path.lower()):
            return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, upgraded_path, parsed.params, parsed.query, parsed.fragment))
    except Exception:
        return value
    return value


def _prefer_card_image_url(url: str, target_width: int = 960) -> str:
    """Return a bandwidth-friendly image URL for magazine cards.

    Cards never need multi-megapixel originals.  Keep IGN on its thumbnail CDN
    and request roughly 960px variants where the URL format is predictable; for
    other publishers reuse the conservative high-res normalizer with a smaller
    target.  Reader images continue to use _prefer_highres_image_url() at its
    larger default size.
    """
    value = html.unescape(str(url or "").strip())
    if not value.startswith(("http://", "https://")):
        return value
    try:
        parsed = urllib.parse.urlparse(value)
        host = parsed.netloc.lower().split(":", 1)[0]
        path = parsed.path
        if host == "sm.ign.com" and path.startswith("/t/"):
            # IGN supports numeric suffixes such as .640/.960/.1536.jpg.  Keeping
            # /t/ avoids downloading the untransformed original for every card.
            if re.search(r"\.(?:320|360|480|540|640|720|768|800|900|960|1024|1080|1200|1280|1440|1536|1600|1920)(?=\.(?:jpe?g|png|webp|avif)$)", path, re.I):
                path = re.sub(r"\.(?:320|360|480|540|640|720|768|800|900|960|1024|1080|1200|1280|1440|1536|1600|1920)(?=\.(?:jpe?g|png|webp|avif)$)", f".{int(target_width)}", path, flags=re.I)
                return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment))
            return value
    except Exception:
        return value
    return _prefer_highres_image_url(value, target_width=max(720, int(target_width or 960)))


def _image_quality_score(url: str, width: int = 0, height: int = 0) -> float:
    if not url:
        return 0.0
    hinted_w, hinted_h = _image_url_dimensions(url)
    width = max(int(width or 0), hinted_w)
    height = max(int(height or 0), hinted_h)
    if width and height:
        score = float(width * height)
    elif width:
        score = float(width * max(500, int(width * .56)))
    elif height:
        score = float(height * max(800, int(height * 1.6)))
    else:
        score = 360000.0
    low = str(url).lower()
    if any(term in low for term in ("original", "fullsize", "full-size", "hires", "high-res", "master")):
        score += 900000.0
    elif any(term in low for term in ("hero", "featured")):
        score += 180000.0
    if any(term in low for term in ("thumbnail", "thumb", "small", "tiny")):
        score *= .45
    return score


def _upgrade_picture_images(value: str) -> str:
    def replace_picture(match: re.Match) -> str:
        inner = match.group(1) or ""
        img_match = re.search(r"<img\b([^>]*)/?>", inner, re.I | re.S)
        if not img_match:
            return inner
        best_url = ""
        best_width = 0
        best_score = 0.0
        for source_match in re.finditer(r"<source\b([^>]*)/?>", inner, re.I | re.S):
            attrs = _parse_attrs(source_match.group(1))
            srcset = attrs.get("srcset") or attrs.get("data-srcset") or attrs.get("data-lazy-srcset") or ""
            candidate, candidate_width = _srcset_best_with_width(srcset)
            if not candidate:
                continue
            score = _image_quality_score(candidate, candidate_width, 0)
            if score > best_score:
                best_url, best_width, best_score = candidate, candidate_width, score
        if not best_url:
            return inner
        escaped = html.escape(best_url, quote=True)
        width_attr = f' data-news-picture-width="{best_width}"' if best_width else ""
        replacement = f'<img data-news-picture-src="{escaped}"{width_attr} {img_match.group(1)}>'
        return inner[:img_match.start()] + replacement + inner[img_match.end():]
    return re.sub(r"<picture\b[^>]*>(.*?)</picture\s*>", replace_picture, str(value or ""), flags=re.I | re.S)


def _find_html_image(value: str, base: str) -> str:
    if not value:
        return ""
    candidates: List[Tuple[float, str]] = []
    upgraded = _upgrade_picture_images(value)
    for match in re.finditer(r"<img\b([^>]*)/?>", upgraded, flags=re.I | re.S):
        attrs = _parse_attrs(match.group(1))
        srcset_url, srcset_width = _srcset_best_with_width(attrs.get("srcset") or attrs.get("data-srcset") or attrs.get("data-lazy-srcset") or "")
        src = (
            attrs.get("data-news-picture-src")
            or srcset_url
            or attrs.get("data-src")
            or attrs.get("data-lazy-src")
            or attrs.get("data-original-src")
            or attrs.get("data-original")
            or attrs.get("data-full-src")
            or attrs.get("data-fullsize")
            or attrs.get("data-hi-res-src")
            or attrs.get("data-high-res-src")
            or attrs.get("data-zoom-image")
            or attrs.get("data-image")
            or attrs.get("data-url")
            or attrs.get("src")
            or ""
        )
        if not src:
            continue
        url = _prefer_highres_image_url(_absolute(base, src))
        width = max(_int_attr(attrs.get("width")), _int_attr(attrs.get("data-news-picture-width")), srcset_width)
        height = _int_attr(attrs.get("height"))
        alt = _clean_text(attrs.get("alt", ""))
        if not _image_candidate_ok(url, width, height, alt):
            continue
        low = f"{url} {attrs.get('class', '')} {alt}".lower()
        score = _image_quality_score(url, width, height)
        if any(term in low for term in ("hero", "featured", "article", "post-image", "main-image", "lead")):
            score += 650000.0
        candidates.append((score, url))
    return max(candidates, default=(0.0, ""), key=lambda row: row[0])[1]


def _best_meta_image(head: "_HeadParser", base: str, fallback: str = "") -> str:
    definitions = [
        ("og:image", "og:image:width", "og:image:height"),
        ("og:image:url", "og:image:width", "og:image:height"),
        ("og:image:secure_url", "og:image:width", "og:image:height"),
        ("twitter:image", "twitter:image:width", "twitter:image:height"),
        ("twitter:image:src", "twitter:image:width", "twitter:image:height"),
        ("twitter:image0", "twitter:image:width", "twitter:image:height"),
        ("twitter:image1", "twitter:image:width", "twitter:image:height"),
    ]
    candidates: List[Tuple[float, str]] = []
    for key, width_key, height_key in definitions:
        raws = list(getattr(head, "meta_all", {}).get(key, [])) or ([head.meta.get(key, "")] if head.meta.get(key) else [])
        widths = list(getattr(head, "meta_all", {}).get(width_key, []))
        heights = list(getattr(head, "meta_all", {}).get(height_key, []))
        for index, raw in enumerate(raws):
            if not raw:
                continue
            url = _prefer_highres_image_url(_absolute(base, raw))
            width = _int_attr(widths[index] if index < len(widths) else (widths[0] if widths else head.meta.get(width_key)))
            height = _int_attr(heights[index] if index < len(heights) else (heights[0] if heights else head.meta.get(height_key)))
            if _image_candidate_ok(url, width, height):
                candidates.append((_image_quality_score(url, width, height), url))
    # rel=image_src and preload images are often the full-resolution hero even
    # when the first og:image is a small social thumbnail.
    for link in getattr(head, "links", []):
        if not isinstance(link, dict):
            continue
        rel = str(link.get("rel") or "").lower()
        as_type = str(link.get("as") or "").lower()
        href = str(link.get("href") or "")
        imagesrcset = str(link.get("imagesrcset") or "")
        candidate = ""
        width = 0
        if imagesrcset:
            candidate, width = _srcset_best_with_width(imagesrcset)
        if not candidate and href and ("image_src" in rel or ("preload" in rel and as_type == "image")):
            candidate = href
        if candidate:
            url = _prefer_highres_image_url(_absolute(base, candidate))
            if _image_candidate_ok(url, width, 0):
                candidates.append((_image_quality_score(url, width, 0), url))
    value = _prefer_highres_image_url(_absolute(base, fallback))
    if _image_candidate_ok(value):
        candidates.append((_image_quality_score(value), value))
    return max(candidates, default=(0.0, ""), key=lambda row: row[0])[1]

def _json_ld_objects(text: str) -> List[Dict[str, Any]]:
    raw = str(text or "")
    results: List[Dict[str, Any]] = []

    def visit(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if isinstance(node, dict):
            graph = node.get("@graph")
            if isinstance(graph, list):
                visit(graph)
            results.append(node)

    for match in re.finditer(r"<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script\s*>", raw, re.I | re.S):
        chunk = _strip_cdata(match.group(1)).strip()
        if not chunk:
            continue
        try:
            parsed = json.loads(chunk)
        except Exception:
            try:
                parsed = json.loads(re.sub(r"\s+", " ", chunk))
            except Exception:
                continue
        visit(parsed)
    return results


def _ld_type_matches(node: Dict[str, Any], names: Iterable[str]) -> bool:
    wanted = {str(name).lower() for name in names}
    raw = node.get("@type")
    values = raw if isinstance(raw, list) else [raw]
    return any(str(value or "").lower() in wanted for value in values)


def _ld_primary_article(objects: List[Dict[str, Any]]) -> Dict[str, Any]:
    for node in objects:
        if _ld_type_matches(node, {"article", "newsarticle", "reportagearticle", "blogposting"}):
            return node
    return {}


def _ld_author_name(node: Dict[str, Any]) -> str:
    author = node.get("author")
    if isinstance(author, dict):
        return _clean_text(author.get("name") or "")
    if isinstance(author, list):
        for item in author:
            if isinstance(item, dict) and _clean_text(item.get("name") or ""):
                return _clean_text(item.get("name") or "")
            if isinstance(item, str) and _clean_text(item):
                return _clean_text(item)
    if isinstance(author, str):
        return _clean_text(author)
    return ""


def _ld_image_candidates(value: Any, base: str) -> List[Tuple[float, str]]:
    results: List[Tuple[float, str]] = []
    if isinstance(value, str):
        url = _prefer_highres_image_url(_absolute(base, value))
        if _image_candidate_ok(url):
            results.append((_image_quality_score(url), url))
        return results
    if isinstance(value, list):
        for item in value:
            results.extend(_ld_image_candidates(item, base))
        return results
    if isinstance(value, dict):
        width = _int_attr(value.get("width"))
        height = _int_attr(value.get("height"))
        for key in ("url", "contentUrl", "thumbnailUrl"):
            if key not in value:
                continue
            url = _prefer_highres_image_url(_absolute(base, str(value.get(key) or "")))
            if _image_candidate_ok(url, width, height):
                results.append((_image_quality_score(url, width, height), url))
        return results
    return results


def _ld_image_url(value: Any, base: str) -> str:
    return max(_ld_image_candidates(value, base), default=(0.0, ""), key=lambda row: row[0])[1]


def _ld_best_image(objects: List[Dict[str, Any]], base: str) -> str:
    article = _ld_primary_article(objects)
    candidates: List[Tuple[float, str]] = []
    for candidate in ([article] if article else []) + objects:
        if not isinstance(candidate, dict):
            continue
        candidates.extend(_ld_image_candidates(candidate.get("image"), base))
    return max(candidates, default=(0.0, ""), key=lambda row: row[0])[1]


def _ld_article_text(node: Dict[str, Any]) -> str:
    for key in ("articleBody", "text", "description"):
        value = _clean_text(node.get(key) or "")
        if value:
            return value
    return ""


def _ld_text_blocks(text: str) -> List[Dict[str, str]]:
    raw = str(text or "").replace("\r", "\n")
    paragraphs = [re.sub(r"\s+", " ", chunk).strip() for chunk in re.split(r"\n{2,}", raw) if re.sub(r"\s+", " ", chunk).strip()]
    if len(paragraphs) <= 1:
        paragraphs = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý0-9])", re.sub(r"\s+", " ", raw)) if len(segment.strip()) >= 80]
    deduped: List[Dict[str, str]] = []
    seen: set[str] = set()
    for paragraph in paragraphs:
        cleaned = _clean_text(paragraph)
        key = cleaned.lower()
        if len(cleaned) < 45 or key in seen:
            continue
        seen.add(key)
        deduped.append({"type": "text", "text": cleaned})
    return deduped[:60]


def _script_article_text(text: str) -> str:
    raw = str(text or "")
    candidates: List[str] = []

    def visit(node: Any, depth: int = 0) -> None:
        if depth > 16:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                low = str(key).lower().replace("_", "")
                if isinstance(value, str) and low in {"articlebody", "bodytext", "body", "contenttext", "articletext"}:
                    cleaned = _clean_text(value)
                    if 300 <= len(cleaned) <= 120000:
                        candidates.append(cleaned)
                elif isinstance(value, (dict, list)):
                    visit(value, depth + 1)
        elif isinstance(node, list):
            for value in node[:1200]:
                visit(value, depth + 1)

    for match in re.finditer(r"<script\b([^>]*)>(.*?)</script\s*>", raw, re.I | re.S):
        attrs = _parse_attrs(match.group(1))
        script_id = str(attrs.get("id") or "").lower()
        script_type = str(attrs.get("type") or "").lower()
        if script_id != "__next_data__" and "json" not in script_type:
            continue
        chunk = _strip_cdata(match.group(2)).strip()
        if not chunk or len(chunk) > 4_000_000:
            continue
        try:
            visit(json.loads(chunk))
        except Exception:
            continue

    # Some publishers expose articleBody inside a JS assignment rather than a
    # valid application/json block. Decode only the targeted string value.
    for match in re.finditer(r'["\'](?:articleBody|article_body|bodyText|articleText)["\']\s*:\s*("(?:\\.|[^"\\])*")', raw, re.I | re.S):
        try:
            value = json.loads(match.group(1))
            cleaned = _clean_text(value)
            if 300 <= len(cleaned) <= 120000:
                candidates.append(cleaned)
        except Exception:
            continue
    return max(candidates, key=len, default="")


def _extract_amp_url(head: "_HeadParser", base: str) -> str:
    for link in head.links:
        rel = str(link.get("rel") or "").lower()
        href = str(link.get("href") or "")
        if href and "amphtml" in rel:
            return _absolute(base, href)
    return ""


def _infer_tab_category(tab_id: str, name: str, explicit: str = "") -> str:
    value = str(explicit or "").strip().lower()
    if value:
        return PRESET_CATEGORY_ALIASES.get(value, value)
    candidates = [str(tab_id or "").lower().replace("preset-", ""), _clean_text(name).lower()]
    for candidate in candidates:
        if candidate in PRESET_CATEGORY_ALIASES:
            return PRESET_CATEGORY_ALIASES[candidate]
    return ""


def _topic_keyword_match(text: str, keyword: str) -> bool:
    value = str(keyword or "").strip().lower()
    if not value:
        return False
    # Multi-word phrases and deliberately padded tokens use substring matching.
    if " " in value or any(ch in value for ch in "+-'’"):
        return value.strip() in text
    return re.search(rf"(?<![\w]){re.escape(value)}(?![\w])", text, re.I) is not None


def _categorize_item(title: str, excerpt: str = "", url: str = "", feed_labels: Optional[Iterable[str]] = None) -> List[str]:
    """Very high precision ARTICLE classifier.

    A wrong category is worse than no category. Only strong article-level
    evidence can place a story outside ``all``. Generic publisher labels,
    broad context words and ambiguous title words are supporting signals only.
    """
    title_text = _clean_text(title).lower()
    body_text = _clean_text(excerpt).lower()[:1600]
    url_text = urllib.parse.unquote(str(url or "")).lower()
    labels = [_clean_text(value).lower() for value in (feed_labels or []) if _clean_text(value)]

    scores: Dict[str, int] = {}
    explicit_hits: Dict[str, int] = {}
    strong_title_hits: Dict[str, int] = {}
    weak_title_hits: Dict[str, int] = {}
    body_hits: Dict[str, int] = {}

    def add(category: str, score: int, bucket: Optional[Dict[str, int]] = None) -> None:
        if not category or category == "all":
            return
        scores[category] = scores.get(category, 0) + score
        if bucket is not None:
            bucket[category] = bucket.get(category, 0) + 1

    ignored_labels = {
        "all", "tutte", "italia", "italy", "world", "mondo", "esteri", "news",
        "breaking news", "latest", "homepage", "home", "top news", "general",
    }

    # Publisher-provided per-item section/category is the strongest evidence,
    # but only for an exact known topic label. Never infer from publisher name.
    for label in labels:
        normalized = re.sub(r"[^a-zà-ÿ0-9]+", " ", label).strip()
        if not normalized or normalized in ignored_labels:
            continue
        words = set(normalized.split())
        for alias, category in CATEGORY_LABEL_ALIASES.items():
            alias_norm = re.sub(r"[^a-zà-ÿ0-9]+", " ", str(alias).lower()).strip()
            if not alias_norm or alias_norm in ignored_labels:
                continue
            if normalized == alias_norm or (" " not in alias_norm and alias_norm in words and len(words) <= 3):
                # Generic RSS buckets such as Business/Technology/Entertainment
                # are often publisher-wide umbrellas rather than the article's
                # real subject. A strong title signal must be able to override
                # them (PS5 -> Games, Formula 1 -> Sports, etc.). Narrow labels
                # such as Economia, Calcio or Scienza remain authoritative.
                label_score = 18 if alias_norm in BROAD_FEED_TOPIC_LABELS else 42
                add(category, label_score, explicit_hits)

    # A real topic section in the article URL is also authoritative.
    for alias, category in CATEGORY_LABEL_ALIASES.items():
        alias_norm = str(alias).strip().lower()
        if alias_norm in ignored_labels or len(alias_norm) < 4:
            continue
        if re.search(rf"(?:^|[/_-]){re.escape(alias_norm)}(?:[/_.?&#-]|$)", url_text):
            add(category, 36, explicit_hits)

    # Strong named entities / phrases in the TITLE are reliable. The same words
    # in an RSS excerpt are only a weak supporting hint because summaries often
    # mention adjacent topics.
    for category, keywords in CATEGORY_STRONG_KEYWORDS.items():
        for keyword in keywords:
            if _topic_keyword_match(title_text, keyword):
                add(category, 24, strong_title_hits)
            elif _topic_keyword_match(body_text, keyword):
                add(category, 2, body_hits)

    # Broad keywords can break ties but are not allowed to create a category.
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if _topic_keyword_match(title_text, keyword):
                add(category, 3, weak_title_hits)
            elif _topic_keyword_match(body_text, keyword):
                body_hits[category] = body_hits.get(category, 0) + 1
                if body_hits[category] >= 3:
                    add(category, 1)

    # Weather stories often contain football-club names purely as geography
    # ("Meteo Napoli", "Roma e Lazio", ...). Suppress Sport unless the title
    # contains an unambiguous sports context as well. This is deliberately a
    # narrow negative guard: a weather story about Formula 1 still classifies
    # as Sport because "formula 1" is explicit sports evidence.
    if any(_topic_keyword_match(title_text, keyword) for keyword in WEATHER_TITLE_KEYWORDS):
        has_real_sports_context = any(_topic_keyword_match(title_text, keyword) for keyword in SPORTS_CONTEXT_KEYWORDS)
        if not has_real_sports_context:
            scores.pop("sports", None)
            explicit_hits.pop("sports", None)
            strong_title_hits.pop("sports", None)
            weak_title_hits.pop("sports", None)
            body_hits.pop("sports", None)

    # Strong subject evidence beats incidental politics/tech context.
    subject_categories = (
        "sports", "games", "cinema", "music", "comics", "art", "food", "travel",
        "economy", "fashion", "science", "health", "tech",
    )
    for category in subject_categories:
        if explicit_hits.get(category, 0) or strong_title_hits.get(category, 0):
            subject_score = scores.get(category, 0)
            for generic in ("politics",):
                if scores.get(generic, 0) < subject_score + 16 and explicit_hits.get(generic, 0) == 0:
                    scores[generic] = max(0, scores.get(generic, 0) - 20)

    ranked = sorted(
        ((category, score) for category, score in scores.items() if score > 0),
        key=lambda pair: (
            pair[1],
            explicit_hits.get(pair[0], 0),
            strong_title_hits.get(pair[0], 0),
        ),
        reverse=True,
    )
    if not ranked:
        return []

    top_category, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0
    hard_evidence = explicit_hits.get(top_category, 0) + strong_title_hits.get(top_category, 0)

    # A generic title word like "president", "market", "series", "final" or
    # "team" can never file a story by itself.
    if hard_evidence == 0:
        return []
    if top_score < 22:
        return []

    # Politics is especially prone to false positives (presidents/ministers are
    # mentioned in sport, culture, business and science reporting). If another
    # subject has multiple title signals but politics has no explicit publisher
    # section, leave the story only in Tutte rather than misfile it.
    if top_category == "politics" and explicit_hits.get("politics", 0) == 0:
        for subject in ("sports", "games", "cinema", "music", "comics", "art", "food", "travel", "economy", "fashion", "science", "health", "tech"):
            if strong_title_hits.get(subject, 0) >= 1 or weak_title_hits.get(subject, 0) >= 2:
                return []

    # If two topics remain close and neither has an explicit section label, do
    # not guess: leave the story only in "Tutte".
    if second_score and top_score - second_score < 10 and explicit_hits.get(top_category, 0) == 0:
        second_category = ranked[1][0]
        if strong_title_hits.get(top_category, 0) <= strong_title_hits.get(second_category, 0):
            return []
    return [top_category]


def _is_google_news_url(url: str) -> bool:
    try:
        host = urllib.parse.urlparse(str(url or "")).netloc.lower()
        return host == "news.google.com" or host.endswith(".news.google.com")
    except Exception:
        return False


def _unwrap_bing_news_url(url: str) -> str:
    """Return the publisher URL carried by a Bing News result redirect."""
    value = html.unescape(str(url or "").strip())
    if not value:
        return ""
    try:
        parsed = urllib.parse.urlparse(value)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        if host == "bing.com" or host.endswith(".bing.com"):
            query = urllib.parse.parse_qs(parsed.query)
            for key in ("url", "u", "target"):
                values = query.get(key) or []
                for raw in values:
                    candidate = urllib.parse.unquote(html.unescape(str(raw or ""))).strip()
                    if candidate.startswith(("http://", "https://")):
                        return candidate
                    # Ordinary Bing result redirects may encode the destination in
                    # the `u` parameter as a1 + URL-safe base64. This is still a
                    # deterministic unwrap of the result itself, not page scraping.
                    if key == "u" and candidate.startswith("a1"):
                        try:
                            token = candidate[2:]
                            token += "=" * ((4 - len(token) % 4) % 4)
                            decoded = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8", "replace").strip()
                            if decoded.startswith(("http://", "https://")):
                                return decoded
                        except Exception:
                            pass
        return value
    except Exception:
        return value


def _decode_google_news_legacy(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        token = parsed.path.rstrip("/").split("/")[-1]
        if not token:
            return ""
        padded = token + "=" * ((4 - len(token) % 4) % 4)
        data = base64.urlsafe_b64decode(padded.encode("ascii"))
        prefix = bytes([0x08, 0x13, 0x22])
        suffix = bytes([0xD2, 0x01, 0x00])
        if data.startswith(prefix):
            data = data[len(prefix):]
        if data.endswith(suffix):
            data = data[:-len(suffix)]
        if not data:
            return ""
        first = data[0]
        offset = 1
        if first >= 0x80 and len(data) > 1:
            length = (first & 0x7F) | (data[1] << 7)
            offset = 2
        else:
            length = first
        candidate = data[offset:offset + length].decode("utf-8", "ignore").strip()
        return candidate if candidate.startswith(("http://", "https://")) else ""
    except Exception:
        return ""


def _extract_google_decode_params(html_text: str) -> Tuple[str, str, str]:
    source_id = ""
    signature = ""
    timestamp = ""
    for pattern in [r'data-n-a-id=["\']([^"\']+)', r'"source"\s*:\s*"([^"]+)"']:
        match = re.search(pattern, html_text, re.I)
        if match:
            source_id = match.group(1)
            break
    for pattern in [r'data-n-a-sg=["\']([^"\']+)', r'"signature"\s*:\s*"([^"]+)"']:
        match = re.search(pattern, html_text, re.I)
        if match:
            signature = match.group(1)
            break
    for pattern in [r'data-n-a-ts=["\']([^"\']+)', r'"timestamp"\s*:\s*"?([0-9]+)']:
        match = re.search(pattern, html_text, re.I)
        if match:
            timestamp = match.group(1)
            break
    return source_id, signature, timestamp


def _extract_google_data_p_request(html_text: str) -> Optional[Any]:
    """Extract Google's alternate c-wiz data-p garturlreq payload.

    Some brand-new Google News wrappers temporarily expose data-p before the
    data-n-a-sg/data-n-a-ts attributes used by the normal decoder. This fallback
    mirrors the currently documented browser request shape without depending on
    BeautifulSoup/selectolax, which are not guaranteed in Decky's Python runtime.
    """
    match = re.search(r'<c-wiz\b[^>]*\bdata-p=(?:"([^"]+)"|\'([^\']+)\')', html_text, re.I | re.S)
    if not match:
        return None
    raw = html.unescape(match.group(1) or match.group(2) or "").strip()
    if not raw:
        return None
    try:
        if "%.@." in raw:
            parsed = json.loads(raw.replace("%.@.", '["garturlreq",', 1))
        else:
            parsed = json.loads(raw)
    except Exception:
        return None
    if not isinstance(parsed, list):
        return None
    # Google's data-p object contains six UI-only tail values before the two
    # decoder values. The Fbv4je request omits those fields.
    if len(parsed) >= 8:
        compact = parsed[:-6] + parsed[-2:]
        return compact if compact else None
    return parsed


def _social_embed_for_url(url: str) -> Optional[Dict[str, str]]:
    value = html.unescape(str(url or "")).strip().rstrip(".,);]}")
    if not value.startswith(("http://", "https://")):
        return None
    try:
        parsed = urllib.parse.urlparse(value)
        host = parsed.netloc.lower().split(":")[0]
        path = parsed.path
        if host.startswith("www."):
            host = host[4:]
        youtube = _youtube_embed(value)
        if youtube:
            return {"type": "embed", "provider": "youtube", "url": value, "embedUrl": youtube, "title": "Video YouTube"}
        if host in {"twitter.com", "x.com", "mobile.twitter.com"}:
            match = re.search(r"/status/(\d+)", path)
            if match:
                tweet_id = match.group(1)
                return {"type": "embed", "provider": "x", "url": value, "embedUrl": f"https://platform.twitter.com/embed/Tweet.html?id={tweet_id}&dnt=true", "title": "Post su X"}
        if host.endswith("instagram.com"):
            match = re.search(r"/(p|reel|tv)/([A-Za-z0-9_-]+)", path)
            if match:
                kind, shortcode = match.groups()
                return {"type": "embed", "provider": "instagram", "url": value, "embedUrl": f"https://www.instagram.com/{kind}/{shortcode}/embed/", "title": "Post Instagram"}
        if host.endswith("tiktok.com"):
            match = re.search(r"/video/(\d+)", path)
            if match:
                video_id = match.group(1)
                return {"type": "embed", "provider": "tiktok", "url": value, "embedUrl": f"https://www.tiktok.com/player/v1/{video_id}?autoplay=0&controls=0&music_info=1&description=1&native_context_menu=0", "title": "Video TikTok"}
        if host in {"facebook.com", "m.facebook.com", "www.facebook.com"} or host.endswith(".facebook.com"):
            if any(bit in path for bit in ("/posts/", "/videos/", "/reel/", "/permalink.php")) or "story_fbid=" in parsed.query:
                encoded = urllib.parse.quote(value, safe="")
                return {"type": "embed", "provider": "facebook", "url": value, "embedUrl": f"https://www.facebook.com/plugins/post.php?href={encoded}&show_text=true&width=500", "title": "Post Facebook"}
    except Exception:
        return None
    return None


def _social_embeds_from_region(region: str) -> List[Dict[str, str]]:
    found: List[Dict[str, str]] = []
    seen: set[str] = set()
    for match in re.finditer(r"<a\b([^>]*)>", str(region or ""), re.I | re.S):
        attrs = _parse_attrs(match.group(1))
        href = attrs.get("href", "")
        embed = _social_embed_for_url(href)
        if not embed:
            continue
        key = f"{embed.get('provider')}:{embed.get('url')}"
        if key in seen:
            continue
        seen.add(key)
        found.append(embed)
        if len(found) >= 12:
            break
    return found



def _markdown_clean_text(value: str) -> str:
    text = str(value or "")
    text = re.sub(r"!\[[^\]]*\]\([^\)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"<https?://[^>]+>", " ", text)
    text = re.sub(r"[*_`~]+", "", text)
    return _clean_text(text)


def _markdown_to_reader_blocks(markdown: str, base_url: str) -> Tuple[List[Dict[str, str]], str]:
    """Convert Jina Reader markdown to our native reader blocks."""
    raw = str(markdown or "").replace("\r\n", "\n")
    blocks: List[Dict[str, str]] = []
    seen: set[str] = set()
    hero = ""
    paragraph: List[str] = []

    def append_block(block: Dict[str, str]) -> None:
        nonlocal hero
        if block.get("type") == "image":
            url = str(block.get("url") or "")
            key = f"img:{url}"
            if not url or key in seen or not _image_candidate_ok(url, alt=str(block.get("alt") or "")):
                return
            seen.add(key)
            if not hero:
                hero = url
            blocks.append(block)
            return
        if block.get("type") == "embed":
            key = f"embed:{block.get('provider')}:{block.get('url')}"
            if key in seen:
                return
            seen.add(key)
            blocks.append(block)
            return
        value = _clean_text(block.get("text") or "")
        if len(value) < (4 if block.get("type") == "heading" else 20):
            return
        key = f"txt:{value.lower()}"
        if key in seen:
            return
        seen.add(key)
        blocks.append({**block, "text": value})

    def flush_paragraph() -> None:
        if not paragraph:
            return
        value = _markdown_clean_text(" ".join(paragraph))
        paragraph.clear()
        if value:
            append_block({"type": "text", "text": value})

    for line in raw.split("\n"):
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            continue
        # Images can coexist with text on the same markdown line.
        image_matches = list(re.finditer(r"!\[([^\]]*)\]\((https?://[^\s\)]+)(?:\s+[^\)]*)?\)", stripped, re.I))
        for match in image_matches:
            flush_paragraph()
            append_block({"type": "image", "url": _absolute(base_url, match.group(2)), "alt": _clean_text(match.group(1))})
        links = re.findall(r"\[[^\]]*\]\((https?://[^\s\)]+)\)|(?<!\()(?<!\[)(https?://[^\s<>\)]+)", stripped, re.I)
        for pair in links:
            link = next((value for value in pair if value), "")
            embed = _social_embed_for_url(link)
            if embed:
                flush_paragraph()
                append_block(embed)
        without_images = re.sub(r"!\[[^\]]*\]\([^\)]+\)", " ", stripped).strip()
        if not without_images:
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", without_images)
        if heading:
            flush_paragraph()
            append_block({"type": "heading", "text": _markdown_clean_text(heading.group(2))})
            continue
        if without_images.startswith(">"):
            flush_paragraph()
            append_block({"type": "quote", "text": _markdown_clean_text(without_images.lstrip("> "))})
            continue
        # Ignore obvious navigation/table noise from markdown conversion.
        low = without_images.lower()
        if low in {"menu", "search", "home", "advertisement", "pubblicità", "privacy", "cookie"}:
            continue
        if re.fullmatch(r"[-*_]{3,}", without_images):
            flush_paragraph()
            continue
        paragraph.append(without_images)
    flush_paragraph()
    return blocks[:260], hero


def _reader_text_length(blocks: Iterable[Dict[str, Any]]) -> int:
    return len(" ".join(str(block.get("text") or "") for block in blocks if isinstance(block, dict) and block.get("type") in {"text", "heading", "quote"}))


def _dedupe_article_blocks(blocks: List[Dict[str, str]], title: str, description: str) -> List[Dict[str, str]]:
    result: List[Dict[str, str]] = []
    seen_text: List[str] = []
    title_norm = _clean_text(title).lower()
    desc_norm = _clean_text(description).lower()
    boilerplate = (
        "continua a leggere", "leggi anche", "potrebbe interessarti", "articoli correlati", "related articles",
        "read more", "also read", "iscriviti alla newsletter", "subscribe to our newsletter", "newsletter",
        "accetta tutti i cookie", "gestisci le preferenze", "privacy policy", "cookie policy", "condividi su",
        "follow us", "seguici su", "advertisement", "pubblicità", "all rights reserved",
    )
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") in {"text", "heading", "quote"}:
            value = _clean_text(block.get("text") or "")
            # Some publishers leak serialized JSON-LD/Next state after legitimate
            # prose. Trim that tail rather than printing schema keys in the Reader.
            pollution_markers = (
                '"articlesection"', '"@type"', '"wordcount"', '"creator"', '"imageobject"',
                'schema.org', '__next_data__', '"datepublished"', '"datecreated"', '"contenturl"',
            )
            lower_value = value.lower()
            cuts = [lower_value.find(marker) for marker in pollution_markers if lower_value.find(marker) >= 0]
            if cuts:
                cut = min(cuts)
                if cut < 40:
                    continue
                value = value[:cut].rstrip(' ,;:{[\"')
            low = value.lower().strip()
            if not value:
                continue
            if len(value) < 260 and any(low == phrase or low.startswith(phrase + " ") for phrase in boilerplate):
                continue
            if len(value) < 180 and any(phrase in low for phrase in boilerplate):
                continue
            if len(value) < 360 and desc_norm and (low == desc_norm or desc_norm.startswith(low) or low.startswith(desc_norm)):
                continue
            if len(value) < 300 and title_norm and (low == title_norm or title_norm.startswith(low) or low.startswith(title_norm)):
                continue
            # Drop truncated/repeated neighboring fragments. This catches pages
            # that expose the same title/deck several times with slightly different truncation.
            duplicate = False
            for prior in seen_text[-14:]:
                shorter, longer = (low, prior) if len(low) <= len(prior) else (prior, low)
                if shorter == longer or (len(shorter) >= 42 and longer.startswith(shorter)):
                    duplicate = True
                    break
                if len(shorter) >= 80:
                    words = set(shorter.split())
                    other = set(longer.split())
                    if words and len(words & other) / max(1, len(words)) > .88:
                        duplicate = True
                        break
            if duplicate:
                continue
            seen_text.append(low)
            result.append({**block, "text": value})
        else:
            result.append(block)
    return result[:260]

def _google_news_params(country: str) -> Tuple[str, str, str]:
    code = str(country or "IT").upper()
    language = COUNTRY_LANGUAGE.get(code, "en")
    hl = f"{language}-{code}" if len(language) == 2 else language
    return code, language, hl


def _google_news_top_feed(country: str) -> str:
    code, language, hl = _google_news_params(country)
    params = urllib.parse.urlencode({"hl": hl, "gl": code, "ceid": f"{code}:{language}"})
    return f"https://news.google.com/rss?{params}"


def _google_news_site_feed(site_url: str, country: str) -> str:
    parsed = urllib.parse.urlparse(str(site_url or ""))
    domain = parsed.netloc.lower().split("@")[-1].split(":")[0]
    if domain.startswith("www."):
        domain = domain[4:]
    if not domain:
        return ""
    code, language, hl = _google_news_params(country)
    params = urllib.parse.urlencode({"q": f"site:{domain} when:30d", "hl": hl, "gl": code, "ceid": f"{code}:{language}"})
    return f"https://news.google.com/rss/search?{params}"


def _canonical_favicon_domain(site_url: str) -> str:
    host = _hostname(site_url)
    if host == "ign.com" or host.endswith(".ign.com"):
        return "ign.com"
    return host


def _favicon_asset_filename(site_url: str) -> str:
    host = _canonical_favicon_domain(site_url)
    if host == "news.google.com":
        return "google-news.png"
    return (re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-") or "news") + ".png"


def _brand_asset_defaults(site_url: str) -> Dict[str, str]:
    value = str(site_url or "").strip()
    if not value:
        return {"faviconUrl": "", "logoUrl": "", "brandColor": ""}
    domain = _canonical_favicon_domain(value)
    if not domain:
        return {"faviconUrl": "", "logoUrl": "", "brandColor": ""}
    # Remote favicon remains non-blocking in the frontend. favicon.im is asked for
    # its largest available version so tiny 16x16 icons are not stretched in QAM.
    # Every predefined source also gets a bundled 256px fallback via logoUrl.
    icon = f"https://a.favicon.im/{domain}?larger=true&throw-error-on-404=true"
    return {"faviconUrl": icon, "logoUrl": f"asset://favicons/{_favicon_asset_filename(value)}", "brandColor": ""}


def _hostname(value: str) -> str:
    try:
        host = urllib.parse.urlparse(str(value or "")).netloc.lower().split("@")[-1].split(":")[0]
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def _normalized_article_url(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = urllib.parse.urlparse(raw)
        scheme = parsed.scheme.lower() or "https"
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        path = re.sub(r"/+", "/", parsed.path or "/").rstrip("/") or "/"
        return urllib.parse.urlunparse((scheme, host, path, "", "", ""))
    except Exception:
        return raw.split("#", 1)[0].split("?", 1)[0].rstrip("/")


def _host_matches(candidate_url: str, expected_site: str) -> bool:
    expected = _hostname(expected_site)
    candidate = _hostname(candidate_url)
    if not expected or not candidate:
        return False
    return candidate == expected or candidate.endswith("." + expected) or expected.endswith("." + candidate)


def _youtube_embed(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        video_id = ""
        if "youtu.be" in host:
            video_id = parsed.path.strip("/").split("/")[0]
        elif "youtube.com" in host:
            if parsed.path.startswith("/watch"):
                video_id = urllib.parse.parse_qs(parsed.query).get("v", [""])[0]
            elif parsed.path.startswith("/shorts/") or parsed.path.startswith("/embed/"):
                video_id = parsed.path.strip("/").split("/")[1]
        if re.fullmatch(r"[A-Za-z0-9_-]{6,20}", video_id or ""):
            return f"https://www.youtube.com/embed/{video_id}?enablejsapi=1&autoplay=0&rel=0&playsinline=1&controls=0"
    except Exception:
        pass
    return ""


class _HeadParser:
    def __init__(self) -> None:
        self.title = ""
        self.links: List[Dict[str, str]] = []
        self.meta: Dict[str, str] = {}
        self.meta_all: Dict[str, List[str]] = {}

    def feed(self, text: str) -> None:
        raw = str(text or "")
        title_match = re.search(r"<title\b[^>]*>(.*?)</title\s*>", raw, re.I | re.S)
        if title_match:
            self.title = _clean_text(title_match.group(1))
        for match in re.finditer(r"<link\b([^>]*)/?>", raw, re.I | re.S):
            self.links.append(_parse_attrs(match.group(1)))
        for match in re.finditer(r"<meta\b([^>]*)/?>", raw, re.I | re.S):
            data = _parse_attrs(match.group(1))
            key = (data.get("property") or data.get("name") or "").lower()
            value = data.get("content", "")
            if key and value:
                self.meta_all.setdefault(key, []).append(value)
                if key not in self.meta:
                    self.meta[key] = value


class _ReaderParser:
    IGNORE_TAGS = {"script", "style", "nav", "footer", "form", "svg", "noscript", "aside", "button"}

    def __init__(self, base_url: str, prefer_article: bool, prefer_main: bool) -> None:
        self.base_url = base_url
        self.prefer_article = prefer_article
        self.prefer_main = prefer_main
        self.blocks: List[Dict[str, str]] = []
        self.seen: set[str] = set()

    def _append_embed(self, embed: Dict[str, str]) -> None:
        key = f"embed:{embed.get('provider')}:{embed.get('url')}"
        if key in self.seen:
            return
        self.seen.add(key)
        self.blocks.append(embed)

    def feed(self, text: str) -> None:
        raw = str(text or "")
        region = raw
        if self.prefer_article:
            match = re.search(r"<article\b[^>]*>(.*?)</article\s*>", raw, re.I | re.S)
            if match:
                region = match.group(1)
        elif self.prefer_main:
            match = re.search(r"<main\b[^>]*>(.*?)</main\s*>", raw, re.I | re.S)
            if match:
                region = match.group(1)

        for tag in self.IGNORE_TAGS:
            region = re.sub(rf"<{tag}\b[^>]*>.*?</{tag}\s*>", " ", region, flags=re.I | re.S)
        region = _upgrade_picture_images(region)

        token = re.compile(
            r"<(p|h1|h2|h3|h4|blockquote|pre)\b[^>]*>(.*?)</\1\s*>|<img\b([^>]*)/?>|<a\b([^>]*)>(.*?)</a>",
            re.I | re.S,
        )
        for match in token.finditer(region):
            tag = (match.group(1) or "").lower()
            if tag:
                inner = match.group(2) or ""
                embeds = _social_embeds_from_region(inner)
                value = _clean_text(inner)
                block_type = "heading" if tag.startswith("h") else "quote" if tag == "blockquote" else "text"
                minimum = 4 if block_type == "heading" else 18
                # Embedded social posts already contain their own quote/caption.
                # Avoid showing the same tweet/post as a giant text quote and then
                # duplicating it again in the preview.
                keep_text = not (embeds and block_type == "quote")
                key = f"txt:{value.lower()}"
                if keep_text and len(value) >= minimum and key not in self.seen:
                    self.seen.add(key)
                    self.blocks.append({"type": block_type, "text": value})
                for embed in embeds:
                    if embed.get("provider") == "x" and value:
                        embed = {**embed, "text": value[:1800]}
                    self._append_embed(embed)
                continue

            if match.group(3) is not None:
                attrs = _parse_attrs(match.group(3) or "")
                srcset_url, srcset_width = _srcset_best_with_width(attrs.get("srcset") or attrs.get("data-srcset") or attrs.get("data-lazy-srcset") or "")
                src = (
                    attrs.get("data-news-picture-src")
                    or srcset_url
                    or attrs.get("data-src")
                    or attrs.get("data-lazy-src")
                    or attrs.get("data-original-src")
                    or attrs.get("data-original")
                    or attrs.get("data-full-src")
                    or attrs.get("data-fullsize")
                    or attrs.get("data-hi-res-src")
                    or attrs.get("data-high-res-src")
                    or attrs.get("data-zoom-image")
                    or attrs.get("data-image")
                    or attrs.get("data-url")
                    or attrs.get("src")
                    or ""
                )
                if src:
                    url = _prefer_highres_image_url(_absolute(self.base_url, src))
                    alt = _clean_text(attrs.get("alt", ""))
                    width = max(_int_attr(attrs.get("width")), _int_attr(attrs.get("data-news-picture-width")), srcset_width)
                    height = _int_attr(attrs.get("height"))
                    key = f"img:{url}"
                    if url and key not in self.seen and _image_candidate_ok(url, width, height, alt):
                        self.seen.add(key)
                        self.blocks.append({"type": "image", "url": url, "alt": alt})
                continue

            attrs = _parse_attrs(match.group(4) or "")
            embed = _social_embed_for_url(attrs.get("href", ""))
            if embed:
                self._append_embed(embed)

def _default_config() -> Dict[str, Any]:
    return {
        "version": 1,
        "onboardingComplete": False,
        "country": "IT",
        "language": "it-IT",
        "refreshMinutes": 15,
        "sources": [],
        "tabs": [],
        "activeTabId": "",
    }


class NewsImageCacheServer:
    """Small, bounded loopback image server for Decky's bundled Python runtime.

    Some Windows loader builds omit http.server/socketserver/mimetypes. Use the
    socket/threading primitives already needed by Decky instead of importing
    these optional modules, adding a dependency or modifying the loader.
    Only immutable, validated cache image names are exposed; never a directory.
    """

    MIME_TYPES = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                  "webp": "image/webp", "gif": "image/gif", "avif": "image/avif"}
    MAX_CLIENTS = 12
    MAX_HEADERS = 16 * 1024
    CLIENT_TIMEOUT = 4.0

    def __init__(self, root: Path, log) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._log = log
        self.token = secrets.token_hex(16)
        self.port = 0
        self._server = None
        self._thread = None
        self._pool = None
        self._stopping = threading.Event()
        self._clients = set()
        self._clients_lock = threading.Lock()
        self._slots = threading.BoundedSemaphore(self.MAX_CLIENTS)

    def start(self) -> None:
        if self._server is not None:
            return
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        pool = None
        try:
            server.bind(("127.0.0.1", 0))
            server.listen(self.MAX_CLIENTS)
            server.settimeout(0.2)
            pool = ThreadPoolExecutor(max_workers=self.MAX_CLIENTS,
                                      thread_name_prefix="NewsImageHTTP")
            self._stopping.clear()
            self._pool = pool
            self._server = server
            self.port = int(server.getsockname()[1])
            self._thread = threading.Thread(target=self._accept, args=(server, pool),
                                            name="News-ImageCache", daemon=True)
            self._thread.start()
        except Exception:
            server.close()
            if pool is not None:
                pool.shutdown(wait=False, cancel_futures=True)
            self._server = self._pool = self._thread = None
            self.port = 0
            raise
        self._log(f"image cache ready on 127.0.0.1:{self.port}")

    def _accept(self, server, pool) -> None:
        while not self._stopping.is_set():
            try:
                client, _address = server.accept()
            except socket.timeout:
                continue
            except OSError:
                if not self._stopping.is_set():
                    self._log("image cache listener closed unexpectedly")
                break
            if self._stopping.is_set() or not self._slots.acquire(blocking=False):
                client.close()
                continue
            with self._clients_lock:
                self._clients.add(client)
            try:
                pool.submit(self._serve, client)
            except RuntimeError:
                self._release_client(client)

    def _release_client(self, client) -> None:
        try:
            client.close()
        finally:
            with self._clients_lock:
                self._clients.discard(client)
            self._slots.release()

    @staticmethod
    def _headers(client, status: int, length: int = 0, mime: str = "text/plain",
                 cache: bool = False, extra: str = "") -> None:
        reason = {200: "OK", 204: "No Content", 400: "Bad Request", 404: "Not Found",
                  405: "Method Not Allowed", 431: "Request Header Fields Too Large"}[status]
        headers = (f"HTTP/1.1 {status} {reason}\r\n"
                   f"Content-Type: {mime}\r\nContent-Length: {length}\r\n"
                   "Connection: close\r\nAccess-Control-Allow-Origin: *\r\n"
                   "Cross-Origin-Resource-Policy: cross-origin\r\n"
                   "X-Content-Type-Options: nosniff\r\n"
                   + ("Cache-Control: public, max-age=604800, immutable\r\n" if cache
                      else "Cache-Control: no-store\r\n") + extra + "\r\n")
        client.sendall(headers.encode("ascii"))

    def _serve(self, client) -> None:
        try:
            client.settimeout(self.CLIENT_TIMEOUT)
            request = bytearray()
            deadline = time.monotonic() + self.CLIENT_TIMEOUT
            while b"\r\n\r\n" not in request:
                if len(request) >= self.MAX_HEADERS:
                    self._headers(client, 431)
                    return
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return
                client.settimeout(remaining)
                chunk = client.recv(min(4096, self.MAX_HEADERS - len(request)))
                if not chunk:
                    return
                request.extend(chunk)
            client.settimeout(self.CLIENT_TIMEOUT)
            line = bytes(request).split(b"\r\n", 1)[0].decode("ascii", "strict")
            parts = line.split(" ")
            if len(parts) != 3 or parts[2] not in ("HTTP/1.0", "HTTP/1.1"):
                self._headers(client, 400)
                return
            method, target, _version = parts
            if method not in ("GET", "HEAD", "OPTIONS"):
                self._headers(client, 405, extra="Allow: GET, HEAD, OPTIONS\r\n")
                return
            # Accept origin-form only. Do not act as a proxy, serve arbitrary
            # paths, decode slash escapes into a filesystem path or follow links
            # outside the cache directory.
            prefix = f"/{self.token}/image/"
            target_path = target.split("?", 1)[0]
            if not target_path.startswith(prefix):
                self._headers(client, 404)
                return
            name = urllib.parse.unquote(target_path[len(prefix):])
            if not re.fullmatch(r"(?:[A-Fa-f0-9]{40}\.(?:jpg|jpeg|png|webp|gif|avif)|asset-[a-z0-9][a-z0-9-]*\.png)", name):
                self._headers(client, 404)
                return
            path = (self.root / name).resolve()
            if self.root.resolve() not in path.parents or not path.is_file():
                self._headers(client, 404)
                return
            if method == "OPTIONS":
                self._headers(client, 204, extra="Access-Control-Allow-Methods: GET, HEAD, OPTIONS\r\n"
                              "Access-Control-Allow-Headers: Content-Type\r\n"
                              "Access-Control-Max-Age: 600\r\n")
                return
            try:
                handle = path.open("rb")
            except (FileNotFoundError, PermissionError):
                self._headers(client, 404)
                return
            with handle:
                size = os.fstat(handle.fileno()).st_size
                if size > MAX_IMAGE_BYTES:
                    self._headers(client, 404)
                    return
                mime = self.MIME_TYPES.get(path.suffix[1:].lower(), "image/jpeg")
                self._headers(client, 200, size, mime, cache=True)
                if method == "GET":
                    while not self._stopping.is_set():
                        chunk = handle.read(128 * 1024)
                        if not chunk:
                            break
                        client.sendall(chunk)
        except (ConnectionError, socket.timeout, OSError):
            # The browser routinely cancels artwork loads during navigation and
            # plugin reloads (including Windows WinError 64/10054). These are
            # local image connections, NOT Decky's RPC socket.
            return
        except (UnicodeError, ValueError):
            try:
                self._headers(client, 400)
            except OSError:
                pass
        except Exception as exc:
            self._log(f"image cache request error: {exc}")
        finally:
            self._release_client(client)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/{self.token}" if self.port else ""

    def image_url(self, filename: str) -> str:
        return f"{self.base_url}/image/{urllib.parse.quote(filename, safe='')}" if self.base_url and filename else ""

    def stop(self) -> None:
        self._stopping.set()
        server, self._server = self._server, None
        self.port = 0
        if server is not None:
            try:
                server.close()
            except OSError:
                pass
        thread, self._thread = self._thread, None
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        with self._clients_lock:
            clients = list(self._clients)
        for client in clients:
            try:
                client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            client.close()
        pool, self._pool = self._pool, None
        if pool is not None:
            # All reads/writes have been interrupted above. Draining submitted
            # handlers releases their slots before the server can be restarted.
            pool.shutdown(wait=True)


class Plugin:
    def __init__(self) -> None:
        self._stopping = threading.Event()
        self._background_timers: set[threading.Timer] = set()
        self._background_timers_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="DeckyNews")
        # Background tab warming fetches unique publishers concurrently without
        # occupying the active-tab/source RPC path. Network I/O benefits from a
        # wider thread pool; true multiprocessing would duplicate caches and add
        # Windows spawn overhead inside Decky.
        self._prefetch_executor = ThreadPoolExecutor(max_workers=24, thread_name_prefix="NewsTabPrefetch")
        # Fast card-cover discovery is isolated from feeds/config/article RPCs.
        # Slow rendered/Jina fallbacks use a second tiny pool so they can never
        # occupy the workers needed by ordinary metadata extraction.
        self._cover_executor = ThreadPoolExecutor(max_workers=40, thread_name_prefix="NewsCoversFast")
        # A separate bounded slow lane is allowed only after strict/cheap discovery
        # has failed. It is especially useful for blocked Google-backed publishers
        # such as Il Post: each rendered request is article-specific, so it cannot
        # steal a neighbouring card's image, and 18 workers keep the tail finite.
        self._cover_slow_executor = ThreadPoolExecutor(max_workers=18, thread_name_prefix="NewsCoversRendered")
        # Background tabs have independent lanes so they cannot consume visible-tab
        # cover slots. Their rendered lane is intentionally smaller.
        self._cover_background_executor = ThreadPoolExecutor(max_workers=24, thread_name_prefix="NewsCoversWarm")
        self._cover_background_slow_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="NewsCoversWarmRendered")
        # Article opens have a dedicated pool and never queue behind feed/image work.
        self._article_executor = ThreadPoolExecutor(max_workers=6, thread_name_prefix="NewsArticle")
        # Remote image downloads/local cache warming are also separate: an image
        # CDN that stalls must not delay feed refresh or article opening.
        self._image_executor = ThreadPoolExecutor(max_workers=16, thread_name_prefix="NewsImageCache")
        self._cover_inflight: set[str] = set()
        # Kept for backward-compatible status bookkeeping only. Cover failure never
        # removes an article from the Edicola.
        self._cover_unavailable: set[str] = set()
        self._cover_inflight_lock = threading.Lock()
        # Single-flight publisher fetches prevent the active tab and simultaneous
        # all-tab prefetch from downloading the same RSS feed twice.
        self._feed_inflight: Dict[str, threading.Event] = {}
        self._feed_inflight_results: Dict[str, Dict[str, Any]] = {}
        self._feed_inflight_lock = threading.Lock()
        self._catalog: Dict[str, List[Dict[str, Any]]] = {}
        self._countries: List[Dict[str, str]] = []
        self._config: Dict[str, Any] = _default_config()
        self._image_server = NewsImageCacheServer(IMAGE_CACHE_DIR, self._log)
        self._image_warm_future = None
        self._image_cache_warm_inflight: set[str] = set()
        self._image_cache_warm_lock = threading.Lock()
        self._spaziogames_home_cache: Tuple[float, Dict[str, str], Dict[str, str]] = (0.0, {}, {})
        self._spaziogames_home_lock = threading.Lock()
        # Generic one-request-per-publisher cover index. This generalises the
        # SpazioGames optimisation to publishers such as Fanpage and Il Post.
        self._publisher_home_cache: Dict[str, Tuple[float, Dict[str, str], Dict[str, str]]] = {}
        self._publisher_home_inflight: Dict[str, threading.Event] = {}
        self._publisher_home_lock = threading.Lock()
        # Only a tiny number of publisher-home Reader fallbacks may use Jina at
        # once. Article-open Reader calls do NOT use this semaphore and keep priority.
        self._publisher_home_jina_slots = threading.BoundedSemaphore(2)
        # Google News' internal URL decoder is sensitive to bursty access. Keep
        # decoder traffic bounded even though cover discovery itself is highly
        # parallel; this avoids turning a 40-worker cover pool into a Google 429
        # storm. Article Reader and cover workers share the same small gate.
        self._google_decode_slots = threading.BoundedSemaphore(5)
        # Google wrapper decoding is single-flight per URL. Cover workers, fresh
        # Il Post warm-up and an explicit Reader open can otherwise all request the
        # same shell at once, multiplying network work and making newest stories
        # slower exactly when they need the decoder most.
        self._google_decode_inflight: Dict[str, threading.Event] = {}
        self._google_decode_inflight_lock = threading.Lock()
        # Il Post's public feed can be blocked from Decky's Python runtime. Google
        # News remains the transport fallback, but the publisher officially exposes
        # per-day archives and a chronological stream. We index those through the
        # already-used rendered Reader once per listing, then resolve many Google
        # wrappers by exact/very-high-confidence title match.
        self._ilpost_listing_cache: Dict[str, Tuple[float, Dict[str, str]]] = {}
        self._ilpost_listing_inflight: Dict[str, threading.Event] = {}
        self._ilpost_listing_lock = threading.Lock()
        # Independent direct-link index for Il Post.  Its native feed/page fetches
        # can return 403 from Decky and Google wrappers occasionally resist decoding;
        # Bing News RSS exposes publisher result URLs (or an apiclick URL carrying
        # the publisher URL) without requiring a browser.  One shared recent index
        # services dozens of cards; an exact-title query is reserved for an explicit
        # Reader open so the Edicola never launches one search per card.
        self._ilpost_bing_cache: Dict[str, Tuple[float, Dict[str, str]]] = {}
        self._ilpost_bing_inflight: Dict[str, threading.Event] = {}
        self._ilpost_bing_lock = threading.Lock()
        # Il Post publishes every new item to its official public Telegram channel
        # together with an ilpost.link short URL. This is substantially more useful
        # for brand-new stories than waiting for Bing to index them or for a Google
        # News wrapper to become decodable. One shared Telegram page therefore acts
        # as the first-party-ish, near-real-time direct-link index for Il Post only.
        self._ilpost_telegram_cache: Dict[str, Tuple[float, Dict[str, str], int]] = {}
        self._ilpost_telegram_inflight: Dict[str, threading.Event] = {}
        self._ilpost_telegram_lock = threading.Lock()
        self._ilpost_shortlink_cache: Dict[str, Tuple[float, str]] = {}
        self._ilpost_shortlink_lock = threading.Lock()
        self._ilpost_exact_cache: Dict[str, Tuple[float, str]] = {}
        self._ilpost_exact_inflight: Dict[str, threading.Event] = {}
        self._ilpost_exact_lock = threading.Lock()
        # Exact-title rescue is now also used proactively by Il Post card workers.
        # Keep it bounded so dozens of unresolved Google wrappers do not flood Bing,
        # while still allowing the remaining cards to converge before the user opens
        # them. The same single-flight resolver is shared with the Reader.
        self._ilpost_exact_slots = threading.BoundedSemaphore(3)
        # The newest Il Post stories often reach Google News before Bing indexes
        # them. Keep a tiny dedicated warm-up for the first fresh wrappers instead
        # of launching exact Bing searches for the whole 80-item feed.
        self._ilpost_fresh_prefetch_lock = threading.Lock()
        self._ilpost_fresh_prefetch_keys: Dict[str, float] = {}
        self._ilpost_fresh_timers: List[threading.Timer] = []

    def _log(self, message: str) -> None:
        try:
            decky_plugin.logger.info(f"[News] {message}")
        except Exception:
            pass

    def _bundled_asset_url(self, value: str) -> str:
        raw = str(value or "").strip()
        if not raw.startswith("asset://favicons/"):
            return raw
        filename = Path(raw.split("asset://favicons/", 1)[1]).name
        if not filename:
            return ""
        source = FAVICON_ASSETS_DIR / filename
        target_name = "asset-" + filename
        target = IMAGE_CACHE_DIR / target_name
        try:
            IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            if source.is_file() and (not target.exists() or source.stat().st_size != target.stat().st_size):
                shutil.copyfile(source, target)
        except Exception:
            pass
        return self._image_server.image_url(target_name) if target.is_file() else ""

    def _bundled_favicon_for_site(self, site_url: str) -> str:
        return self._bundled_asset_url(f"asset://favicons/{_favicon_asset_filename(site_url)}")

    def _prepare_bundled_favicons(self) -> None:
        if not FAVICON_ASSETS_DIR.is_dir():
            return
        IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        for source in FAVICON_ASSETS_DIR.glob("*.png"):
            target = IMAGE_CACHE_DIR / ("asset-" + source.name)
            try:
                if not target.exists() or source.stat().st_size != target.stat().st_size:
                    shutil.copyfile(source, target)
            except Exception:
                continue

    def _load_assets(self) -> None:
        self._prepare_bundled_favicons()
        self._catalog = _load_json(CATALOG_PATH, {})
        self._countries = _load_json(COUNTRIES_PATH, [{"code": "IT", "name": "Italia"}])
        config = _load_json(CONFIG_PATH, _default_config())
        merged = _default_config()
        if isinstance(config, dict):
            merged.update(config)
        if not isinstance(merged.get("sources"), list):
            merged["sources"] = []
        if not isinstance(merged.get("tabs"), list):
            merged["tabs"] = []
        # Normalize/migrate source branding at load time too, so bootstrap/QAM do
        # not keep stale favicon.im URLs from older configs. This is pure string
        # normalization: absolutely no network I/O is performed here.
        did_migrate = False
        normalized_sources: List[Dict[str, Any]] = []
        for raw_source in merged.get("sources", []):
            if not isinstance(raw_source, dict):
                continue
            normalized = self._normalized_source(raw_source)
            normalized_sources.append(normalized)
            if normalized != raw_source:
                did_migrate = True
        merged["sources"] = normalized_sources
        source_ids = [str(source.get("id") or "") for source in normalized_sources if str(source.get("id") or "")]
        migrated_tabs: List[Dict[str, Any]] = []
        for raw in merged.get("tabs", []):
            if not isinstance(raw, dict):
                continue
            tab = dict(raw)
            tab_id = str(tab.get("id") or "")
            tab_name = str(tab.get("name") or "")
            explicit_category = str(tab.get("category") or "")
            category = _infer_tab_category(tab_id, tab_name, explicit_category)
            # Culture is no longer a default category. Remove only the old preset,
            # never a custom user tab that happens to be named similarly.
            if tab_id == "preset-culture":
                did_migrate = True
                continue
            if category and not tab.get("category"):
                tab["category"] = category
                # Older builds selected sources by the source's category. Migrate
                # preset tabs to all sources so the ARTICLE decides its category.
                tab["sourceIds"] = list(source_ids)
                did_migrate = True
            if category == "cinema" and tab.get("name") != "Cinema e Serie":
                tab["name"] = "Cinema e Serie"
                did_migrate = True
            migrated_tabs.append(tab)
        merged["tabs"] = migrated_tabs
        self._config = merged
        if did_migrate:
            try:
                self._save()
            except Exception:
                pass

    def _save(self) -> None:
        _atomic_json(CONFIG_PATH, self._config)

    def _catalog_source(self, country: str, raw: Dict[str, Any]) -> Dict[str, Any]:
        site = str(raw.get("site_url") or "")
        feed = str(raw.get("feed_url") or "")
        name = str(raw.get("name") or urllib.parse.urlparse(site).netloc or "Fonte")
        source_id = str(raw.get("id") or _stable_id("src", f"{country}|{name}|{site}|{feed}"))
        brand = _brand_asset_defaults(site)
        favicon = str(raw.get("favicon_url") or raw.get("faviconUrl") or brand["faviconUrl"])
        logo = str(raw.get("logo_url") or raw.get("logoUrl") or brand["logoUrl"])
        if not favicon or "google.com/s2/favicons" in favicon:
            favicon = brand["faviconUrl"]
        # All predefined sources always carry a local 256px fallback, even when
        # their real favicon is temporarily unavailable or low-resolution.
        logo = self._bundled_asset_url(logo) or self._bundled_asset_url(brand["logoUrl"]) or logo
        return {
            "id": source_id,
            "name": name,
            "country": country.upper(),
            "siteUrl": site,
            "feedUrl": feed,
            "tags": list(raw.get("tags") or []),
            "custom": False,
            "enabled": True,
            "faviconUrl": favicon,
            "logoUrl": logo,
            "brandColor": str(raw.get("brand_color") or raw.get("brandColor") or brand["brandColor"]),
        }

    def _normalized_source(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        country = str(raw.get("country") or self._config.get("country") or "IT").upper()
        site = str(raw.get("siteUrl") or raw.get("site_url") or "")
        feed = str(raw.get("feedUrl") or raw.get("feed_url") or "")
        if not feed and site:
            feed = _google_news_site_feed(site, country)
        name = str(raw.get("name") or urllib.parse.urlparse(site or feed).netloc or "Fonte")
        source_id = str(raw.get("id") or _stable_id("src", f"{country}|{name}|{site}|{feed}"))
        brand = _brand_asset_defaults(site)
        favicon = str(raw.get("faviconUrl") or raw.get("favicon_url") or "")
        logo = str(raw.get("logoUrl") or raw.get("logo_url") or "")
        # Predefined sources always use the canonical high-resolution favicon URL
        # for their publisher. This also migrates first-party /favicon.ico values
        # written by the previous build. IGN editions intentionally all resolve to
        # ign.com through _canonical_favicon_domain().
        is_predefined = not bool(raw.get("custom", True))
        if is_predefined:
            # Predefined source transport is canonical too, not only branding.
            # This lets us migrate an existing config when a publisher gains a
            # better native RSS endpoint (Fanpage is the important 2026-08 case)
            # without changing its stored source id / tab associations.
            site_key = site.rstrip("/").lower()
            name_key = name.strip().lower()
            for catalog_raw in self._catalog.get(country, []) if isinstance(self._catalog, dict) else []:
                if not isinstance(catalog_raw, dict):
                    continue
                catalog_site = str(catalog_raw.get("site_url") or "").rstrip("/").lower()
                catalog_name = str(catalog_raw.get("name") or "").strip().lower()
                if (site_key and catalog_site == site_key) or (name_key and catalog_name == name_key):
                    canonical_feed = str(catalog_raw.get("feed_url") or "").strip()
                    if canonical_feed:
                        feed = canonical_feed
                    break
            favicon = brand["faviconUrl"]
            logo = self._bundled_asset_url(brand["logoUrl"]) or logo
        else:
            if not favicon or "google.com/s2/favicons" in favicon or "a.favicon.im/" in favicon:
                favicon = brand["faviconUrl"]
            if logo.startswith("asset://favicons/"):
                logo = self._bundled_asset_url(logo)
            elif not logo:
                logo = brand["logoUrl"]
        return {
            "id": source_id,
            "name": name[:120],
            "country": country,
            "siteUrl": site,
            "feedUrl": feed,
            "tags": [str(value) for value in raw.get("tags", []) if str(value)],
            "custom": bool(raw.get("custom", True)),
            "enabled": bool(raw.get("enabled", True)),
            "faviconUrl": favicon,
            "logoUrl": logo,
            "brandColor": str(raw.get("brandColor") or raw.get("brand_color") or brand["brandColor"]),
        }

    def _country_name(self, country: str) -> str:
        code = str(country or "IT").upper()
        for entry in self._countries:
            if isinstance(entry, dict) and str(entry.get("code") or "").upper() == code:
                return str(entry.get("name") or code)
        return code

    def _make_country_source(self, country: str) -> Dict[str, Any]:
        code = str(country or "IT").upper()
        return self._normalized_source({
            "id": f"country-news-{code.lower()}",
            "name": f"Notizie principali · {self._country_name(code)}",
            "country": code,
            "siteUrl": "https://news.google.com/",
            "feedUrl": _google_news_top_feed(code),
            "tags": ["all", "headlines"],
            "custom": True,
            "enabled": True,
            "faviconUrl": "https://a.favicon.im/news.google.com?larger=true&throw-error-on-404=true",
            "logoUrl": "asset://favicons/google-news.png",
        })

    def _image_cache_path(self, article_url: str) -> Path:
        return CACHE_DIR / f"image-{hashlib.sha1(str(article_url or '').encode('utf-8', 'ignore')).hexdigest()[:20]}.json"

    def _read_image_cache(self, article_url: str) -> Dict[str, Any]:
        payload = _load_json(self._image_cache_path(article_url), {})
        if not isinstance(payload, dict) or int(payload.get("cacheVersion") or 0) != IMAGE_CACHE_VERSION:
            return {}
        return payload

    def _write_image_cache(self, article_url: str, remote_image: str, cached_file: str = "") -> None:
        """Persist cover metadata without allowing a slower failed race to erase it.

        Card discovery is intentionally concurrent. A successful direct request and
        a slower fallback may finish in either order, so an empty result must never
        overwrite a usable cover. Once a cover has been selected for the current
        cache revision, keep it stable unless the same remote image gains a local
        cached file. This also prevents cards changing artwork after refresh/reopen.
        """
        key = str(article_url or "").strip()
        if not key:
            return
        remote = str(remote_image or "").strip()
        filename = str(cached_file or "").strip()
        existing = self._read_image_cache(key)
        existing_remote = str(existing.get("remoteImage") or existing.get("image") or "").strip() if existing else ""
        existing_file = str(existing.get("cachedFile") or "").strip() if existing else ""
        if existing and (existing_remote or existing_file):
            if not remote and not filename:
                return
            # Preserve the first visible artwork. The only allowed mutation is
            # attaching the local file produced while warming that exact image.
            if existing_remote and remote and existing_remote != remote:
                return
            remote = existing_remote or remote
            filename = filename or existing_file
        _atomic_json(self._image_cache_path(key), {
            "cacheVersion": IMAGE_CACHE_VERSION,
            "fetchedAt": int(time.time()),
            "remoteImage": remote,
            "cachedFile": filename,
        })

    def _image_extension(self, content_type: str, url: str, data: bytes) -> str:
        value = str(content_type or "").split(";", 1)[0].strip().lower()
        by_type = {
            "image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png",
            "image/webp": "webp", "image/gif": "gif", "image/avif": "avif",
        }
        if value in by_type:
            return by_type[value]
        path = urllib.parse.urlparse(str(url or "")).path.lower()
        match = re.search(r"\.(jpe?g|png|webp|gif|avif)$", path)
        if match:
            return "jpg" if match.group(1) in {"jpeg", "jpg"} else match.group(1)
        if data.startswith(b"\x89PNG"):
            return "png"
        if data.startswith((b"GIF87a", b"GIF89a")):
            return "gif"
        if data[:3] == b"\xff\xd8\xff":
            return "jpg"
        if data[:4] == b"RIFF" and b"WEBP" in data[:16]:
            return "webp"
        return "jpg"

    def _cached_image_url(self, filename: str) -> str:
        if not filename:
            return ""
        path = IMAGE_CACHE_DIR / filename
        if not path.is_file():
            return ""
        return self._image_server.image_url(filename)

    def _cache_remote_image_sync(self, image_url: str, referer: str = "") -> Tuple[str, str]:
        value = str(image_url or "").strip()
        if not value.startswith(("http://", "https://")):
            return value, ""
        key = hashlib.sha1(value.encode("utf-8", "ignore")).hexdigest()
        for ext in ("jpg", "jpeg", "png", "webp", "gif", "avif"):
            candidate = IMAGE_CACHE_DIR / f"{key}.{ext}"
            if candidate.is_file() and candidate.stat().st_size > 1024:
                return self._image_server.image_url(candidate.name), candidate.name
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "it-IT,it;q=0.8,en;q=0.6",
        }
        if referer.startswith(("http://", "https://")):
            headers["Referer"] = referer
        request = urllib.request.Request(value, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=7.0) as response:
                data = response.read(MAX_IMAGE_BYTES + 1)
                content_type = str(response.headers.get("Content-Type") or "")
            if not data or len(data) > MAX_IMAGE_BYTES or not content_type.lower().startswith("image/"):
                return value, ""
            ext = self._image_extension(content_type, value, data)
            filename = f"{key}.{ext}"
            IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            tmp = IMAGE_CACHE_DIR / f"{filename}.tmp"
            tmp.write_bytes(data)
            os.replace(tmp, IMAGE_CACHE_DIR / filename)
            return self._image_server.image_url(filename), filename
        except Exception:
            return value, ""

    def _schedule_background(self, delay: float, callback) -> None:
        """Track and cancel every delayed task owned by this plugin instance."""
        if self._stopping.is_set():
            return
        def run() -> None:
            try:
                if not self._stopping.is_set():
                    callback()
            finally:
                with self._background_timers_lock:
                    self._background_timers.discard(timer)
        timer = threading.Timer(max(0.0, delay), run)
        timer.daemon = True
        with self._background_timers_lock:
            if self._stopping.is_set():
                return
            self._background_timers.add(timer)
            timer.start()

    def _schedule_image_cache_warm(self, image_url: str, referer: str, cache_key: str, delay_seconds: float = 6.0) -> None:
        """Cache a discovered cover only after the browser has had first dibs.

        The card UI downloads the remote image as soon as cover metadata arrives.
        Older builds simultaneously downloaded the same bytes in Python to build a
        local cache, effectively doubling cover bandwidth during the most visible
        loading window. Defer that persistence work; NewsImage can still call the
        explicit cache_image RPC immediately if the browser's remote load fails.
        """
        value = str(image_url or "").strip()
        if not value.startswith(("http://", "https://")):
            return
        if self._stopping.is_set():
            return
        token = f"{cache_key}|{value}"
        with self._image_cache_warm_lock:
            if token in self._image_cache_warm_inflight:
                return
            self._image_cache_warm_inflight.add(token)

        def task() -> None:
            try:
                if self._stopping.is_set():
                    return
                _local, filename = self._cache_remote_image_sync(value, referer)
                self._write_image_cache(cache_key, value, filename)
            finally:
                with self._image_cache_warm_lock:
                    self._image_cache_warm_inflight.discard(token)

        def submit_later() -> None:
            try:
                if self._stopping.is_set():
                    return
                self._image_executor.submit(task)
            except Exception:
                with self._image_cache_warm_lock:
                    self._image_cache_warm_inflight.discard(token)

        delay = max(0.0, float(delay_seconds or 0.0))
        if delay <= 0:
            submit_later()
            return
        self._schedule_background(delay, submit_later)

    def _title_match_key(self, value: str) -> str:
        # Unicode-aware normalization: keep accented letters instead of deleting
        # them, because Italian headlines frequently contain them.
        text = html.unescape(_clean_text(value)).casefold()
        return re.sub(r"[^\w]+", " ", text, flags=re.UNICODE).strip()

    def _is_ilpost_public_url(self, value: str) -> bool:
        host = _hostname(str(value or ""))
        return host == "ilpost.link" or _host_matches(str(value or ""), "https://www.ilpost.it/")

    def _resolve_ilpost_shortlink_sync(self, value: str) -> str:
        """Resolve an official ilpost.link URL without downloading the full article.

        The short URL itself remains a valid fallback: Jina/Steam can follow it even
        when Decky's urllib runtime is blocked by the final publisher page.
        """
        short = str(value or "").strip()
        if _hostname(short) != "ilpost.link":
            return short if _host_matches(short, "https://www.ilpost.it/") else ""
        now = time.time()
        with self._ilpost_shortlink_lock:
            cached = self._ilpost_shortlink_cache.get(short)
            if cached and now - cached[0] < 30 * 60:
                return cached[1] or short

        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
                return None

        resolved = ""
        current = short
        try:
            opener = urllib.request.build_opener(_NoRedirect())
            for _ in range(3):
                request = urllib.request.Request(
                    current,
                    headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,*/*;q=0.6"},
                    method="GET",
                )
                location = ""
                try:
                    with opener.open(request, timeout=2.2) as response:
                        final = str(response.geturl() or current)
                        if _host_matches(final, "https://www.ilpost.it/"):
                            resolved = final
                            break
                        location = str(response.headers.get("Location") or "")
                except urllib.error.HTTPError as exc:
                    location = str(exc.headers.get("Location") or "") if exc.headers else ""
                    final = str(exc.geturl() or current)
                    if _host_matches(final, "https://www.ilpost.it/"):
                        resolved = final
                        break
                if not location:
                    break
                candidate = urllib.parse.urljoin(current, html.unescape(location).strip())
                if _host_matches(candidate, "https://www.ilpost.it/"):
                    resolved = candidate
                    break
                if _hostname(candidate) != "ilpost.link" or candidate == current:
                    break
                current = candidate
        except Exception:
            resolved = ""
        result = resolved or short
        with self._ilpost_shortlink_lock:
            self._ilpost_shortlink_cache[short] = (time.time(), result)
        return result

    def _ilpost_telegram_page_parse(self, raw: str) -> Tuple[Dict[str, str], int]:
        links: Dict[str, str] = {}
        message_ids = [int(value) for value in re.findall(r'data-post=["\']ilpost_official/(\d+)', raw, re.I) if value.isdigit()]
        # Telegram's public HTML keeps each message in a tgme_widget_message_wrap.
        # Split only at wrapper boundaries so a short link can never be paired with
        # the title from the neighbouring post.
        chunks = re.split(r'(?=<div[^>]+class=["\'][^"\']*tgme_widget_message_wrap)', raw, flags=re.I)
        for chunk in chunks:
            if "ilpost.link/" not in chunk:
                continue
            text_match = re.search(r'<div[^>]+class=["\'][^"\']*tgme_widget_message_text[^"\']*["\'][^>]*>(.*?)</div>', chunk, re.I | re.S)
            if not text_match:
                continue
            inner = text_match.group(1)
            parts = re.split(r'<br\s*/?>', inner, maxsplit=1, flags=re.I)
            title = _clean_text(parts[0] if parts else inner)
            short_match = re.search(r'https?://(?:www\.)?ilpost\.link/[A-Za-z0-9_-]+(?:#[^"\'<>\s]+)?', html.unescape(inner), re.I)
            if not short_match or len(self._title_match_key(title)) < 5:
                continue
            short = short_match.group(0).rstrip(".,);]")
            links.setdefault(self._title_match_key(title), short)
        return links, (min(message_ids) if message_ids else 0)

    def _ilpost_telegram_recent_links_sync(self, deep: bool = False) -> Dict[str, str]:
        cache_key = "deep" if deep else "recent"
        now = time.time()
        with self._ilpost_telegram_lock:
            cached = self._ilpost_telegram_cache.get(cache_key)
            if cached and now - cached[0] < (4 * 60 if cached[1] else 35):
                return dict(cached[1])
            waiter = self._ilpost_telegram_inflight.get(cache_key)
            if waiter is None:
                waiter = threading.Event()
                self._ilpost_telegram_inflight[cache_key] = waiter
                owner = True
            else:
                owner = False
        if not owner:
            waiter.wait(timeout=7.0)
            with self._ilpost_telegram_lock:
                cached = self._ilpost_telegram_cache.get(cache_key)
                return dict(cached[1]) if cached else {}

        started = time.perf_counter()
        combined: Dict[str, str] = {}
        before = 0
        pages = 3 if deep else 1
        try:
            for page in range(pages):
                url = "https://t.me/s/ilpost_official"
                if before:
                    url += "?before=" + str(before)
                try:
                    data, content_type, _final = self._request(
                        url, 1800 * 1024, timeout=2.7,
                        accept="text/html,application/xhtml+xml,*/*;q=0.5",
                    )
                    raw = self._decode(data, content_type)
                except Exception:
                    break
                page_links, min_id = self._ilpost_telegram_page_parse(raw)
                for key, value in page_links.items():
                    combined.setdefault(key, value)
                if not deep or not min_id or min_id == before:
                    break
                before = min_id
        finally:
            self._log(f"Il Post Telegram {'deep' if deep else 'recent'}: {time.perf_counter() - started:.2f}s links={len(combined)}")
            with self._ilpost_telegram_lock:
                self._ilpost_telegram_cache[cache_key] = (time.time(), dict(combined), before)
                # A deep scan is a superset of the current page; let the normal hot
                # path benefit from it too without another request.
                if deep and combined:
                    self._ilpost_telegram_cache["recent"] = (time.time(), dict(combined), before)
                event = self._ilpost_telegram_inflight.pop(cache_key, None)
                if event is not None:
                    event.set()
        return combined

    def _resolve_ilpost_telegram_sync(self, title: str, deep: bool = False) -> str:
        links = self._ilpost_telegram_recent_links_sync(deep=deep)
        short = self._ilpost_match_listing_url(title, links)
        if not short:
            return ""
        resolved = self._resolve_ilpost_shortlink_sync(short)
        if self._is_ilpost_public_url(resolved):
            self._log(f"Il Post resolve Telegram -> {_hostname(resolved)} title={_clean_text(title)[:72]}")
            return resolved
        return ""

    def _ilpost_listing_links_sync(self, cache_key: str, listing_url: str) -> Dict[str, str]:
        now = time.time()
        with self._ilpost_listing_lock:
            cached = self._ilpost_listing_cache.get(cache_key)
            if cached and now - cached[0] < 15 * 60:
                return dict(cached[1])
            waiter = self._ilpost_listing_inflight.get(cache_key)
            if waiter is None:
                waiter = threading.Event()
                self._ilpost_listing_inflight[cache_key] = waiter
                owner = True
            else:
                owner = False
        if not owner:
            waiter.wait(timeout=6.5)
            with self._ilpost_listing_lock:
                cached = self._ilpost_listing_cache.get(cache_key)
                return dict(cached[1]) if cached else {}

        links: Dict[str, str] = {}
        listing_started = time.perf_counter()
        try:
            rendered = self._jina_reader_article_sync(listing_url, timeout=5.5)
            markdown = str(rendered.get("rawContent") or "") if isinstance(rendered, dict) else ""
            # Jina renders navigation/listing pages as Markdown. Only accept real
            # Il Post links and pair them with their own link label, never nearby
            # text/images. This makes URL resolution strict and deterministic.
            for match in re.finditer(r"(?<!!)\[([^\]]{6,})\]\((https?://[^\s\)]+)(?:\s+[^\)]*)?\)", markdown, re.I):
                title = _clean_text(match.group(1))
                url = html.unescape(match.group(2)).strip().rstrip(".,);]")
                if not _host_matches(url, "https://www.ilpost.it/"):
                    continue
                path = urllib.parse.urlparse(url).path.lower()
                if any(part in path for part in ("/podcasts/", "/newsletter/", "/tag/", "/stream", "/media/", "/shop/", "/events/")):
                    continue
                key = self._title_match_key(title)
                if len(key) >= 12:
                    links.setdefault(key, url)
        except Exception:
            links = {}
        finally:
            self._log(f"Il Post listing {cache_key}: {time.perf_counter() - listing_started:.2f}s links={len(links)}")
            with self._ilpost_listing_lock:
                self._ilpost_listing_cache[cache_key] = (time.time(), dict(links))
                event = self._ilpost_listing_inflight.pop(cache_key, None)
                if event is not None:
                    event.set()
        return links

    def _ilpost_match_listing_url(self, title: str, links: Dict[str, str]) -> str:
        target = self._title_match_key(title)
        if not target or not links:
            return ""
        exact = links.get(target)
        if exact:
            return exact
        target_words = {word for word in target.split() if len(word) >= 3}
        if len(target_words) < 4:
            return ""
        best_url = ""
        best_score = 0.0
        second_score = 0.0
        for key, url in links.items():
            words = {word for word in key.split() if len(word) >= 3}
            if len(words) < 3:
                continue
            overlap = len(target_words & words)
            if overlap < 3:
                continue
            coverage = overlap / min(len(target_words), len(words))
            jaccard = overlap / len(target_words | words)
            score = max(jaccard, coverage * 0.94)
            if score > best_score:
                second_score = best_score
                best_score, best_url = score, url
            elif score > second_score:
                second_score = score
        # Wrong article URLs are worse than a fallback. Accept fuzzy matching only
        # when almost the whole headline agrees and the winner is unambiguous.
        return best_url if best_score >= 0.90 and best_score - second_score >= 0.08 else ""

    def _ilpost_search_rss_links_from_data(self, data: bytes, base_url: str) -> Dict[str, str]:
        try:
            parsed = _parse_feed_document(data)
        except Exception:
            return {}
        links: Dict[str, str] = {}
        for node in parsed.items[:28]:
            title = _clean_text(_item_text(node, ["title"]))
            # Search feeds frequently append the publisher to result titles. Strip
            # only the exact Il Post suffix so matching stays deterministic.
            title = re.sub(r"\s+[\-–—|]\s+Il Post\s*$", "", title, flags=re.I).strip()
            href = ""
            for candidate in node.get("links") or []:
                raw = str(candidate.get("href") or "").strip()
                if raw:
                    href = _absolute(base_url, raw)
                    break
            if not href:
                href = _absolute(base_url, _item_text(node, ["link", "guid", "id"]))
            href = _unwrap_bing_news_url(href).rstrip(".,);]")
            if not title or not _host_matches(href, "https://www.ilpost.it/"):
                continue
            path = urllib.parse.urlparse(href).path.lower()
            if any(part in path for part in ("/podcasts/", "/newsletter/", "/tag/", "/stream", "/media/", "/shop/", "/events/")):
                continue
            key = self._title_match_key(title)
            if len(key) >= 12:
                links.setdefault(key, href)
        return links

    def _ilpost_bing_rss_page_sync(self, query: str, first: int = 1) -> Dict[str, str]:
        params = {
            "q": str(query or "site:ilpost.it"),
            "format": "RSS",
            "first": str(max(1, int(first or 1))),
            "setlang": "it-IT",
            "cc": "it",
            "qft": 'sortbydate="1"',
        }
        rss_url = "https://www.bing.com/news/search?" + urllib.parse.urlencode(params)
        try:
            data, _content_type, final_url = self._request(
                rss_url,
                900 * 1024,
                timeout=3.4,
                accept="application/rss+xml,application/xml,text/xml,*/*;q=0.4",
            )
        except Exception:
            return {}
        return self._ilpost_search_rss_links_from_data(data, final_url or rss_url)

    def _ilpost_bing_web_rss_sync(self, query: str) -> Dict[str, str]:
        # Bing's ordinary web search also exposes RSS. Use it only for one explicit
        # Reader-open exact-title rescue, never for bulk card enrichment.
        params = {"q": str(query or ""), "format": "rss", "count": "12", "setlang": "it-IT", "cc": "it"}
        rss_url = "https://www.bing.com/search?" + urllib.parse.urlencode(params)
        try:
            data, _content_type, final_url = self._request(
                rss_url,
                900 * 1024,
                timeout=3.4,
                accept="application/rss+xml,application/xml,text/xml,*/*;q=0.4",
            )
        except Exception:
            return {}
        return self._ilpost_search_rss_links_from_data(data, final_url or rss_url)

    def _ilpost_bing_recent_links_sync(self) -> Dict[str, str]:
        cache_key = "recent"
        now = time.time()
        with self._ilpost_bing_lock:
            cached = self._ilpost_bing_cache.get(cache_key)
            if cached:
                ttl = 10 * 60 if cached[1] else 90
                if now - cached[0] < ttl:
                    return dict(cached[1])
            waiter = self._ilpost_bing_inflight.get(cache_key)
            if waiter is None:
                waiter = threading.Event()
                self._ilpost_bing_inflight[cache_key] = waiter
                owner = True
            else:
                owner = False
        if not owner:
            waiter.wait(timeout=12.0)
            with self._ilpost_bing_lock:
                cached = self._ilpost_bing_cache.get(cache_key)
                return dict(cached[1]) if cached else {}

        started = time.perf_counter()
        combined: Dict[str, str] = {}
        try:
            # Bing News exposes a modest number of results per RSS page. Page the
            # recent publisher query in three concurrent lanes; this is one shared
            # publisher operation, not one web request per card.
            offsets = (1, 11, 21, 31, 41, 51, 61, 71)
            with ThreadPoolExecutor(max_workers=3, thread_name_prefix="IlPostBing") as pool:
                futures = [pool.submit(self._ilpost_bing_rss_page_sync, "site:ilpost.it", first) for first in offsets]
                for future in as_completed(futures):
                    try:
                        for key, value in future.result().items():
                            combined.setdefault(key, value)
                    except Exception:
                        continue
        finally:
            self._log(f"Il Post Bing recent: {time.perf_counter() - started:.2f}s links={len(combined)}")
            with self._ilpost_bing_lock:
                self._ilpost_bing_cache[cache_key] = (time.time(), dict(combined))
                event = self._ilpost_bing_inflight.pop(cache_key, None)
                if event is not None:
                    event.set()
        return combined

    def _resolve_ilpost_bing_exact_sync(self, title: str, force: bool = False) -> str:
        """Resolve one Il Post headline through strict search, shared by cards/Reader.

        The recent publisher index is deliberately cheap but cannot contain every
        Google-News item. Older builds reserved exact search for an explicit Reader
        open, which is why opening a cover-less card often made its image suddenly
        appear on Back. Exact rescue now runs proactively too, with a bounded
        semaphore and per-title single-flight so the Edicola does the same useful
        work before the user clicks.
        """
        key = self._title_match_key(title)
        if len(key) < 12:
            return ""
        now = time.time()
        with self._ilpost_exact_lock:
            cached = self._ilpost_exact_cache.get(key)
            if cached:
                # Positive matches are stable. Negative results are intentionally
                # very short-lived because search indexing/transport failures are
                # transient and an explicit Reader open must be allowed to retry.
                ttl = 30 * 60 if cached[1] else (0 if force else 60)
                if ttl and now - cached[0] < ttl:
                    return cached[1]
            waiter = self._ilpost_exact_inflight.get(key)
            if waiter is None:
                waiter = threading.Event()
                self._ilpost_exact_inflight[key] = waiter
                owner = True
            else:
                owner = False
        if not owner:
            waiter.wait(timeout=8.0)
            with self._ilpost_exact_lock:
                cached = self._ilpost_exact_cache.get(key)
                return cached[1] if cached else ""

        resolved = ""
        started = time.perf_counter()
        attempts = 0
        # Before asking a search engine, consult Il Post's own official Telegram
        # stream. Its ilpost.link entry is generally published at the same time as
        # the story, which is exactly the gap visible in the user's newest-item logs.
        resolved = self._resolve_ilpost_telegram_sync(title, deep=force)
        if resolved:
            with self._ilpost_exact_lock:
                self._ilpost_exact_cache[key] = (time.time(), resolved)
                event = self._ilpost_exact_inflight.pop(key, None)
                if event is not None:
                    event.set()
            self._log(f"Il Post resolve exact Telegram -> {_hostname(resolved)} {time.perf_counter() - started:.2f}s title={_clean_text(title)[:72]}")
            return resolved
        acquired = self._ilpost_exact_slots.acquire(timeout=5.0 if force else 3.0)
        try:
            if not acquired:
                return ""
            clean = _clean_text(title)
            # Curly punctuation is harmless for matching but can make literal
            # search phrases brittle. Keep the original first, then one normalized
            # variant and finally a shorter unquoted query for freshly indexed news.
            normalized = (clean.replace("’", "'").replace("‘", "'")
                               .replace("“", '"').replace("”", '"'))
            words = [word for word in re.split(r"\s+", normalized) if word]
            short = " ".join(words[:14])
            queries: List[Tuple[str, str]] = [
                ("news", f'site:ilpost.it "{clean}"'),
                ("web", f'site:ilpost.it "{normalized}"'),
            ]
            if short:
                queries.append(("news", f"site:ilpost.it {short}"))
            if force and normalized != short:
                queries.append(("web", f"site:ilpost.it {short or normalized}"))

            seen_queries: set[Tuple[str, str]] = set()
            for transport, query in queries:
                query_key = (transport, query)
                if query_key in seen_queries:
                    continue
                seen_queries.add(query_key)
                attempts += 1
                try:
                    links = (self._ilpost_bing_web_rss_sync(query)
                             if transport == "web"
                             else self._ilpost_bing_rss_page_sync(query, 1))
                except Exception:
                    links = {}
                resolved = self._ilpost_match_listing_url(title, links)
                if resolved:
                    break
        finally:
            if acquired:
                self._ilpost_exact_slots.release()
            with self._ilpost_exact_lock:
                self._ilpost_exact_cache[key] = (time.time(), resolved)
                event = self._ilpost_exact_inflight.pop(key, None)
                if event is not None:
                    event.set()
            elapsed = time.perf_counter() - started
            if resolved:
                self._log(f"Il Post resolve Bing exact -> {_hostname(resolved)} attempts={attempts} {elapsed:.2f}s title={_clean_text(title)[:72]}")
            else:
                self._log(f"Il Post resolve Bing exact MISS attempts={attempts} {elapsed:.2f}s title={_clean_text(title)[:72]}")
        return resolved

    def _ilpost_fresh_prefetch_sync(self, items: List[Dict[str, Any]]) -> None:
        """Warm only the newest unresolved Il Post wrappers and their covers.

        Search engines lag new publication. The Google wrapper exists immediately,
        so a small delayed pass can resolve stories that were only seconds old when
        the feed first arrived. Keep this deliberately tiny so the rest of Edicola
        never pays for an 80-item retry storm.
        """
        now = int(time.time())
        candidates = [item for item in items if isinstance(item, dict)
                      and _hostname(str(item.get("sourceSiteUrl") or "")) == "ilpost.it"
                      and _is_google_news_url(str(item.get("url") or ""))]
        candidates.sort(key=lambda item: int(item.get("published") or 0), reverse=True)
        for item in candidates[:8]:
            published = int(item.get("published") or 0)
            if published > 0 and now - published > 48 * 60 * 60:
                continue
            target = str(item.get("url") or "")
            cached = self._read_resolve_cache(target)
            if cached and self._is_ilpost_public_url(cached):
                continue
            # Use the same complete resolver as the card/Reader. The Telegram
            # channel makes this useful immediately instead of merely repeating a
            # Google decoder that the live log shows can stay opaque for minutes.
            resolved = self._resolve_ilpost_item_sync(item)
            if not resolved or not self._is_ilpost_public_url(resolved):
                continue
            self._write_resolve_cache(target, resolved)
            try:
                # Warm og:image immediately too, so the card does not need the user
                # to open the Reader before its cover appears.
                self._enrich_one_image_sync(item, allow_rendered_fallback=False)
            except Exception:
                pass

    def _schedule_ilpost_fresh_prefetch(self, items: List[Dict[str, Any]]) -> None:
        if self._stopping.is_set():
            return
        candidates = [item for item in items if isinstance(item, dict) and _is_google_news_url(str(item.get("url") or ""))]
        candidates.sort(key=lambda item: int(item.get("published") or 0), reverse=True)
        sample = candidates[:8]
        if not sample:
            return
        snapshot = hashlib.sha1("|".join(str(item.get("url") or "") for item in sample).encode("utf-8", "ignore")).hexdigest()[:16]
        now = time.time()
        with self._ilpost_fresh_prefetch_lock:
            last = self._ilpost_fresh_prefetch_keys.get(snapshot, 0.0)
            if now - last < 60.0:
                return
            self._ilpost_fresh_prefetch_keys[snapshot] = now
            # Keep the bookkeeping bounded over long Decky sessions.
            self._ilpost_fresh_prefetch_keys = {key: stamp for key, stamp in self._ilpost_fresh_prefetch_keys.items() if now - stamp < 10 * 60}
        payload = [dict(item) for item in sample]
        try:
            self._prefetch_executor.submit(self._ilpost_fresh_prefetch_sync, payload)
        except Exception:
            return
        # A freshly published Google wrapper can need a short moment before its
        # decoder shell becomes usable. Retry twice without blocking the UI/feed.
        for delay in (12.0, 32.0):
            def retry(values=[dict(item) for item in payload]) -> None:
                if not self._stopping.is_set():
                    try:
                        self._prefetch_executor.submit(self._ilpost_fresh_prefetch_sync, values)
                    except RuntimeError:
                        pass
            self._schedule_background(delay, retry)

    def _resolve_ilpost_item_sync(self, item: Dict[str, Any]) -> str:
        target = str(item.get("url") or "").strip()
        if not _is_google_news_url(target) or _hostname(str(item.get("sourceSiteUrl") or "")) != "ilpost.it":
            return ""
        cached = self._read_resolve_cache(target)
        if cached and self._is_ilpost_public_url(cached):
            return cached
        title = str(item.get("title") or "").strip()
        # The official Il Post Telegram stream is updated as content is published.
        # It therefore closes the exact gap that Bing/Google leave for newest
        # headlines while remaining a single shared request for the whole tab.
        resolved = self._resolve_ilpost_telegram_sync(title, deep=False)
        if resolved:
            self._write_resolve_cache(target, resolved)
            return resolved
        # Then use the shared direct-link search index. Unlike the Google transport this
        # already yields ilpost.it URLs, and unlike an exact web search it is one
        # bounded operation shared by the entire Edicola.
        recent = self._ilpost_bing_recent_links_sync()
        resolved = self._ilpost_match_listing_url(title, recent)
        if resolved:
            self._write_resolve_cache(target, resolved)
            self._log(f"Il Post resolve Bing recent -> {_hostname(resolved)} title={title[:72]}")
            return resolved
        published = int(item.get("published") or 0)
        # Bing is excellent once a headline has been indexed, but the newest Il Post
        # stories in the user's logs consistently arrive in Google News first. For
        # fresh wrappers ask Google for its own destination before wasting time on
        # exact Bing searches that cannot know about the story yet.
        age_seconds = max(0, int(time.time()) - published) if published > 0 else 10**9
        if age_seconds <= 48 * 60 * 60:
            google_resolved = self._resolve_google_news_url_sync(target, str(item.get("sourceSiteUrl") or ""), fast=True, reader_rescue=True)
            if google_resolved and not _is_google_news_url(google_resolved) and self._is_ilpost_public_url(google_resolved):
                self._write_resolve_cache(target, google_resolved)
                self._log(f"Il Post resolve Google fresh -> {_hostname(google_resolved)} age={age_seconds}s title={title[:72]}")
                return google_resolved
        published = int(item.get("published") or 0)
        candidates: List[Tuple[str, str]] = []
        if published > 0:
            # Keep the official archive as one bounded fallback, not a chain of
            # neighbouring dates + stream. The shared Bing index is now the bulk
            # resolver; one archive request preserves an independent publisher path
            # without recreating long cover tails when Il Post blocks automation.
            dt = datetime.fromtimestamp(published, tz=timezone.utc)
            date_key = dt.strftime("%Y-%m-%d")
            archive_url = f"https://www.ilpost.it/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}/"
            candidates.append(("date:" + date_key, archive_url))
        seen: set[str] = set()
        for cache_key, listing_url in candidates:
            if cache_key in seen:
                continue
            seen.add(cache_key)
            links = self._ilpost_listing_links_sync(cache_key, listing_url)
            resolved = self._ilpost_match_listing_url(title, links)
            if resolved:
                self._write_resolve_cache(target, resolved)
                self._log(f"Il Post resolve archive: {cache_key} -> {_hostname(resolved)} title={title[:72]}")
                return resolved
        return ""

    def _resolve_cache_path(self, google_url: str) -> Path:
        return CACHE_DIR / f"resolve-{hashlib.sha1(str(google_url or '').encode('utf-8', 'ignore')).hexdigest()[:24]}.json"

    def _read_resolve_cache(self, google_url: str) -> str:
        payload = _load_json(self._resolve_cache_path(google_url), {})
        if not isinstance(payload, dict) or int(payload.get("cacheVersion") or 0) != RESOLVE_CACHE_VERSION:
            return ""
        if int(time.time()) - int(payload.get("fetchedAt") or 0) > GOOGLE_RESOLVE_CACHE_SECONDS:
            return ""
        value = str(payload.get("url") or "").strip()
        return value if value.startswith(("http://", "https://")) and not _is_google_news_url(value) else ""

    def _write_resolve_cache(self, google_url: str, resolved: str) -> None:
        if not resolved or _is_google_news_url(resolved):
            return
        try:
            _atomic_json(self._resolve_cache_path(google_url), {"cacheVersion": RESOLVE_CACHE_VERSION, "fetchedAt": int(time.time()), "url": resolved})
        except Exception:
            pass

    def _extract_decoded_google_url(self, payload: str) -> str:
        def visit(value: Any) -> str:
            if isinstance(value, str):
                candidate = html.unescape(value).replace("\\/", "/").strip()
                if candidate.startswith(("http://", "https://")) and not _is_google_news_url(candidate):
                    host = urllib.parse.urlparse(candidate).netloc.lower()
                    if host and "google." not in host and "gstatic.com" not in host and "googleusercontent.com" not in host:
                        return candidate
                try:
                    nested = json.loads(value)
                except Exception:
                    return ""
                return visit(nested)
            if isinstance(value, list):
                for item in value:
                    found = visit(item)
                    if found:
                        return found
            if isinstance(value, dict):
                for item in value.values():
                    found = visit(item)
                    if found:
                        return found
            return ""

        text = str(payload or "")
        for segment in text.split("\n\n"):
            chunk = segment.strip()
            if not chunk:
                continue
            if chunk.startswith(")]}'"):
                chunk = chunk.split("\n", 1)[-1]
            try:
                parsed = json.loads(chunk)
            except Exception:
                continue
            found = visit(parsed)
            if found:
                return found
        # Last-resort parse of the structured garturlres string only. Do not
        # scrape arbitrary external links from Google's HTML: older builds did
        # that and could map many articles to the same publisher homepage.
        match = re.search(r'garturlres[^h]{0,200}(https?:\?/\?/[^"\s]+)', text, re.I)
        if match:
            candidate = match.group(1).replace("\\/", "/")
            if candidate.startswith(("http://", "https://")) and not _is_google_news_url(candidate):
                return candidate
        return ""

    def _google_decoder_opener(self) -> Any:
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def _google_decoder_shell_sync(self, url: str, max_bytes: int, timeout: float, opener: Any = None) -> Tuple[bytes, str, str]:
        """Fetch a Google decoder shell without the feed-request consent cookie.

        Current Google News decoders fetch /articles/<id> with ordinary browser
        headers. Reusing News' feed request added a forced CONSENT=PENDING cookie,
        which can return a different shell and hide data-n-a-sg/data-n-a-ts.
        """
        request = urllib.request.Request(
            str(url or ""),
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                "Accept-Language": "it-IT,it;q=0.9,en;q=0.7",
                "Cache-Control": "no-cache",
            },
        )
        open_fn = opener.open if opener is not None else urllib.request.urlopen
        with open_fn(request, timeout=timeout) as response:
            data = response.read(max_bytes + 1)
            if len(data) > max_bytes:
                data = data[:max_bytes]
            return data, str(response.headers.get("Content-Type") or ""), str(response.geturl() or url)

    def _resolve_google_news_url_impl_sync(self, url: str, expected_site: str = "", fast: bool = False, reader_rescue: bool = False) -> str:
        value = str(url or "").strip()
        if not _is_google_news_url(value):
            return value
        cached = self._read_resolve_cache(value)
        if cached and (not expected_site or _host_matches(cached, expected_site)):
            return cached
        legacy = _decode_google_news_legacy(value)
        if legacy and (not expected_site or _host_matches(legacy, expected_site)):
            self._write_resolve_cache(value, legacy)
            return legacy
        article_id = urllib.parse.urlparse(value).path.rstrip("/").split("/")[-1]
        if not article_id:
            return value

        # Keep GET shell + Fbv4je POST in the same cookie session. Current public
        # decoders use one persistent HTTP client; using unrelated urlopen calls can
        # make brand-new wrappers intermittently fail even when older IDs decode.
        decoder_opener = self._google_decoder_opener()

        # Current Google News URLs need source-id + signature + timestamp followed
        # by Fbv4je. The RSS URL itself is the fastest shell and normally already
        # carries the decoder attributes; article reading keeps the compatibility
        # shell fallbacks, while card-cover discovery uses only this short hot path.
        # Modern Google News decoder attributes are most reliably exposed by the
        # canonical /articles/<id> shell. The RSS wrapper sometimes omits them
        # (observed with current Il Post fallback items), so even the fast path
        # gets one short canonical-shell attempt before giving up.
        quoted_id = urllib.parse.quote(article_id, safe='')
        canonical_shell = f"https://news.google.com/articles/{quoted_id}"
        # Upstream decoder implementations now try /articles/<id> first and only
        # then the RSS wrapper. This materially reduces missing decoder attributes
        # and rate-limit failures on current Google News URLs.
        shell_urls = [canonical_shell, value]
        # Explicit Reader opens may spend a couple of extra short attempts to
        # rescue Google wrappers that omit decoder attributes in the generic
        # shell. Keep these variants OUT of card-cover enrichment so the Edicola
        # remains fast even when dozens of Il Post items are unresolved.
        if fast and reader_rescue:
            shell_urls.extend([
                f"https://news.google.com/articles/{quoted_id}?hl=it&gl=IT&ceid=IT:it",
                f"https://news.google.com/read/{quoted_id}?hl=it&gl=IT&ceid=IT:it",
            ])
        if not fast:
            shell_urls.append(f"https://news.google.com/rss/articles/{quoted_id}")
        seen_shells: set[str] = set()
        for param_url in shell_urls:
            if param_url in seen_shells:
                continue
            seen_shells.add(param_url)
            try:
                data, content_type, _ = self._google_decoder_shell_sync(param_url, 480 * 1024 if fast else 850 * 1024, timeout=1.65 if fast else 7.0, opener=decoder_opener)
                page = self._decode(data, content_type)
                source_id, signature, timestamp = _extract_google_decode_params(page)
                # Very fresh wrappers can expose c-wiz[data-p] before the ordinary
                # signature/timestamp attributes. Replicate that alternate Fbv4je
                # request immediately; unlike Bing exact search this does not wait
                # for a third-party index to discover the new headline.
                if not (signature and timestamp):
                    data_p_request = _extract_google_data_p_request(page)
                    if data_p_request is not None:
                        try:
                            payload_row = ["Fbv4je", json.dumps(data_p_request, separators=(",", ":")), None, "generic"]
                            body = urllib.parse.urlencode({"f.req": json.dumps([[payload_row]], separators=(",", ":"))}).encode("utf-8")
                            request = urllib.request.Request(
                                "https://news.google.com/_/DotsSplashUi/data/batchexecute",
                                data=body, method="POST",
                                headers={
                                    "User-Agent": USER_AGENT,
                                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                                    "Accept": "*/*",
                                    "Origin": "https://news.google.com",
                                    "Referer": param_url,
                                },
                            )
                            with decoder_opener.open(request, timeout=2.4 if fast else 8.0) as response:
                                payload = response.read(1600 * 1024).decode("utf-8", "replace")
                            decoded = self._extract_decoded_google_url(payload)
                            if decoded and (not expected_site or _host_matches(decoded, expected_site)):
                                self._write_resolve_cache(value, decoded)
                                return decoded
                        except Exception:
                            pass
                if signature and timestamp and article_id:
                    # Current decoder implementations use the path article id; some
                    # older shells expose a distinct data-n-a-id. Try the path id
                    # first (current behaviour), then the page id only as a fallback.
                    decode_ids: List[str] = [article_id]
                    if source_id and source_id not in decode_ids:
                        decode_ids.append(source_id)
                    for decode_id in decode_ids:
                        inner = (
                            '["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],'
                            '"X","X",1,[1,1,1],1,1,null,0,0,null,0],'
                            f'"{decode_id}",{int(timestamp)},"{signature}"]'
                        )
                        # Current Fbv4je implementations send the compact two-field
                        # row. Keep the older generic shape as an immediate fallback
                        # because Google rolls variants gradually across regions.
                        payload_rows = (["Fbv4je", inner], ["Fbv4je", inner, None, "generic"])
                        for payload_row in payload_rows:
                            body = urllib.parse.urlencode({"f.req": json.dumps([[payload_row]], separators=(",", ":"))}).encode("utf-8")
                            request = urllib.request.Request(
                                "https://news.google.com/_/DotsSplashUi/data/batchexecute",
                                data=body,
                                method="POST",
                                headers={
                                    "User-Agent": USER_AGENT,
                                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                                    "Accept": "*/*",
                                    "Accept-Language": "it-IT,it;q=0.9,en;q=0.7",
                                    "Origin": "https://news.google.com",
                                    "Referer": param_url,
                                },
                            )
                            try:
                                with decoder_opener.open(request, timeout=2.4 if fast else 8.0) as response:
                                    payload = response.read(1600 * 1024).decode("utf-8", "replace")
                            except Exception:
                                continue
                            decoded = ""
                            # Prefer the exact structured response shape, then fall back
                            # to the tolerant parser for Google variants.
                            try:
                                segments = [segment for segment in payload.split("\n\n") if segment.strip()]
                                for segment in segments:
                                    cleaned = segment.strip()
                                    if cleaned.startswith(")]}'"):
                                        cleaned = cleaned.split("\n", 1)[-1]
                                    parsed = json.loads(cleaned)
                                    if isinstance(parsed, list):
                                        for row in parsed:
                                            if isinstance(row, list) and len(row) > 2 and isinstance(row[2], str):
                                                try:
                                                    nested = json.loads(row[2])
                                                    if isinstance(nested, list) and len(nested) > 1 and str(nested[1]).startswith(("http://", "https://")):
                                                        decoded = str(nested[1])
                                                        break
                                                except Exception:
                                                    pass
                                            if decoded:
                                                break
                                    if decoded:
                                        break
                            except Exception:
                                decoded = ""
                            if not decoded:
                                decoded = self._extract_decoded_google_url(payload)
                            if decoded and (not expected_site or _host_matches(decoded, expected_site)):
                                self._write_resolve_cache(value, decoded)
                                return decoded
            except Exception:
                continue

        if fast:
            return value

        # Compatibility fallback for IDs that still work with the older
        # signature-less request. Accept only a structured garturl response.
        try:
            req_data = [
                "garturlreq",
                [["en-US", "US", ["FINANCE_TOP_INDICES", "WEB_TEST_1_0_0"], None, None, 1, 1, "US:en", None, 180, None, None, None, None, None, 0, None, None, [1608992183, 723341000]], "en-US", "US", 1, [2, 3, 4, 8], 1, 0, "655000234", 0, 0, None, 0],
                article_id,
            ]
            batch = [[["Fbv4je", json.dumps(req_data, separators=(",", ":")), None, "generic"]]]
            body = urllib.parse.urlencode({"f.req": json.dumps(batch, separators=(",", ":"))}).encode("utf-8")
            request = urllib.request.Request(
                "https://news.google.com/_/DotsSplashUi/data/batchexecute?rpcids=Fbv4je",
                data=body,
                method="POST",
                headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8", "Referer": "https://news.google.com/"},
            )
            with decoder_opener.open(request, timeout=9.0) as response:
                payload = response.read(1400 * 1024).decode("utf-8", "replace")
            decoded = self._extract_decoded_google_url(payload)
            if decoded and (not expected_site or _host_matches(decoded, expected_site)):
                self._write_resolve_cache(value, decoded)
                return decoded
        except Exception:
            pass

        # Publisher-constrained last resort. We only accept an external URL from
        # Google's article shell when its host matches the source that produced
        # the feed item, avoiding the cache poisoning caused by old generic scraping.
        if expected_site:
            try:
                shell_url = f"https://news.google.com/articles/{urllib.parse.quote(article_id, safe='')}"
                data, content_type, _ = self._request(shell_url, 1400 * 1024, timeout=9.0)
                shell = html.unescape(self._decode(data, content_type)).replace("\\/", "/")
                candidates = re.findall(r"https?://[^\s\"'<>]+", shell, flags=re.I)
                for candidate in candidates:
                    candidate = candidate.rstrip(".,);]")
                    if _host_matches(candidate, expected_site):
                        self._write_resolve_cache(value, candidate)
                        return candidate
            except Exception:
                pass
        return value

    def _resolve_google_news_url_sync(self, url: str, expected_site: str = "", fast: bool = False, reader_rescue: bool = False) -> str:
        value = str(url or "").strip()
        if not _is_google_news_url(value):
            return value
        cached = self._read_resolve_cache(value)
        if cached and (not expected_site or _host_matches(cached, expected_site)):
            return cached

        with self._google_decode_inflight_lock:
            waiter = self._google_decode_inflight.get(value)
            if waiter is None:
                waiter = threading.Event()
                self._google_decode_inflight[value] = waiter
                owner = True
            else:
                owner = False
        if not owner:
            waiter.wait(timeout=7.5 if reader_rescue else 4.5)
            cached = self._read_resolve_cache(value)
            return cached if cached and (not expected_site or _host_matches(cached, expected_site)) else value

        acquired = False
        try:
            acquired = self._google_decode_slots.acquire(timeout=6.0 if reader_rescue else 3.5)
            if not acquired:
                return value
            return self._resolve_google_news_url_impl_sync(value, expected_site, fast, reader_rescue)
        finally:
            if acquired:
                self._google_decode_slots.release()
            with self._google_decode_inflight_lock:
                event = self._google_decode_inflight.pop(value, None)
                if event is not None:
                    event.set()

    def _apply_cached_item_enrichment(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Apply already-cached URL/image data without doing network work.

        This runs on the hot get_news path so returning to a tab can paint cached
        covers immediately instead of waiting for the asynchronous enrichment RPC.
        """
        result = dict(item)
        original_url = str(result.get("url") or "").strip()
        resolved = self._read_resolve_cache(original_url) if original_url else ""
        if resolved and not _is_google_news_url(resolved):
            result["url"] = resolved
        cache_keys = [value for value in (resolved, original_url) if value]
        for cache_key in cache_keys:
            cached = self._read_image_cache(cache_key)
            if not cached:
                continue
            filename = str(cached.get("cachedFile") or "")
            local = self._cached_image_url(filename)
            if local:
                result["image"] = local
                break
            remote = str(cached.get("remoteImage") or cached.get("image") or "")
            if remote:
                result["image"] = remote
                break
        # Article cache often knows the hero even when the feed did not.
        article_cached = self._read_article_cache(str(result.get("url") or original_url)) if (result.get("url") or original_url) else {}
        if article_cached and not str(result.get("image") or "").strip():
            hero = str(article_cached.get("hero") or "").strip()
            if hero:
                result["image"] = hero
        return result

    def _spaziogames_home_images_sync(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Conservative one-shot SpazioGames homepage index.

        Older builds searched a wide byte window around every link.  On dense
        pages that frequently attached the previous/next card image to the wrong
        article.  Reuse the generic strict index instead: JSON-LD or an image
        physically inside the article anchor only.
        """
        now = time.time()
        with self._spaziogames_home_lock:
            cached_at, cached_urls, cached_titles = self._spaziogames_home_cache
            if (cached_urls or cached_titles) and now - cached_at < 300:
                return dict(cached_urls), dict(cached_titles)
            try:
                data, content_type, final_url = self._request("https://www.spaziogames.it/", 2200 * 1024, timeout=2.2)
                text = self._decode(data, content_type)
                by_url, by_title = self._publisher_home_index_from_html(text, final_url)
            except Exception:
                by_url, by_title = {}, {}
            self._spaziogames_home_cache = (now, dict(by_url), dict(by_title))
            return by_url, by_title

    def _spaziogames_cover_for_item_sync(self, item: Dict[str, Any], resolved_url: str = "") -> str:
        site = _hostname(str(item.get("sourceSiteUrl") or ""))
        source_name = str(item.get("source") or "").lower()
        if "spaziogames" not in site and "spaziogames" not in source_name:
            return ""
        by_url, by_title = self._spaziogames_home_images_sync()
        for value in (resolved_url, str(item.get("resolvedUrl") or ""), str(item.get("url") or "")):
            key = _normalized_article_url(value)
            if key and key in by_url:
                return by_url[key]
        title_key = re.sub(r"[^a-z0-9]+", " ", str(item.get("title") or "").lower()).strip()
        # Exact title only.  SpazioGames headlines are stable enough that a fuzzy
        # match is not worth the risk of assigning another card's artwork.
        return by_title.get(title_key, "") if title_key else ""

    def _publisher_home_index_from_html(self, text: str, final_url: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Build a lightweight URL/title -> image index from one publisher page.

        This is intentionally generic and conservative: it only accepts links on
        the publisher host and credible images. One homepage request can therefore
        satisfy dozens of card covers, which is dramatically cheaper than opening
        every article page or invoking a rendered Reader per card.
        """
        raw = str(text or "")
        by_url: Dict[str, str] = {}
        by_title: Dict[str, str] = {}

        def add(href: str, title: str, image: str) -> None:
            href = _absolute(final_url, str(href or "").strip())
            image = _absolute(final_url, str(image or "").strip())
            if not href.startswith(("http://", "https://")) or not image.startswith(("http://", "https://")):
                return
            if not _host_matches(href, final_url) or not _image_candidate_ok(image):
                return
            image = _prefer_card_image_url(image)
            url_key = _normalized_article_url(href)
            if url_key:
                by_url[url_key] = image
            title_key = re.sub(r"[^a-z0-9]+", " ", _clean_text(title).lower()).strip()
            if len(title_key) >= 12:
                by_title[title_key] = image

        # Structured article data is cheap and often gives the cleanest mapping.
        try:
            for obj in _json_ld_objects(raw[: min(len(raw), 2600000)]):
                if not isinstance(obj, dict):
                    continue
                obj_type = str(obj.get("@type") or "").lower()
                if "article" not in obj_type and "news" not in obj_type and "blogposting" not in obj_type:
                    continue
                href = str(obj.get("url") or "")
                main = obj.get("mainEntityOfPage")
                if not href and isinstance(main, dict):
                    href = str(main.get("@id") or main.get("url") or "")
                title = str(obj.get("headline") or obj.get("name") or "")
                image = _ld_best_image([obj], final_url)
                if href and image:
                    add(href, title, image)
        except Exception:
            pass

        # Real homepage cards usually keep the image inside the anchor or within a
        # nearby card wrapper. A bounded surrounding window handles both patterns.
        for match in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a\s*>", raw, re.I | re.S):
            href = _absolute(final_url, match.group(1))
            if not _host_matches(href, final_url):
                continue
            path = urllib.parse.urlparse(href).path.rstrip("/")
            if not path or path.count("/") < 1:
                continue
            body = match.group(2)
            # Never borrow an image from surrounding markup: dense homepages often
            # place several links beside one another and that was the main source
            # of repeated/wrong artwork across cards.
            image = _find_html_image(body, final_url)
            if not image:
                continue
            title = _clean_text(body)
            add(href, title, image)
        return by_url, by_title

    def _publisher_home_index_from_markdown(self, markdown: str, base_url: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Index rendered homepage markdown without cross-card image borrowing.

        An image may be paired with a nearby link only when its alt text strongly
        matches that link title, and each image is consumed at most once.
        """
        lines = [line.strip() for line in str(markdown or "").splitlines() if line.strip()]
        by_url: Dict[str, str] = {}
        by_title: Dict[str, str] = {}
        image_re = re.compile(r"!\[([^\]]*)\]\((https?://[^\s\)]+)(?:\s+[^\)]*)?\)", re.I)
        link_re = re.compile(r"(?<!!)\[([^\]]{6,})\]\((https?://[^\s\)]+)(?:\s+[^\)]*)?\)", re.I)
        used_images: set[str] = set()

        def title_words(value: str) -> set[str]:
            return {word for word in re.sub(r"[^a-z0-9]+", " ", _clean_text(value).lower()).split() if len(word) >= 3}

        def similarity(left: str, right: str) -> float:
            a, b = title_words(left), title_words(right)
            if len(a) < 2 or len(b) < 2:
                return 0.0
            overlap = len(a & b)
            if not overlap:
                return 0.0
            return max(overlap / len(a | b), overlap / min(len(a), len(b)))

        def add(url: str, title: str, image: str) -> None:
            url = html.unescape(str(url or "")).strip()
            image = html.unescape(str(image or "")).strip()
            if not url.startswith(("http://", "https://")) or not image.startswith(("http://", "https://")):
                return
            if not _host_matches(url, base_url) or not _image_candidate_ok(image):
                return
            image = _prefer_card_image_url(image)
            key = _normalized_article_url(url)
            if key:
                by_url[key] = image
            title_key = re.sub(r"[^a-z0-9]+", " ", _clean_text(title).lower()).strip()
            if len(title_key) >= 12:
                by_title[title_key] = image

        # Strongest case: image and article link are emitted together.
        for line in lines:
            images = list(image_re.finditer(line))
            links = list(link_re.finditer(line))
            if not images or not links:
                continue
            for link in links:
                ranked = sorted(((similarity(link.group(1), image.group(1)), image) for image in images), key=lambda row: row[0], reverse=True)
                if ranked and (ranked[0][0] >= .80 or len(images) == 1 and len(links) == 1):
                    image = ranked[0][1]
                    add(link.group(2), link.group(1), image.group(2))
                    used_images.add(image.group(2))

        # Separate markdown lines are common.  Search only two lines around the
        # link and require strong title/alt agreement; never map one image to four
        # unrelated links as the previous implementation did.
        for index, line in enumerate(lines):
            for link in link_re.finditer(line):
                window = lines[max(0, index - 2): min(len(lines), index + 3)]
                candidates = []
                for row in window:
                    for image in image_re.finditer(row):
                        if image.group(2) in used_images:
                            continue
                        candidates.append((similarity(link.group(1), image.group(1)), image))
                candidates.sort(key=lambda row: row[0], reverse=True)
                if not candidates or candidates[0][0] < .86:
                    continue
                if len(candidates) > 1 and candidates[0][0] - candidates[1][0] < .10:
                    continue
                image = candidates[0][1]
                add(link.group(2), link.group(1), image.group(2))
                used_images.add(image.group(2))
        return by_url, by_title

    def _publisher_home_images_sync(self, site_url: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Fetch/index a publisher homepage once with single-flight semantics."""
        site = str(site_url or "").strip()
        host = _hostname(site)
        if not site.startswith(("http://", "https://")) or not host or "news.google." in host:
            return {}, {}
        now = time.time()
        owner = False
        event: Optional[threading.Event] = None
        with self._publisher_home_lock:
            cached = self._publisher_home_cache.get(host)
            if cached and now - cached[0] < 180:
                return dict(cached[1]), dict(cached[2])
            event = self._publisher_home_inflight.get(host)
            if event is None:
                event = threading.Event()
                self._publisher_home_inflight[host] = event
                owner = True
        if not owner:
            # One publisher scan is already running. Waiting is still much cheaper
            # than launching 20 article requests for 20 cards from the same source.
            event.wait(5.2)
            with self._publisher_home_lock:
                cached = self._publisher_home_cache.get(host)
                return (dict(cached[1]), dict(cached[2])) if cached else ({}, {})

        by_url: Dict[str, str] = {}
        by_title: Dict[str, str] = {}
        final_url = site
        try:
            data, content_type, final_url = self._request(site, 2800 * 1024, timeout=1.9)
            text = self._decode(data, content_type)
            by_url, by_title = self._publisher_home_index_from_html(text, final_url)
        except Exception:
            pass

        # If a site blocks urllib, allow at most two concurrent *homepage* Reader
        # fallbacks globally. This rescues publishers such as Il Post without the
        # previous 50+ simultaneous Jina cover calls that caused rate-limit tails.
        if len(by_title) < 3 and self._publisher_home_jina_slots.acquire(timeout=0.03):
            try:
                rendered = self._jina_reader_article_sync(site, timeout=3.5)
                raw = str(rendered.get("rawContent") or "") if rendered else ""
                rendered_base = str(rendered.get("url") or final_url or site) if rendered else (final_url or site)
                if raw:
                    md_urls, md_titles = self._publisher_home_index_from_markdown(raw, rendered_base)
                    by_url.update(md_urls)
                    by_title.update(md_titles)
            except Exception:
                pass
            finally:
                self._publisher_home_jina_slots.release()

        with self._publisher_home_lock:
            # Cache even an empty result briefly, otherwise a blocked publisher
            # would be hammered again for every card batch.
            self._publisher_home_cache[host] = (time.time(), dict(by_url), dict(by_title))
            finished = self._publisher_home_inflight.pop(host, None)
            if finished is not None:
                finished.set()
        return by_url, by_title

    def _publisher_home_cover_for_item_sync(self, item: Dict[str, Any], resolved_url: str = "") -> str:
        site = str(item.get("sourceSiteUrl") or "").strip()
        if not site:
            return ""
        by_url, by_title = self._publisher_home_images_sync(site)
        for value in (resolved_url, str(item.get("resolvedUrl") or ""), str(item.get("url") or "")):
            key = _normalized_article_url(value)
            if key and key in by_url:
                return by_url[key]
        title_key = re.sub(r"[^a-z0-9]+", " ", str(item.get("title") or "").lower()).strip()
        if not title_key:
            return ""
        if title_key in by_title:
            return by_title[title_key]
        target_words = {word for word in title_key.split() if len(word) >= 3}
        if len(target_words) < 3:
            return ""
        best = ""
        best_score = 0.0
        second_score = 0.0
        for key, image in by_title.items():
            words = {word for word in key.split() if len(word) >= 3}
            if not words:
                continue
            overlap = len(target_words & words)
            union = len(target_words | words)
            jaccard = overlap / union if union else 0.0
            coverage = overlap / min(len(target_words), len(words))
            score = max(jaccard, coverage * 0.90)
            if score > best_score:
                second_score = best_score
                best_score, best = score, image
            elif score > second_score:
                second_score = score
        # Fuzzy homepage matches are intentionally rare.  A wrong cover is worse
        # than a publisher fallback, and direct article metadata runs immediately
        # after this stage anyway.
        return best if best_score >= 0.88 and best_score - second_score >= 0.10 else ""

    def _enrich_one_image_sync(self, item: Dict[str, Any], allow_rendered_fallback: bool = False) -> Tuple[str, str, str]:
        article_id = str(item.get("id") or "")
        target = str(item.get("url") or "").strip()
        supplied_image = str(item.get("image") or "").strip()
        if not article_id or not target.startswith(("http://", "https://")):
            return article_id, supplied_image, target

        # Cheapest path first: if RSS/Atom already gave us a real image, never do
        # URL decoding, homepage scraping or publisher requests for this card.
        if supplied_image and _image_candidate_ok(supplied_image):
            supplied_image = _prefer_card_image_url(supplied_image)
            self._write_image_cache(target, supplied_image, "")
            self._schedule_image_cache_warm(supplied_image, str(item.get("sourceSiteUrl") or target), target)
            return article_id, supplied_image, target

        source_site = str(item.get("sourceSiteUrl") or "")
        source_host = _hostname(source_site)
        resolved = ""
        # Il Post Google wrappers are best handled through the publisher's own
        # archive index before any homepage guess. This both gives the Reader the
        # real URL and prevents an unnecessary publisher-home scan from delaying
        # dozens of same-day cards.
        if source_host == "ilpost.it" and _is_google_news_url(target):
            resolved = self._resolve_ilpost_item_sync(item)

        # Batch publisher-home lookup remains the cheap first path for every other
        # publisher. SpazioGames keeps its proven specialised matcher.
        image = ""
        if source_host != "ilpost.it" or not resolved:
            image = self._spaziogames_cover_for_item_sync(item)
            if not image:
                image = self._publisher_home_cover_for_item_sync(item)
        if image:
            image = _prefer_card_image_url(image)
            self._write_image_cache(target, image, "")
            self._schedule_image_cache_warm(image, source_site or target, target)
            return article_id, image, resolved or target

        if not resolved:
            resolved = self._resolve_google_news_url_sync(target, source_site, fast=True)
        cache_key = resolved or target
        cached = self._read_image_cache(cache_key)
        now = int(time.time())
        if cached and now - int(cached.get("fetchedAt") or 0) < IMAGE_CACHE_SECONDS:
            filename = str(cached.get("cachedFile") or "")
            local = self._cached_image_url(filename)
            if local:
                return article_id, local, resolved
            remote = str(cached.get("remoteImage") or cached.get("image") or "")
            if remote:
                self._schedule_image_cache_warm(remote, resolved or target, cache_key)
                return article_id, remote, resolved

        # Do not invoke Jina per card. When Google News cannot be decoded quickly,
        # leave the card on the publisher/source fallback rather than adding a
        # rate-limited rendered request that may finish minutes later. The generic
        # publisher-home scan above already had one bounded rendered opportunity.
        if _is_google_news_url(resolved):
            self._write_image_cache(cache_key, "", "")
            return article_id, "", resolved

        image = ""
        try:
            data, content_type, final_url = self._request(resolved, 900 * 1024, timeout=2.25)
            if final_url and not _is_google_news_url(final_url):
                resolved = final_url
                cache_key = resolved
            text = self._decode(data, content_type)
            head = _HeadParser()
            head.feed(text[: min(len(text), 1000000)])
            image = _best_meta_image(head, final_url)
            if not image:
                image = _ld_best_image(_json_ld_objects(text[: min(len(text), 1800000)]), final_url)
            if not image:
                regions: List[str] = []
                regions.extend(match.group(1) for match in re.finditer(r"<article\b[^>]*>(.*?)</article\s*>", text, re.I | re.S))
                regions.extend(match.group(1) for match in re.finditer(r"<main\b[^>]*>(.*?)</main\s*>", text, re.I | re.S))
                regions.sort(key=lambda value: len(_clean_text(value)), reverse=True)
                for region in regions[:4] + [text[: min(len(text), 2200000)]]:
                    candidate = _find_html_image(region, final_url)
                    if candidate:
                        image = candidate
                        break
        except Exception:
            image = ""

        if image:
            image = _prefer_card_image_url(image)
            self._write_image_cache(cache_key, image, "")
            if cache_key != target:
                self._write_image_cache(target, image, "")
            self._schedule_image_cache_warm(image, resolved, cache_key)
        else:
            self._write_image_cache(cache_key, "", "")
        return article_id, image, resolved

    def _should_rendered_cover_fallback(self, item: Dict[str, Any], resolved_hint: str = "") -> bool:
        """Allow a strict article-specific rendered fallback only where it helps.

        We never use fuzzy rendered-homepage guessing here. A Google-backed story
        or a known bot-blocking publisher gets one bounded Reader request for THAT
        article, which preserves image correctness while filling lower-page holes.
        """
        site_host = _hostname(str(item.get("sourceSiteUrl") or ""))
        target = str(item.get("url") or "")
        resolved = str(resolved_hint or "")
        if site_host in {"ilpost.it", "open.online"}:
            return True
        # Generalise safely to Google-wrapper stories that were actually decoded to
        # their publisher. Do not render arbitrary unresolved Google shells for every
        # source, which would recreate the old rate-limit storm.
        return _is_google_news_url(target) and bool(resolved) and not _is_google_news_url(resolved)

    def _rendered_cover_only_sync(self, item: Dict[str, Any], resolved_hint: str = "") -> Tuple[str, str, str]:
        """Rendered/Jina cover fallback without repeating the fast HTML request.

        The fast worker already attempted Google decoding + publisher metadata.
        Re-running that whole path in the slow pool doubled latency and network
        work. This continuation performs only the rendered fallback, with a short
        cover-specific timeout so a complete 120-card tab can converge within a
        bounded window instead of leaving permanent placeholders.
        """
        article_id = str(item.get("id") or "").strip()
        target = str(item.get("url") or "").strip()
        if not article_id or not target.startswith(("http://", "https://")):
            return article_id, "", resolved_hint or target
        cached = self._apply_cached_item_enrichment(item)
        cached_image = str(cached.get("image") or "").strip()
        if cached_image:
            return article_id, cached_image, str(cached.get("url") or resolved_hint or target)

        rendered_target = str(resolved_hint or target).strip()
        is_ilpost = _hostname(str(item.get("sourceSiteUrl") or "")) == "ilpost.it"
        if _is_google_news_url(rendered_target) and is_ilpost:
            archive_target = self._resolve_ilpost_item_sync(item)
            if not archive_target:
                # Exact Bing rescue is useful for older/special headlines, but it
                # predictably misses brand-new Il Post stories until Bing indexes
                # them. Skip that known-dead branch for the first 90 minutes: the
                # fresh Google decoder above is both faster and index-independent.
                published = int(item.get("published") or 0)
                age_seconds = max(0, int(time.time()) - published) if published > 0 else 10**9
                if age_seconds > 90 * 60:
                    archive_target = self._resolve_ilpost_bing_exact_sync(str(item.get("title") or ""), force=False)
            if archive_target:
                rendered_target = archive_target
                self._write_resolve_cache(target, archive_target)
            else:
                # Rendering the still-opaque Google shell has proven effectively
                # useless for Il Post and used to pin a slow worker for another
                # ~5 seconds. Move immediately to the next headline so the exact
                # resolver can sweep the whole tab instead of leaving lower cards
                # untouched while doomed Jina calls occupy the pool.
                return article_id, "", rendered_target

        # Once Il Post has a real publisher URL, try its metadata before spending a
        # rendered/Jina request. Even when the body is bot-blocked, og:image is often
        # available and this makes cards converge much faster.
        if is_ilpost and rendered_target and not _is_google_news_url(rendered_target):
            try:
                data, content_type, final_url = self._request(rendered_target, 950 * 1024, timeout=2.4)
                raw = self._decode(data, content_type)
                head = _HeadParser()
                head.feed(raw[: min(len(raw), 1000000)])
                direct_image = _best_meta_image(head, final_url)
                if not direct_image:
                    direct_image = _ld_best_image(_json_ld_objects(raw[: min(len(raw), 1800000)]), final_url)
                if direct_image:
                    image = _prefer_card_image_url(direct_image)
                    self._write_image_cache(rendered_target, image, "")
                    if rendered_target != target:
                        self._write_image_cache(target, image, "")
                    self._schedule_image_cache_warm(image, rendered_target, rendered_target)
                    return article_id, image, rendered_target
            except Exception:
                pass

        rendered = self._jina_reader_article_sync(rendered_target, timeout=JINA_COVER_TIMEOUT)
        if not rendered:
            return article_id, "", rendered_target
        image = str(rendered.get("hero") or "").strip()
        resolved = str(rendered.get("url") or rendered_target).strip()
        if resolved and not _is_google_news_url(resolved) and _is_google_news_url(target):
            self._write_resolve_cache(target, resolved)
        if not image:
            return article_id, "", resolved
        image = _prefer_card_image_url(image)
        cache_key = resolved if resolved and not _is_google_news_url(resolved) else target
        self._write_image_cache(cache_key, image, "")
        if cache_key != target:
            self._write_image_cache(target, image, "")
        self._schedule_image_cache_warm(image, resolved or target, cache_key)
        return article_id, image, resolved

    def _start_cover_enrichment_sync(self, items: List[Dict[str, Any]], rendered_limit: int = 0, background: bool = False) -> Dict[str, Any]:
        """Start finite concurrent cover discovery with a bounded strict slow lane."""
        safe = [item for item in (items or []) if isinstance(item, dict) and str(item.get("url") or "").startswith(("http://", "https://"))]
        queued: List[Tuple[Dict[str, Any], str]] = []
        for item in safe:
            article_id = str(item.get("id") or "").strip()
            target = str(item.get("url") or "").strip()
            token = article_id or target
            if not token:
                continue
            cached_item = self._apply_cached_item_enrichment(item)
            if str(cached_item.get("image") or "").strip():
                with self._cover_inflight_lock:
                    self._cover_unavailable.discard(article_id)
                continue
            with self._cover_inflight_lock:
                if token in self._cover_inflight:
                    continue
                self._cover_inflight.add(token)
                self._cover_unavailable.discard(article_id)
            queued.append((dict(item), token))

        if not queued:
            return {"ok": True, "started": 0, "pending": len(self._cover_inflight), "slowBudget": 0, "background": bool(background)}

        batch_started = time.perf_counter()
        metrics_lock = threading.Lock()
        remaining = {"count": len(queued), "ok": 0, "miss": 0, "slow": 0, "slowOk": 0, "unavailable": 0}
        per_source: Dict[str, List[int]] = {}

        def finish(payload: Dict[str, Any], key: str, image: str, used_slow: bool = False, unavailable: bool = False) -> None:
            article_id = str(payload.get("id") or "").strip()
            with self._cover_inflight_lock:
                self._cover_inflight.discard(key)
                if image:
                    self._cover_unavailable.discard(article_id)
                elif unavailable and article_id:
                    self._cover_unavailable.add(article_id)
            source_name = str(payload.get("source") or "?")[:48]
            should_log = False
            summary = ""
            with metrics_lock:
                bucket = per_source.setdefault(source_name, [0, 0])
                bucket[0] += 1
                if image:
                    bucket[1] += 1
                    remaining["ok"] += 1
                    if used_slow:
                        remaining["slowOk"] += 1
                else:
                    remaining["miss"] += 1
                    if unavailable:
                        remaining["unavailable"] += 1
                remaining["count"] -= 1
                if remaining["count"] == 0:
                    elapsed = time.perf_counter() - batch_started
                    parts = ", ".join(f"{name}:{ok}/{total}" for name, (total, ok) in sorted(per_source.items()))
                    summary = (f"cover batch {'background' if background else 'visible'}: {elapsed:.2f}s "
                               f"ok={remaining['ok']}/{len(queued)} miss={remaining['miss']} "
                               f"rendered={remaining['slowOk']}/{remaining['slow']} unavailable={remaining['unavailable']} [{parts}]")
                    should_log = True
            if should_log:
                self._log(summary)

        slow_executor = self._cover_background_slow_executor if background else self._cover_slow_executor

        def slow_task(payload: Dict[str, Any], key: str, resolved: str) -> None:
            image = ""
            final_resolved = str(resolved or payload.get("url") or "")
            try:
                _article_id, image, final_resolved = self._rendered_cover_only_sync(payload, resolved)
            except Exception:
                image = ""
            # A missing cover or an unresolved Google shell must never make an
            # article disappear from the Edicola. Keep the story visible and
            # clickable; cover polling will simply retire after its normal bounded
            # misses and a later refresh can retry resolution.
            finish(payload, key, image, True, False)

        def task(payload: Dict[str, Any], key: str) -> None:
            image = ""
            resolved = ""
            try:
                _article_id, image, resolved = self._enrich_one_image_sync(payload, False)
            except Exception:
                image = ""
            if not image and self._should_rendered_cover_fallback(payload, resolved):
                try:
                    with metrics_lock:
                        remaining["slow"] += 1
                    slow_executor.submit(slow_task, payload, key, resolved)
                    return
                except Exception:
                    pass
            finish(payload, key, image, False)

        executor = self._cover_background_executor if background else self._cover_executor
        started = 0
        for payload, token in queued:
            try:
                executor.submit(task, payload, token)
                started += 1
            except Exception:
                finish(payload, token, "", False)
        return {"ok": True, "started": started, "pending": len(self._cover_inflight), "slowBudget": len(queued), "background": bool(background)}

    def _cached_cover_status_sync(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        images: Dict[str, str] = {}
        resolved_urls: Dict[str, str] = {}
        pending: List[str] = []
        with self._cover_inflight_lock:
            inflight = set(self._cover_inflight)
        for item in (items or []):
            if not isinstance(item, dict):
                continue
            article_id = str(item.get("id") or "").strip()
            if not article_id:
                continue
            enriched = self._apply_cached_item_enrichment(item)
            image = str(enriched.get("image") or "").strip()
            if image:
                images[article_id] = image
                with self._cover_inflight_lock:
                    self._cover_unavailable.discard(article_id)
            original_url = str(item.get("url") or "").strip()
            enriched_url = str(enriched.get("url") or "").strip()
            if enriched_url and enriched_url != original_url and not _is_google_news_url(enriched_url):
                resolved_urls[article_id] = enriched_url
            if article_id in inflight or original_url in inflight:
                pending.append(article_id)
        # Keep the field for frontend/backward compatibility, but it is
        # intentionally always empty: cover extraction failure is not a reason to
        # remove a news item.
        return {"ok": True, "images": images, "resolvedUrls": resolved_urls, "pending": pending, "unavailable": []}

    def _enrich_images_sync(self, items: List[Dict[str, Any]], limit: int = 40) -> Dict[str, Any]:
        safe = [item for item in (items or []) if isinstance(item, dict) and str(item.get("url") or "").startswith(("http://", "https://"))]
        requested = max(0, min(int(limit or 40), 160))
        # Feed-provided images are cheap to cache. Missing covers need article-page
        # extraction, so prioritize them but allow a full QAM refresh to warm many
        # more cards than older builds did.
        missing = [item for item in safe if not str(item.get("image") or "").strip()][:requested]
        existing = [item for item in safe if str(item.get("image") or "").strip()][:requested]
        candidates = (missing + existing)[:requested]
        images: Dict[str, str] = {}
        resolved_urls: Dict[str, str] = {}
        if not candidates:
            return {"ok": True, "images": images, "resolvedUrls": resolved_urls}
        with ThreadPoolExecutor(max_workers=min(32, max(1, len(candidates))), thread_name_prefix="NewsImages") as pool:
            # Bulk warming deliberately has no per-card rendered/Jina tail. Every
            # candidate uses the finite RSS -> shared publisher-home -> cheap
            # metadata path, so background work cannot monopolize the Reader.
            futures = [pool.submit(self._enrich_one_image_sync, item, False) for item in candidates]
            for future in as_completed(futures):
                try:
                    article_id, image, resolved = future.result()
                    if article_id and image:
                        images[article_id] = image
                    if article_id and resolved and not _is_google_news_url(resolved):
                        resolved_urls[article_id] = resolved
                except Exception:
                    continue
        return {"ok": True, "images": images, "resolvedUrls": resolved_urls}

    def _request(self, url: str, max_bytes: int, timeout: float = 12.0, accept: str = "text/html,application/xhtml+xml,application/xml,text/xml,application/rss+xml,application/atom+xml,*/*;q=0.5") -> Tuple[bytes, str, str]:
        headers = {"User-Agent": USER_AGENT, "Accept": accept, "Accept-Language": "it-IT,it;q=0.8,en;q=0.6"}
        if _hostname(url) == "news.google.com":
            headers.update({
                "Cookie": "CONSENT=PENDING+987",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Upgrade-Insecure-Requests": "1",
            })
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(max_bytes + 1)
            if len(data) > max_bytes:
                data = data[:max_bytes]
            content_type = str(response.headers.get("Content-Type") or "")
            final_url = str(response.geturl() or url)
            return data, content_type, final_url

    def _decode(self, data: bytes, content_type: str) -> str:
        match = re.search(r"charset=([\w.-]+)", content_type or "", flags=re.I)
        encodings = [match.group(1)] if match else []
        encodings += ["utf-8", "iso-8859-1"]
        for encoding in encodings:
            try:
                return data.decode(encoding)
            except Exception:
                continue
        return data.decode("utf-8", "replace")

    def _looks_feed(self, data: bytes) -> bool:
        head = data[:1500].lstrip().lower()
        return b"<rss" in head or b"<feed" in head or b"<rdf:rdf" in head

    def _discover_source_sync(self, url: str, country: str, preferred_name: str = "") -> Dict[str, Any]:
        value = str(url or "").strip()
        if not value:
            return {"ok": False, "error": "Inserisci l'indirizzo del sito o del feed."}
        if not re.match(r"^https?://", value, flags=re.I):
            value = "https://" + value
        try:
            data, content_type, final_url = self._request(value, 2 * 1024 * 1024)
        except Exception as exc:
            fallback_feed = _google_news_site_feed(value, country)
            if fallback_feed:
                parsed = urllib.parse.urlparse(value)
                fallback_name = _clean_text(preferred_name) or parsed.netloc.replace("www.", "") or "Fonte"
                return {"ok": True, "source": self._normalized_source({
                    "name": fallback_name,
                    "country": country,
                    "siteUrl": value,
                    "feedUrl": fallback_feed,
                    "tags": ["all"],
                    "custom": True,
                    "enabled": True,
                }), "fallback": True}
            return {"ok": False, "error": f"Impossibile raggiungere la fonte: {exc}"}

        feed_url = ""
        site_url = final_url
        page_title = ""
        parsed_final = urllib.parse.urlparse(final_url)
        if "youtube.com" in parsed_final.netloc.lower():
            page_text = self._decode(data, content_type)
            channel_id = ""
            direct = re.search(r"/channel/(UC[A-Za-z0-9_-]{20,30})", final_url)
            if direct:
                channel_id = direct.group(1)
            if not channel_id:
                for pattern in [r'"channelId"\s*:\s*"(UC[A-Za-z0-9_-]{20,30})"', r'itemprop=["\']channelId["\'][^>]+content=["\'](UC[A-Za-z0-9_-]{20,30})']:
                    match = re.search(pattern, page_text, flags=re.I)
                    if match:
                        channel_id = match.group(1)
                        break
            if channel_id:
                feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                parser = _HeadParser()
                try:
                    parser.feed(page_text[:750000])
                except Exception:
                    pass
                page_title = _clean_text(parser.meta.get("og:title") or parser.title)
        if not feed_url and (self._looks_feed(data) or "xml" in content_type.lower()):
            feed_url = final_url
            try:
                parsed_feed = _parse_feed_document(data)
                page_title = parsed_feed.feed_title
                link = parsed_feed.feed_link
                if link.startswith("http"):
                    site_url = link
            except Exception:
                pass
        elif not feed_url:
            text = self._decode(data, content_type)
            parser = _HeadParser()
            try:
                parser.feed(text)
            except Exception:
                pass
            page_title = _clean_text(parser.meta.get("og:site_name") or parser.title)
            candidates: List[str] = []
            for link in parser.links:
                rel = link.get("rel", "").lower()
                typ = link.get("type", "").lower()
                href = link.get("href", "")
                if "alternate" in rel and href and ("rss" in typ or "atom" in typ or "xml" in typ):
                    candidates.append(_absolute(final_url, href))
            base = final_url.rstrip("/")
            parsed = urllib.parse.urlparse(final_url)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            candidates.extend([
                origin + "/feed/", origin + "/feed", origin + "/rss", origin + "/rss.xml",
                origin + "/feed.xml", origin + "/atom.xml", base + "/feed/",
            ])
            seen: set[str] = set()
            for candidate in candidates:
                if not candidate or candidate in seen:
                    continue
                seen.add(candidate)
                try:
                    probe, _, probe_final = self._request(candidate, 512 * 1024, timeout=7.0)
                    if self._looks_feed(probe):
                        feed_url = probe_final
                        break
                except Exception:
                    continue

        if not feed_url:
            # A site may intentionally expose no public RSS/Atom feed. Keep the
            # source usable by falling back to a country-aware publisher feed.
            feed_url = _google_news_site_feed(site_url, country)
        if not feed_url:
            return {"ok": False, "error": "Non sono riuscito a creare una fonte utilizzabile per questo indirizzo."}

        name = _clean_text(preferred_name) or page_title or urllib.parse.urlparse(site_url).netloc.replace("www.", "")
        source = self._normalized_source({
            "name": name,
            "country": country,
            "siteUrl": site_url,
            "feedUrl": feed_url,
            "tags": ["all"],
            "custom": True,
            "enabled": True,
        })
        return {"ok": True, "source": source}

    def _feed_cache_path(self, source_id: str) -> Path:
        return CACHE_DIR / f"feed-{re.sub(r'[^A-Za-z0-9_-]+', '_', source_id)}.json"

    def _read_feed_cache(self, source_id: str) -> Dict[str, Any]:
        payload = _load_json(self._feed_cache_path(source_id), {})
        if not isinstance(payload, dict) or int(payload.get("cacheVersion") or 0) != FEED_CACHE_VERSION:
            return {}
        return payload

    def _write_feed_cache(self, source_id: str, payload: Dict[str, Any]) -> None:
        value = dict(payload or {})
        value["cacheVersion"] = FEED_CACHE_VERSION
        _atomic_json(self._feed_cache_path(source_id), value)

    def _parse_feed(self, source: Dict[str, Any], data: bytes, final_url: str) -> List[Dict[str, Any]]:
        parsed = _parse_feed_document(data)
        source_id = str(source.get("id") or "")
        source_name = str(source.get("name") or "Fonte")
        feed_base = final_url or str(source.get("feedUrl") or source.get("siteUrl") or "")
        google_transport = "news.google." in _hostname(feed_base)
        now_ts = int(time.time())
        google_oldest = now_ts - 45 * 86400
        google_future_limit = now_ts + 2 * 86400
        result: List[Dict[str, Any]] = []
        for node in parsed.items[:80]:
            title = _clean_text(_item_text(node, ["title"]))
            item_source_hint = _clean_text(node.get("sourceName") or "")
            if item_source_hint and title.lower().endswith((" - " + item_source_hint).lower()):
                title = title[: -(len(item_source_hint) + 3)].rstrip()
            if not title:
                continue
            link = ""
            for candidate in node.get("links") or []:
                href = str(candidate.get("href") or "")
                rel = str(candidate.get("rel") or "alternate")
                if href and rel in {"alternate", ""}:
                    link = _absolute(feed_base, href)
                    break
            if not link:
                link = _absolute(feed_base, _item_text(node, ["link", "guid", "id"]))
            description_raw = _item_text(node, ["encoded", "content", "description", "summary"])
            excerpt = _clean_text(description_raw)[:420]
            # Preserve a bounded copy of content:encoded/content for the Reader.
            # Several publishers expose useful/full article prose in RSS even when
            # their article page blocks automated requests. Google News wrapper
            # descriptions are retained too but explicitly filtered in _article_sync.
            feed_content = str(description_raw or "")[:120000]
            published_raw = _item_text(node, ["pubdate", "published", "updated", "date"])
            published = _parse_date(published_raw)
            # Google site-search feeds occasionally surface archive results many
            # years old. News is a current-news reader: reject obviously stale or
            # future-dated Google wrapper items before they reach tabs/sorting.
            if google_transport and published and (published < google_oldest or published > google_future_limit):
                continue
            image = ""
            media_url = ""
            media_type = ""
            image_candidates: List[Tuple[float, str]] = []
            for media in node.get("media") or []:
                lname = str(media.get("tag") or "")
                url = str(media.get("url") or "")
                typ = str(media.get("type") or "").lower()
                medium = str(media.get("medium") or "").lower()
                if not url:
                    continue
                absolute = _absolute(feed_base, url)
                width = _int_attr(media.get("width"))
                height = _int_attr(media.get("height"))
                if lname in {"thumbnail", "content"}:
                    if medium == "video" or typ.startswith("video/"):
                        media_url, media_type = absolute, typ or "video"
                    elif (medium == "image" or typ.startswith("image/") or lname == "thumbnail") and _image_candidate_ok(absolute, width, height):
                        image_candidates.append((_image_quality_score(absolute, width, height), absolute))
                elif lname == "enclosure":
                    if typ.startswith("video/") or typ.startswith("audio/"):
                        media_url, media_type = absolute, typ
                    elif typ.startswith("image/") and _image_candidate_ok(absolute, width, height):
                        image_candidates.append((_image_quality_score(absolute, width, height), absolute))
            if image_candidates:
                image = max(image_candidates, key=lambda row: row[0])[1]
            if not image:
                image = _find_html_image(description_raw, feed_base)
            if image:
                image = _prefer_card_image_url(image)
            embed = _youtube_embed(link) or _youtube_embed(media_url)
            kind = "video" if embed or media_type.startswith("video/") else "article"
            article_url = link or media_url
            if not article_url:
                continue
            article_id = _stable_id("article", article_url or title)
            item_source_name = item_source_hint or source_name
            feed_labels = list((node.get("fields") or {}).get("category") or []) + list((node.get("fields") or {}).get("subject") or [])
            categories = _categorize_item(title, excerpt, article_url, feed_labels)
            result.append({
                "id": article_id,
                "title": title,
                "url": article_url,
                "sourceId": source_id,
                "source": item_source_name,
                "country": source.get("country", ""),
                "sourceSiteUrl": str(source.get("siteUrl") or ""),
                "sourceLogo": str(source.get("logoUrl") or ""),
                "sourceFavicon": str(source.get("faviconUrl") or ""),
                "sourceColor": str(source.get("brandColor") or ""),
                "published": published,
                "publishedText": published_raw,
                "excerpt": excerpt,
                "feedContent": feed_content,
                "image": image,
                "type": kind,
                "videoUrl": media_url,
                "embedUrl": embed,
                "categories": categories,
                "feedCategories": [_clean_text(value) for value in feed_labels if _clean_text(value)][:12],
            })
        return result

    def _localize_source_assets_sync(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Persist source favicon/logo locally so QAM branding cannot disappear
        after route transitions or transient remote favicon failures."""
        localized = dict(source)
        site = str(localized.get("siteUrl") or "")
        favicon = str(localized.get("faviconUrl") or "")
        logo = str(localized.get("logoUrl") or "")
        if favicon.startswith(("http://", "https://")):
            local_favicon, _ = self._cache_remote_image_sync(favicon, site)
            if local_favicon:
                localized["faviconUrl"] = local_favicon
        if logo and logo == favicon and localized.get("faviconUrl"):
            localized["logoUrl"] = localized["faviconUrl"]
        elif logo.startswith(("http://", "https://")):
            local_logo, _ = self._cache_remote_image_sync(logo, site)
            if local_logo:
                localized["logoUrl"] = local_logo
        return localized

    def _fetch_source_sync(self, source: Dict[str, Any], force: bool, refresh_seconds: int) -> Dict[str, Any]:
        source = self._normalized_source(source)
        source_id = str(source.get("id") or source.get("feedUrl") or source.get("siteUrl") or "")
        if not source_id:
            return self._fetch_source_actual_sync(source, force, refresh_seconds)

        with self._feed_inflight_lock:
            event = self._feed_inflight.get(source_id)
            if event is None:
                event = threading.Event()
                self._feed_inflight[source_id] = event
                owner = True
            else:
                owner = False

        if not owner:
            # A simultaneous tab/source request is already doing the network work.
            # Wait for that shared result instead of opening another connection.
            event.wait(timeout=12.0)
            with self._feed_inflight_lock:
                shared = self._feed_inflight_results.get(source_id)
            if isinstance(shared, dict):
                return shared
            # Extremely defensive timeout path: the ordinary cache check below is
            # still safe and avoids failing the caller because a worker vanished.
            return self._fetch_source_actual_sync(source, False, refresh_seconds)

        try:
            result = self._fetch_source_actual_sync(source, force, refresh_seconds)
            with self._feed_inflight_lock:
                self._feed_inflight_results[source_id] = result
            return result
        finally:
            with self._feed_inflight_lock:
                finished = self._feed_inflight.pop(source_id, None)
            if finished is not None:
                finished.set()

    def _fetch_source_actual_sync(self, source: Dict[str, Any], force: bool, refresh_seconds: int) -> Dict[str, Any]:
        # CRITICAL HOT PATH: never perform source-logo/favicon network I/O here.
        # Feed cache must be checked first and cached news must return immediately.
        source = self._normalized_source(source)
        source_id = str(source.get("id") or "")
        feed_url = str(source.get("feedUrl") or "")
        cached = self._read_feed_cache(source_id)
        now = int(time.time())
        if not force and cached and now - int(cached.get("fetchedAt") or 0) < refresh_seconds:
            cached_items = []
            for raw_item in list(cached.get("items") or []):
                if not isinstance(raw_item, dict):
                    continue
                cached_items.append({
                    **raw_item,
                    "sourceSiteUrl": str(source.get("siteUrl") or raw_item.get("sourceSiteUrl") or ""),
                    "sourceLogo": str(source.get("logoUrl") or raw_item.get("sourceLogo") or ""),
                    "sourceFavicon": str(source.get("faviconUrl") or raw_item.get("sourceFavicon") or ""),
                    "sourceColor": str(source.get("brandColor") or raw_item.get("sourceColor") or ""),
                })
            if _hostname(str(source.get("siteUrl") or "")) == "ilpost.it":
                try:
                    self._prefetch_executor.submit(self._ilpost_bing_recent_links_sync)
                except Exception:
                    pass
                self._schedule_ilpost_fresh_prefetch(cached_items)
            return {"source": source, "items": cached_items, "cached": True, "error": ""}
        if not feed_url:
            discovered = self._discover_source_sync(str(source.get("siteUrl") or ""), str(source.get("country") or ""), str(source.get("name") or ""))
            if discovered.get("ok"):
                feed_url = str(discovered.get("source", {}).get("feedUrl") or "")
                source = {**source, "feedUrl": feed_url}
            else:
                feed_url = _google_news_site_feed(str(source.get("siteUrl") or ""), str(source.get("country") or "IT"))
                if feed_url:
                    source = {**source, "feedUrl": feed_url}
                else:
                    return {"source": source, "items": list(cached.get("items") or []), "cached": bool(cached), "error": str(discovered.get("error") or "Feed non disponibile")}
        try:
            fetch_started = time.perf_counter()
            data, _, final_url = self._request(feed_url, MAX_FEED_BYTES, timeout=5.0, accept="application/rss+xml,application/atom+xml,application/xml,text/xml,*/*;q=0.5")
            fetch_elapsed = time.perf_counter() - fetch_started
            items = self._parse_feed(source, data, final_url)
            cover_count = sum(1 for item in items if str(item.get("image") or "").strip())
            source_name = str(source.get("name") or source_id)
            # Always expose transport/coverage for the two publishers currently
            # under investigation; log other sources when they are slow or sparse.
            if source_name in {"IGN Italia", "SpazioGames"} or fetch_elapsed >= 1.25 or (items and cover_count < len(items) * .65):
                self._log(f"feed {source_name}: {fetch_elapsed:.2f}s items={len(items)} covers={cover_count}/{len(items)} transport={_hostname(final_url or feed_url)}")
            if not items and str(source.get("siteUrl") or ""):
                raise RuntimeError("Il feed non ha restituito notizie utilizzabili.")
            payload = {"fetchedAt": now, "items": items}
            self._write_feed_cache(source_id, payload)
            return {"source": source, "items": items, "cached": False, "error": ""}
        except Exception as exc:
            fallback_feed = _google_news_site_feed(str(source.get("siteUrl") or ""), str(source.get("country") or "IT"))
            if fallback_feed and fallback_feed != feed_url:
                try:
                    data, _, final_url = self._request(fallback_feed, MAX_FEED_BYTES, timeout=4.5, accept="application/rss+xml,application/atom+xml,application/xml,text/xml,*/*;q=0.5")
                    fallback_source = {**source, "feedUrl": fallback_feed}
                    items = self._parse_feed(fallback_source, data, final_url)
                    if items:
                        payload = {"fetchedAt": now, "items": items}
                        self._write_feed_cache(source_id, payload)
                        self._log(f"feed fallback {source.get('name') or source_id}: native={_hostname(feed_url)} -> google items={len(items)} covers={sum(1 for item in items if str(item.get('image') or '').strip())}/{len(items)}")
                        if _hostname(str(source.get("siteUrl") or "")) == "ilpost.it":
                            try:
                                self._prefetch_executor.submit(self._ilpost_bing_recent_links_sync)
                            except Exception:
                                pass
                            self._schedule_ilpost_fresh_prefetch(items)
                        return {"source": fallback_source, "items": items, "cached": False, "error": ""}
                except Exception:
                    pass
            return {"source": source, "items": list(cached.get("items") or []), "cached": bool(cached), "error": str(exc)}

    def _tab_for_id(self, tab_id: str) -> Optional[Dict[str, Any]]:
        tabs = [value for value in self._config.get("tabs", []) if isinstance(value, dict)]
        if not tab_id:
            tab_id = str(self._config.get("activeTabId") or (tabs[0].get("id") if tabs else ""))
        return next((value for value in tabs if str(value.get("id")) == tab_id), None)

    def _selected_sources_for_tab(self, tab_id: str) -> List[Dict[str, Any]]:
        sources = [self._normalized_source(value) for value in self._config.get("sources", []) if isinstance(value, dict) and value.get("enabled", True)]
        tab = self._tab_for_id(tab_id)
        if not tab:
            return sources
        allowed = {str(value) for value in tab.get("sourceIds", [])}
        return [source for source in sources if source["id"] in allowed]

    def _news_source_sync(self, tab_id: str, source_id: str, force: bool, limit: int) -> Dict[str, Any]:
        """Fetch exactly one source for a tab so the frontend can paint stories
        progressively as each publisher responds instead of waiting for the slowest
        source in the whole tab.
        """
        tab = self._tab_for_id(tab_id)
        category = _infer_tab_category(str((tab or {}).get("id") or ""), str((tab or {}).get("name") or ""), str((tab or {}).get("category") or ""))
        sources = self._selected_sources_for_tab(tab_id)
        source = next((value for value in sources if str(value.get("id") or "") == str(source_id or "")), None)
        if not source:
            return {"ok": True, "sourceId": str(source_id or ""), "items": [], "errors": [], "fetchedAt": int(time.time()), "category": category}
        refresh_seconds = max(60, int(self._config.get("refreshMinutes") or 15) * 60)
        try:
            payload = self._fetch_source_sync(source, force, refresh_seconds)
        except Exception as exc:
            return {"ok": True, "sourceId": str(source.get("id") or source_id or ""), "items": [], "errors": [{"source": str(source.get("name") or "Fonte"), "error": str(exc)}], "fetchedAt": int(time.time()), "category": category}
        items: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for raw in (payload.get("items") or []):
            if not isinstance(raw, dict):
                continue
            item = dict(raw)
            key = str(item.get("url") or item.get("id") or item.get("title") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            item["categories"] = _categorize_item(
                str(item.get("title") or ""),
                str(item.get("excerpt") or ""),
                str(item.get("url") or ""),
                item.get("feedCategories") if isinstance(item.get("feedCategories"), list) else [],
            )
            if category and category != "all" and category not in set(str(value) for value in item.get("categories", [])):
                continue
            items.append(self._apply_cached_item_enrichment(item))
        items.sort(key=lambda item: (int(item.get("published") or 0), str(item.get("title") or "")), reverse=True)
        errors: List[Dict[str, str]] = []
        if payload.get("error"):
            errors.append({"source": str(payload.get("source", {}).get("name") or source.get("name") or "Fonte"), "error": str(payload.get("error"))})
        return {"ok": True, "sourceId": str(source.get("id") or source_id or ""), "items": items[: max(1, min(int(limit or 80), 160))], "errors": errors, "fetchedAt": int(time.time()), "category": category}

    def _news_sync(self, tab_id: str, force: bool, limit: int) -> Dict[str, Any]:
        tab = self._tab_for_id(tab_id)
        category = _infer_tab_category(str((tab or {}).get("id") or ""), str((tab or {}).get("name") or ""), str((tab or {}).get("category") or ""))
        sources = self._selected_sources_for_tab(tab_id)
        refresh_seconds = max(60, int(self._config.get("refreshMinutes") or 15) * 60)
        if not sources:
            return {"ok": True, "items": [], "errors": [], "fetchedAt": int(time.time())}
        futures = [self._executor.submit(self._fetch_source_sync, source, force, refresh_seconds) for source in sources]
        combined: List[Dict[str, Any]] = []
        errors: List[Dict[str, str]] = []
        for future in as_completed(futures):
            try:
                payload = future.result()
                combined.extend(payload.get("items") or [])
                if payload.get("error"):
                    errors.append({"source": str(payload.get("source", {}).get("name") or "Fonte"), "error": str(payload.get("error"))})
            except Exception as exc:
                errors.append({"source": "Fonte", "error": str(exc)})
        unique: Dict[str, Dict[str, Any]] = {}
        for item in combined:
            key = str(item.get("url") or item.get("id") or item.get("title") or "")
            if not key or key in unique:
                continue
            item["categories"] = _categorize_item(
                str(item.get("title") or ""),
                str(item.get("excerpt") or ""),
                str(item.get("url") or ""),
                item.get("feedCategories") if isinstance(item.get("feedCategories"), list) else [],
            )
            if category and category != "all" and category not in set(str(value) for value in item.get("categories", [])):
                continue
            unique[key] = item
        items = [self._apply_cached_item_enrichment(item) for item in unique.values()]
        items.sort(key=lambda item: (int(item.get("published") or 0), str(item.get("title") or "")), reverse=True)
        return {"ok": True, "items": items[: max(1, min(int(limit or 80), 160))], "errors": errors, "fetchedAt": int(time.time()), "category": category}

    def _refresh_all_sync(self, limit: int = 120) -> Dict[str, Any]:
        sources = [self._normalized_source(value) for value in self._config.get("sources", []) if isinstance(value, dict) and value.get("enabled", True)]
        if not sources:
            return {"ok": True, "tabs": {}, "errors": [], "fetchedAt": int(time.time())}
        refresh_seconds = max(60, int(self._config.get("refreshMinutes") or 15) * 60)
        futures = [self._executor.submit(self._fetch_source_sync, source, True, refresh_seconds) for source in sources]
        combined: List[Dict[str, Any]] = []
        errors: List[Dict[str, str]] = []
        for future in as_completed(futures):
            try:
                payload = future.result()
                combined.extend(payload.get("items") or [])
                if payload.get("error"):
                    errors.append({"source": str(payload.get("source", {}).get("name") or "Fonte"), "error": str(payload.get("error"))})
            except Exception as exc:
                errors.append({"source": "Fonte", "error": str(exc)})
        unique: Dict[str, Dict[str, Any]] = {}
        for item in combined:
            key = str(item.get("url") or item.get("id") or item.get("title") or "")
            if not key or key in unique:
                continue
            item = dict(item)
            item["categories"] = _categorize_item(
                str(item.get("title") or ""), str(item.get("excerpt") or ""), str(item.get("url") or ""),
                item.get("feedCategories") if isinstance(item.get("feedCategories"), list) else [],
            )
            unique[key] = self._apply_cached_item_enrichment(item)
        all_items = list(unique.values())
        all_items.sort(key=lambda item: (int(item.get("published") or 0), str(item.get("title") or "")), reverse=True)

        tabs_out: Dict[str, List[Dict[str, Any]]] = {}
        for tab in [value for value in self._config.get("tabs", []) if isinstance(value, dict) and value.get("enabled", True)]:
            tab_id = str(tab.get("id") or "")
            category = _infer_tab_category(tab_id, str(tab.get("name") or ""), str(tab.get("category") or ""))
            allowed = {str(value) for value in tab.get("sourceIds", [])}
            filtered: List[Dict[str, Any]] = []
            for item in all_items:
                if allowed and str(item.get("sourceId") or "") not in allowed:
                    continue
                if category and category != "all" and category not in set(str(value) for value in item.get("categories", [])):
                    continue
                filtered.append(item)
                if len(filtered) >= max(1, min(int(limit or 120), 160)):
                    break
            tabs_out[tab_id] = filtered

        # Start expensive missing-cover warming only once after the shared refresh.
        # It deliberately runs in the background so the QAM does not wait minutes
        # for publishers that are slow or hostile to automated requests.
        warm_items = all_items[:160]
        try:
            self._image_warm_future = self._image_executor.submit(self._enrich_images_sync, warm_items, min(160, max(80, int(limit or 120))))
        except Exception:
            self._image_warm_future = None
        return {"ok": True, "tabs": tabs_out, "errors": errors, "fetchedAt": int(time.time()), "warmingImages": bool(self._image_warm_future)}

    def _prefetch_tabs_sync(self, active_tab_id: str = "", limit: int = 120) -> Dict[str, Any]:
        """Warm every enabled tab at once using one shared publisher fan-out.

        Each enabled RSS source is fetched at most once for this pass. Results are
        then classified into every tab in memory, and cover discovery starts in
        parallel pools: visible-tab covers retain their own high-priority workers
        while all other tabs warm independently in the background.
        """
        tabs = [value for value in self._config.get("tabs", []) if isinstance(value, dict) and value.get("enabled", True)]
        if not tabs:
            return {"ok": True, "tabs": {}, "errors": [], "fetchedAt": int(time.time())}
        tab_ids = {str(tab.get("id") or "") for tab in tabs}
        active_id = str(active_tab_id or self._config.get("activeTabId") or "")
        if active_id not in tab_ids:
            active_id = str(tabs[0].get("id") or "")
        referenced_ids = {str(source_id) for tab in tabs for source_id in (tab.get("sourceIds") or [])}
        sources = [
            self._normalized_source(value) for value in self._config.get("sources", [])
            if isinstance(value, dict) and value.get("enabled", True) and str(value.get("id") or "") in referenced_ids
        ]
        if not sources:
            return {"ok": True, "tabs": {str(tab.get("id") or ""): [] for tab in tabs}, "errors": [], "fetchedAt": int(time.time())}

        refresh_seconds = max(60, int(self._config.get("refreshMinutes") or 15) * 60)
        futures = {
            self._prefetch_executor.submit(self._fetch_source_sync, source, False, refresh_seconds): str(source.get("id") or "")
            for source in sources
        }
        by_source: Dict[str, List[Dict[str, Any]]] = {}
        errors: List[Dict[str, str]] = []
        for future in as_completed(futures):
            source_id = futures[future]
            try:
                payload = future.result()
                by_source[source_id] = [dict(item) for item in (payload.get("items") or []) if isinstance(item, dict)]
                if payload.get("error"):
                    errors.append({"source": str(payload.get("source", {}).get("name") or source_id or "Fonte"), "error": str(payload.get("error"))})
            except Exception as exc:
                by_source[source_id] = []
                errors.append({"source": source_id or "Fonte", "error": str(exc)})

        max_items = max(1, min(int(limit or 120), 160))
        tabs_out: Dict[str, List[Dict[str, Any]]] = {}
        cover_union: Dict[str, Dict[str, Any]] = {}
        active_cover_items: List[Dict[str, Any]] = []
        for tab in tabs:
            tab_id = str(tab.get("id") or "")
            category = _infer_tab_category(tab_id, str(tab.get("name") or ""), str(tab.get("category") or ""))
            allowed = {str(value) for value in (tab.get("sourceIds") or [])}
            unique: Dict[str, Dict[str, Any]] = {}
            for source_id in allowed:
                for raw in by_source.get(source_id, []):
                    item = dict(raw)
                    key = str(item.get("url") or item.get("id") or item.get("title") or "")
                    if not key or key in unique:
                        continue
                    item["categories"] = _categorize_item(
                        str(item.get("title") or ""), str(item.get("excerpt") or ""), str(item.get("url") or ""),
                        item.get("feedCategories") if isinstance(item.get("feedCategories"), list) else [],
                    )
                    if category and category != "all" and category not in set(str(value) for value in item.get("categories", [])):
                        continue
                    unique[key] = self._apply_cached_item_enrichment(item)
            items = list(unique.values())
            items.sort(key=lambda item: (int(item.get("published") or 0), str(item.get("title") or "")), reverse=True)
            items = items[:max_items]
            tabs_out[tab_id] = items
            for item in items:
                if str(item.get("type") or "article") != "article" or str(item.get("image") or ""):
                    continue
                token = str(item.get("id") or item.get("url") or "")
                if token:
                    cover_union[token] = item
            if tab_id == active_id:
                active_cover_items = [item for item in items if str(item.get("type") or "article") == "article" and not str(item.get("image") or "")]

        # Queue all cheap cover discovery immediately. Background work has its own
        # executors, so it cannot starve the active tab. In-flight tokens dedupe
        # stories that appear in more than one category.
        if active_cover_items:
            self._start_cover_enrichment_sync(active_cover_items, len(active_cover_items), background=False)
        active_tokens = {str(item.get("id") or item.get("url") or "") for item in active_cover_items}
        background_items = [item for token, item in cover_union.items() if token not in active_tokens]
        if background_items:
            self._start_cover_enrichment_sync(background_items, len(background_items), background=True)

        # This RPC itself is background-only. A tiny bounded grace period lets the
        # many easy metadata covers land in cache before the frontend stores the
        # prefetched tabs, eliminating most fallback flashes when the user switches.
        if cover_union:
            time.sleep(0.30)
            for tab_id, items in list(tabs_out.items()):
                tabs_out[tab_id] = [self._apply_cached_item_enrichment(item) for item in items]

        return {
            "ok": True, "tabs": tabs_out, "errors": errors, "fetchedAt": int(time.time()),
            "activeTabId": active_id, "sources": len(sources), "coverJobs": len(cover_union),
        }

    def _article_cache_path(self, article_url: str) -> Path:
        return CACHE_DIR / f"article-{hashlib.sha1(str(article_url or '').encode('utf-8', 'ignore')).hexdigest()[:24]}.json"

    def _read_article_cache(self, article_url: str) -> Dict[str, Any]:
        payload = _load_json(self._article_cache_path(article_url), {})
        if not isinstance(payload, dict) or int(payload.get("cacheVersion") or 0) != ARTICLE_CACHE_VERSION:
            return {}
        if int(time.time()) - int(payload.get("fetchedAt") or 0) > ARTICLE_CACHE_SECONDS:
            return {}
        result = payload.get("article")
        if not isinstance(result, dict):
            return {}
        # Never reuse the old pathological "description twice" result.
        text_len = len(" ".join(str(block.get("text") or "") for block in result.get("blocks", []) if isinstance(block, dict) and block.get("type") == "text"))
        if result.get("readerAvailable") and text_len < 160:
            return {}
        return result

    def _write_article_cache(self, article_url: str, article: Dict[str, Any]) -> None:
        try:
            _atomic_json(self._article_cache_path(article_url), {"cacheVersion": ARTICLE_CACHE_VERSION, "fetchedAt": int(time.time()), "article": article})
        except Exception:
            pass

    def _cached_local_image_for_remote(self, image_url: str) -> str:
        value = str(image_url or "").strip()
        if not value.startswith(("http://", "https://")):
            return value
        key = hashlib.sha1(value.encode("utf-8", "ignore")).hexdigest()
        for ext in ("jpg", "jpeg", "png", "webp", "gif", "avif"):
            candidate = IMAGE_CACHE_DIR / f"{key}.{ext}"
            try:
                if candidate.is_file() and candidate.stat().st_size > 1024:
                    return self._image_server.image_url(candidate.name)
            except Exception:
                continue
        return ""

    def _localize_article_images_cached_only(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Rewrite article image URLs only when bytes are already in the persistent
        image cache. This function never touches the network, so reopening a cached
        article stays immediate even when a publisher is currently slow/offline.
        """
        result = dict(article)
        hero = str(result.get("hero") or "")
        cached_hero = self._cached_local_image_for_remote(hero)
        if cached_hero:
            result["hero"] = cached_hero
        blocks: List[Dict[str, Any]] = []
        for block in (result.get("blocks") or []):
            if not isinstance(block, dict):
                continue
            copy = dict(block)
            if copy.get("type") == "image":
                remote = str(copy.get("url") or "")
                cached = self._cached_local_image_for_remote(remote)
                if cached:
                    copy["url"] = cached
            blocks.append(copy)
        result["blocks"] = blocks
        return result

    def _warm_article_images_sync(self, article: Dict[str, Any], max_body_images: int = 16) -> None:
        """Download article artwork after the Reader result has already been returned.
        This preserves hotlink compatibility for future opens without making the
        current article wait for every body image.
        """
        result = dict(article or {})
        referer = str(result.get("url") or "")
        urls: List[str] = []
        hero = str(result.get("hero") or "")
        if hero.startswith(("http://", "https://")):
            urls.append(hero)
        for block in (result.get("blocks") or []):
            if not isinstance(block, dict) or block.get("type") != "image":
                continue
            remote = str(block.get("url") or "")
            if remote.startswith(("http://", "https://")) and remote not in urls:
                urls.append(remote)
            if len(urls) >= max(1, int(max_body_images or 16)) + 1:
                break
        if not urls:
            return
        with ThreadPoolExecutor(max_workers=min(10, len(urls)), thread_name_prefix="NewsArticleWarm") as pool:
            futures = [pool.submit(self._cache_remote_image_sync, url, referer) for url in urls]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    pass

    def _extract_article_blocks_from_html(self, text: str, final_url: str) -> Tuple[List[Dict[str, str]], str]:
        """Extract the strongest readable region instead of blindly using the
        first <article>. Several news sites place teaser/related <article> nodes
        before the real story, which caused the short duplicated fragments seen
        in older builds.
        """
        raw = str(text or "")
        candidate_regions: List[str] = []
        candidate_regions.extend(match.group(1) for match in re.finditer(r"<article\b[^>]*>(.*?)</article\s*>", raw, re.I | re.S))
        candidate_regions.extend(match.group(1) for match in re.finditer(r"<main\b[^>]*>(.*?)</main\s*>", raw, re.I | re.S))
        # Also try common article-body containers. The bounded slice avoids trying
        # to balance arbitrary nested divs with a fragile HTML regex parser.
        for match in re.finditer(r"<(?:div|section)\b[^>]*(?:class|id)=[\"'].*?(?:article[-_ ]?(?:body|content|text)|story[-_ ]?(?:body|content)|post[-_ ]?content|entry[-_ ]?content|content[-_ ]?body).*?[\"'][^>]*>", raw, re.I | re.S):
            candidate_regions.append(raw[match.end(): min(len(raw), match.end() + 900000)])
        # Whole page remains a fallback; ReaderParser removes nav/footer/forms.
        candidate_regions.append(raw)

        best_blocks: List[Dict[str, str]] = []
        best_score = -1
        seen_regions: set[str] = set()
        for region in candidate_regions:
            signature = hashlib.sha1(region[:5000].encode("utf-8", "ignore")).hexdigest()[:16]
            if signature in seen_regions:
                continue
            seen_regions.add(signature)
            reader = _ReaderParser(final_url, False, False)
            try:
                reader.feed(region)
            except Exception:
                continue
            blocks: List[Dict[str, str]] = []
            for block in reader.blocks:
                if block.get("type") == "text":
                    value = str(block.get("text") or "")
                    low = value.lower()
                    if len(value) < 18 or low in {"cookie", "privacy", "newsletter", "advertisement", "pubblicità"}:
                        continue
                    if any(term in low for term in ("accetta tutti i cookie", "gestisci le preferenze", "iscriviti alla newsletter")) and len(value) < 260:
                        continue
                blocks.append(block)
            text_len = _reader_text_length(blocks)
            paragraphs = sum(1 for block in blocks if block.get("type") == "text" and len(str(block.get("text") or "")) >= 60)
            images = sum(1 for block in blocks if block.get("type") == "image")
            # Text length dominates; multiple real paragraphs are a strong signal.
            score = text_len + paragraphs * 220 + min(images, 3) * 50
            if score > best_score:
                best_score = score
                best_blocks = blocks[:260]

        script_text = _script_article_text(raw)
        return best_blocks, script_text

    def _jina_reader_article_sync(self, article_url: str, timeout: float = JINA_READER_TIMEOUT) -> Dict[str, Any]:
        """Last-resort rendered-page extraction.

        Article Reader keeps the normal timeout. Cover enrichment can request a
        shorter timeout so dozens of cards can resolve concurrently with a bounded
        completion window.
        """
        value = str(article_url or "").strip()
        if not value.startswith(("http://", "https://")):
            return {}
        request = urllib.request.Request(
            JINA_READER_BASE + value,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                "X-Timeout": str(max(2, min(9, int(round(float(timeout or JINA_READER_TIMEOUT)))))),
                "X-Cache-Tolerance": "86400",
                "X-Base": "true",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=max(2.0, float(timeout or JINA_READER_TIMEOUT))) as response:
                payload = json.loads(response.read(MAX_ARTICLE_BYTES).decode("utf-8", "replace"))
        except Exception:
            return {}
        data = payload.get("data") if isinstance(payload, dict) and isinstance(payload.get("data"), dict) else payload
        if not isinstance(data, dict):
            return {}
        content = str(data.get("content") or data.get("markdown") or "")
        if not content:
            return {}
        final_url = str(data.get("url") or value)
        blocks, hero = _markdown_to_reader_blocks(content, final_url)
        return {
            "url": final_url,
            "title": _clean_text(data.get("title") or ""),
            "description": _clean_text(data.get("description") or ""),
            "published": _parse_date(str(data.get("timestamp") or data.get("publishedTime") or "")),
            "blocks": blocks,
            "hero": hero,
            "textLength": _reader_text_length(blocks),
            "rawContent": content,
        }

    def _article_from_feed_content_sync(self, target: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        """Return a strong native RSS/Atom article body without touching the network.

        Some publishers include most or all of the story in content:encoded. The
        previous Reader still performed URL resolution/direct/AMP/rendered work
        before considering that body, turning a perfectly usable feed item into a
        multi-second or even multi-minute open. Only accept a substantial body so
        summaries/excerpts keep using the normal article pipeline.
        """
        raw = str(fallback.get("feedContent") or "")
        if not raw or "news.google.com/rss/articles/" in raw.lower():
            return {}
        clean = _clean_text(raw)
        if len(clean) < 360:
            return {}
        base_url = target if target.startswith(("http://", "https://")) else str(fallback.get("sourceSiteUrl") or "")
        if "<" in raw and ">" in raw:
            blocks, _script = self._extract_article_blocks_from_html(f"<article>{raw}</article>", base_url)
        else:
            blocks = _ld_text_blocks(clean)
        title = _clean_text(fallback.get("title") or "Articolo")
        description = _clean_text(fallback.get("excerpt") or "")
        blocks = _dedupe_article_blocks(blocks, title, description)
        body_len = _reader_text_length(blocks)
        text_count = sum(1 for block in blocks if isinstance(block, dict) and block.get("type") == "text")
        if body_len < 420 or (text_count < 2 and body_len < 760):
            return {}
        hero = ""
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "image" and str(block.get("url") or ""):
                hero = _prefer_highres_image_url(str(block.get("url") or ""))
                break
        if not hero:
            hero = _prefer_highres_image_url(_find_html_image(raw, base_url) or str(fallback.get("image") or ""))
        raw_result = {
            "ok": True,
            "readerAvailable": True,
            "readerPartial": body_len < 700,
            "title": title,
            "author": "",
            "description": description,
            "hero": hero,
            "published": int(fallback.get("published") or 0),
            "url": target,
            "blocks": blocks,
            "embedUrl": _youtube_embed(target) or str(fallback.get("embedUrl") or ""),
        }
        self._write_article_cache(target, raw_result)
        try:
            self._image_executor.submit(self._warm_article_images_sync, raw_result, 16)
        except Exception:
            pass
        return self._localize_article_images_cached_only(raw_result)

    def _article_sync(self, url: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        target = str(url or "").strip()
        fallback = fallback or {}
        if not target:
            return {"ok": False, "error": "URL articolo mancante."}

        # Reopens must be immediate. Check the exact feed URL before performing
        # any Google decoder or publisher request.
        cached_target = self._read_article_cache(target)
        if cached_target:
            return self._localize_article_images_cached_only(cached_target)

        feed_result = self._article_from_feed_content_sync(target, fallback)
        if feed_result:
            return feed_result

        expected_site = str(fallback.get("sourceSiteUrl") or "")
        # Il Post fallback items are Google wrappers because its native RSS often
        # returns 403 in Decky's Python runtime. Resolve those first through the
        # publisher's own date archive/stream index; this is shared across every
        # story from the same day and avoids dozens of fragile Google RPCs.
        resolved_target = ""
        if _hostname(expected_site) == "ilpost.it" and _is_google_news_url(target):
            # Reader opens get the strongest Il Post path without waiting for the
            # whole 80-story bulk resolver. Reuse any known direct URL / already
            # warmed recent index first, then issue one exact-title Bing RSS query.
            # Only if all of those miss do we fall through to Google's decoder.
            cached_resolve = self._read_resolve_cache(target)
            if cached_resolve and self._is_ilpost_public_url(cached_resolve):
                resolved_target = cached_resolve
            if not resolved_target:
                resolved_target = self._resolve_ilpost_telegram_sync(str(fallback.get("title") or ""), deep=False)
                if resolved_target:
                    self._write_resolve_cache(target, resolved_target)
            if not resolved_target:
                with self._ilpost_bing_lock:
                    recent_cached = self._ilpost_bing_cache.get("recent")
                    recent_links = dict(recent_cached[1]) if recent_cached and time.time() - recent_cached[0] < 10 * 60 else {}
                resolved_target = self._ilpost_match_listing_url(str(fallback.get("title") or ""), recent_links)
                if resolved_target:
                    self._write_resolve_cache(target, resolved_target)
            if not resolved_target:
                # For a just-published story Google knows the destination before
                # Bing can index the headline. Decode the wrapper first; this also
                # avoids adding an exact-search delay to the newest articles.
                google_target = self._resolve_google_news_url_sync(target, expected_site, fast=True, reader_rescue=True)
                if google_target and not _is_google_news_url(google_target):
                    resolved_target = google_target
                    self._write_resolve_cache(target, resolved_target)
                    self._log(f"Il Post Reader Google fresh -> {_hostname(resolved_target)} title={_clean_text(fallback.get('title') or '')[:72]}")
            if not resolved_target:
                published = int(fallback.get("published") or 0)
                age_seconds = max(0, int(time.time()) - published) if published > 0 else 10**9
                if age_seconds <= 2 * 60 * 60:
                    # Google can publish the RSS item a few seconds before the
                    # decoder shell is ready. One short retry is cheaper and more
                    # useful than declaring the newest story unavailable.
                    time.sleep(0.22)
                    google_target = self._resolve_google_news_url_sync(target, expected_site, fast=True, reader_rescue=True)
                    if google_target and not _is_google_news_url(google_target):
                        resolved_target = google_target
                        self._write_resolve_cache(target, resolved_target)
                        self._log(f"Il Post Reader Google retry -> {_hostname(resolved_target)} age={age_seconds}s title={_clean_text(fallback.get('title') or '')[:72]}")
            if not resolved_target:
                resolved_target = self._resolve_ilpost_bing_exact_sync(str(fallback.get("title") or ""), force=True)
                if resolved_target:
                    self._write_resolve_cache(target, resolved_target)
        # Other Google-backed items keep the bounded current Google decoder. Il Post
        # has already tried it above before falling back to search indexing.
        if not resolved_target:
            resolved_target = self._resolve_google_news_url_sync(target, expected_site, fast=True, reader_rescue=True)
        google_rendered: Dict[str, Any] = {}

        cached_resolved = self._read_article_cache(resolved_target) if resolved_target != target else {}
        if cached_resolved:
            return self._localize_article_images_cached_only(cached_resolved)

        if _is_google_news_url(resolved_target):
            google_rendered = self._jina_reader_article_sync(resolved_target, timeout=6.0)
            raw_content = str(google_rendered.get("rawContent") or "")
            if expected_site and raw_content:
                candidates = re.findall(r"https?://[^\\s\\)\\]<>\"']+", raw_content, re.I)
                publisher = next((candidate.rstrip(".,);]") for candidate in candidates if _host_matches(candidate, expected_site)), "")
                if publisher:
                    resolved_target = publisher
                    self._write_resolve_cache(target, publisher)
            rendered_url = str(google_rendered.get("url") or "")
            if _is_google_news_url(resolved_target) and rendered_url and not _is_google_news_url(rendered_url) and (not expected_site or _host_matches(rendered_url, expected_site)):
                resolved_target = rendered_url
                self._write_resolve_cache(target, rendered_url)

            # If the rendered Google shell already produced a real article, return
            # it now instead of opening the publisher and potentially rendering a
            # second time.
            gr_blocks = list(google_rendered.get("blocks") or [])
            gr_len = int(google_rendered.get("textLength") or _reader_text_length(gr_blocks))
            gr_text_count = sum(1 for block in gr_blocks if isinstance(block, dict) and block.get("type") == "text")
            if gr_len >= 480 and (gr_text_count >= 2 or gr_len >= 900):
                title = _clean_text(google_rendered.get("title") or fallback.get("title") or "Articolo")
                description = _clean_text(google_rendered.get("description") or fallback.get("excerpt") or "")
                hero = _prefer_highres_image_url(str(google_rendered.get("hero") or fallback.get("image") or ""))
                final_url = str(google_rendered.get("url") or resolved_target or target)
                raw_result = {
                    "ok": True, "readerAvailable": True, "readerPartial": gr_len < 700,
                    "title": title, "author": "", "description": description,
                    "hero": hero, "published": int(fallback.get("published") or 0),
                    "url": final_url, "blocks": _dedupe_article_blocks(gr_blocks, title, description),
                    "embedUrl": _youtube_embed(final_url) or str(fallback.get("embedUrl") or ""),
                }
                for key in {target, final_url}:
                    if key:
                        self._write_article_cache(key, raw_result)
                try:
                    self._image_executor.submit(self._warm_article_images_sync, raw_result, 16)
                except Exception:
                    pass
                return self._localize_article_images_cached_only(raw_result)

        cache_key = resolved_target or target
        cached = self._read_article_cache(cache_key)
        if cached:
            return self._localize_article_images_cached_only(cached)

        data = b""
        content_type = ""
        final_url = resolved_target
        text = ""
        direct_error = ""
        if not _is_google_news_url(resolved_target):
            try:
                data, content_type, final_url = self._request(resolved_target, MAX_ARTICLE_BYTES, timeout=4.0)
                text = self._decode(data, content_type)
            except Exception as exc:
                direct_error = str(exc)

        head = _HeadParser()
        if text:
            try:
                head.feed(text[: min(len(text), 1200000)])
            except Exception:
                pass
        ld_objects = _json_ld_objects(text[: min(len(text), 2200000)]) if text else []
        ld_article = _ld_primary_article(ld_objects)

        title = _clean_text(head.meta.get("og:title") or head.meta.get("twitter:title") or ld_article.get("headline") or head.title or fallback.get("title") or "Articolo")
        author = _clean_text(head.meta.get("author") or head.meta.get("article:author") or _ld_author_name(ld_article))
        description = _clean_text(head.meta.get("description") or head.meta.get("og:description") or ld_article.get("description") or fallback.get("excerpt") or "")
        title_low = title.lower().strip()
        desc_low = description.lower().strip()
        common_prefix = 0
        for left, right in zip(title_low, desc_low):
            if left != right:
                break
            common_prefix += 1
        if description and common_prefix >= min(48, max(24, len(description) // 2)) and len(description) < len(title) + 100:
            description = ""
        if _is_google_news_url(final_url) and "google news" in title.lower():
            title = _clean_text(fallback.get("title") or title)
            description = _clean_text(fallback.get("excerpt") or description)

        hero_candidates: List[str] = []
        if text:
            meta_hero = _best_meta_image(head, final_url, "")
            if meta_hero:
                hero_candidates.append(meta_hero)
        if ld_objects:
            ld_hero = _ld_best_image(ld_objects, final_url)
            if ld_hero:
                hero_candidates.append(ld_hero)
        if text:
            regions = [match.group(1) for match in re.finditer(r"<article\\b[^>]*>(.*?)</article\\s*>", text, re.I | re.S)]
            regions.extend(match.group(1) for match in re.finditer(r"<main\\b[^>]*>(.*?)</main\\s*>", text, re.I | re.S))
            regions.sort(key=lambda value: len(_clean_text(value)), reverse=True)
            for region in regions[:4] + [text[: min(len(text), 2600000)]]:
                candidate = _find_html_image(region, final_url)
                if candidate:
                    hero_candidates.insert(0, candidate)
                    break
        hero = max(hero_candidates, default="", key=lambda value: _image_quality_score(value))

        blocks: List[Dict[str, str]] = []
        script_text = ""
        if text:
            blocks, script_text = self._extract_article_blocks_from_html(text, final_url)

        # A shorter feed body that was not sufficient on its own can still beat a
        # publisher consent/error shell and is therefore compared after direct fetch.
        feed_content_raw = str(fallback.get("feedContent") or "")
        feed_content_clean = _clean_text(feed_content_raw)
        if feed_content_raw and "news.google.com/rss/articles/" not in feed_content_raw.lower() and len(feed_content_clean) >= 180:
            if "<" in feed_content_raw and ">" in feed_content_raw:
                feed_blocks, _feed_script = self._extract_article_blocks_from_html(f"<article>{feed_content_raw}</article>", final_url or resolved_target)
            else:
                feed_blocks = _ld_text_blocks(feed_content_clean)
            if _reader_text_length(feed_blocks) > _reader_text_length(blocks):
                blocks = feed_blocks
            if not hero:
                for feed_block in feed_blocks:
                    if feed_block.get("type") == "image" and str(feed_block.get("url") or ""):
                        hero = str(feed_block.get("url") or "")
                        break

        ld_text = _ld_article_text(ld_article) if ld_article else ""
        strongest_structured = max((ld_text, script_text), key=len, default="")
        if strongest_structured:
            structured_blocks = _ld_text_blocks(strongest_structured)
            if _reader_text_length(structured_blocks) > _reader_text_length(blocks) * 1.12:
                media_blocks = [block for block in blocks if block.get("type") in {"image", "embed"}]
                blocks = structured_blocks + media_blocks

        # AMP remains useful, but its budget is short and only runs when a direct
        # page was actually received and contains too little article text.
        if text and (_reader_text_length(blocks) < 520 or sum(1 for block in blocks if block.get("type") == "text") < 2):
            amp_url = _extract_amp_url(head, final_url)
            if amp_url and amp_url != final_url:
                try:
                    amp_data, amp_type, amp_final = self._request(amp_url, MAX_ARTICLE_BYTES, timeout=3.8)
                    amp_text = self._decode(amp_data, amp_type)
                    amp_blocks, amp_script = self._extract_article_blocks_from_html(amp_text, amp_final)
                    if amp_script:
                        amp_structured = _ld_text_blocks(amp_script)
                        if _reader_text_length(amp_structured) > _reader_text_length(amp_blocks):
                            amp_blocks = amp_structured + [block for block in amp_blocks if block.get("type") in {"image", "embed"}]
                    if _reader_text_length(amp_blocks) > _reader_text_length(blocks):
                        blocks = amp_blocks
                        final_url = amp_final
                except Exception:
                    pass

        direct_len = _reader_text_length(blocks)
        needs_rendered = bool(direct_error) or direct_len < 480 or sum(1 for block in blocks if block.get("type") == "text") < 2
        if needs_rendered:
            # Reuse the first rendered result if Google already supplied one. This
            # avoids a second public-Reader request in the same article open.
            jina = google_rendered or self._jina_reader_article_sync(resolved_target, timeout=6.0)
            if jina:
                jina_blocks = list(jina.get("blocks") or [])
                jina_len = int(jina.get("textLength") or _reader_text_length(jina_blocks))
                if jina_len > max(240, direct_len * 0.88):
                    blocks = jina_blocks
                    direct_len = jina_len
                jina_hero = _prefer_highres_image_url(str(jina.get("hero") or ""))
                if jina_hero and _image_quality_score(jina_hero) > _image_quality_score(hero):
                    hero = jina_hero
                if (not title or title.lower() in {"articolo", "google news"}) and jina.get("title"):
                    title = _clean_text(jina.get("title"))
                if not description and jina.get("description"):
                    description = _clean_text(jina.get("description"))
                if jina.get("url") and not _is_google_news_url(str(jina.get("url"))):
                    final_url = str(jina.get("url"))

        if not hero:
            for block in blocks:
                if block.get("type") == "image" and str(block.get("url") or ""):
                    hero = str(block.get("url") or "")
                    break
        if not hero and text:
            regions = [match.group(1) for match in re.finditer(r"<article\\b[^>]*>(.*?)</article\\s*>", text, re.I | re.S)]
            regions.sort(key=lambda value: len(_clean_text(value)), reverse=True)
            for region in regions[:4] + [text[: min(len(text), 2600000)]]:
                candidate = _find_html_image(region, final_url)
                if candidate:
                    hero = candidate
                    break
        if not hero:
            fallback_image = _prefer_highres_image_url(str(fallback.get("image") or "").strip())
            if fallback_image and _image_candidate_ok(fallback_image):
                hero = fallback_image

        hero = _prefer_highres_image_url(hero)
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "image" and str(block.get("url") or ""):
                block["url"] = _prefer_highres_image_url(str(block.get("url") or ""))
        blocks = _dedupe_article_blocks(blocks, title, description)
        if not blocks and description and len(description) >= 140:
            blocks = [{"type": "text", "text": description}]
        published = _parse_date(head.meta.get("article:published_time") or head.meta.get("date") or str(ld_article.get("datePublished") or ld_article.get("dateCreated") or "")) or int(fallback.get("published") or 0)
        body_len = _reader_text_length(blocks)
        text_blocks_count = sum(1 for block in blocks if block.get("type") == "text")
        reader_available = body_len >= 120 and text_blocks_count >= 1
        reader_partial = reader_available and body_len < 700

        # Il Post last-chance rescue: search transports can transiently miss a fresh
        # story. Never declare a Google wrapper unreadable until we retry exact-title
        # resolution after the other bounded attempts have completed. If it resolves,
        # run the ordinary direct-URL Reader path and cache the success under the
        # original Google wrapper too.
        if (not reader_available and _hostname(expected_site) == "ilpost.it"
                and _is_google_news_url(target)):
            late_target = self._resolve_ilpost_bing_exact_sync(str(fallback.get("title") or title or ""), force=True)
            if late_target and not _is_google_news_url(late_target) and late_target != resolved_target:
                self._write_resolve_cache(target, late_target)
                late_result = self._article_sync(late_target, fallback)
                if isinstance(late_result, dict) and (late_result.get("readerAvailable") or late_result.get("hero")):
                    self._write_article_cache(target, late_result)
                    self._log(f"Il Post Reader late rescue -> {_hostname(late_target)} title={_clean_text(fallback.get('title') or title)[:72]}")
                    return self._localize_article_images_cached_only(late_result)

        raw_result = {
            "ok": True,
            "readerAvailable": reader_available,
            "readerPartial": reader_partial,
            "title": title,
            "author": author,
            "description": description,
            "hero": hero,
            "published": published,
            "url": final_url or resolved_target,
            "blocks": blocks if reader_available else [],
            "embedUrl": _youtube_embed(final_url) or str(fallback.get("embedUrl") or ""),
        }
        if reader_available or hero:
            for key in {target, cache_key, str(final_url or "")}:
                if key:
                    self._write_article_cache(key, raw_result)
            try:
                self._image_executor.submit(self._warm_article_images_sync, raw_result, 16)
            except Exception:
                pass
        return self._localize_article_images_cached_only(raw_result)

    async def get_bootstrap(self) -> Dict[str, Any]:
        return {"ok": True, "config": self._config, "countries": self._countries}

    async def search_sources(self, country: str = "IT", query: str = "") -> Dict[str, Any]:
        code = str(country or "IT").upper()
        q = _clean_text(query).lower()
        result: List[Dict[str, Any]] = []
        for raw in self._catalog.get(code, []) if isinstance(self._catalog, dict) else []:
            if not isinstance(raw, dict):
                continue
            source = self._catalog_source(code, raw)
            haystack = f"{source['name']} {source['siteUrl']} {' '.join(source['tags'])}".lower()
            if not q or q in haystack:
                result.append(source)
        for raw in self._config.get("sources", []):
            if not isinstance(raw, dict):
                continue
            source = self._normalized_source(raw)
            if source.get("country") != code or not source.get("custom"):
                continue
            haystack = f"{source['name']} {source['siteUrl']}".lower()
            if not q or q in haystack:
                result.append(source)
        unique = {source["id"]: source for source in result}
        return {"ok": True, "sources": list(unique.values())}

    async def search_online_sources(self, country: str = "IT", query: str = "") -> Dict[str, Any]:
        return await asyncio.to_thread(self._search_online_sources_sync, country, query)

    async def search_global_sources(self) -> Dict[str, Any]:
        sources = [self._normalized_source(value) for value in WORLD_SOURCE_RECOMMENDATIONS]
        for source in sources:
            if not source.get("feedUrl"):
                source["feedUrl"] = _google_news_site_feed(str(source.get("siteUrl") or ""), str(source.get("country") or "US"))
        return {"ok": True, "sources": sources}

    async def discover_source(self, url: str, country: str = "IT", name: str = "") -> Dict[str, Any]:
        return await asyncio.to_thread(self._discover_source_sync, url, country, name)

    async def make_country_source(self, country: str = "IT") -> Dict[str, Any]:
        return {"ok": True, "source": self._make_country_source(country)}

    async def cache_image(self, url: str = "", referer: str = "") -> Dict[str, Any]:
        value = str(url or "").strip()
        if not value.startswith(("http://", "https://")):
            return {"ok": False, "url": ""}
        local, _filename = await asyncio.to_thread(self._cache_remote_image_sync, value, str(referer or ""))
        return {"ok": bool(local), "url": local or value}

    async def start_cover_enrichment(self, items: Optional[List[Dict[str, Any]]] = None, rendered_limit: int = 28) -> Dict[str, Any]:
        safe_items = items if isinstance(items, list) else []
        return self._start_cover_enrichment_sync(safe_items, int(rendered_limit or 0))

    async def get_cached_covers(self, items: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        safe_items = items if isinstance(items, list) else []
        return self._cached_cover_status_sync(safe_items)

    async def enrich_image(self, item: Optional[Dict[str, Any]] = None, allow_rendered_fallback: bool = True) -> Dict[str, Any]:
        safe_item = item if isinstance(item, dict) else {}
        article_id, image, resolved = await asyncio.to_thread(self._enrich_one_image_sync, safe_item, bool(allow_rendered_fallback))
        return {
            "ok": True,
            "id": article_id,
            "image": image,
            "resolvedUrl": resolved if resolved and not _is_google_news_url(resolved) else "",
        }

    async def enrich_images(self, items: Optional[List[Dict[str, Any]]] = None, limit: int = 24) -> Dict[str, Any]:
        safe_items = items if isinstance(items, list) else []
        return await asyncio.to_thread(self._enrich_images_sync, safe_items, int(limit or 24))

    async def save_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(config, dict):
            return {"ok": False, "error": "Configurazione non valida."}
        next_config = _default_config()
        next_config.update(self._config)
        next_config.update({key: value for key, value in config.items() if key in next_config})
        sources = [self._normalized_source(value) for value in config.get("sources", next_config.get("sources", [])) if isinstance(value, dict)]
        source_ids = {source["id"] for source in sources}
        tabs: List[Dict[str, Any]] = []
        for index, raw in enumerate(config.get("tabs", next_config.get("tabs", []))):
            if not isinstance(raw, dict):
                continue
            name = _clean_text(raw.get("name"))[:42] or f"Tab {index + 1}"
            tab_id = str(raw.get("id") or _stable_id("tab", f"{name}|{index}|{time.time_ns()}"))
            ids = [str(value) for value in raw.get("sourceIds", []) if str(value) in source_ids]
            category = _infer_tab_category(tab_id, name, str(raw.get("category") or ""))
            if tab_id == "preset-culture":
                continue
            if category == "cinema":
                name = "Cinema e Serie"
            tabs.append({"id": tab_id, "name": name, "sourceIds": ids, "enabled": bool(raw.get("enabled", True)), "category": category})
        if next_config.get("onboardingComplete") and sources and not tabs:
            tabs = [{"id": "all", "name": "Tutte", "sourceIds": list(source_ids), "enabled": True, "category": "all"}]
        next_config["sources"] = sources
        next_config["tabs"] = tabs
        enabled_tab_ids = [tab["id"] for tab in tabs if tab.get("enabled", True)]
        if tabs and str(next_config.get("activeTabId") or "") not in set(enabled_tab_ids):
            next_config["activeTabId"] = enabled_tab_ids[0] if enabled_tab_ids else tabs[0]["id"]
        next_config["refreshMinutes"] = max(5, min(int(next_config.get("refreshMinutes") or 15), 180))
        next_config["country"] = str(next_config.get("country") or "IT").upper()
        self._config = next_config
        self._save()
        return {"ok": True, "config": self._config}

    async def prefetch_tabs(self, active_tab_id: str = "", limit: int = 120) -> Dict[str, Any]:
        return await asyncio.to_thread(self._prefetch_tabs_sync, str(active_tab_id or ""), int(limit or 120))

    async def get_news_source(self, tab_id: str = "", source_id: str = "", force: bool = False, limit: int = 80) -> Dict[str, Any]:
        return await asyncio.to_thread(self._news_source_sync, tab_id, source_id, bool(force), int(limit or 80))

    async def get_news(self, tab_id: str = "", force: bool = False, limit: int = 80) -> Dict[str, Any]:
        return await asyncio.to_thread(self._news_sync, tab_id, bool(force), int(limit or 80))

    async def refresh_all(self, limit: int = 120) -> Dict[str, Any]:
        return await asyncio.to_thread(self._refresh_all_sync, int(limit or 120))

    async def get_image_warm_status(self) -> Dict[str, Any]:
        future = self._image_warm_future
        if future is None:
            return {"ok": True, "done": True, "images": 0}
        if not future.done():
            return {"ok": True, "done": False}
        try:
            result = future.result()
            images = len(result.get("images") or {}) if isinstance(result, dict) else 0
            return {"ok": True, "done": True, "images": images}
        except Exception as exc:
            return {"ok": True, "done": True, "images": 0, "error": str(exc)}

    def _article_sync_logged(self, url: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        started = time.perf_counter()
        payload = fallback or {}
        result = self._article_sync(url, payload)
        elapsed = time.perf_counter() - started
        source = str(payload.get("source") or _hostname(str(payload.get("sourceSiteUrl") or "")) or "?")
        body_len = _reader_text_length(list(result.get("blocks") or [])) if isinstance(result, dict) else 0
        self._log(f"reader {source}: {elapsed:.2f}s available={bool(result.get('readerAvailable')) if isinstance(result, dict) else False} chars={body_len} target={_hostname(str(result.get('url') or url)) if isinstance(result, dict) else _hostname(url)} title={_clean_text((fallback or {}).get('title') or result.get('title') if isinstance(result, dict) else '')[:72]}")
        return result

    async def get_article(self, url: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Article opens have a dedicated pool so feed refresh, prefetch and image
        # warming can never put the Reader behind a long queue.
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._article_executor, self._article_sync_logged, url, fallback or {})

    def _foreground_browser_windows_sync(self) -> None:
        if os.name != "nt":
            return
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            SW_RESTORE = 9
            browser_names = {
                "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe",
                "opera_gx.exe", "vivaldi.exe", "waterfox.exe", "librewolf.exe", "arc.exe",
            }
            candidates: List[Tuple[int, int]] = []
            EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

            def process_name(pid: int) -> str:
                handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                if not handle:
                    return ""
                try:
                    size = wintypes.DWORD(32768)
                    buffer = ctypes.create_unicode_buffer(size.value)
                    if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                        return os.path.basename(buffer.value).lower()
                finally:
                    kernel32.CloseHandle(handle)
                return ""

            @EnumProc
            def enum_window(hwnd, _lparam):
                if not user32.IsWindowVisible(hwnd):
                    return True
                length = user32.GetWindowTextLengthW(hwnd)
                if length <= 0:
                    return True
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if process_name(int(pid.value)) in browser_names:
                    candidates.append((int(hwnd), int(pid.value)))
                return True

            user32.EnumWindows(enum_window, 0)
            if not candidates:
                return
            hwnd = candidates[0][0]
            user32.ShowWindow(hwnd, SW_RESTORE)
            # Windows can reject SetForegroundWindow when Steam owns the input
            # foreground lock. A harmless Alt press releases that lock, then the
            # browser window can be brought above Big Picture reliably.
            VK_MENU = 0x12
            KEYEVENTF_KEYUP = 0x0002
            user32.keybd_event(VK_MENU, 0, 0, 0)
            user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            # If Steam/Big Picture currently owns a topmost window, briefly raise
            # the browser above it and immediately return the browser to normal
            # non-topmost state. The page stays in front without permanently
            # changing the user's browser window mode.
            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_SHOWWINDOW = 0x0040
            flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags)
            user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, flags)
            user32.SetForegroundWindow(hwnd)
        except Exception:
            return

    def _open_external_url_sync(self, value: str) -> bool:
        if os.name == "nt":
            opened = False
            try:
                import ctypes
                result = ctypes.windll.shell32.ShellExecuteW(None, "open", value, None, None, 1)  # type: ignore[name-defined]
                opened = int(result) > 32
            except Exception:
                try:
                    os.startfile(value)  # type: ignore[attr-defined]
                    opened = True
                except Exception:
                    opened = False
            if opened:
                time.sleep(0.22)
                self._foreground_browser_windows_sync()
                # Existing browser instances may create/rename their target window
                # a little later; re-assert once without blocking the Decky event loop.
                time.sleep(0.38)
                self._foreground_browser_windows_sync()
            return opened
        try:
            import webbrowser
            return bool(webbrowser.open(value))
        except Exception:
            return False

    async def open_external_url(self, url: str) -> bool:
        value = str(url or "").strip()
        if not value.startswith(("http://", "https://")):
            return False
        return bool(await asyncio.to_thread(self._open_external_url_sync, value))

    async def clear_cache(self) -> Dict[str, Any]:
        removed = 0
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        for pattern in ("feed-*.json", "image-*.json", "article-*.json", "resolve-*.json"):
            for path in CACHE_DIR.glob(pattern):
                try:
                    path.unlink()
                    removed += 1
                except Exception:
                    pass
        if IMAGE_CACHE_DIR.exists():
            for path in IMAGE_CACHE_DIR.iterdir():
                if not path.is_file() or path.name.startswith("asset-"):
                    continue
                try:
                    path.unlink()
                    removed += 1
                except Exception:
                    pass
        return {"ok": True, "removed": removed}

    async def reset_config(self) -> Dict[str, Any]:
        self._config = _default_config()
        self._save()
        await self.clear_cache()
        return {"ok": True, "config": self._config}

    async def _main(self) -> None:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            self._image_server.start()
        except Exception as exc:
            self._log(f"image cache server unavailable: {exc}")
        self._load_assets()
        self._log("News 1.0.1 loaded")

    async def _unload(self) -> None:
        self._stopping.set()
        with self._background_timers_lock:
            pending_timers = list(self._background_timers)
            self._background_timers.clear()
        for timer in pending_timers:
            timer.cancel()
        try:
            with self._ilpost_fresh_prefetch_lock:
                timers = list(self._ilpost_fresh_timers)
                self._ilpost_fresh_timers = []
            for timer in timers:
                try:
                    timer.cancel()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            await asyncio.to_thread(self._image_server.stop)
        except Exception:
            pass
        try:
            self._cover_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        try:
            self._cover_background_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        try:
            self._cover_slow_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        try:
            self._cover_background_slow_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        try:
            self._prefetch_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        try:
            self._article_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        try:
            self._image_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        try:
            self._executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        self._log("News unloaded")

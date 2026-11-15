import importlib.util, json, sys, types
from pathlib import Path

root = Path(__file__).resolve().parents[1]
stub = types.ModuleType('decky_plugin')
stub.SETTINGS_DIR = str(root / '.test-settings')
stub.RUNTIME_DIR = str(root / '.test-runtime')
class Log:
    def info(self,*args,**kwargs): pass
stub.logger = Log()
sys.modules['decky_plugin'] = stub
spec = importlib.util.spec_from_file_location('news_main', root / 'main.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

cases = [
    ("Gattuso, penso ti serva questo: il post social che accende i tifosi della Lazio", "", "https://example.com/sport/calcio/foo", [], 'sports'),
    ("LIV cancels final event to focus on next chapter", "The golf league announced the move", "https://example.com/news/foo", [], 'sports'),
    ("Trump says North Korea's Kim has responded to his overtures", "White House diplomacy", "https://example.com/world/foo", [], 'politics'),
    ("Clair Obscur: Expedition 33 rischiava grosso ad essere presentato come RPG a turni", "Shuhei Yoshida e PlayStation", "https://multiplayer.it/notizie/foo.html", ["Videogiochi"], 'games'),
    ("Nuovo album di Taylor Swift conquista le classifiche", "", "https://example.com/music/foo", [], 'music'),
    ("Wall Street sale dopo i dati sull'inflazione", "Mercati e tassi di interesse", "https://example.com/economia/mercati", ["Economia"], 'economy'),
    ("Nuovo studio NASA sulla formazione delle galassie", "Ricerca scientifica e astronomia", "https://example.com/scienza/space", ["Scienza"], 'science'),
    ("Nuova terapia approvata per il trattamento della malattia", "Salute e medicina", "https://example.com/salute/medicina", ["Salute"], 'health'),
    ("Milano Fashion Week, le nuove collezioni in passerella", "Moda e designer", "https://example.com/moda/fashion-week", ["Moda"], 'fashion'),
]
for title, excerpt, url, labels, expected in cases:
    got = mod._categorize_item(title, excerpt, url, labels)
    assert got and got[0] == expected, (title, got, expected)


# Ambiguous/generic stories must stay only in Tutte rather than leak into a topic.
for title, excerpt in [
    ("Il presidente del club presenta il nuovo progetto per la città", "Una lunga intervista sul futuro dell'organizzazione"),
    ("La finale del progetto arriva dopo una lunga attesa", "Nessun contenuto sportivo"),
    ("Il mercato cambia volto dopo l'annuncio", "Analisi generale senza segnali economici forti"),
]:
    got = mod._categorize_item(title, excerpt, 'https://example.com/news/story', [])
    assert got == [], (title, got)

# Strong sports title must not leak into politics even if the excerpt mentions government context.
got = mod._categorize_item("Serie A: la Juventus vince a San Siro", "Il ministro commenta l'evento e la sicurezza", 'https://example.com/news/story', [])
assert got == ['sports'], got

sample_html = '''<html><head><meta property="og:image" content="https://cdn.example.com/hero.jpg"></head><body>
<article class="teaser"><p>Breve teaser che non deve vincere la selezione del corpo.</p></article>
<article class="story"><h1>Clair Obscur</h1><p>''' + ('Testo reale dell articolo con dettagli importanti. ' * 20) + '''</p>
<img src="https://cdn.example.com/article.jpg" width="1200" height="675" alt="Clair Obscur"></article></body></html>'''
plugin = mod.Plugin()
blocks, script = plugin._extract_article_blocks_from_html(sample_html, 'https://multiplayer.it/notizie/test.html')
assert mod._reader_text_length(blocks) > 500, mod._reader_text_length(blocks)
assert any(b.get('type') == 'image' for b in blocks), blocks

markdown = '''# Titolo\n\n![Hero](https://cdn.example.com/cover.jpg)\n\nPrimo paragrafo abbastanza lungo da essere un vero testo di articolo, con molte informazioni utili e complete.\n\nSecondo paragrafo altrettanto corposo che continua il contenuto della notizia con ulteriori dettagli importanti.\n'''
mb, hero = mod._markdown_to_reader_blocks(markdown, 'https://example.com/story')
assert hero == 'https://cdn.example.com/cover.jpg'
assert mod._reader_text_length(mb) > 150



# Google News RSS escaped anchor markup must never leak into visible article text.
raw_google = '&lt;a href="https://news.google.com/rss/articles/abc" target="_blank"&gt;Titolo ANSA&lt;/a&gt;&amp;nbsp;&amp;nbsp;&lt;font color="#6f6f6f"&gt;ANSA&lt;/font&gt;'
clean_google = mod._clean_text(raw_google)
assert '<a ' not in clean_google.lower() and '</a>' not in clean_google.lower(), clean_google
assert 'Titolo ANSA' in clean_google, clean_google

# Script/JSON-LD pollution must be dropped from reader paragraphs.
noisy_blocks = [
    {"type":"text","text":"Un paragrafo giornalistico normale e sufficientemente lungo da essere mantenuto dal reader."},
    {"type":"text","text":"{\\\"articleSection\\\":\\\"Musica\\\",\\\"@type\\\":\\\"ImageObject\\\",\\\"contentUrl\\\":\\\"https://cdn.example/x.jpg\\\"}"},
]
clean_blocks = mod._dedupe_article_blocks(noisy_blocks, 'Titolo', '')
assert len(clean_blocks) == 1, clean_blocks

# Jina Reader parser path with a mocked JSON response.
class FakeResponse:
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n=-1):
        payload = {"data": {"url": "https://example.com/full", "title": "Titolo completo", "content": markdown, "timestamp": "2026-08-17T20:00:00Z"}}
        return json.dumps(payload).encode("utf-8")
orig_urlopen = mod._policy_urlopen
mod._policy_urlopen = lambda *args, **kwargs: FakeResponse()
try:
    jr = plugin._jina_reader_article_sync("https://example.com/story")
    assert jr.get("hero") == "https://cdn.example.com/cover.jpg", jr
    assert int(jr.get("textLength") or 0) > 150, jr
finally:
    mod._policy_urlopen = orig_urlopen

catalog = json.loads((root / 'source_catalog.json').read_text(encoding='utf-8'))
it_names = {x['name'] for x in catalog['IT']}
assert 'Wired Italia' not in it_names
assert sum(len(v) for v in catalog.values()) == 61
for country_sources in catalog.values():
    for src in country_sources:
        assert src.get('favicon_url'), src['name']
        assert src.get('logo_url'), src['name']
        assert src.get('feed_url'), src['name']
for required in ['BadTaste', 'SpazioGames', "Tom's Hardware Italia", 'Multiplayer.it', 'Il Post', 'Open', 'Fanpage']:
    assert required in it_names, required
mp = next(x for x in catalog['IT'] if x['name'] == 'Multiplayer.it')
assert mp.get('feed_url') == 'https://multiplayer.it/feed/rss/homepage/'
fanpage = next(x for x in catalog['IT'] if x['name'] == 'Fanpage')
assert fanpage.get('feed_url') == 'https://www.fanpage.it/feed/', fanpage
plugin._catalog = catalog
migrated_fanpage = plugin._normalized_source({
    'id':'fanpage-existing','name':'Fanpage','country':'IT','siteUrl':'https://www.fanpage.it/',
    'feedUrl':'https://news.google.com/rss/search?q=when:7d+site:fanpage.it&hl=it&gl=IT&ceid=IT:it',
    'enabled':True,'custom':False,'tags':['all']
})
assert migrated_fanpage.get('id') == 'fanpage-existing', migrated_fanpage
assert migrated_fanpage.get('feedUrl') == 'https://www.fanpage.it/feed/', migrated_fanpage

# Cache identity must never collide between different article URLs.
a = plugin._article_cache_path('https://example.com/a')
b = plugin._article_cache_path('https://example.com/b')
assert a != b
print('offline smoke tests: OK')

# Dangerous generic words must not create false categories.
assert mod._categorize_item("È nato un nuovo festival dedicato alla fotografia", "Arte e cultura", "https://example.com/news/festival", []) == []
assert mod._categorize_item("Roma inaugura il nuovo museo sul Tevere", "Mostra e arte contemporanea", "https://example.com/citta/museo", []) in ([], ['art'])
assert mod._categorize_item("Il ministro premia i vincitori della Champions League", "Calcio e finale europea", "https://example.com/sport/champions", []) == ['sports']

# Full article content embedded in an RSS/Atom item must be usable even if the
# publisher page itself is only a small shell or blocks automated extraction.
plugin2 = mod.Plugin()
plugin2._request = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('network request before strong feedContent'))
plugin2._jina_reader_article_sync = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('Jina request before strong feedContent'))
feed_body = '<p>' + ('Questo e un paragrafo completo proveniente dal feed della testata con informazioni sostanziali. ' * 12) + '</p>'
article = plugin2._article_sync('https://example.com/feed-first-round16', {'title':'Titolo dal feed','feedContent':feed_body,'sourceSiteUrl':'https://example.com/'})
assert article.get('readerAvailable') is True, article
assert mod._reader_text_length(article.get('blocks') or []) > 300, article

# Reader must prefer the largest <picture>/<source> candidate instead of the
# low-resolution fallback <img> that many publisher pages expose first.
picture_html = '''<article><p>''' + ('Testo dell articolo sufficientemente lungo per la prova. ' * 8) + '''</p>
<picture><source media="(min-width: 900px)" srcset="https://cdn.example.com/photo-800.jpg 800w, https://cdn.example.com/photo-1800.jpg 1800w"><img src="https://cdn.example.com/photo-320.jpg" width="320" height="180" alt="Foto articolo"></picture></article>'''
picture_blocks, _ = plugin._extract_article_blocks_from_html(picture_html, 'https://example.com/story')
picture_urls = [block.get('url') for block in picture_blocks if block.get('type') == 'image']
assert 'https://cdn.example.com/photo-1800.jpg' in picture_urls, picture_urls

# Metadata selection must choose the better declared image rather than simply
# the first image tag encountered.
head = mod._HeadParser()
head.feed('''<head><meta property="og:image" content="https://cdn.example.com/og-640.jpg"><meta property="og:image:width" content="640"><meta property="og:image:height" content="360"><meta name="twitter:image" content="https://cdn.example.com/card-1600.jpg"><meta name="twitter:image:width" content="1600"><meta name="twitter:image:height" content="900"></head>''')
assert mod._best_meta_image(head, 'https://example.com/') == 'https://cdn.example.com/card-1600.jpg'

# Current Google News decoder flow must send the page's data-n-a-id, which may
# differ from the path id in the RSS URL.
plugin3 = mod.Plugin()
plugin3._read_resolve_cache = lambda *args, **kwargs: {}
plugin3._write_resolve_cache = lambda *args, **kwargs: None
shell = '<div data-n-a-id="PAGE_DECODER_ID" data-n-a-ts="1760000000" data-n-a-sg="signature-value"></div>'
plugin3._google_decoder_shell_sync = lambda url, *args, **kwargs: (shell.encode('utf-8'), 'text/html; charset=utf-8', url)
class FakeBatchResponse:
    def __init__(self, request): self.request = request
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n=-1):
        body = (self.request.data or b'').decode('utf-8', 'replace')
        decoded = mod.urllib.parse.unquote_plus(body)
        assert 'RSS_PATH_ID' in decoded, decoded
        assert 'generic' not in decoded, decoded  # compact Fbv4je row must be first
        nested = json.dumps([None, 'https://publisher.example.com/full-story'])
        return ("\n\n" + json.dumps([["wrb.fr", "Fbv4je", nested]])).encode('utf-8')
class FakeOpener:
    def __init__(self, factory): self.factory = factory
    def open(self, request, *args, **kwargs): return self.factory(request)
plugin3._google_decoder_opener = lambda: FakeOpener(lambda request: FakeBatchResponse(request))
resolved = plugin3._resolve_google_news_url_sync('https://news.google.com/rss/articles/RSS_PATH_ID', 'https://publisher.example.com/')
assert resolved == 'https://publisher.example.com/full-story', resolved

# Fast Google decoding must also try the canonical /articles/<id> shell when
# the RSS wrapper lacks decoder attributes (the live Il Post failure mode).
plugin3b = mod.Plugin()
plugin3b._read_resolve_cache = lambda *args, **kwargs: ""
plugin3b._write_resolve_cache = lambda *args, **kwargs: None
requested_shells = []
def _google_shell_request(url, *args, **kwargs):
    requested_shells.append(url)
    if '/articles/FAST_CANONICAL_ID' in url and '/rss/articles/' not in url:
        body = '<c-wiz><div data-n-a-id="FAST_CANONICAL_ID" data-n-a-ts="1760000001" data-n-a-sg="sig-fast"></div></c-wiz>'
    else:
        body = '<html><body>No decoder attributes here</body></html>'
    return body.encode(), 'text/html; charset=utf-8', url
plugin3b._google_decoder_shell_sync = _google_shell_request
class FastBatchResponse(FakeBatchResponse):
    def read(self, n=-1):
        nested = json.dumps([None, 'https://www.ilpost.it/2026/08/20/story-test/'])
        return ("\n\n" + json.dumps([["wrb.fr", "Fbv4je", nested]])).encode('utf-8')
plugin3b._google_decoder_opener = lambda: FakeOpener(lambda request: FastBatchResponse(request))
resolved_fast = plugin3b._resolve_google_news_url_sync('https://news.google.com/rss/articles/FAST_CANONICAL_ID', 'https://www.ilpost.it/', fast=True)
assert resolved_fast == 'https://www.ilpost.it/2026/08/20/story-test/', resolved_fast
assert any('/articles/FAST_CANONICAL_ID' in url and '/rss/articles/' not in url for url in requested_shells), requested_shells

# Reader-only rescue may try locale-aware Google shells without burdening cover
# enrichment. The generic fast cover path must remain just RSS + canonical.
plugin3c = mod.Plugin()
plugin3c._read_resolve_cache = lambda *args, **kwargs: ""
plugin3c._write_resolve_cache = lambda *args, **kwargs: None
reader_shells = []
def _reader_shell_request(url, *args, **kwargs):
    reader_shells.append(url)
    if '/read/READER_RESCUE_ID' in url:
        body = '<div data-n-a-id="READER_RESCUE_ID" data-n-a-ts="1760000002" data-n-a-sg="sig-reader"></div>'
    else:
        body = '<html><body>No decoder attrs</body></html>'
    return body.encode(), 'text/html; charset=utf-8', url
plugin3c._google_decoder_shell_sync = _reader_shell_request
class ReaderRescueBatch(FakeBatchResponse):
    def read(self, n=-1):
        nested = json.dumps([None, 'https://www.ilpost.it/2026/08/20/reader-rescue/'])
        return ("\n\n" + json.dumps([["wrb.fr", "Fbv4je", nested]])).encode('utf-8')
plugin3c._google_decoder_opener = lambda: FakeOpener(lambda request: ReaderRescueBatch(request))
rescued = plugin3c._resolve_google_news_url_sync('https://news.google.com/rss/articles/READER_RESCUE_ID', 'https://www.ilpost.it/', fast=True, reader_rescue=True)
assert rescued == 'https://www.ilpost.it/2026/08/20/reader-rescue/', rescued
assert any('/read/READER_RESCUE_ID' in url for url in reader_shells), reader_shells

# Il Post Google fallback must be recoverable without hiding articles. The new
# shared Bing RSS index supplies direct publisher URLs for many same-tab stories
# without one search request per card.
plugin3d = mod.Plugin()
plugin3d._read_resolve_cache = lambda *args, **kwargs: ""
written_resolves = []
plugin3d._write_resolve_cache = lambda src, dst: written_resolves.append((src, dst))
post_timestamp = int(__import__('datetime').datetime(2026, 8, 20, 12, 0, tzinfo=__import__('datetime').timezone.utc).timestamp())
recent_links = {
    plugin3d._title_match_key('La storia molto importante del giorno'): 'https://www.ilpost.it/2026/08/20/storia-molto-importante/',
    plugin3d._title_match_key('Un secondo articolo con un titolo diverso'): 'https://www.ilpost.it/2026/08/20/secondo-articolo/',
}
recent_calls = []
plugin3d._ilpost_bing_recent_links_sync = lambda: (recent_calls.append(1) or dict(recent_links))
plugin3d._jina_reader_article_sync = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('archive fallback used despite Bing direct match'))
post_one = {'title':'La storia molto importante del giorno','url':'https://news.google.com/rss/articles/POST_ARCHIVE_1','sourceSiteUrl':'https://www.ilpost.it/','published':post_timestamp}
post_two = {'title':'Un secondo articolo con un titolo diverso','url':'https://news.google.com/rss/articles/POST_ARCHIVE_2','sourceSiteUrl':'https://www.ilpost.it/','published':post_timestamp}
resolved_one = plugin3d._resolve_ilpost_item_sync(post_one)
resolved_two = plugin3d._resolve_ilpost_item_sync(post_two)
assert resolved_one.endswith('/storia-molto-importante/'), resolved_one
assert resolved_two.endswith('/secondo-articolo/'), resolved_two
assert len(written_resolves) == 2, written_resolves

# Reader must prefer a direct Il Post exact-title rescue over Google decoding, then
# use the real publisher URL for rendered extraction when direct access is blocked.
plugin3e = mod.Plugin()
real_post_url = 'https://www.ilpost.it/2026/08/20/storia-molto-importante/'
plugin3e._read_resolve_cache = lambda *args, **kwargs: ""
plugin3e._write_resolve_cache = lambda *args, **kwargs: None
plugin3e._ilpost_bing_cache['recent'] = (0, {})
plugin3e._resolve_ilpost_bing_exact_sync = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('Bing exact used before fresh Google decoder'))
plugin3e._resolve_google_news_url_sync = lambda *args, **kwargs: real_post_url
plugin3e._request = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError('publisher blocks direct Python request'))
post_blocks = [
    {'type':'text','text':'Primo paragrafo completo del Post recuperato dal renderer. ' * 10},
    {'type':'text','text':'Secondo paragrafo completo del Post con altri dettagli. ' * 10},
]
plugin3e._jina_reader_article_sync = lambda url, timeout=0: {
    'url':real_post_url,'title':'La storia molto importante del giorno','description':'Descrizione',
    'hero':'https://cdn.ilpost.it/hero.jpg','blocks':post_blocks,'textLength':mod._reader_text_length(post_blocks),
    'rawContent':'contenuto renderizzato'
}
post_reader = plugin3e._article_sync('https://news.google.com/rss/articles/POST_READER_ARCHIVE', {
    'title':'La storia molto importante del giorno','source':'Il Post','sourceSiteUrl':'https://www.ilpost.it/','published':post_timestamp
})
assert post_reader.get('readerAvailable') is True, post_reader
assert post_reader.get('url') == real_post_url, post_reader
assert post_reader.get('hero'), post_reader

# The strict rendered cover lane must likewise switch from an unresolved Google
# shell to the real Il Post URL before asking Jina for the hero.
plugin3f = mod.Plugin()
plugin3f._apply_cached_item_enrichment = lambda item: dict(item)
plugin3f._resolve_ilpost_item_sync = lambda item: real_post_url
cover_seen = []
plugin3f._jina_reader_article_sync = lambda url, timeout=0: (cover_seen.append(url) or {
    'url':real_post_url,'title':'Titolo','description':'','hero':'https://cdn.ilpost.it/card-1600.jpg',
    'blocks':[],'textLength':0,'rawContent':''
})
plugin3f._write_image_cache = lambda *args, **kwargs: None
plugin3f._schedule_image_cache_warm = lambda *args, **kwargs: None
cover_item = {'id':'post-cover-archive','title':'La storia molto importante del giorno','url':'https://news.google.com/rss/articles/POST_COVER_ARCHIVE','source':'Il Post','sourceSiteUrl':'https://www.ilpost.it/','published':post_timestamp}
_cover_id, cover_url, cover_resolved = plugin3f._rendered_cover_only_sync(cover_item, cover_item['url'])
assert cover_url and cover_resolved == real_post_url, (cover_url, cover_resolved)
assert cover_seen == [real_post_url], cover_seen

print('Il Post archive-rescue regression tests: OK')
print('extended offline smoke tests: OK')

# Reopening a cached article must never wait on publisher/image network access.
plugin4 = mod.Plugin()
cache_url = 'https://example.com/cached-reopen-v11'
cached_article = {
    'ok': True, 'readerAvailable': True, 'readerPartial': False,
    'title': 'Cached article', 'description': '',
    'hero': 'https://cdn.example.com/hero-1600.jpg',
    'published': 0, 'url': cache_url,
    'blocks': [{'type':'text','text':'Contenuto cache sufficientemente lungo. ' * 12}, {'type':'image','url':'https://cdn.example.com/body-1600.jpg','alt':''}],
    'embedUrl': ''
}
plugin4._write_article_cache(cache_url, cached_article)
plugin4._request = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('network request on cached reopen'))
plugin4._cache_remote_image_sync = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('image download on cached reopen'))
reopened = plugin4._article_sync(cache_url, {})
assert reopened.get('title') == 'Cached article', reopened
assert reopened.get('hero'), reopened

# Per-source feed RPC backend path must return one publisher independently so
# the frontend can paint stories progressively.
plugin5 = mod.Plugin()
source = plugin5._normalized_source({'id':'src-a','name':'Source A','country':'IT','siteUrl':'https://a.example/','feedUrl':'https://a.example/feed','enabled':True,'tags':['all']})
plugin5._config = {**mod._default_config(), 'onboardingComplete':True, 'sources':[source], 'tabs':[{'id':'all','name':'Tutte','sourceIds':['src-a'],'enabled':True,'category':'all'}], 'activeTabId':'all'}
plugin5._fetch_source_sync = lambda *args, **kwargs: {'source':source,'items':[{'id':'one','title':'Story one','url':'https://a.example/story','sourceId':'src-a','source':'Source A','published':123,'excerpt':'','feedCategories':[]}], 'error':''}
progressive = plugin5._news_source_sync('all','src-a',False,20)
assert progressive.get('ok') is True and len(progressive.get('items') or []) == 1, progressive
assert progressive['items'][0].get('sourceId') == 'src-a', progressive

print('progressive/cache regression tests: OK')

# High-resolution URL normalization used by the article hero pipeline.
assert mod._prefer_highres_image_url('https://sm.ign.com/t/ign_it/screenshot/default/gta.640.jpg') == 'https://sm.ign.com/ign_it/screenshot/default/gta.jpg'
assert mod._prefer_highres_image_url('https://img.example.com/photo.jpg?width=640&height=360') == 'https://img.example.com/photo.jpg?width=1920&height=1080'
assert mod._prefer_highres_image_url('https://site.example/wp-content/uploads/2026/08/photo-640x360.jpg') == 'https://site.example/wp-content/uploads/2026/08/photo.jpg'

# An explicitly empty custom tab means no sources; it must never silently fall
# back to every enabled publisher.
plugin6 = mod.Plugin()
s1 = plugin6._normalized_source({'id':'s1','name':'One','country':'IT','siteUrl':'https://one.example/','feedUrl':'https://one.example/feed','enabled':True,'tags':['all']})
plugin6._config = {**mod._default_config(), 'onboardingComplete':True, 'sources':[s1], 'tabs':[{'id':'empty','name':'Empty','sourceIds':[],'enabled':True,'category':'all'}], 'activeTabId':'empty'}
assert plugin6._selected_sources_for_tab('empty') == []
print('high-res/empty-tab regression tests: OK')

# Concurrent cover discovery must be monotonic: a late failure or a different
# fallback result cannot erase/change artwork that was already selected.
plugin7 = mod.Plugin()
cover_key = 'https://example.com/stable-cover-round4'
plugin7._write_image_cache(cover_key, 'https://cdn.example.com/first-1600.jpg', '')
plugin7._write_image_cache(cover_key, '', '')
kept = plugin7._read_image_cache(cover_key)
assert kept.get('remoteImage') == 'https://cdn.example.com/first-1600.jpg', kept
plugin7._write_image_cache(cover_key, 'https://cdn.example.com/different-hero.jpg', '')
kept2 = plugin7._read_image_cache(cover_key)
assert kept2.get('remoteImage') == 'https://cdn.example.com/first-1600.jpg', kept2
status = plugin7._cached_cover_status_sync([{'id':'stable','url':cover_key,'title':'Stable','source':'Source','sourceId':'s','published':0,'type':'article'}])
assert status.get('images', {}).get('stable') == 'https://cdn.example.com/first-1600.jpg', status
print('stable-cover regression tests: OK')

# Feed parsing must prefer the largest media image instead of blindly accepting
# the first thumbnail, avoiding slow article-page enrichment when RSS already
# contains a high-quality cover.
feed_xml = b'''<?xml version="1.0"?><rss xmlns:media="http://search.yahoo.com/mrss/"><channel><item>
<title>High-res feed cover</title><link>https://feed.example/story</link><description>Descrizione articolo</description>
<media:thumbnail url="https://cdn.example/thumb-320.jpg" width="320" height="180" />
<media:content url="https://cdn.example/hero-1600.jpg" type="image/jpeg" width="1600" height="900" />
</item></channel></rss>'''
source7 = plugin7._normalized_source({'id':'feed-hires','name':'Feed HiRes','country':'IT','siteUrl':'https://feed.example/','feedUrl':'https://feed.example/rss','enabled':True,'tags':['all']})
parsed7 = plugin7._parse_feed(source7, feed_xml, 'https://feed.example/rss')
assert parsed7 and parsed7[0].get('image') == 'https://cdn.example/hero-1600.jpg', parsed7
print('feed-cover quality regression tests: OK')

# Every predefined catalog source must have a real high-resolution favicon URL
# plus a bundled local fallback asset. IGN editions deliberately share ign.com.
catalog = json.load(open(root / 'source_catalog.json', encoding='utf-8'))
for country, rows in catalog.items():
    for row in rows:
        assert row.get('favicon_url'), (country, row.get('name'), 'missing favicon')
        assert 'larger=true' in row.get('favicon_url',''), (country, row.get('name'), row.get('favicon_url'))
        asset = str(row.get('logo_url') or '')
        assert asset.startswith('asset://favicons/'), (country, row.get('name'), asset)
        assert (root / 'assets' / 'favicons' / asset.rsplit('/',1)[-1]).is_file(), (country, row.get('name'), asset)
        if str(row.get('name') or '').lower().startswith('ign'):
            assert '/ign.com?' in row.get('favicon_url',''), row

plugin8 = mod.Plugin()
plugin8._image_server.start()
plugin8._prepare_bundled_favicons()
country_headline = plugin8._make_country_source('NZ')
assert country_headline.get('faviconUrl'), country_headline
assert country_headline.get('logoUrl','').startswith('http://127.0.0.1:'), country_headline

# SpazioGames: a single homepage scan must be able to recover artwork from the
# "most read" style cards by title, without fetching every individual article.
plugin8._request = lambda *args, **kwargs: (b'''<html><body><section><h2>Le notizie piu lette</h2>
<a href="https://www.spaziogames.it/notizie/elden-ring-news"><img src="https://cdn.spaziogames.it/images/elden-1600.jpg" width="1600" height="900">Elden Ring ha una sorpresa per i fan</a>
</section></body></html>''', 'text/html; charset=utf-8', 'https://www.spaziogames.it/')
spazio_item = {'id':'spazio-test','title':'Elden Ring ha una sorpresa per i fan','url':'https://news.google.com/rss/articles/test','source':'SpazioGames','sourceSiteUrl':'https://www.spaziogames.it/'}
spazio_cover = plugin8._spaziogames_cover_for_item_sync(spazio_item)
assert spazio_cover == 'https://cdn.spaziogames.it/images/elden-1600.jpg', spazio_cover
print('favicon/spaziogames regression tests: OK')

# Broad RSS buckets must not override a clearly different article subject.
assert mod._categorize_item(
    "PlayStation 5: Sony annuncia il nuovo aggiornamento PS5", "", "https://example.com/news/ps5", ["Technology"]
) == ["games"]
assert mod._categorize_item(
    "Formula 1, Ferrari pronta al GP di Monza", "", "https://example.com/news/f1", ["Business"]
) == ["sports"]
assert mod._categorize_item(
    "Wall Street sale dopo i dati sull'inflazione", "", "https://example.com/news/markets", ["Business"]
) == ["economy"]
# Geographic club names must not leak weather stories into Sport.
assert mod._categorize_item(
    "Meteo Napoli e Campania, le previsioni di venerdì 21 agosto: sole e caldo stabile, 32° C, temperature in aumento",
    "Le previsioni del tempo in Campania",
    "https://www.fanpage.it/napoli/meteo-napoli-campania-previsioni-venerdi-21-agosto/",
    []
) == []
# Weather can still be Sport when the sports subject is explicit.
assert mod._categorize_item(
    "Formula 1, meteo del GP: rischio pioggia durante la gara", "", "https://example.com/f1/weather", []
) == ["sports"]
print('broad-feed/weather category override regression tests: OK')

# All-tab prefetch must fetch one shared source only once even when it is used by
# several category tabs, then warm active/background cover pools independently.
plugin9 = mod.Plugin()
shared = plugin9._normalized_source({
    'id':'shared-src','name':'Shared','country':'IT','siteUrl':'https://shared.example/',
    'feedUrl':'https://shared.example/feed','enabled':True,'tags':['all']
})
plugin9._config = {
    **mod._default_config(), 'onboardingComplete': True, 'sources': [shared],
    'tabs': [
        {'id':'all','name':'Tutte','sourceIds':['shared-src'],'enabled':True,'category':'all'},
        {'id':'preset-games','name':'Videogiochi','sourceIds':['shared-src'],'enabled':True,'category':'games'},
        {'id':'preset-sports','name':'Sport','sourceIds':['shared-src'],'enabled':True,'category':'sports'},
        {'id':'preset-economy','name':'Economia','sourceIds':['shared-src'],'enabled':True,'category':'economy'},
    ],
    'activeTabId':'preset-games'
}
fetch_calls = []
plugin9._fetch_source_sync = lambda source, force, refresh: (
    fetch_calls.append(source['id']) or {
        'source': source, 'error':'', 'items': [
            {'id':'g','title':'PS5 riceve un grande aggiornamento','url':'https://shared.example/g','sourceId':'shared-src','source':'Shared','published':30,'excerpt':'','feedCategories':['Technology'],'type':'article','image':''},
            {'id':'s','title':'Formula 1, Ferrari pronta al GP','url':'https://shared.example/s','sourceId':'shared-src','source':'Shared','published':20,'excerpt':'','feedCategories':['Business'],'type':'article','image':''},
            {'id':'e','title':"Wall Street sale dopo i dati sull'inflazione",'url':'https://shared.example/e','sourceId':'shared-src','source':'Shared','published':10,'excerpt':'','feedCategories':['Business'],'type':'article','image':''},
        ]
    }
)
cover_calls = []
plugin9._start_cover_enrichment_sync = lambda items, rendered_limit=28, background=False: (cover_calls.append((background, [x['id'] for x in items])) or {'ok':True})
plugin9._apply_cached_item_enrichment = lambda item: dict(item)
prefetched = plugin9._prefetch_tabs_sync('preset-games', 120)
assert fetch_calls == ['shared-src'], fetch_calls
assert [x['id'] for x in prefetched['tabs']['preset-games']] == ['g'], prefetched['tabs']['preset-games']
assert [x['id'] for x in prefetched['tabs']['preset-sports']] == ['s'], prefetched['tabs']['preset-sports']
assert [x['id'] for x in prefetched['tabs']['preset-economy']] == ['e'], prefetched['tabs']['preset-economy']
assert any(not bg and ids == ['g'] for bg, ids in cover_calls), cover_calls
assert any(bg and set(ids) == {'s','e'} for bg, ids in cover_calls), cover_calls
print('simultaneous all-tab prefetch regression tests: OK')

# Generic publisher homepage cover discovery must fetch one publisher page once
# and reuse its index for multiple article cards.
plugin10 = mod.Plugin()
home_calls = []
home_html = b"""<html><body>
<a href="https://publisher.example/news/alpha"><img src="https://cdn.publisher.example/alpha-1600.jpg">Alpha story complete headline</a>
<a href="https://publisher.example/news/beta"><img src="https://cdn.publisher.example/beta-1600.jpg">Beta story complete headline</a>
<a href="https://publisher.example/news/gamma"><img src="https://cdn.publisher.example/gamma-1600.jpg">Gamma story complete headline</a>
</body></html>"""
plugin10._request = lambda url, *args, **kwargs: (home_calls.append(url) or (home_html, 'text/html; charset=utf-8', 'https://publisher.example/'))
plugin10._jina_reader_article_sync = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('unexpected rendered homepage fallback'))
for slug, title in [('alpha','Alpha story complete headline'),('beta','Beta story complete headline'),('gamma','Gamma story complete headline')]:
    item = {'id':slug,'title':title,'url':f'https://publisher.example/news/{slug}','source':'Publisher','sourceSiteUrl':'https://publisher.example/'}
    cover = plugin10._publisher_home_cover_for_item_sync(item)
    assert cover == f'https://cdn.publisher.example/{slug}-1600.jpg', (slug, cover)
assert home_calls == ['https://publisher.example/'], home_calls
print('publisher-home batch-cover regression tests: OK')

# Missing covers keep a finite fast path, but blocked publishers get a separate
# article-specific rendered lane. This must never reuse neighbouring homepage art.
class _InlineExecutor:
    def submit(self, fn, *args, **kwargs):
        class _Done:
            def result(self): return None
            def done(self): return True
        fn(*args, **kwargs)
        return _Done()

plugin11 = mod.Plugin()
plugin11._cover_executor = _InlineExecutor()
plugin11._cover_slow_executor = _InlineExecutor()
plugin11._apply_cached_item_enrichment = lambda item: dict(item)
fast_calls = []
rendered_calls = []
plugin11._enrich_one_image_sync = lambda item, allow=False: (fast_calls.append((item['id'], allow)) or (item['id'], '', item['url']))
plugin11._rendered_cover_only_sync = lambda item, resolved='': (rendered_calls.append(item['id']) or (item['id'], f"https://cdn.ilpost.it/{item['id']}.jpg", resolved or item['url']))
cover_items = [
    {'id':f'cover-{i}','title':f'Cover {i}','url':f'https://www.ilpost.it/story-{i}/','source':'Il Post','sourceId':'ilpost','sourceSiteUrl':'https://www.ilpost.it/','published':i,'type':'article'}
    for i in range(12)
]
cover_started = plugin11._start_cover_enrichment_sync(cover_items, rendered_limit=len(cover_items), background=False)
assert cover_started.get('slowBudget') == 12, cover_started
assert len(fast_calls) == 12 and all(allow is False for _, allow in fast_calls), fast_calls
assert rendered_calls == [f'cover-{i}' for i in range(12)], rendered_calls
assert not plugin11._cover_inflight, plugin11._cover_inflight

# If an Il Post Google shell survives both fast and strict rendered recovery with
# no image and no publisher URL, it must STILL remain in the Edicola. Cover failure
# is never a reason to delete a story; the Reader/site button can still be used and
# a later refresh may resolve it.
plugin11b = mod.Plugin()
plugin11b._cover_executor = _InlineExecutor()
plugin11b._cover_slow_executor = _InlineExecutor()
plugin11b._apply_cached_item_enrichment = lambda item: dict(item)
dead = {'id':'post-dead','title':'Dead Post shell','url':'https://news.google.com/rss/articles/DEAD','source':'Il Post','sourceId':'post','sourceSiteUrl':'https://www.ilpost.it/','published':1,'type':'article'}
plugin11b._enrich_one_image_sync = lambda item, allow=False: (item['id'], '', item['url'])
plugin11b._rendered_cover_only_sync = lambda item, resolved='': (item['id'], '', resolved or item['url'])
plugin11b._start_cover_enrichment_sync([dead], rendered_limit=1, background=False)
dead_status = plugin11b._cached_cover_status_sync([dead])
assert dead_status.get('unavailable') == [], dead_status
print('finite strict-rendered cover-pipeline regression tests: OK')

frontend_keep = (root / 'src' / 'index.tsx').read_text(encoding='utf-8')
assert '.filter((raw) => !unavailable.has' not in frontend_keep
assert '.filter((item) => !unavailable.has' not in frontend_keep
print('Il Post keep-all-items frontend regression test: OK')

# A Google-backed article must use only the fast decoder path. If decoding still
# returns the Google shell, one bounded rendered result can satisfy the Reader
# directly without entering the old compatibility resolver cascade.
plugin12 = mod.Plugin()
google_url = 'https://news.google.com/rss/articles/FAST_READER_TEST'
try:
    plugin12._article_cache_path(google_url).unlink(missing_ok=True)
    plugin12._article_cache_path('https://publisher.example/full-story').unlink(missing_ok=True)
except Exception:
    pass
resolve_flags = []
plugin12._resolve_google_news_url_sync = lambda url, site='', fast=False, reader_rescue=False: (resolve_flags.append((fast, reader_rescue)) or url)
rendered_blocks = [
    {'type':'text','text':'Primo paragrafo completo del reader renderizzato. ' * 12},
    {'type':'text','text':'Secondo paragrafo completo con altri dettagli. ' * 12},
]
plugin12._jina_reader_article_sync = lambda *args, **kwargs: {
    'url':'https://publisher.example/full-story','title':'Titolo renderizzato','description':'Descrizione',
    'hero':'https://cdn.publisher.example/hero-1600.jpg','blocks':rendered_blocks,
    'textLength':mod._reader_text_length(rendered_blocks),'rawContent':''
}
plugin12._request = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('publisher request after sufficient rendered Google body'))
google_article = plugin12._article_sync(google_url, {'title':'Fallback','sourceSiteUrl':'https://publisher.example/'})
assert resolve_flags == [(True, True)], resolve_flags
assert google_article.get('readerAvailable') is True, google_article
assert google_article.get('title') == 'Titolo renderizzato', google_article
print('bounded Google article-reader regression tests: OK')

# 2026-08-20 native-feed + cover-correctness regression tests.
catalog = json.loads((root / 'source_catalog.json').read_text(encoding='utf-8'))
spazio = next(x for x in catalog['IT'] if x['name'] == 'SpazioGames')
ign_it = next(x for x in catalog['IT'] if x['name'] == 'IGN Italia')
open_it = next(x for x in catalog['IT'] if x['name'] == 'Open')
assert spazio.get('feed_url') == 'https://www.spaziogames.it/feed', spazio
assert ign_it.get('feed_url') == 'https://it.ign.com/feed.xml', ign_it
assert open_it.get('feed_url') == 'https://www.open.online/feed/', open_it
plugin13 = mod.Plugin(); plugin13._catalog = catalog
for name, site, old_feed, expected in [
    ('SpazioGames','https://www.spaziogames.it/','https://news.google.com/rss/search?q=site%3Aspaziogames.it&hl=it-IT&gl=IT&ceid=IT%3Ait','https://www.spaziogames.it/feed'),
    ('IGN Italia','https://it.ign.com/','https://news.google.com/rss/search?q=site%3Ait.ign.com&hl=it-IT&gl=IT&ceid=IT%3Ait','https://it.ign.com/feed.xml'),
    ('Open','https://www.open.online/','https://news.google.com/rss/search?q=site%3Aopen.online&hl=it-IT&gl=IT&ceid=IT%3Ait','https://www.open.online/feed/'),
]:
    migrated = plugin13._normalized_source({'id':'existing-'+name,'name':name,'country':'IT','siteUrl':site,'feedUrl':old_feed,'enabled':True,'custom':False,'tags':['games']})
    assert migrated['feedUrl'] == expected, migrated

# Card images should be bandwidth-friendly. IGN thumbnails stay on /t/ and use
# a ~960px transform instead of being expanded to the original asset.
ign_thumb = 'https://sm.ign.com/t/ign_it/screenshot/default/example_abcd.640.jpg'
assert mod._prefer_card_image_url(ign_thumb) == 'https://sm.ign.com/t/ign_it/screenshot/default/example_abcd.960.jpg'
assert '/t/' not in mod._prefer_highres_image_url(ign_thumb), mod._prefer_highres_image_url(ign_thumb)

native_rss = b'''<?xml version="1.0"?><rss xmlns:media="http://search.yahoo.com/mrss/"><channel><title>IGN Italia</title>
<item><title>PS5: nuova esclusiva annunciata</title><link>https://it.ign.com/test/story</link>
<media:content url="https://sm.ign.com/t/ign_it/screenshot/default/story_abcd.640.jpg" type="image/jpeg" width="640" height="360" />
<description>Una descrizione sufficientemente chiara.</description></item></channel></rss>'''
parsed_native = plugin13._parse_feed({'id':'ign','name':'IGN Italia','country':'IT','siteUrl':'https://it.ign.com/','feedUrl':'https://it.ign.com/feed.xml','logoUrl':'','faviconUrl':'','brandColor':''}, native_rss, 'https://it.ign.com/feed.xml')
assert len(parsed_native) == 1, parsed_native
assert parsed_native[0]['url'] == 'https://it.ign.com/test/story', parsed_native[0]
assert parsed_native[0]['image'].endswith('.960.jpg'), parsed_native[0]['image']

# Google site-search fallbacks are freshness bounded: an archive result from years
# ago must never surface beside current news.
import email.utils, time as _time
_now = int(_time.time())
_old = email.utils.formatdate(_now - 400 * 86400, usegmt=True)
_fresh = email.utils.formatdate(_now - 2 * 3600, usegmt=True)
stale_rss = f'''<?xml version="1.0"?><rss><channel><title>Google News</title>
<item><title>Very old archive item</title><link>https://news.google.com/rss/articles/OLD</link><pubDate>{_old}</pubDate><description>old</description></item>
<item><title>Fresh current item</title><link>https://news.google.com/rss/articles/NEW</link><pubDate>{_fresh}</pubDate><description>fresh</description></item>
</channel></rss>'''.encode()
stale_parsed = plugin13._parse_feed({'id':'post','name':'Il Post','country':'IT','siteUrl':'https://www.ilpost.it/','feedUrl':'https://news.google.com/rss/search?q=site%3Ailpost.it','logoUrl':'','faviconUrl':'','brandColor':''}, stale_rss, 'https://news.google.com/rss/search?q=site%3Ailpost.it')
assert [x['title'] for x in stale_parsed] == ['Fresh current item'], stale_parsed
assert 'when%3A30d' in mod._google_news_site_feed('https://www.ilpost.it/', 'IT'), mod._google_news_site_feed('https://www.ilpost.it/', 'IT')

# A neighbouring link with no image must NOT steal the previous card's image.
strict_html = '''<html><body>
<a href="https://publisher.example/news/one"><img src="https://cdn.publisher.example/one.jpg">First totally different headline</a>
<a href="https://publisher.example/news/two">Second unrelated headline that has no artwork in its own anchor</a>
</body></html>'''
by_url, by_title = plugin13._publisher_home_index_from_html(strict_html, 'https://publisher.example/')
assert mod._normalized_article_url('https://publisher.example/news/one') in by_url, by_url
assert mod._normalized_article_url('https://publisher.example/news/two') not in by_url, by_url

# Rendered markdown must not assign one nearby image to multiple unrelated links.
strict_md = '''![Alpha story complete headline](https://cdn.publisher.example/alpha.jpg)
[Alpha story complete headline](https://publisher.example/news/alpha)
[Completely unrelated beta headline](https://publisher.example/news/beta)'''
md_url, md_title = plugin13._publisher_home_index_from_markdown(strict_md, 'https://publisher.example/')
assert mod._normalized_article_url('https://publisher.example/news/alpha') in md_url, md_url
assert mod._normalized_article_url('https://publisher.example/news/beta') not in md_url, md_url
print('native-feed/strict-cover regression tests: OK')

# Edicola is nearest-neighbour again; only the opened Reader uses stepped smooth
# scrolling. Reader title text must never be line-clamped/ellipsized.
frontend = (root / 'src' / 'index.tsx').read_text(encoding='utf-8')
assert 'const scrollReaderStep = useCallback' in frontend
assert 'node.clientHeight * .40' in frontend
assert 'behavior: "smooth"' in frontend
assert 'startReaderDirectionalScroll' in frontend
assert 'readerHoldFrameRef.current = window.requestAnimationFrame(tick)' in frontend
assert '}, 260);' in frontend
assert 'stopReaderContinuousScroll();' in frontend
assert 'desiredVerticalTravel' not in frontend
assert 'revealMagazineCardSmooth(best, 460)' in frontend
assert 'WebkitLineClamp:3' not in frontend
assert 'whiteSpace:"normal",overflow:"visible",textOverflow:"clip"' in frontend
assert 'preferFaviconFallback={true}' in frontend
assert 'const unavailable = new Set<string>(Array.isArray(status?.unavailable)' not in frontend
print('reader/hold-scroll + article-favicon + precise-edicola navigation regression tests: OK')

# 2026-08-20 Il Post imperative-rescue + raw Reader favicon regression tests.
# Bing News may wrap the publisher URL in apiclick.aspx; parsing must recover the
# exact Il Post URL without scraping a neighbouring result.
plugin14 = mod.Plugin()
bing_target = 'https://www.ilpost.it/2026/08/20/articolo-diretto-del-post/'
bing_wrapped = 'https://www.bing.com/news/apiclick.aspx?ref=example&url=' + mod.urllib.parse.quote(bing_target, safe='') + '&c=xyz'
bing_xml_link = bing_wrapped.replace('&', '&amp;')
bing_rss = ('<?xml version="1.0"?><rss><channel><title>Bing News</title>'
            '<item><title>Un articolo diretto del Post - Il Post</title><link>' + bing_xml_link +
            '</link><description>result</description></item></channel></rss>').encode()
parsed_bing = plugin14._ilpost_search_rss_links_from_data(bing_rss, 'https://www.bing.com/news/search?q=site%3Ailpost.it')
assert parsed_bing.get(plugin14._title_match_key('Un articolo diretto del Post')) == bing_target, parsed_bing
assert mod._unwrap_bing_news_url(bing_wrapped) == bing_target
bing_u = 'a1' + mod.base64.urlsafe_b64encode(bing_target.encode()).decode().rstrip('=')
assert mod._unwrap_bing_news_url('https://www.bing.com/ck/a?u=' + bing_u) == bing_target

# Explicit Reader rescue gets a second independent web-RSS route if Bing News
# has not indexed the story yet. Empty failures are cached only briefly.
plugin14._ilpost_bing_rss_page_sync = lambda *args, **kwargs: {}
plugin14._ilpost_bing_web_rss_sync = lambda *args, **kwargs: {
    plugin14._title_match_key('Titolo fondamentale del Post'): 'https://www.ilpost.it/2026/08/20/titolo-fondamentale/'
}
resolved_exact = plugin14._resolve_ilpost_bing_exact_sync('Titolo fondamentale del Post')
assert resolved_exact.endswith('/titolo-fondamentale/'), resolved_exact

# The opened article fallback must render the publisher PNG naked: a Google News
# transport URL must not add the rounded white Google tile around an Il Post icon.
frontend_raw = (root / 'src' / 'index.tsx').read_text(encoding='utf-8')
assert 'const rawReaderFavicon = preferFavicon && !!brandImage;' in frontend_raw
assert 'const googleBrand = !rawReaderFavicon' in frontend_raw
assert 'overflow:rawReaderFavicon?"visible":"hidden"' in frontend_raw
assert 'background:rawReaderFavicon?"transparent"' in frontend_raw
assert 'boxShadow:rawReaderFavicon?"none"' in frontend_raw

# Resolver cache generations are bumped so old failed Google/cover/article results
# cannot survive installation of this build.
assert mod.RESOLVE_CACHE_VERSION >= 10
assert mod.IMAGE_CACHE_VERSION >= 14
assert mod.ARTICLE_CACHE_VERSION >= 17
print('Il Post direct-link + raw Reader-favicon regression tests: OK')


# 2026-08-20 Il Post proactive exact-cover + Reader late-retry regression tests.
plugin15 = mod.Plugin()
plugin15._apply_cached_item_enrichment = lambda item: dict(item)
google_post = 'https://news.google.com/rss/articles/POST_PROACTIVE_EXACT_V2'
direct_post = 'https://www.ilpost.it/2026/08/20/post-proactive-exact-v2/'
proactive_item = {
    'id':'post-proactive','title':'Un titolo del Post non presente nell indice recente',
    'url':google_post,'source':'Il Post','sourceId':'post',
    'sourceSiteUrl':'https://www.ilpost.it/','published':int(mod.time.time()) - 3*60*60,'type':'article'
}
plugin15._resolve_ilpost_item_sync = lambda item: ''
exact_cover_calls = []
plugin15._resolve_ilpost_bing_exact_sync = lambda title, force=False: (exact_cover_calls.append((title, force)) or direct_post)
plugin15._request = lambda url, *args, **kwargs: (
    b'<html><head><meta property="og:image" content="https://cdn.ilpost.it/proactive-cover.jpg"></head><body></body></html>',
    'text/html; charset=utf-8', url
)
plugin15._jina_reader_article_sync = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('Jina used despite direct Il Post og:image'))
aid, proactive_image, proactive_resolved = plugin15._rendered_cover_only_sync(proactive_item, google_post)
assert aid == 'post-proactive'
assert proactive_resolved == direct_post, proactive_resolved
assert proactive_image == 'https://cdn.ilpost.it/proactive-cover.jpg', proactive_image
assert exact_cover_calls and exact_cover_calls[0][1] is False, exact_cover_calls
assert plugin15._read_resolve_cache(google_post) == direct_post

# Exact resolver failures must be retryable immediately by an explicit Reader open.
plugin16 = mod.Plugin()
q_calls = []
def fake_news(query, first=1):
    q_calls.append(('news', query))
    if len(q_calls) < 3:
        return {}
    return {plugin16._title_match_key('Titolo freschissimo del Post'): direct_post}
plugin16._ilpost_bing_rss_page_sync = fake_news
plugin16._ilpost_bing_web_rss_sync = lambda query: (q_calls.append(('web', query)) or {})
first_miss = plugin16._resolve_ilpost_bing_exact_sync('Titolo freschissimo del Post', force=False)
if first_miss:
    plugin16._ilpost_exact_cache[plugin16._title_match_key('Titolo freschissimo del Post')] = (mod.time.time(), '')
forced = plugin16._resolve_ilpost_bing_exact_sync('Titolo freschissimo del Post', force=True)
assert forced == direct_post, (first_miss, forced, q_calls)

main_text = (root / 'main.py').read_text(encoding='utf-8')
assert 'Il Post Reader late rescue' in main_text
assert 'title={_clean_text((fallback or {}).get' in main_text
print('Il Post proactive exact-cover + late Reader retry regression tests: OK')

# 2026-08-20 Il Post newest-story decoder + bounded fresh-card regression tests.
# Brand-new Google wrappers may expose c-wiz[data-p] before data-n-a-sg/ts.
plugin17 = mod.Plugin()
plugin17._read_resolve_cache = lambda *args, **kwargs: ""
plugin17._write_resolve_cache = lambda *args, **kwargs: None
raw_data_p = json.dumps(["garturlreq", ["X"], "DATA_P_ID", 1, "sig", "drop1", "drop2", "drop3", "drop4", "tailA", "tailB"])
data_p_shell = '<c-wiz data-p="' + raw_data_p.replace('&','&amp;').replace('"','&quot;') + '"></c-wiz>'
plugin17._google_decoder_shell_sync = lambda url, *args, **kwargs: (data_p_shell.encode(), 'text/html; charset=utf-8', url)
class DataPBatchResponse(FakeBatchResponse):
    def read(self, n=-1):
        nested = json.dumps([None, 'https://www.ilpost.it/2026/08/20/fresh-data-p/'])
        return ("\n\n" + json.dumps([["wrb.fr", "Fbv4je", nested]])).encode('utf-8')
plugin17._google_decoder_opener = lambda: FakeOpener(lambda request: DataPBatchResponse(request))
data_p_resolved = plugin17._resolve_google_news_url_sync('https://news.google.com/rss/articles/FRESH_DATA_P', 'https://www.ilpost.it/', fast=True, reader_rescue=True)
assert data_p_resolved.endswith('/fresh-data-p/'), data_p_resolved

# Fresh Il Post items must try Google's own wrapper decoder before any lagging
# exact-search route. This is the production case seen for the newest headlines.
plugin18 = mod.Plugin()
fresh_google = 'https://news.google.com/rss/articles/VERY_FRESH_POST'
fresh_direct = 'https://www.ilpost.it/2026/08/20/very-fresh-post/'
plugin18._read_resolve_cache = lambda *args, **kwargs: ""
plugin18._write_resolve_cache = lambda *args, **kwargs: None
plugin18._ilpost_bing_recent_links_sync = lambda: {}
plugin18._resolve_google_news_url_sync = lambda *args, **kwargs: fresh_direct
plugin18._ilpost_listing_links_sync = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('archive used before fresh Google decoder'))
fresh_item = {
    'id':'fresh-post','title':'Titolo appena pubblicato del Post','url':fresh_google,
    'source':'Il Post','sourceSiteUrl':'https://www.ilpost.it/',
    'published':int(mod.time.time()) - 30,'type':'article'
}
assert plugin18._resolve_ilpost_item_sync(fresh_item) == fresh_direct

# If the very newest wrapper is not decodable yet, the cover lane must not waste
# time on Bing exact (known to lag) or Jina on the opaque Google shell.
plugin19 = mod.Plugin()
plugin19._apply_cached_item_enrichment = lambda item: dict(item)
plugin19._read_resolve_cache = lambda *args, **kwargs: ""
plugin19._ilpost_bing_recent_links_sync = lambda: {}
plugin19._resolve_google_news_url_sync = lambda url, *args, **kwargs: url
plugin19._ilpost_listing_links_sync = lambda *args, **kwargs: {}
plugin19._resolve_ilpost_bing_exact_sync = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('Bing exact used for <90m fresh story'))
plugin19._jina_reader_article_sync = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('Jina used on unresolved fresh Google shell'))
aid, image, unresolved = plugin19._rendered_cover_only_sync(fresh_item, fresh_google)
assert aid == 'fresh-post' and not image and unresolved == fresh_google, (aid, image, unresolved)

main_text_latest = (root / 'main.py').read_text(encoding='utf-8')
assert 'Il Post resolve Google fresh' in main_text_latest
assert 'Il Post Reader Google fresh' in main_text_latest
assert '_schedule_ilpost_fresh_prefetch' in main_text_latest
assert 'HTTPCookieProcessor' in main_text_latest
assert mod.RESOLVE_CACHE_VERSION >= 11
print('Il Post newest-wrapper/session + bounded fresh-card regression tests: OK')

# 2026-08-20 Il Post official-Telegram + stable Reader hero + Steam browser tests.
plugin20 = mod.Plugin()
telegram_html = r'''
<div class="tgme_widget_message_wrap js-widget_message_wrap">
  <div class="tgme_widget_message" data-post="ilpost_official/71234">
    <div class="tgme_widget_message_text js-message_text" dir="auto">Il cancro ha un indirizzo<br>Una descrizione breve<br>Leggi tutto: <a href="https://ilpost.link/AbCdEf1234">https://ilpost.link/AbCdEf1234</a></div>
  </div>
</div>
<div class="tgme_widget_message_wrap js-widget_message_wrap">
  <div class="tgme_widget_message" data-post="ilpost_official/71235">
    <div class="tgme_widget_message_text js-message_text" dir="auto">Giovedì 20 agosto<br>Le foto dal mondo<br>Leggi tutto: <a href="https://ilpost.link/ZyXwVu9876">https://ilpost.link/ZyXwVu9876</a></div>
  </div>
</div>
'''
telegram_links, telegram_before = plugin20._ilpost_telegram_page_parse(telegram_html)
assert telegram_before == 71234, telegram_before
assert telegram_links[plugin20._title_match_key('Il cancro ha un indirizzo')] == 'https://ilpost.link/AbCdEf1234'
assert telegram_links[plugin20._title_match_key('Giovedì 20 agosto')] == 'https://ilpost.link/ZyXwVu9876'

# A newest story must be able to resolve from the official Telegram index before
# Bing/Google indexing catches up. Keeping the short link is valid even if urllib
# cannot follow the publisher redirect; Reader/Jina and Steam can follow it.
plugin20._ilpost_telegram_recent_links_sync = lambda deep=False: dict(telegram_links)
plugin20._resolve_ilpost_shortlink_sync = lambda url: url
plugin20._ilpost_bing_recent_links_sync = lambda: (_ for _ in ()).throw(AssertionError('Bing used before Telegram'))
plugin20._resolve_google_news_url_sync = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('Google used before Telegram'))
fresh_telegram_item = {
    'id':'telegram-fresh','title':'Il cancro ha un indirizzo',
    'url':'https://news.google.com/rss/articles/TELEGRAM_FRESH',
    'source':'Il Post','sourceSiteUrl':'https://www.ilpost.it/',
    'published':int(mod.time.time()) - 30,'type':'article'
}
assert plugin20._resolve_ilpost_item_sync(fresh_telegram_item) == 'https://ilpost.link/AbCdEf1234'

# Exact rescue also checks Telegram before issuing a lagging Bing search.
plugin21 = mod.Plugin()
plugin21._resolve_ilpost_telegram_sync = lambda title, deep=False: 'https://ilpost.link/ExactFresh42'
plugin21._ilpost_bing_rss_page_sync = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('Bing exact used despite Telegram hit'))
assert plugin21._resolve_ilpost_bing_exact_sync('Titolo nuovissimo del Post', force=True) == 'https://ilpost.link/ExactFresh42'

frontend_latest = (root / 'src' / 'index.tsx').read_text(encoding='utf-8')
# The correct card cover is authoritative after opening; the Reader parser may only
# provide a fallback when the card genuinely had no image.
assert '<ArticleHeroImage primary={item?.image || ""} fallback={articleHero}' in frontend_latest
assert 'The card cover is the canonical visual for the opened article' in frontend_latest
# "Leggi sul sito" now uses Steam's in-client browser (Instagram-style), with the
# old external/backend launch path only as a compatibility fallback.
assert 'NavigateToSteamWeb' in frontend_latest
assert 'openWebsiteInSteam(article?.url || item?.resolvedUrl || item?.url || "")' in frontend_latest
assert 'onClick={() => void rpc("open_external_url", article?.url || item?.url || "")}' not in frontend_latest
assert mod.RESOLVE_CACHE_VERSION >= 12
print('Il Post Telegram/newest + stable hero + Steam browser regression tests: OK')

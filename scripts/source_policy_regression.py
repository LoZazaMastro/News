"""Synthetic publisher-policy regressions. No publisher/site/RSS/network fetches."""
import asyncio
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
TEMP=tempfile.TemporaryDirectory(prefix="news-source-policy-")
stub=types.ModuleType("decky_plugin")
stub.SETTINGS_DIR=str(Path(TEMP.name)/"settings")
stub.RUNTIME_DIR=str(Path(TEMP.name)/"runtime")
stub.logger=types.SimpleNamespace(info=lambda *a,**k:None)
sys.modules["decky_plugin"]=stub
spec=importlib.util.spec_from_file_location("news_source_policy_tests",Path(os.environ.get("NEWS_POLICY_TEST_MODULE",ROOT/"main.py")))
news=importlib.util.module_from_spec(spec);spec.loader.exec_module(news)
FEED="https://publisher.invalid/approved/rss"
URL="https://publisher.invalid/original/article"
APPROVED={"id":"synthetic-approved","version":3,"hosts":("publisher.invalid",),"publisher":"Synthetic publication","state":"approved","mode":"metadata_only","feedUrls":(FEED,),"cacheSeconds":3600}
RSS=('''<rss xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>Ignored channel</title><item>
<content:encoded><![CDATA[<title>FORGED_TITLE_CANARY</title><description>FORGED_DESCRIPTION_CANARY</description>FULL_ARTICLE_CANARY<img src="https://cdn.invalid/EXCLUDED_IMAGE_CANARY.jpg">]]></content:encoded>
<title>AIとLinuxの速報 — Original headline</title><link>'''+URL+'''</link><description><![CDATA[出版社の短い説明。]]></description><pubDate>Sun, 15 Nov 2026 10:00:00 GMT</pubDate>
<media:content url="https://cdn.invalid/EXCLUDED_IMAGE_CANARY.jpg" type="image/jpeg"/><enclosure url="https://cdn.invalid/EXCLUDED_VIDEO_CANARY.mp4" type="video/mp4"/>
<category>FORGED_CATEGORY_CANARY</category></item></channel></rss>''').encode()

class PolicyTests(unittest.TestCase):
 def setUp(self):
  self.policies=patch.object(news,"SOURCE_POLICIES",news.SOURCE_POLICIES+(copy.deepcopy(APPROVED),));self.policies.start()
  self.plugin=news.Plugin()
  self.source={"id":"fixture-publisher","name":"Untrusted overridden name","country":"JP","siteUrl":"https://publisher.invalid/","feedUrl":FEED,"enabled":True,"custom":True,"logoUrl":"https://publisher.invalid/ICON_CANARY.png"}
  self.pending={"id":"pending-publisher","name":"Review only","country":"JP","siteUrl":"https://joho-todai.com/","feedUrl":"https://joho-todai.com/not-a-real-fixture-feed","enabled":True,"custom":True}
  self.plugin._config["sources"]=[self.source,self.pending]
  self.net=patch.object(news,"_policy_urlopen",side_effect=AssertionError("No network is permitted in these tests"));self.net.start()
  news.CACHE_DIR.mkdir(parents=True,exist_ok=True);news.IMAGE_CACHE_DIR.mkdir(parents=True,exist_ok=True)
 def tearDown(self):
  asyncio.run(self.plugin._unload());self.net.stop();self.policies.stop()
 def items(self):return self.plugin._parse_feed(self.source,RSS,FEED)
 def test_pending_review_never_discovers_enables_or_fetches(self):
  self.assertFalse(any("joho-todai.com" in json.dumps(x) for rows in json.loads((ROOT/'source_catalog.json').read_text(encoding='utf-8')).values() for x in rows))
  normalized=self.plugin._normalized_source(self.pending)
  self.assertFalse(normalized['enabled']);self.assertEqual(normalized['faviconUrl'],'');self.assertEqual(normalized['logoUrl'],'')
  self.assertEqual(normalized['policyState'],'pending_review')
  self.assertFalse(self.plugin._discover_source_sync(self.pending['siteUrl'],'JP')['ok'])
  before=copy.deepcopy(self.plugin._config)
  self.assertFalse(asyncio.run(self.plugin.save_config({'sources':[self.pending]}))['ok']);self.assertEqual(self.plugin._config,before)
  with patch.object(self.plugin,'_request',side_effect=AssertionError('Pending feed requested')):
   for force in [False,True]:self.assertEqual(self.plugin._fetch_source_sync(self.pending,force,60)['items'],[])
 def test_rss_only_original_metadata_no_body_media_or_category(self):
  result=self.items();self.assertEqual(len(result),1);item=result[0]
  self.assertEqual(item['title'],'AIとLinuxの速報 — Original headline');self.assertEqual(item['excerpt'],'出版社の短い説明。')
  self.assertEqual(item['source'],'Synthetic publication');self.assertEqual(item['url'],URL)
  self.assertGreater(item['published'],0);self.assertEqual(item['contentMode'],'metadata_only')
  raw=json.dumps(result,ensure_ascii=False)
  for canary in ['CANARY','feedContent','image','video','embed','categories','logo','favicon','author']:
   self.assertNotIn(canary,raw)
 def test_atom_summary_is_not_content_and_keeps_english(self):
  atom=f'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><content><![CDATA[FULL_ARTICLE_CANARY <summary>FORGED_DESCRIPTION_CANARY</summary>]]></content><title>Original English Linux headline</title><summary>Publisher supplied short description.</summary><link rel="alternate" href="{URL}"/><published>2026-11-15T10:00:00Z</published></entry></feed>'''.encode()
  item=self.plugin._parse_feed(self.source,atom,FEED)[0]
  self.assertEqual(item['title'],'Original English Linux headline');self.assertEqual(item['excerpt'],'Publisher supplied short description.');self.assertNotIn('CANARY',json.dumps(item))
 def test_no_body_fallback_if_description_is_missing_or_long(self):
  for xml in [RSS.replace(b'<description><![CDATA['+'出版社の短い説明。'.encode()+b']]></description>',b''),RSS.replace('出版社の短い説明。'.encode(),b'x'*2001)]:
   item=self.plugin._parse_feed(self.source,xml,FEED)[0];self.assertEqual(item['excerpt'],'');self.assertNotIn('CANARY',json.dumps(item))
 def test_feed_identity_and_original_host_are_pinned(self):
  self.assertEqual(self.plugin._parse_feed(self.source,RSS,'https://publisher.invalid/not-approved'),[])
  self.assertEqual(self.plugin._parse_feed(self.pending,RSS,self.pending['feedUrl']),[])
  self.assertEqual(self.plugin._parse_feed(self.source,RSS.replace(URL.encode(),b'https://elsewhere.invalid/story'),FEED),[])
  with self.assertRaises(ValueError):self.plugin._parse_feed(self.source,b'<!DOCTYPE rss [<!ENTITY x SYSTEM "file:///secret">]>'+RSS,FEED)
 def test_cache_allowlist_and_expiry_apply_before_and_after_disk(self):
  item={**self.items()[0],'feedContent':'FULL_ARTICLE_CANARY','image':'EXCLUDED_IMAGE_CANARY','blocks':[{'type':'text','text':'FULL_ARTICLE_CANARY'}]}
  payload={'fetchedAt':int(time.time()),'items':[item],'arbitrary':'FULL_ARTICLE_CANARY'}
  self.plugin._write_feed_cache(self.source['id'],payload,self.source)
  path=self.plugin._feed_cache_path(self.source['id']);raw=path.read_text(encoding='utf-8');self.assertNotIn('CANARY',raw)
  restored=self.plugin._read_feed_cache(self.source['id'],self.source);self.assertEqual(restored['items'],self.items())
  old=json.loads(raw);old['arbitrary']='FULL_ARTICLE_CANARY';old['items'][0]['image']='EXCLUDED_IMAGE_CANARY';old['items'][0]['feedContent']='FULL_ARTICLE_CANARY'
  news._atomic_json(path,old);self.assertNotIn('CANARY',json.dumps(self.plugin._read_feed_cache(self.source['id'],self.source)));self.assertNotIn('CANARY',path.read_text(encoding='utf-8'))
  old['fetchedAt']=int(time.time())-3600;news._atomic_json(path,old);self.assertEqual(self.plugin._read_feed_cache(self.source['id'],self.source),{});self.assertFalse(path.exists())
 def test_legacy_cache_cannot_bring_back_bodies_or_images(self):
  item={**self.items()[0],'feedContent':'FULL_ARTICLE_CANARY'}
  filename='a'*40+'.jpg';(news.IMAGE_CACHE_DIR/filename).write_bytes(b'EXCLUDED_IMAGE_CANARY')
  news._atomic_json(self.plugin._image_cache_path(URL),{'cacheVersion':news.IMAGE_CACHE_VERSION,'cachedFile':filename,'remoteImage':'https://cdn.invalid/image.jpg'})
  news._atomic_json(self.plugin._article_cache_path(URL),{'cacheVersion':news.ARTICLE_CACHE_VERSION,'fetchedAt':int(time.time()),'article':{'url':URL,'blocks':[{'type':'text','text':'FULL_ARTICLE_CANARY'}]}})
  news._atomic_json(self.plugin._feed_cache_path(self.source['id']),{'cacheVersion':news.FEED_CACHE_VERSION,'fetchedAt':int(time.time()),'items':[item]})
  self.assertEqual(self.plugin._read_feed_cache(self.source['id'],self.source),{})
  self.assertFalse(self.plugin._article_cache_path(URL).exists());self.assertFalse(self.plugin._image_cache_path(URL).exists());self.assertFalse((news.IMAGE_CACHE_DIR/filename).exists())
 def test_reader_and_forged_client_fallback_are_denied_before_cache(self):
  fake={**self.items()[0],'contentMode':'reader','policyId':'unrestricted','feedContent':'FULL_ARTICLE_CANARY','readerAvailable':True,'sourceSiteUrl':'https://unrestricted.invalid/'}
  for result in [self.plugin._article_sync(URL,fake),self.plugin._article_from_feed_content_sync(URL,fake),self.plugin._jina_reader_article_sync(URL),asyncio.run(self.plugin.get_article(URL,fake))]:
   self.assertFalse(result['readerAvailable']);self.assertEqual(result['contentMode'],'metadata_only');self.assertNotIn('CANARY',json.dumps(result))
  fake['url']='https://unrestricted.invalid/story';fake['sourceId']=self.pending['id']
  self.assertEqual(self.plugin._article_sync(fake['url'],fake)['errorCode'],'source_pending_review')
 def test_image_rpcs_and_cache_only_enrichment_never_restore_images(self):
  item={**self.items()[0],'image':'https://cdn.invalid/EXCLUDED_IMAGE_CANARY.jpg'}
  self.assertEqual(self.plugin._enrich_one_image_sync(item),(item['id'],'',''))
  self.assertEqual(self.plugin._rendered_cover_only_sync(item),(item['id'],'',''))
  self.assertEqual(self.plugin._start_cover_enrichment_sync([item])['started'],0)
  self.assertEqual(self.plugin._cached_cover_status_sync([item])['images'],{})
  self.assertEqual(self.plugin._enrich_images_sync([item])['images'],{})
  self.assertEqual(asyncio.run(self.plugin.cache_image(item['image'],URL))['url'],'')
  self.assertEqual(self.plugin._cache_remote_image_sync(item['image'],URL),('',''))
  self.assertNotIn('image',self.plugin._apply_cached_item_enrichment(item))
 def test_redirect_and_proxy_cannot_bypass_review(self):
  request=urllib.request.Request('https://unrestricted.invalid/')
  handler=news._SourcePolicyRedirect()
  for target in ['https://joho-todai.com/story','https://www.joho-todai.com/story','https://joho-todai.com./story','https://r.jina.ai/https://joho-todai.com/story',URL]:
   with self.assertRaises(PermissionError):handler.redirect_request(request,None,302,'',{},target)
  self.assertEqual(handler.redirect_request(request,None,302,'',{},FEED).full_url,FEED)
 def test_fetch_error_has_no_discovery_or_google_fallback(self):
  calls=[]
  with patch.object(self.plugin,'_request',side_effect=lambda url,*a,**k:calls.append(url) or (_ for _ in ()).throw(IOError('fixture offline'))),patch.object(self.plugin,'_discover_source_sync',side_effect=AssertionError('Discovery fallback')):
   result=self.plugin._fetch_source_actual_sync(self.source,True,60)
  self.assertEqual(calls,[FEED]);self.assertEqual(result['items'],[])
 def test_policy_fields_from_client_never_relax_packaged_rules(self):
  forged={**self.pending,'policyState':'approved','contentMode':'reader','cacheSeconds':86400,'enabled':True,'faviconUrl':'https://cdn.invalid/icon.png'}
  normalized=self.plugin._normalized_source(forged)
  self.assertFalse(normalized['enabled']);self.assertEqual(normalized['policyState'],'pending_review');self.assertEqual(normalized['logoUrl'],'')
 def test_public_payloads_strip_forbidden_data(self):
  item={**self.items()[0],'image':'CANARY','feedContent':'CANARY'}
  result=self.plugin._policy_payload({'items':[item], 'tabs':{'one':[item]}})
  self.assertNotIn('CANARY',json.dumps(result));self.assertEqual(result['items'],result['tabs']['one'])
 def test_scheme_less_discovery_and_foreign_restricted_images_are_blocked(self):
  self.assertFalse(self.plugin._discover_source_sync("joho-todai.com", "JP")["ok"])
  item={"title":"Unrestricted original", "url":"https://plain.invalid/story", "image":"https://joho-todai.com/image.jpg"}
  self.assertNotIn("image",self.plugin._policy_item(item))
  article={"url":"https://plain.invalid/story","hero":"https://joho-todai.com/image.jpg","blocks":[{"type":"image","url":"https://joho-todai.com/body.jpg"},{"type":"text","text":"Original unrestricted article"}]}
  safe=self.plugin._localize_article_images_cached_only(article)
  self.assertEqual(safe['hero'],'');self.assertEqual(len(safe['blocks']),1)
 def test_unrestricted_feeds_keep_existing_reader_images(self):
  plain={'id':'plain','name':'Unrestricted fixture','siteUrl':'https://plain.invalid/','feedUrl':'https://plain.invalid/rss'}
  item=self.plugin._parse_feed(plain,RSS.replace(URL.encode(),b'https://plain.invalid/story'),plain['feedUrl'])[0]
  self.assertIn('FULL_ARTICLE_CANARY',item['feedContent']);self.assertTrue(item['image']);self.assertNotIn('contentMode',item)

if __name__=='__main__':unittest.main(verbosity=2)

/** Offline News frontend checks. Optional --steamui-root=/path/to/steamui uses
 * React straight from the supplied Steam bundle, without redistributing it.
 * These are VM/unit tests, not a live Steam rendering or controller test.
 */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let React = { memo: (value) => value, Fragment: Symbol.for('react.fragment'),
  createElement: (type, props, ...children) => ({$$typeof: Symbol.for('react.transitional.element'), type, props: {...props, children}}),
  useCallback() {}, useEffect() {}, useLayoutEffect() {}, useMemo() {}, useRef() {}, useState() {} };
const argument = process.argv.find((item) => item.startsWith('--steamui-root='));
if (argument) {
  const steamRoot = argument.slice('--steamui-root='.length);
  const modules = {};
  const self = {webpackChunksteamui: {push: (entry) => Object.assign(modules, entry[1])}};
  for (const entry of fs.readdirSync(path.join(steamRoot, 'libraries')).filter((item) => item.endsWith('.js'))) {
    vm.runInNewContext(fs.readFileSync(path.join(steamRoot, 'libraries', entry), 'utf8'), {self, console}, {timeout: 8000});
  }
  const factory = Object.values(modules).find((fn) => fn.toString().includes('.createElement=') &&
    fn.toString().includes('.version=') && !fn.toString().includes('rendererPackageName'));
  assert.ok(factory, 'A React runtime must be present in supplied Steam libraries');
  const module = {exports: {}};
  factory(module, module.exports);
  React = module.exports;
  console.log(`Using real Steam React ${React.version}`);
  const chunk = fs.readdirSync(steamRoot).filter((item) => /^(?:chunk.*|sp)\.js$/.test(item))
    .map((item) => fs.readFileSync(path.join(steamRoot, item), 'utf8')).join('\n');
  for (const signature of ['window.SteamUIStore=', 'get GamepadUIMainWindowInstance()',
      'NavigateToSteamWeb(', 'BCanNavigate()', '.OPTIONS=4]', '.START=14]', '.DIR_UP=9]']) {
    assert.ok(chunk.includes(signature), `Steam signature missing: ${signature}`);
  }
  console.log('Supplied Steam navigation/input signatures: OK');
}

function fixture({legacy = false} = {}) {
  const state = {events: [], calls: [], bridgeError: false, disposed: false};
  const timers = new Map(); const frames = new Map(); const elements = new Map(); let serial = 0;
  const classSet = () => {const values = new Set(); return {add: (key) => values.add(key), remove: (key) => values.delete(key), contains: (key) => values.has(key)}};
  const style = () => {const props = new Map();return {
    setProperty: (key, value, priority = '') => props.set(key, {value, priority}),
    getPropertyValue: (key) => props.get(key)?.value || '',
    getPropertyPriority: (key) => props.get(key)?.priority || '',
    removeProperty: (key) => props.delete(key),
  }};
  const doc = {
    documentElement: {lang: 'it', classList: classSet()},
    body: {classList: classSet()},
    getElementById: (id) => elements.get(id),
    querySelector: () => null, querySelectorAll: () => [],
    createElement: () => {const elem={id: '', style: style(), remove: () => elements.delete(elem.id)}; return elem},
    head: {appendChild: (elem) => elements.set(elem.id, elem)},
  };
  const win = {document: doc, innerWidth: 1920, innerHeight: 1080,
    setTimeout: (fn) => {const id=++serial;timers.set(id,fn);return id}, clearTimeout: (id) => timers.delete(id),
    requestAnimationFrame: (fn) => {const id=++serial;frames.set(id,fn);return id}, cancelAnimationFrame: (id) => frames.delete(id),
    dispatchEvent() {}, addEventListener() {}, removeEventListener() {},
  };
  doc.defaultView = win;
  const main = {Navigate: (url) => state.events.push(['navigate', url]),
    NavigateBack: () => state.events.push(['back']),
    NavigateToSteamWeb: (url) => state.events.push(['web', url]),
    BCanNavigate: () => true, IsGamepadUIWindow: () => true,
    BrowserWindow: win, MenuStore: {CloseSideMenus: () => state.events.push(['close'])}};
  const router = {WindowStore: {GamepadUIMainWindowInstance: main, SteamUIWindows: [main]}, GetFocusedWindowInstance: () => main};
  win.SteamUIStore = router;
  const Navigation = {Navigate: (url) => state.events.push(['fallback-navigate', url]),
    NavigateBack: () => state.events.push(['fallback-back']),
    CloseSideMenus: () => state.events.push(['fallback-close'])};
  const routes = new Map();
  const api = {routerHook: {addRoute: (key, value) => routes.set(key, value), removeRoute: (key) => routes.delete(key)},
    call(method, ...args) {
      assert.equal(this, api, 'Decky call must retain its receiver');
      if(state.bridgeError) throw new Error('bridge disconnected');
      state.calls.push([method, ...args]);
      return Promise.resolve({ok: true, value: 42});
    }};
  const connections = [];
  win.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit = {
    connect(version) {connections.push(version);if(legacy && version === 2) throw new Error('older API');return api;}
  };
  const DFL = {Navigation, Router: router, findModuleExport: () => undefined,
    DialogButton: 'button', Focusable: 'div', PanelSection: 'section', PanelSectionRow: 'div', TextField: 'input',
    GamepadButton: {OK:1,CANCEL:2,SECONDARY:3,OPTIONS:4,BUMPER_LEFT:5,BUMPER_RIGHT:6,DIR_UP:9,DIR_DOWN:10,DIR_LEFT:11,DIR_RIGHT:12,SELECT:13,START:14}};
  const context = vm.createContext({window: win, document: doc, navigator: {language:'en-US',languages:['en-US']},
    DFL, SP_REACT: React, URL, console, CustomEvent: class {constructor(type, data) {this.type=type;this.detail=data?.detail}},
    queueMicrotask: (fn) => fn(), MutationObserver: class {observe(){} disconnect(){}},
    setTimeout:win.setTimeout, clearTimeout:win.clearTimeout,
  });
  let source = fs.readFileSync(process.env.NEWS_TEST_BUNDLE || path.join(root, 'dist/index.js'), 'utf8').replace('export default ', 'globalThis.__pluginFactory = ');
  source += `\n;globalThis.__test = {mainWindow, navigate, goBack, openWebsiteInSteam, callBackend, scheduleNewsTask,
    hideChromeElement, forceRestoreChrome, CURRENT_LOCALE, resolveNewsLocale,
    openArticle, isMetadataOnly, metadataNewsItem, stabilizeNewsItem, mergeNewsItemStable, rememberCardImage,
    NewsQamCard, ArticleCard, NewsImage, ArticleRoute, MetadataArticlePreview,
    get timerCount() {return backgroundUiTimers.size}, get disposed() {return newsDisposed}};`;
  vm.runInContext(source, context, {timeout: 8000});
  return {state, timers, frames, elements, style, context, test: context.__test, win, main, router, Navigation, routes, connections};
}
let count=0;
async function test(name, run) {await run(); count++;console.log(`OK ${String(count).padStart(2,'0')} ${name}`)}

await test('bundle loads and connects with Decky API v2', () => {
  const f=fixture();assert.deepEqual(f.connections,[2]);assert.equal(f.test.CURRENT_LOCALE, 'it');
});
await test('API fallback keeps callable legacy connection', () => {
  const f=fixture({legacy:true});assert.deepEqual(f.connections,[2,1]);
});
await test('registers six routes and creates current React elements', () => {
  const f=fixture();const plugin=f.context.__pluginFactory();assert.equal(f.routes.size,6);
  assert.equal(plugin.content.$$typeof,Symbol.for('react.transitional.element'));
  assert.equal(plugin.titleView.$$typeof,plugin.content.$$typeof);
  plugin.onDismount();assert.equal(f.routes.size,0);
});
await test('navigate BEFORE closing QAM', () => {
  const f=fixture();f.test.navigate('/news/edicola');assert.deepEqual(f.state.events.slice(0,2),[['navigate','/news/edicola'],['close']]);
});
await test('public SteamUIStore remains usable if DFL router discovery is stale', () => {
  const f=fixture();f.win.SteamUIStore={WindowStore:{GamepadUIMainWindowInstance:f.main}};
  f.router.WindowStore=undefined;assert.equal(f.test.mainWindow(),f.main);
});
await test('a non-navigable first window is not chosen', () => {
  const f=fixture();f.router.WindowStore.GamepadUIMainWindowInstance={Navigate(){},BCanNavigate:()=>false};
  assert.equal(f.test.mainWindow(),f.main);
});
await test('supports iterable window collections', () => {
  const f=fixture();f.router.WindowStore.GamepadUIMainWindowInstance=null;
  f.router.WindowStore.SteamUIWindows=new Map([[1,{Navigate(){},BCanNavigate:()=>false}],[2,f.main]]);
  assert.equal(f.test.mainWindow(),f.main);
});
await test('opens websites through the real window method', () => {
  const f=fixture();f.test.openWebsiteInSteam('https://example.invalid/story');
  assert.deepEqual(f.state.events,[['web','https://example.invalid/story'],['close']]);
});
await test('uses Navigator.SteamWeb fallback and rejects non-web URLs', () => {
  const f=fixture();delete f.main.NavigateToSteamWeb;
  f.main.Navigator={SteamWeb:(url)=>f.state.events.push(['navigator-web',url])};
  f.test.openWebsiteInSteam('javascript:alert(1)');assert.equal(f.state.events.length,0);
  f.test.openWebsiteInSteam('https://example.invalid/');assert.equal(f.state.events[0][0],'navigator-web');
});
await test('falls back to backend external URL when Steam web methods are missing', async () => {
  const f=fixture();delete f.main.NavigateToSteamWeb;
  f.test.openWebsiteInSteam('https://example.invalid/');await Promise.resolve();
  assert.deepEqual(f.state.calls,[['open_external_url','https://example.invalid/']]);
});
await test('RPC preserves receiver and converts synchronous failures to rejection', async () => {
  const f=fixture();assert.equal((await f.test.callBackend('get_bootstrap')).value,42);
  f.state.bridgeError=true;let request;
  assert.doesNotThrow(()=>{request=f.test.callBackend('get_bootstrap')});
  await assert.rejects(request,/bridge disconnected/);
});
await test('restores pre-existing inline chrome styles and priority', () => {
  const f=fixture();const elem={dataset:{},style:f.style()};
  elem.style.setProperty('display','flex','important');elem.style.setProperty('opacity','.85');
  f.test.hideChromeElement(elem);f.test.hideChromeElement(elem);assert.equal(elem.style.getPropertyValue('display'),'none');
  f.test.forceRestoreChrome();assert.equal(elem.style.getPropertyValue('display'),'flex');
  assert.equal(elem.style.getPropertyPriority('display'),'important');assert.equal(elem.style.getPropertyValue('opacity'),'.85');
  assert.equal(elem.style.getPropertyValue('pointer-events'),'');assert.equal(elem.dataset.newsFullscreenChrome,undefined);
});
await test('failed navigation restores chrome instead of leaving the client hidden', () => {
  const f=fixture();f.main.Navigate=()=>{throw new Error('test route failure')};f.test.navigate('/news/edicola');
  assert.equal(f.win.document.documentElement.classList.contains('deckyNewsFullscreen'),false);
});
await test('unload clears timers, styles and routes and blocks late RPCs', async () => {
  const f=fixture();const plugin=f.context.__pluginFactory();
  f.test.scheduleNewsTask(()=>{throw new Error('timer survived unload')},1000);
  f.test.navigate('/news/edicola');assert.ok(f.timers.size);plugin.onDismount();
  assert.equal(f.timers.size,0);assert.equal(f.frames.size,0);assert.equal(f.routes.size,0);assert.equal(f.elements.size,0);
  const calls=f.state.calls.length;await assert.rejects(f.test.callBackend('get_news'),/unloaded/);
  assert.equal(f.state.calls.length,calls);
});
await test('all existing interface locales keep their Steam mappings', () => {
  const f=fixture();for(const [steam,expected] of Object.entries({italian:'it',english:'en',spanish:'es',french:'fr',german:'de',brazilian:'pt-br',russian:'ru',japanese:'ja',schinese:'zh'}))
    assert.equal(f.test.resolveNewsLocale([steam]),expected);
});
await test('Reader does not mistake Steam OPTIONS/Y for Start/Menu', () => {
  const source=fs.readFileSync(path.join(root,'src/index.tsx'),'utf8');
  const fontUp=source.match(/const fontUp = ([^;]+);/)[1];assert.ok(!fontUp.includes('gp.OPTIONS'));
  assert.ok(fontUp.includes('gp.START'));
});
const metadataFixture = {id:'metadata',title:'AIとLinuxの速報',url:'https://publisher.invalid/original',sourceId:'publisher',source:'Synthetic publication',country:'JP',published:1794736800,excerpt:'出版社の短い説明。',type:'article',contentMode:'metadata_only'};
const children = (node) => {const value=node?.props?.children;const nested=Array.isArray(value)?value.flat(Infinity):[value];return [node,...nested.filter(Boolean).flatMap(children)];};
const renderMemo = (component, props) => (typeof component === 'function' ? component : component.type)(props);
await test('metadata-only whole-card activation visits original website without Reader or backend fetch', () => {
  const f=fixture();const polluted={...metadataFixture,resolvedUrl:'https://elsewhere.invalid/enriched',image:'IMAGE_CANARY',feedContent:'FULL_ARTICLE_CANARY'};
  f.test.openArticle(polluted);assert.equal(f.state.events[0][0],'web');assert.equal(f.state.events[0][1],metadataFixture.url);
  assert.ok(!f.state.events.some(([kind,url])=>kind==='navigate'&&url==='/news/article'));assert.equal(f.state.calls.length,0);
});
await test('metadata-only QAM and magazine cards do not render images or generated publisher icons', () => {
  const f=fixture();const item={...metadataFixture,image:'IMAGE_CANARY',sourceLogo:'LOGO_CANARY',sourceFavicon:'ICON_CANARY'};
  const qam=f.test.NewsQamCard({item});const magazine=renderMemo(f.test.ArticleCard,{item,index:0,placement:{x:0,y:0,w:6,h:2,style:{}}});
  for(const node of [qam,magazine]){
    const nodes=children(node);assert.ok(!nodes.some(n=>n?.type==='img'||n?.type==='svg'||n?.type===f.test.NewsImage));
    assert.ok(JSON.stringify(node).includes(metadataFixture.title));assert.ok(!JSON.stringify(node).includes('CANARY'));
    node.props.onClick();
  }
  assert.equal(f.state.events.filter(([kind])=>kind==='web').length,2);assert.equal(f.state.calls.length,0);
});
await test('metadata policy replaces stale UI artwork and full-body memory', () => {
  const f=fixture();const old={...metadataFixture,contentMode:undefined,image:'IMAGE_CANARY',feedContent:'FULL_ARTICLE_CANARY',resolvedUrl:'https://elsewhere.invalid/enriched'};
  f.test.rememberCardImage(old,old.image);
  for(const value of [f.test.stabilizeNewsItem({...old,contentMode:'metadata_only'}),f.test.mergeNewsItemStable(old,metadataFixture)]){
    assert.equal(value.title,metadataFixture.title);assert.equal(value.excerpt,metadataFixture.excerpt);assert.equal(value.url,metadataFixture.url);
    assert.ok(!JSON.stringify(value).includes('CANARY'));assert.ok(!('image' in value));assert.ok(!('resolvedUrl' in value));
  }
});
await test('direct metadata route entries use text preview without mounting Reader', () => {
  const f=fixture();f.win.__deckyNewsOpenItem={...metadataFixture,image:'IMAGE_CANARY'};
  const route=f.test.ArticleRoute();assert.equal(route.type,f.test.MetadataArticlePreview);
  const tree=f.test.MetadataArticlePreview(route.props);assert.ok(!children(tree).some(n=>n?.type==='img'||n?.type===f.test.NewsImage));
  assert.equal(f.state.calls.length,0);
});
console.log(`Frontend regression tests: ${count} passed${React.version ? ` (Steam React ${React.version})` : ' (mock React)'}.`);

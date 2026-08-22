# News

**News** is a Decky Loader plugin by **LoZazaMastro** that turns the Quick Access Menu into a fast news feed and adds a fullscreen, gamepad-first **Edicola** for reading news like a living magazine.

## What it does

- Quick headlines directly in the **QAM**.
- Fullscreen **Edicola** with a dynamic magazine layout instead of a uniform grid.
- Full 4-way controller navigation through Decky focusable components.
- Custom tabs such as Politics, Sport, Games, Music, Cinema, Comics, Art, Travel, Food, or any user-defined category.
- Article-level categorization: a general publication can contribute different stories to Politics, Sport, Technology, Games, Cinema and the other sections.
- Different sources can be assigned to each tab.
- Built-in source catalog by country plus online publisher discovery, country-wide headline feeds and manual RSS/Atom/site discovery.
- Sources from multiple countries can be mixed freely; country selection uses a controller-friendly picker.
- Category tabs can be renamed, reordered, disabled or deleted.
- First-run onboarding for country, sources and initial tabs.
- Reader view that extracts article text and images without opening a desktop browser when possible.
- Article artwork is filtered to reject tiny icons, avatars, logos and social-media graphics; missing artwork is enriched in the background when possible.
- Video cards, gamepad-focusable YouTube playback, and embedded social previews for supported X, Instagram and TikTok links found inside articles.
- Cached feeds with a configurable refresh interval.
- No API key is required for normal RSS/Atom sources.
- Designed without Windows-only helpers so the core plugin can run on Windows and Linux.

## First run

The QAM initially shows **Configure News**. The onboarding flow asks for:

1. Country.
2. Sources.
3. Edicola tabs/categories.
4. Final review.

The configuration can later be edited from **News → Settings**. Re-running onboarding does not erase the existing setup until the new configuration is explicitly completed.

## Sources

The included catalog is only a convenience layer. The source picker can also search publishers online for the selected country. A source can additionally be added by pasting:

- the home page of a publication (News attempts RSS/Atom discovery),
- a direct RSS/Atom URL,
- a YouTube channel URL when its channel feed can be identified.

Some sites do not expose a public feed or block automated page access. In that case News leaves the original site available through **Open on website** rather than attempting to bypass access controls or paywalls.

## Reader mode

News downloads the public article page and extracts readable headings, paragraphs, quotes and images. If the page cannot be cleanly extracted, the plugin keeps the headline/preview and offers the original website.

## Reader and artwork caching

- News classifies **individual articles**, not entire publishers, before placing them in category tabs.
- Article artwork is progressively resolved from the publisher page, JSON-LD and article-body images.
- Resolved images are downloaded to a local cache and served from a tiny localhost image server, reducing repeated hotlink requests while browsing tabs or reopening articles.
- Reader extraction also checks structured JSON/application data and AMP pages when normal HTML is only a shell.
- Public X, Instagram, Facebook and TikTok links are kept in article order as centered embeds; YouTube and TikTok video embeds can be controlled with the gamepad.

## Languages

News automatically follows the Steam / Big Picture interface language. It recognizes both normal locale codes and Steam-style identifiers such as `italian`, `brazilian`, `russian`, `japanese` and `schinese`. Unsupported languages fall back consistently to English.

The interface currently includes Italian plus eight additional translations:

- Italian
- English
- Spanish
- French
- German
- Brazilian Portuguese
- Russian
- Japanese
- Simplified Chinese

Country names, category labels, relative timestamps, onboarding, QAM, Edicola, Reader, Settings and common runtime messages all follow the detected interface locale. Translation catalogs are kept in `src/locales.json` and validated with `npm run validate:translations`.

## Project structure

- `src/index.tsx` — QAM, onboarding, Edicola, reader, settings UI and runtime locale detection.
- `src/locales.json` — validated interface translations.
- `main.py` — feed discovery/fetching, cache, article extraction and persistence.
- `source_catalog.json` — starter source catalog.
- `countries.json` — country picker data.
- `dist/index.js` — bundled frontend loaded by Decky.

## Build

```bash
npm install
npm run build
python -m py_compile main.py
```

## Version

Current development version: **1.0.0**.

## License

MIT.

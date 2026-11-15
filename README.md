<div align="center">

# News

### News becomes a Newsstand to browse with your controller.

Quick headlines in the QAM and a full-screen reader that transforms RSS feeds, websites, and channels into a personal magazine for Steam Big Picture.

[![Release](https://img.shields.io/github/v/release/LoZazaMastro/News?style=for-the-badge&label=Release&labelColor=111111&color=ffffff)](https://github.com/LoZazaMastro/News/releases/latest)
[![Licenza MIT](https://img.shields.io/badge/Licenza-MIT-ffffff?style=for-the-badge&labelColor=111111)](LICENSE)

</div>

## Information, without leaving Gaming Mode

News utilizes the quick access menu for instant updates and a full-screen **Newsstand** for reading. The layout adapts dynamically based on content, resembling a magazine, and every element remains fully accessible through Decky's native navigation.

- recent headlines directly inside the QAM;
- full-screen Newsstand with dynamic layouts and 4-way direction navigation;
- dedicated tabs for politics, sports, video games, music, cinema, comics, art, travel, cooking, or personal categories;
- different sources for each tab, with the ability to mix multiple countries;
- renameable, reorderable, toggleable, or deleteable categories;
- initial catalog by country, online publisher search, and manual addition of websites or RSS/Atom feeds;
- Reader mode that extracts public text and images whenever possible;
- supported video cards and embedded content for YouTube and select social links;
- local cache and configurable update intervals;
- no API keys required for standard RSS/Atom sources.

Classification occurs on a per-article basis: a general publication can feed multiple sections simultaneously without being forced into a single category.

## First startup

The onboarding process guides you through choosing your:

1. country;
2. sources;
3. Newsstand tabs and categories;
4. final summary.

You can rerun it anytime from the settings. Your existing configuration remains active until the new setup process is fully completed and confirmed.

## Sources and Reader Mode

You can paste the home page of a news outlet, a direct RSS/Atom feed, or a recognized YouTube channel. If a website does not expose public feeds, blocks automatic access, or does not provide an extractable article, News retains the preview and an **Open on website** link: it does not bypass paywalls or source restrictions.

Images are crawled from the page, structured data, and the article body, discarding icons, avatars, and logos that are too small. Resolved assets are cached locally to avoid repeated requests and loading times during navigation.

## Publisher-specific metadata-only handling

News 1.0.2 adds a package-owned `metadata_only` policy for sources whose approved display is limited to the original headline, publication name, date, publisher-supplied short description and original article link. It does not change the default Reader behavior of other sources.

For a restricted source:

- Activation requires a maintainer-approved policy, exact HTTPS feed endpoints and an explicit cache lifetime (at most 24 hours). User settings, source edits and client RPC flags cannot grant approval.
- RSS `description` or Atom `summary` is used as supplied. `content`, `content:encoded`, media/enclosures, images, icons, generated covers, Reader extraction, page/proxy fetching, discovery fallbacks and derived article categories are excluded. A missing description remains empty; a description over 2,000 characters is omitted rather than summarized.
- Newsstand/QAM cards contain text only. Selecting one visits the original website at the reader's request; it does not open News Reader or preload the article. Interface labels may be localized; publication text is not translated, summarized, sent to TTS or used for model training by this implementation.
- Persistent feed caches contain only these display fields plus necessary item/source identifiers, policy version and cache timing. Older incompatible caches are rejected, restricted Reader/cover records are purged when encountered, and expired metadata is not reused as an offline fallback. Image and Reader RPCs independently enforce the host policy before consulting caches or doing network work.
- HTTP necessarily transfers the **whole bounded RSS/Atom response**, including any extra fields the feed server includes. The metadata parser ignores those extra fields and never stores or displays them. This is not a promise of server-side field selection. The publisher must approve the feed retrieval and display conditions before activation.

**Joho no Todai remains pending review.** This release does not add it to `source_catalog.json`, include a live feed endpoint or source assets, fetch its site/feed, or activate it. The English RSS supplied in issue #1 is a review reference, not activation permission. Catalogue eligibility, listing conditions and any agreed retention/display terms still require the maintainer's editorial decision and publisher confirmation. The software's MIT license does not sublicense publisher articles or images or authorize redistribution beyond agreed display.

Synthetic policy checks (no publisher requests):

```bash
python -X utf8 scripts/source_policy_regression.py
node scripts/frontend-regression.mjs
```

## Languages

News automatically follows Steam's interface language. Translations are included for Italian, English, Spanish, French, German, Brazilian Portuguese, Russian, Japanese, and Simplified Chinese; unavailable languages default to English.

## Installation

You can install and update News from the [Playhub](https://github.com/LoZazaMastro/Playhub) Plugin Store, or download the ZIP from the [latest release](https://github.com/LoZazaMastro/News/releases/latest) and install it via **Decky → Settings → Developer → Install plugin from ZIP**.

The core does not rely on Windows-exclusive helpers and is designed to work on Linux installations supported by Decky as well.

## Development

```bash
npm install
npm run validate:translations
npm run build
python -m py_compile main.py
```

The frontend and translations are located in `src/`; source discovery, downloading, Reader mode, and caching are managed by `main.py`.

## License

News is distributed under the [MIT](LICENSE) license. Displayed content remains the property of its respective sources.

<div align="center">

Created and maintained by **[LoZazaMastro](https://github.com/LoZazaMastro)**.

</div>

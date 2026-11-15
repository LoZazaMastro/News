// News 1.0.1 — generated from src/index.tsx; do not edit dist by hand.
const manifest = {"name":"News"};
const API_VERSION = 2;
const internalAPIConnection = window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit;
if (!internalAPIConnection) throw new Error("[@decky/api]: Decky Loader API is unavailable.");
let api;
try { api = internalAPIConnection.connect(API_VERSION, manifest.name); }
catch { api = internalAPIConnection.connect(1, manifest.name); console.warn("[News] Falling back to Decky API v1."); }
if (typeof api?.call !== "function" || !api?.routerHook) throw new Error("[News]: This Decky Loader does not expose the required plugin API.");
const call = api.call.bind(api);
const routerHook = api.routerHook;
const definePlugin = (fn) => (...args) => fn(...args);
const { DialogButton, Focusable, GamepadButton, Navigation, PanelSection, PanelSectionRow, Router, TextField, findModuleExport } = DFL;
const { memo, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } = SP_REACT;

const EDICOLA_ROUTE = "/news/edicola";
const ARTICLE_ROUTE = "/news/article";
const ONBOARDING_ROUTE = "/news/onboarding";
const SETTINGS_ROUTE = "/news/settings";
const TAB_EDITOR_ROUTE = "/news/tab-editor";
const SOURCE_EDITOR_ROUTE = "/news/source-editor";
const CHROME_STYLE_ID = "decky-news-fullscreen-style";
const ROOT_CLASS = "deckyNewsFullscreen";
const CONFIG_CHANGED_EVENT = "decky-news:config-changed";
// Keep bootstrap/config alive across fullscreen route unmounts. Going from the
// reader back to the Edicola remounts the route; without this cache there is a
// first render where config/tabs are temporarily empty, which used to flash the
// impossible "no active tabs" + "preparing" state reported by Andrea.
let newsDisposed = false;
const backgroundUiTimers = new Set();
function scheduleNewsTask(callback, delay) {
    if (newsDisposed)
        return;
    const timer = window.setTimeout(() => {
        backgroundUiTimers.delete(timer);
        if (!newsDisposed)
            callback();
    }, delay);
    backgroundUiTimers.add(timer);
}
let bootstrapUiCache = null;
let bootstrapLoadPromise = null;
const NEWS_TRANSLATIONS = { "it": { "openKiosk": "Apri l'edicola", "settings": "Impostazioni", "settingsDetail": "Fonti, tab e aggiornamento dell'Edicola", "refresh": "Aggiorna", "back": "Indietro", "cancel": "Annulla", "close": "Chiudi", "retry": "Riprova", "continue": "Continua", "add": "Aggiungi", "remove": "Rimuovi", "enable": "Attiva", "disable": "Disattiva", "delete": "Elimina", "save": "Salva", "saving": "Salvataggio…", "search": "Cerca online", "findFeed": "Trova feed", "readSite": "Leggi sul sito", "loading": "Caricamento…", "updating": "Aggiornamento…", "play": "Riproduci", "pause": "Pausa", "now": "adesso", "yesterday": "ieri", "minutesAgo": "{n} min fa", "hoursAgo": "{n} ore fa", "daysAgo": "{n} giorni fa", "video": "Video", "minutesUnit": "min", "personalKiosk": "La tua edicola personale", "personalKioskDetail": "Scegli paesi, fonti e categorie. News organizzerà tutto per la lettura rapida e per l'Edicola.", "configure": "Configura News", "noNews": "Nessuna notizia", "noNewsDetail": "Controlla le fonti o aggiorna il feed.", "noActiveTab": "Nessun tab attivo", "emptyPage": "Questa pagina è ancora vuota", "prepareKiosk": "Preparazione dell'edicola…", "prepareOnboarding": "Preparazione…", "articleLoading": "Caricamento dell'articolo…", "readerPartial": "La fonte rende disponibile solo una parte del contenuto in questa modalità. Puoi continuare con “Leggi sul sito”.", "readerUnavailable": "Non sono riuscito a estrarre un corpo leggibile da questa pagina. La copertina e i dati disponibili restano visibili; puoi continuare con “Leggi sul sito”.", "setup": "Configurazione", "startTitle": "Da dove vuoi iniziare?", "startDetail": "Scegli il paese principale. In seguito potrai aggiungere fonti e notizie da tutti gli altri paesi senza cambiare questa preferenza.", "primaryCountry": "Paese principale", "chooseSources": "Scegli le tue fonti", "chooseSourcesDetail": "Scegli un paese, cerca una testata oppure aggiungi un sito/feed. Puoi mescolare liberamente fonti di paesi diversi nella stessa Edicola.", "sourceCountry": "Paese delle fonti", "sourceName": "Nome della fonte", "addSiteFeed": "Aggiungi un sito o un feed", "sourcesWorldwide": "Fonti suggerite dal mondo", "sourcesWorldwideDetail": "Una selezione rapida di testate utili per costruire un'Edicola internazionale.", "addOtherCountries": "Vuoi aggiungere fonti anche da altri paesi?", "addOtherCountriesDetail": "Le fonti che hai già selezionato restano salvate. Scegli un altro paese nel menu sopra per continuare a costruire un'Edicola internazionale.", "buildKiosk": "Costruisci l'Edicola", "buildKioskDetail": "Scegli le sezioni che vuoi in alto. Le notizie vengono categorizzate articolo per articolo.", "customTab": "Tab personalizzata", "tabName": "Nome della tab", "readyTitle": "La tua edicola è pronta", "readyDetail": "Questa è la configurazione iniziale. Potrai aggiungere, rimuovere e riordinare fonti e tab dalle impostazioni.", "enterKiosk": "Entra nell'Edicola", "sources": "Fonti", "country": "Paese", "tabs": "Tab", "tabsHeading": "Tab dell'Edicola", "newTab": "Nuova tab", "createTab": "Crea tab", "addSourcesAny": "Aggiungi fonti da qualsiasi paese", "countryHeadlines": "Notizie principali del paese", "updateHeading": "Aggiornamento", "cacheInterval": "Intervallo cache", "clearCache": "Svuota cache", "repeatSetup": "Ripeti configurazione iniziale", "resetHeading": "Ripristino", "resetAll": "Cancella tutto e ricomincia da zero", "resetDetail": "Elimina fonti, tab e cache di News e riapre la configurazione iniziale.", "includedSources": "Fonti incluse", "tabVisibility": "Visibilità della tab", "tabVisibilityDetail": "Puoi nasconderla senza eliminare la configurazione.", "edit": "Modifica", "editTab": "MODIFICA TAB", "name": "Nome", "activateTab": "Attiva tab", "deactivateTab": "Disattiva tab", "deleteTab": "Elimina tab", "active": "Attiva", "inactive": "Disattivata", "availableSourcesFor": "{n} fonti disponibili per {country}", "noPreconfiguredSources": "Nessuna fonte preconfigurata per {country}: usa la ricerca online o aggiungi le notizie principali.", "selectedSourcesSummary": "{sources} fonti selezionate da {countries} paesi", "onlineSearchMinChars": "Scrivi almeno due caratteri per cercare fonti online.", "onlineSourcesAdded": "{n} fonti online aggiunte ai risultati.", "onlineSourcesFound": "{n} fonti trovate online.", "noMoreSources": "Nessun’altra fonte trovata online.", "onlineSearchUnavailable": "Ricerca online non disponibile.", "sourceAdded": "{name} aggiunta.", "sourceNotFound": "Fonte non trovata.", "countryHeadlinesFailed": "Impossibile aggiungere le notizie principali del paese.", "selectAtLeastOneSource": "Seleziona almeno una fonte.", "saveConfigFailed": "Non ho potuto salvare la configurazione.", "alreadyPresent": "{name} è già presente.", "mustKeepActiveTab": "Deve rimanere almeno una tab attiva.", "mustKeepTab": "Deve rimanere almeno una tab.", "resetFailed": "Non sono riuscito a cancellare la configurazione.", "cacheCleared": "Cache delle notizie svuotata.", "tabUnavailable": "Tab non disponibile", "saveTabFailed": "Non sono riuscito a salvare la tab.", "deleteTabFailed": "Non sono riuscito a eliminare la tab.", "sourcesAvailable": "{n} fonti disponibili", "noSourcesAvailable": "Nessuna fonte disponibile", "selected": "Selezionata", "catAll": "Tutte", "catPolitics": "Politica", "catEconomy": "Economia", "catSports": "Sport", "catGames": "Videogiochi", "catMusic": "Musica", "catCinema": "Cinema e Serie", "catFashion": "Moda", "catScience": "Scienza", "catHealth": "Salute", "catComics": "Fumetti", "catTech": "Tecnologia", "catArt": "Arte", "catTravel": "Viaggi", "catFood": "Cucina", "feedErrorsSummary": "{n} fonti non hanno risposto. Le altre notizie sono state caricate normalmente.", "backendUnavailable": "Il backend di News non risponde.", "enterSourceAddress": "Inserisci l'indirizzo del sito o del feed.", "unusableSource": "Non sono riuscito a creare una fonte utilizzabile per questo indirizzo.", "articleUrlMissing": "URL articolo mancante.", "invalidConfiguration": "Configurazione non valida.", "sourceUnreachable": "Impossibile raggiungere la fonte" }, "en": { "openKiosk": "Open newsstand", "settings": "Settings", "settingsDetail": "Sources, tabs and newsstand refresh settings", "refresh": "Refresh", "back": "Back", "cancel": "Cancel", "close": "Close", "retry": "Retry", "continue": "Continue", "add": "Add", "remove": "Remove", "enable": "Enable", "disable": "Disable", "delete": "Delete", "save": "Save", "saving": "Saving…", "search": "Search online", "findFeed": "Find feed", "readSite": "Read on website", "loading": "Loading…", "updating": "Refreshing…", "play": "Play", "pause": "Pause", "now": "now", "yesterday": "yesterday", "minutesAgo": "{n} min ago", "hoursAgo": "{n} hr ago", "daysAgo": "{n} days ago", "video": "Video", "minutesUnit": "min", "personalKiosk": "Your personal newsstand", "personalKioskDetail": "Choose countries, sources and categories. News organizes everything for quick reading and the full newsstand.", "configure": "Set up News", "noNews": "No news", "noNewsDetail": "Check your sources or refresh the feed.", "noActiveTab": "No active tabs", "emptyPage": "This page is still empty", "prepareKiosk": "Preparing the newsstand…", "prepareOnboarding": "Preparing…", "articleLoading": "Loading article…", "readerPartial": "This source only makes part of the content available in Reader mode. You can continue with “Read on website”.", "readerUnavailable": "I could not extract a readable article body from this page. The cover and available details remain visible; you can continue with “Read on website”.", "setup": "Setup", "startTitle": "Where would you like to start?", "startDetail": "Choose your main country. You can add sources and news from any other country later without changing this preference.", "primaryCountry": "Main country", "chooseSources": "Choose your sources", "chooseSourcesDetail": "Choose a country, search for a publisher or add a website/feed. You can freely mix sources from different countries in the same newsstand.", "sourceCountry": "Source country", "sourceName": "Source name", "addSiteFeed": "Add a website or feed", "sourcesWorldwide": "Suggested sources worldwide", "sourcesWorldwideDetail": "A quick selection of useful publishers for building an international newsstand.", "addOtherCountries": "Would you like to add sources from other countries?", "addOtherCountriesDetail": "Your current selections stay saved. Choose another country above to keep building an international newsstand.", "buildKiosk": "Build your newsstand", "buildKioskDetail": "Choose the sections shown at the top. News stories are categorized article by article.", "customTab": "Custom tab", "tabName": "Tab name", "readyTitle": "Your newsstand is ready", "readyDetail": "This is the initial setup. You can add, remove and reorder sources and tabs later in Settings.", "enterKiosk": "Enter newsstand", "sources": "Sources", "country": "Country", "tabs": "Tabs", "tabsHeading": "Newsstand tabs", "newTab": "New tab", "createTab": "Create tab", "addSourcesAny": "Add sources from any country", "countryHeadlines": "Top news from this country", "updateHeading": "Refresh", "cacheInterval": "Cache interval", "clearCache": "Clear cache", "repeatSetup": "Run setup again", "resetHeading": "Reset", "resetAll": "Delete everything and start over", "resetDetail": "Deletes News sources, tabs and cache, then opens the initial setup again.", "includedSources": "Included sources", "tabVisibility": "Tab visibility", "tabVisibilityDetail": "Hide it without deleting its configuration.", "edit": "Edit", "editTab": "EDIT TAB", "name": "Name", "activateTab": "Enable tab", "deactivateTab": "Disable tab", "deleteTab": "Delete tab", "active": "Active", "inactive": "Disabled", "availableSourcesFor": "{n} sources available for {country}", "noPreconfiguredSources": "No preconfigured sources for {country}: use online search or add the country’s top news.", "selectedSourcesSummary": "{sources} sources selected from {countries} countries", "onlineSearchMinChars": "Enter at least two characters to search sources online.", "onlineSourcesAdded": "{n} online sources added to the results.", "onlineSourcesFound": "{n} sources found online.", "noMoreSources": "No additional sources found online.", "onlineSearchUnavailable": "Online search is unavailable.", "sourceAdded": "{name} added.", "sourceNotFound": "Source not found.", "countryHeadlinesFailed": "Could not add the country’s top news.", "selectAtLeastOneSource": "Select at least one source.", "saveConfigFailed": "Could not save the configuration.", "alreadyPresent": "{name} is already added.", "mustKeepActiveTab": "At least one tab must remain enabled.", "mustKeepTab": "At least one tab must remain.", "resetFailed": "Could not reset the configuration.", "cacheCleared": "News cache cleared.", "tabUnavailable": "Tab unavailable", "saveTabFailed": "Could not save the tab.", "deleteTabFailed": "Could not delete the tab.", "sourcesAvailable": "{n} sources available", "noSourcesAvailable": "No sources available", "selected": "Selected", "catAll": "All", "catPolitics": "Politics", "catEconomy": "Economy", "catSports": "Sports", "catGames": "Gaming", "catMusic": "Music", "catCinema": "Movies & Series", "catFashion": "Fashion", "catScience": "Science", "catHealth": "Health", "catComics": "Comics", "catTech": "Technology", "catArt": "Art", "catTravel": "Travel", "catFood": "Food", "feedErrorsSummary": "{n} sources did not respond. The other news stories loaded normally.", "backendUnavailable": "The News backend is not responding.", "enterSourceAddress": "Enter the website or feed address.", "unusableSource": "Could not create a usable source from this address.", "articleUrlMissing": "Article URL is missing.", "invalidConfiguration": "Invalid configuration.", "sourceUnreachable": "Could not reach the source" }, "es": { "openKiosk": "Abrir el quiosco", "settings": "Ajustes", "settingsDetail": "Fuentes, pestañas y actualización del quiosco", "refresh": "Actualizar", "back": "Atrás", "cancel": "Cancelar", "close": "Cerrar", "retry": "Reintentar", "continue": "Continuar", "add": "Añadir", "remove": "Eliminar", "enable": "Activar", "disable": "Desactivar", "delete": "Eliminar", "save": "Guardar", "saving": "Guardando…", "search": "Buscar en línea", "findFeed": "Buscar feed", "readSite": "Leer en el sitio", "loading": "Cargando…", "updating": "Actualizando…", "play": "Reproducir", "pause": "Pausa", "now": "ahora", "yesterday": "ayer", "minutesAgo": "hace {n} min", "hoursAgo": "hace {n} h", "daysAgo": "hace {n} días", "video": "Vídeo", "minutesUnit": "min", "personalKiosk": "Tu quiosco personal", "personalKioskDetail": "Elige países, fuentes y categorías. News lo organiza todo para una lectura rápida y para el quiosco.", "configure": "Configurar News", "noNews": "Sin noticias", "noNewsDetail": "Comprueba las fuentes o actualiza el feed.", "noActiveTab": "No hay pestañas activas", "emptyPage": "Esta página todavía está vacía", "prepareKiosk": "Preparando el quiosco…", "prepareOnboarding": "Preparando…", "articleLoading": "Cargando el artículo…", "readerPartial": "Esta fuente solo ofrece parte del contenido en el modo de lectura. Puedes continuar con “Leer en el sitio”.", "readerUnavailable": "No he podido extraer un cuerpo de artículo legible de esta página. La portada y los datos disponibles siguen visibles; puedes continuar con “Leer en el sitio”.", "setup": "Configuración", "startTitle": "¿Por dónde quieres empezar?", "startDetail": "Elige tu país principal. Más adelante podrás añadir fuentes y noticias de cualquier otro país sin cambiar esta preferencia.", "primaryCountry": "País principal", "chooseSources": "Elige tus fuentes", "chooseSourcesDetail": "Elige un país, busca un medio o añade un sitio/feed. Puedes mezclar libremente fuentes de distintos países en el mismo quiosco.", "sourceCountry": "País de las fuentes", "sourceName": "Nombre de la fuente", "addSiteFeed": "Añadir un sitio o feed", "sourcesWorldwide": "Fuentes sugeridas del mundo", "sourcesWorldwideDetail": "Una selección rápida de medios útiles para crear un quiosco internacional.", "addOtherCountries": "¿Quieres añadir fuentes de otros países?", "addOtherCountriesDetail": "Las fuentes ya seleccionadas permanecen guardadas. Elige otro país arriba para seguir creando un quiosco internacional.", "buildKiosk": "Construye tu quiosco", "buildKioskDetail": "Elige las secciones que aparecerán arriba. Las noticias se categorizan artículo por artículo.", "customTab": "Pestaña personalizada", "tabName": "Nombre de la pestaña", "readyTitle": "Tu quiosco está listo", "readyDetail": "Esta es la configuración inicial. Después podrás añadir, eliminar y reordenar fuentes y pestañas desde Ajustes.", "enterKiosk": "Entrar al quiosco", "sources": "Fuentes", "country": "País", "tabs": "Pestañas", "tabsHeading": "Pestañas del quiosco", "newTab": "Nueva pestaña", "createTab": "Crear pestaña", "addSourcesAny": "Añadir fuentes de cualquier país", "countryHeadlines": "Noticias principales del país", "updateHeading": "Actualización", "cacheInterval": "Intervalo de caché", "clearCache": "Vaciar caché", "repeatSetup": "Repetir configuración inicial", "resetHeading": "Restablecer", "resetAll": "Borrar todo y empezar de nuevo", "resetDetail": "Elimina fuentes, pestañas y caché de News y vuelve a abrir la configuración inicial.", "includedSources": "Fuentes incluidas", "tabVisibility": "Visibilidad de la pestaña", "tabVisibilityDetail": "Puedes ocultarla sin eliminar su configuración.", "edit": "Editar", "editTab": "EDITAR PESTAÑA", "name": "Nombre", "activateTab": "Activar pestaña", "deactivateTab": "Desactivar pestaña", "deleteTab": "Eliminar pestaña", "active": "Activa", "inactive": "Desactivada", "availableSourcesFor": "{n} fuentes disponibles para {country}", "noPreconfiguredSources": "No hay fuentes preconfiguradas para {country}: usa la búsqueda en línea o añade las noticias principales del país.", "selectedSourcesSummary": "{sources} fuentes seleccionadas de {countries} países", "onlineSearchMinChars": "Escribe al menos dos caracteres para buscar fuentes en línea.", "onlineSourcesAdded": "{n} fuentes en línea añadidas a los resultados.", "onlineSourcesFound": "{n} fuentes encontradas en línea.", "noMoreSources": "No se encontraron más fuentes en línea.", "onlineSearchUnavailable": "La búsqueda en línea no está disponible.", "sourceAdded": "{name} añadida.", "sourceNotFound": "Fuente no encontrada.", "countryHeadlinesFailed": "No se pudieron añadir las noticias principales del país.", "selectAtLeastOneSource": "Selecciona al menos una fuente.", "saveConfigFailed": "No se pudo guardar la configuración.", "alreadyPresent": "{name} ya está añadida.", "mustKeepActiveTab": "Debe quedar al menos una pestaña activa.", "mustKeepTab": "Debe quedar al menos una pestaña.", "resetFailed": "No se pudo borrar la configuración.", "cacheCleared": "Caché de noticias vaciada.", "tabUnavailable": "Pestaña no disponible", "saveTabFailed": "No se pudo guardar la pestaña.", "deleteTabFailed": "No se pudo eliminar la pestaña.", "sourcesAvailable": "{n} fuentes disponibles", "noSourcesAvailable": "No hay fuentes disponibles", "selected": "Seleccionada", "catAll": "Todas", "catPolitics": "Política", "catEconomy": "Economía", "catSports": "Deportes", "catGames": "Videojuegos", "catMusic": "Música", "catCinema": "Cine y Series", "catFashion": "Moda", "catScience": "Ciencia", "catHealth": "Salud", "catComics": "Cómics", "catTech": "Tecnología", "catArt": "Arte", "catTravel": "Viajes", "catFood": "Cocina", "feedErrorsSummary": "{n} fuentes no respondieron. Las demás noticias se cargaron normalmente.", "backendUnavailable": "El backend de News no responde.", "enterSourceAddress": "Introduce la dirección del sitio o del feed.", "unusableSource": "No se pudo crear una fuente utilizable a partir de esta dirección.", "articleUrlMissing": "Falta la URL del artículo.", "invalidConfiguration": "Configuración no válida.", "sourceUnreachable": "No se pudo acceder a la fuente" }, "fr": { "openKiosk": "Ouvrir le kiosque", "settings": "Paramètres", "settingsDetail": "Sources, onglets et actualisation du kiosque", "refresh": "Actualiser", "back": "Retour", "cancel": "Annuler", "close": "Fermer", "retry": "Réessayer", "continue": "Continuer", "add": "Ajouter", "remove": "Supprimer", "enable": "Activer", "disable": "Désactiver", "delete": "Supprimer", "save": "Enregistrer", "saving": "Enregistrement…", "search": "Rechercher en ligne", "findFeed": "Trouver le flux", "readSite": "Lire sur le site", "loading": "Chargement…", "updating": "Actualisation…", "play": "Lecture", "pause": "Pause", "now": "à l’instant", "yesterday": "hier", "minutesAgo": "il y a {n} min", "hoursAgo": "il y a {n} h", "daysAgo": "il y a {n} jours", "video": "Vidéo", "minutesUnit": "min", "personalKiosk": "Votre kiosque personnel", "personalKioskDetail": "Choisissez des pays, des sources et des catégories. News organise tout pour une lecture rapide et pour le kiosque.", "configure": "Configurer News", "noNews": "Aucune actualité", "noNewsDetail": "Vérifiez les sources ou actualisez le flux.", "noActiveTab": "Aucun onglet actif", "emptyPage": "Cette page est encore vide", "prepareKiosk": "Préparation du kiosque…", "prepareOnboarding": "Préparation…", "articleLoading": "Chargement de l’article…", "readerPartial": "Cette source ne fournit qu’une partie du contenu en mode lecture. Vous pouvez continuer avec « Lire sur le site ».", "readerUnavailable": "Impossible d’extraire un corps d’article lisible de cette page. La couverture et les informations disponibles restent visibles ; vous pouvez continuer avec « Lire sur le site ».", "setup": "Configuration", "startTitle": "Par où voulez-vous commencer ?", "startDetail": "Choisissez votre pays principal. Vous pourrez ensuite ajouter des sources et des actualités de n’importe quel autre pays sans modifier cette préférence.", "primaryCountry": "Pays principal", "chooseSources": "Choisissez vos sources", "chooseSourcesDetail": "Choisissez un pays, recherchez un média ou ajoutez un site/flux. Vous pouvez mélanger librement des sources de différents pays dans le même kiosque.", "sourceCountry": "Pays des sources", "sourceName": "Nom de la source", "addSiteFeed": "Ajouter un site ou un flux", "sourcesWorldwide": "Sources suggérées dans le monde", "sourcesWorldwideDetail": "Une sélection rapide de médias utiles pour créer un kiosque international.", "addOtherCountries": "Voulez-vous ajouter des sources d’autres pays ?", "addOtherCountriesDetail": "Les sources déjà sélectionnées restent enregistrées. Choisissez un autre pays ci-dessus pour continuer à créer un kiosque international.", "buildKiosk": "Construisez votre kiosque", "buildKioskDetail": "Choisissez les sections à afficher en haut. Les actualités sont classées article par article.", "customTab": "Onglet personnalisé", "tabName": "Nom de l’onglet", "readyTitle": "Votre kiosque est prêt", "readyDetail": "Il s’agit de la configuration initiale. Vous pourrez ensuite ajouter, supprimer et réorganiser les sources et les onglets dans les Paramètres.", "enterKiosk": "Entrer dans le kiosque", "sources": "Sources", "country": "Pays", "tabs": "Onglets", "tabsHeading": "Onglets du kiosque", "newTab": "Nouvel onglet", "createTab": "Créer un onglet", "addSourcesAny": "Ajouter des sources de n’importe quel pays", "countryHeadlines": "Principales actualités du pays", "updateHeading": "Actualisation", "cacheInterval": "Intervalle du cache", "clearCache": "Vider le cache", "repeatSetup": "Relancer la configuration initiale", "resetHeading": "Réinitialisation", "resetAll": "Tout supprimer et recommencer", "resetDetail": "Supprime les sources, les onglets et le cache de News, puis rouvre la configuration initiale.", "includedSources": "Sources incluses", "tabVisibility": "Visibilité de l’onglet", "tabVisibilityDetail": "Vous pouvez le masquer sans supprimer sa configuration.", "edit": "Modifier", "editTab": "MODIFIER L’ONGLET", "name": "Nom", "activateTab": "Activer l’onglet", "deactivateTab": "Désactiver l’onglet", "deleteTab": "Supprimer l’onglet", "active": "Active", "inactive": "Désactivée", "availableSourcesFor": "{n} sources disponibles pour {country}", "noPreconfiguredSources": "Aucune source préconfigurée pour {country} : utilisez la recherche en ligne ou ajoutez les principales actualités du pays.", "selectedSourcesSummary": "{sources} sources sélectionnées dans {countries} pays", "onlineSearchMinChars": "Saisissez au moins deux caractères pour rechercher des sources en ligne.", "onlineSourcesAdded": "{n} sources en ligne ajoutées aux résultats.", "onlineSourcesFound": "{n} sources trouvées en ligne.", "noMoreSources": "Aucune autre source trouvée en ligne.", "onlineSearchUnavailable": "La recherche en ligne n’est pas disponible.", "sourceAdded": "{name} ajoutée.", "sourceNotFound": "Source introuvable.", "countryHeadlinesFailed": "Impossible d’ajouter les principales actualités du pays.", "selectAtLeastOneSource": "Sélectionnez au moins une source.", "saveConfigFailed": "Impossible d’enregistrer la configuration.", "alreadyPresent": "{name} est déjà ajoutée.", "mustKeepActiveTab": "Au moins un onglet doit rester actif.", "mustKeepTab": "Au moins un onglet doit rester.", "resetFailed": "Impossible de réinitialiser la configuration.", "cacheCleared": "Cache des actualités vidé.", "tabUnavailable": "Onglet indisponible", "saveTabFailed": "Impossible d’enregistrer l’onglet.", "deleteTabFailed": "Impossible de supprimer l’onglet.", "sourcesAvailable": "{n} sources disponibles", "noSourcesAvailable": "Aucune source disponible", "selected": "Sélectionnée", "catAll": "Toutes", "catPolitics": "Politique", "catEconomy": "Économie", "catSports": "Sport", "catGames": "Jeux vidéo", "catMusic": "Musique", "catCinema": "Cinéma et Séries", "catFashion": "Mode", "catScience": "Science", "catHealth": "Santé", "catComics": "BD", "catTech": "Technologie", "catArt": "Art", "catTravel": "Voyages", "catFood": "Cuisine", "feedErrorsSummary": "{n} sources n’ont pas répondu. Les autres actualités ont été chargées normalement.", "backendUnavailable": "Le service News ne répond pas.", "enterSourceAddress": "Saisissez l’adresse du site ou du flux.", "unusableSource": "Impossible de créer une source utilisable à partir de cette adresse.", "articleUrlMissing": "URL de l’article manquante.", "invalidConfiguration": "Configuration invalide.", "sourceUnreachable": "Impossible de joindre la source" }, "de": { "openKiosk": "Kiosk öffnen", "settings": "Einstellungen", "settingsDetail": "Quellen, Tabs und Aktualisierung des Kiosks", "refresh": "Aktualisieren", "back": "Zurück", "cancel": "Abbrechen", "close": "Schließen", "retry": "Erneut versuchen", "continue": "Weiter", "add": "Hinzufügen", "remove": "Entfernen", "enable": "Aktivieren", "disable": "Deaktivieren", "delete": "Löschen", "save": "Speichern", "saving": "Speichern…", "search": "Online suchen", "findFeed": "Feed finden", "readSite": "Auf Website lesen", "loading": "Laden…", "updating": "Aktualisieren…", "play": "Wiedergabe", "pause": "Pause", "now": "gerade eben", "yesterday": "gestern", "minutesAgo": "vor {n} Min.", "hoursAgo": "vor {n} Std.", "daysAgo": "vor {n} Tagen", "video": "Video", "minutesUnit": "Min.", "personalKiosk": "Dein persönlicher Kiosk", "personalKioskDetail": "Wähle Länder, Quellen und Kategorien. News organisiert alles für schnelles Lesen und den Kiosk.", "configure": "News einrichten", "noNews": "Keine Nachrichten", "noNewsDetail": "Prüfe die Quellen oder aktualisiere den Feed.", "noActiveTab": "Keine aktiven Tabs", "emptyPage": "Diese Seite ist noch leer", "prepareKiosk": "Kiosk wird vorbereitet…", "prepareOnboarding": "Vorbereitung…", "articleLoading": "Artikel wird geladen…", "readerPartial": "Diese Quelle stellt im Lesemodus nur einen Teil des Inhalts bereit. Du kannst mit „Auf Website lesen“ fortfahren.", "readerUnavailable": "Aus dieser Seite konnte kein lesbarer Artikeltext extrahiert werden. Titelbild und verfügbare Angaben bleiben sichtbar; du kannst mit „Auf Website lesen“ fortfahren.", "setup": "Einrichtung", "startTitle": "Wo möchtest du anfangen?", "startDetail": "Wähle dein Hauptland. Später kannst du Quellen und Nachrichten aus jedem anderen Land hinzufügen, ohne diese Einstellung zu ändern.", "primaryCountry": "Hauptland", "chooseSources": "Wähle deine Quellen", "chooseSourcesDetail": "Wähle ein Land, suche nach einem Medium oder füge eine Website/einen Feed hinzu. Quellen aus verschiedenen Ländern lassen sich frei im selben Kiosk mischen.", "sourceCountry": "Land der Quellen", "sourceName": "Name der Quelle", "addSiteFeed": "Website oder Feed hinzufügen", "sourcesWorldwide": "Empfohlene Quellen weltweit", "sourcesWorldwideDetail": "Eine schnelle Auswahl nützlicher Medien für einen internationalen Kiosk.", "addOtherCountries": "Möchtest du Quellen aus weiteren Ländern hinzufügen?", "addOtherCountriesDetail": "Deine bisherigen Quellen bleiben gespeichert. Wähle oben ein anderes Land, um den internationalen Kiosk weiter aufzubauen.", "buildKiosk": "Kiosk zusammenstellen", "buildKioskDetail": "Wähle die Bereiche, die oben angezeigt werden. Nachrichten werden Artikel für Artikel kategorisiert.", "customTab": "Benutzerdefinierter Tab", "tabName": "Tab-Name", "readyTitle": "Dein Kiosk ist bereit", "readyDetail": "Das ist die Ersteinrichtung. Quellen und Tabs kannst du später in den Einstellungen hinzufügen, entfernen und neu anordnen.", "enterKiosk": "Kiosk öffnen", "sources": "Quellen", "country": "Land", "tabs": "Tabs", "tabsHeading": "Kiosk-Tabs", "newTab": "Neuer Tab", "createTab": "Tab erstellen", "addSourcesAny": "Quellen aus jedem Land hinzufügen", "countryHeadlines": "Top-Nachrichten des Landes", "updateHeading": "Aktualisierung", "cacheInterval": "Cache-Intervall", "clearCache": "Cache leeren", "repeatSetup": "Ersteinrichtung wiederholen", "resetHeading": "Zurücksetzen", "resetAll": "Alles löschen und neu beginnen", "resetDetail": "Löscht Quellen, Tabs und Cache von News und öffnet die Ersteinrichtung erneut.", "includedSources": "Enthaltene Quellen", "tabVisibility": "Sichtbarkeit des Tabs", "tabVisibilityDetail": "Du kannst ihn ausblenden, ohne seine Konfiguration zu löschen.", "edit": "Bearbeiten", "editTab": "TAB BEARBEITEN", "name": "Name", "activateTab": "Tab aktivieren", "deactivateTab": "Tab deaktivieren", "deleteTab": "Tab löschen", "active": "Aktiv", "inactive": "Deaktiviert", "availableSourcesFor": "{n} Quellen für {country} verfügbar", "noPreconfiguredSources": "Keine vorkonfigurierten Quellen für {country}: Nutze die Online-Suche oder füge die Top-Nachrichten des Landes hinzu.", "selectedSourcesSummary": "{sources} Quellen aus {countries} Ländern ausgewählt", "onlineSearchMinChars": "Gib mindestens zwei Zeichen ein, um online nach Quellen zu suchen.", "onlineSourcesAdded": "{n} Online-Quellen zu den Ergebnissen hinzugefügt.", "onlineSourcesFound": "{n} Quellen online gefunden.", "noMoreSources": "Keine weiteren Online-Quellen gefunden.", "onlineSearchUnavailable": "Online-Suche nicht verfügbar.", "sourceAdded": "{name} hinzugefügt.", "sourceNotFound": "Quelle nicht gefunden.", "countryHeadlinesFailed": "Top-Nachrichten des Landes konnten nicht hinzugefügt werden.", "selectAtLeastOneSource": "Wähle mindestens eine Quelle aus.", "saveConfigFailed": "Konfiguration konnte nicht gespeichert werden.", "alreadyPresent": "{name} ist bereits vorhanden.", "mustKeepActiveTab": "Mindestens ein Tab muss aktiv bleiben.", "mustKeepTab": "Mindestens ein Tab muss erhalten bleiben.", "resetFailed": "Konfiguration konnte nicht zurückgesetzt werden.", "cacheCleared": "News-Cache geleert.", "tabUnavailable": "Tab nicht verfügbar", "saveTabFailed": "Tab konnte nicht gespeichert werden.", "deleteTabFailed": "Tab konnte nicht gelöscht werden.", "sourcesAvailable": "{n} Quellen verfügbar", "noSourcesAvailable": "Keine Quellen verfügbar", "selected": "Ausgewählt", "catAll": "Alle", "catPolitics": "Politik", "catEconomy": "Wirtschaft", "catSports": "Sport", "catGames": "Videospiele", "catMusic": "Musik", "catCinema": "Filme und Serien", "catFashion": "Mode", "catScience": "Wissenschaft", "catHealth": "Gesundheit", "catComics": "Comics", "catTech": "Technologie", "catArt": "Kunst", "catTravel": "Reisen", "catFood": "Essen", "feedErrorsSummary": "{n} Quellen haben nicht geantwortet. Die übrigen Nachrichten wurden normal geladen.", "backendUnavailable": "Das News-Backend antwortet nicht.", "enterSourceAddress": "Gib die Adresse der Website oder des Feeds ein.", "unusableSource": "Aus dieser Adresse konnte keine verwendbare Quelle erstellt werden.", "articleUrlMissing": "Artikel-URL fehlt.", "invalidConfiguration": "Ungültige Konfiguration.", "sourceUnreachable": "Quelle konnte nicht erreicht werden" }, "pt-br": { "openKiosk": "Abrir banca", "settings": "Configurações", "settingsDetail": "Fontes, abas e atualização da banca", "refresh": "Atualizar", "back": "Voltar", "cancel": "Cancelar", "close": "Fechar", "retry": "Tentar novamente", "continue": "Continuar", "add": "Adicionar", "remove": "Remover", "enable": "Ativar", "disable": "Desativar", "delete": "Excluir", "save": "Salvar", "saving": "Salvando…", "search": "Pesquisar online", "findFeed": "Encontrar feed", "readSite": "Ler no site", "loading": "Carregando…", "updating": "Atualizando…", "play": "Reproduzir", "pause": "Pausar", "now": "agora", "yesterday": "ontem", "minutesAgo": "há {n} min", "hoursAgo": "há {n} h", "daysAgo": "há {n} dias", "video": "Vídeo", "minutesUnit": "min", "personalKiosk": "Sua banca pessoal", "personalKioskDetail": "Escolha países, fontes e categorias. O News organiza tudo para leitura rápida e para a banca.", "configure": "Configurar News", "noNews": "Nenhuma notícia", "noNewsDetail": "Verifique as fontes ou atualize o feed.", "noActiveTab": "Nenhuma aba ativa", "emptyPage": "Esta página ainda está vazia", "prepareKiosk": "Preparando a banca…", "prepareOnboarding": "Preparando…", "articleLoading": "Carregando artigo…", "readerPartial": "Esta fonte disponibiliza apenas parte do conteúdo no modo de leitura. Você pode continuar em “Ler no site”.", "readerUnavailable": "Não foi possível extrair um corpo de artigo legível desta página. A capa e os dados disponíveis continuam visíveis; você pode continuar em “Ler no site”.", "setup": "Configuração", "startTitle": "Por onde você quer começar?", "startDetail": "Escolha seu país principal. Depois você poderá adicionar fontes e notícias de qualquer outro país sem alterar esta preferência.", "primaryCountry": "País principal", "chooseSources": "Escolha suas fontes", "chooseSourcesDetail": "Escolha um país, pesquise um veículo ou adicione um site/feed. Você pode misturar livremente fontes de países diferentes na mesma banca.", "sourceCountry": "País das fontes", "sourceName": "Nome da fonte", "addSiteFeed": "Adicionar site ou feed", "sourcesWorldwide": "Fontes sugeridas do mundo", "sourcesWorldwideDetail": "Uma seleção rápida de veículos úteis para montar uma banca internacional.", "addOtherCountries": "Quer adicionar fontes de outros países?", "addOtherCountriesDetail": "As fontes já selecionadas permanecem salvas. Escolha outro país acima para continuar montando uma banca internacional.", "buildKiosk": "Monte sua banca", "buildKioskDetail": "Escolha as seções que aparecem no topo. As notícias são categorizadas artigo por artigo.", "customTab": "Aba personalizada", "tabName": "Nome da aba", "readyTitle": "Sua banca está pronta", "readyDetail": "Esta é a configuração inicial. Depois você poderá adicionar, remover e reordenar fontes e abas nas Configurações.", "enterKiosk": "Entrar na banca", "sources": "Fontes", "country": "País", "tabs": "Abas", "tabsHeading": "Abas da banca", "newTab": "Nova aba", "createTab": "Criar aba", "addSourcesAny": "Adicionar fontes de qualquer país", "countryHeadlines": "Principais notícias do país", "updateHeading": "Atualização", "cacheInterval": "Intervalo do cache", "clearCache": "Limpar cache", "repeatSetup": "Refazer configuração inicial", "resetHeading": "Redefinir", "resetAll": "Apagar tudo e começar de novo", "resetDetail": "Exclui fontes, abas e cache do News e abre novamente a configuração inicial.", "includedSources": "Fontes incluídas", "tabVisibility": "Visibilidade da aba", "tabVisibilityDetail": "Você pode ocultá-la sem excluir a configuração.", "edit": "Editar", "editTab": "EDITAR ABA", "name": "Nome", "activateTab": "Ativar aba", "deactivateTab": "Desativar aba", "deleteTab": "Excluir aba", "active": "Ativa", "inactive": "Desativada", "availableSourcesFor": "{n} fontes disponíveis para {country}", "noPreconfiguredSources": "Nenhuma fonte pré-configurada para {country}: use a pesquisa online ou adicione as principais notícias do país.", "selectedSourcesSummary": "{sources} fontes selecionadas de {countries} países", "onlineSearchMinChars": "Digite pelo menos dois caracteres para pesquisar fontes online.", "onlineSourcesAdded": "{n} fontes online adicionadas aos resultados.", "onlineSourcesFound": "{n} fontes encontradas online.", "noMoreSources": "Nenhuma outra fonte encontrada online.", "onlineSearchUnavailable": "Pesquisa online indisponível.", "sourceAdded": "{name} adicionada.", "sourceNotFound": "Fonte não encontrada.", "countryHeadlinesFailed": "Não foi possível adicionar as principais notícias do país.", "selectAtLeastOneSource": "Selecione pelo menos uma fonte.", "saveConfigFailed": "Não foi possível salvar a configuração.", "alreadyPresent": "{name} já está presente.", "mustKeepActiveTab": "Pelo menos uma aba deve permanecer ativa.", "mustKeepTab": "Pelo menos uma aba deve permanecer.", "resetFailed": "Não foi possível redefinir a configuração.", "cacheCleared": "Cache de notícias limpo.", "tabUnavailable": "Aba indisponível", "saveTabFailed": "Não foi possível salvar a aba.", "deleteTabFailed": "Não foi possível excluir a aba.", "sourcesAvailable": "{n} fontes disponíveis", "noSourcesAvailable": "Nenhuma fonte disponível", "selected": "Selecionada", "catAll": "Todas", "catPolitics": "Política", "catEconomy": "Economia", "catSports": "Esportes", "catGames": "Jogos", "catMusic": "Música", "catCinema": "Filmes e Séries", "catFashion": "Moda", "catScience": "Ciência", "catHealth": "Saúde", "catComics": "Quadrinhos", "catTech": "Tecnologia", "catArt": "Arte", "catTravel": "Viagens", "catFood": "Culinária", "feedErrorsSummary": "{n} fontes não responderam. As outras notícias foram carregadas normalmente.", "backendUnavailable": "O backend do News não está respondendo.", "enterSourceAddress": "Digite o endereço do site ou feed.", "unusableSource": "Não foi possível criar uma fonte utilizável a partir deste endereço.", "articleUrlMissing": "A URL do artigo está ausente.", "invalidConfiguration": "Configuração inválida.", "sourceUnreachable": "Não foi possível acessar a fonte" }, "ru": { "openKiosk": "Открыть киоск", "settings": "Настройки", "settingsDetail": "Источники, вкладки и обновление киоска", "refresh": "Обновить", "back": "Назад", "cancel": "Отмена", "close": "Закрыть", "retry": "Повторить", "continue": "Продолжить", "add": "Добавить", "remove": "Удалить", "enable": "Включить", "disable": "Отключить", "delete": "Удалить", "save": "Сохранить", "saving": "Сохранение…", "search": "Искать онлайн", "findFeed": "Найти ленту", "readSite": "Читать на сайте", "loading": "Загрузка…", "updating": "Обновление…", "play": "Воспроизвести", "pause": "Пауза", "now": "сейчас", "yesterday": "вчера", "minutesAgo": "{n} мин назад", "hoursAgo": "{n} ч назад", "daysAgo": "{n} дн. назад", "video": "Видео", "minutesUnit": "мин", "personalKiosk": "Ваш персональный киоск", "personalKioskDetail": "Выберите страны, источники и категории. News организует всё для быстрого чтения и полноэкранного киоска.", "configure": "Настроить News", "noNews": "Нет новостей", "noNewsDetail": "Проверьте источники или обновите ленту.", "noActiveTab": "Нет активных вкладок", "emptyPage": "Эта страница пока пуста", "prepareKiosk": "Подготовка киоска…", "prepareOnboarding": "Подготовка…", "articleLoading": "Загрузка статьи…", "readerPartial": "Этот источник предоставляет в режиме чтения только часть материала. Можно продолжить через «Читать на сайте».", "readerUnavailable": "Не удалось извлечь читаемый текст статьи с этой страницы. Обложка и доступные данные остаются видимыми; можно продолжить через «Читать на сайте».", "setup": "Настройка", "startTitle": "С чего начать?", "startDetail": "Выберите основную страну. Позже можно добавлять источники и новости из любых других стран, не меняя эту настройку.", "primaryCountry": "Основная страна", "chooseSources": "Выберите источники", "chooseSourcesDetail": "Выберите страну, найдите издание или добавьте сайт/ленту. Источники из разных стран можно свободно смешивать в одном киоске.", "sourceCountry": "Страна источников", "sourceName": "Название источника", "addSiteFeed": "Добавить сайт или ленту", "sourcesWorldwide": "Рекомендуемые источники мира", "sourcesWorldwideDetail": "Быстрая подборка полезных изданий для международного киоска.", "addOtherCountries": "Добавить источники из других стран?", "addOtherCountriesDetail": "Уже выбранные источники сохраняются. Выберите другую страну выше, чтобы продолжить собирать международный киоск.", "buildKiosk": "Соберите киоск", "buildKioskDetail": "Выберите разделы, которые будут показаны сверху. Новости классифицируются по каждой статье отдельно.", "customTab": "Своя вкладка", "tabName": "Название вкладки", "readyTitle": "Ваш киоск готов", "readyDetail": "Это начальная настройка. Позже источники и вкладки можно добавлять, удалять и переставлять в Настройках.", "enterKiosk": "Открыть киоск", "sources": "Источники", "country": "Страна", "tabs": "Вкладки", "tabsHeading": "Вкладки киоска", "newTab": "Новая вкладка", "createTab": "Создать вкладку", "addSourcesAny": "Добавить источники из любой страны", "countryHeadlines": "Главные новости страны", "updateHeading": "Обновление", "cacheInterval": "Интервал кэша", "clearCache": "Очистить кэш", "repeatSetup": "Повторить начальную настройку", "resetHeading": "Сброс", "resetAll": "Удалить всё и начать заново", "resetDetail": "Удаляет источники, вкладки и кэш News и снова открывает начальную настройку.", "includedSources": "Включённые источники", "tabVisibility": "Видимость вкладки", "tabVisibilityDetail": "Её можно скрыть, не удаляя настройки.", "edit": "Изменить", "editTab": "ИЗМЕНИТЬ ВКЛАДКУ", "name": "Название", "activateTab": "Включить вкладку", "deactivateTab": "Отключить вкладку", "deleteTab": "Удалить вкладку", "active": "Активен", "inactive": "Отключён", "availableSourcesFor": "{n} источников доступно для {country}", "noPreconfiguredSources": "Для {country} нет готовых источников: используйте онлайн-поиск или добавьте главные новости страны.", "selectedSourcesSummary": "Выбрано источников: {sources}; стран: {countries}", "onlineSearchMinChars": "Введите минимум два символа для поиска источников онлайн.", "onlineSourcesAdded": "Онлайн-источников добавлено в результаты: {n}.", "onlineSourcesFound": "Найдено онлайн-источников: {n}.", "noMoreSources": "Других онлайн-источников не найдено.", "onlineSearchUnavailable": "Онлайн-поиск недоступен.", "sourceAdded": "{name} добавлен.", "sourceNotFound": "Источник не найден.", "countryHeadlinesFailed": "Не удалось добавить главные новости страны.", "selectAtLeastOneSource": "Выберите хотя бы один источник.", "saveConfigFailed": "Не удалось сохранить настройки.", "alreadyPresent": "{name} уже добавлен.", "mustKeepActiveTab": "Хотя бы одна вкладка должна оставаться активной.", "mustKeepTab": "Должна остаться хотя бы одна вкладка.", "resetFailed": "Не удалось сбросить настройки.", "cacheCleared": "Кэш новостей очищен.", "tabUnavailable": "Вкладка недоступна", "saveTabFailed": "Не удалось сохранить вкладку.", "deleteTabFailed": "Не удалось удалить вкладку.", "sourcesAvailable": "Доступно источников: {n}", "noSourcesAvailable": "Нет доступных источников", "selected": "Выбрано", "catAll": "Все", "catPolitics": "Политика", "catEconomy": "Экономика", "catSports": "Спорт", "catGames": "Игры", "catMusic": "Музыка", "catCinema": "Кино и сериалы", "catFashion": "Мода", "catScience": "Наука", "catHealth": "Здоровье", "catComics": "Комиксы", "catTech": "Технологии", "catArt": "Искусство", "catTravel": "Путешествия", "catFood": "Еда", "feedErrorsSummary": "{n} источников не ответили. Остальные новости загрузились нормально.", "backendUnavailable": "Служба News не отвечает.", "enterSourceAddress": "Введите адрес сайта или ленты.", "unusableSource": "Не удалось создать рабочий источник по этому адресу.", "articleUrlMissing": "Отсутствует URL статьи.", "invalidConfiguration": "Недопустимая конфигурация.", "sourceUnreachable": "Не удалось связаться с источником" }, "ja": { "openKiosk": "ニューススタンドを開く", "settings": "設定", "settingsDetail": "ソース、タブ、ニューススタンドの更新設定", "refresh": "更新", "back": "戻る", "cancel": "キャンセル", "close": "閉じる", "retry": "再試行", "continue": "続行", "add": "追加", "remove": "削除", "enable": "有効化", "disable": "無効化", "delete": "削除", "save": "保存", "saving": "保存中…", "search": "オンライン検索", "findFeed": "フィードを検索", "readSite": "サイトで読む", "loading": "読み込み中…", "updating": "更新中…", "play": "再生", "pause": "一時停止", "now": "たった今", "yesterday": "昨日", "minutesAgo": "{n}分前", "hoursAgo": "{n}時間前", "daysAgo": "{n}日前", "video": "動画", "minutesUnit": "分", "personalKiosk": "あなたのニューススタンド", "personalKioskDetail": "国、ソース、カテゴリを選択すると、News がクイック閲覧とニューススタンド用に整理します。", "configure": "News を設定", "noNews": "ニュースがありません", "noNewsDetail": "ソースを確認するか、フィードを更新してください。", "noActiveTab": "有効なタブがありません", "emptyPage": "このページはまだ空です", "prepareKiosk": "ニューススタンドを準備中…", "prepareOnboarding": "準備中…", "articleLoading": "記事を読み込み中…", "readerPartial": "このソースではリーダーモードで記事の一部のみ利用できます。「サイトで読む」で続行できます。", "readerUnavailable": "このページから読みやすい記事本文を抽出できませんでした。カバー画像と利用可能な情報は表示されたままです。「サイトで読む」で続行できます。", "setup": "セットアップ", "startTitle": "どこから始めますか？", "startDetail": "メインの国を選択してください。後から設定を変えずに、他の国のソースやニュースを追加できます。", "primaryCountry": "メインの国", "chooseSources": "ソースを選択", "chooseSourcesDetail": "国を選び、媒体を検索するか、サイト/フィードを追加してください。異なる国のソースを同じニューススタンドで自由に組み合わせられます。", "sourceCountry": "ソースの国", "sourceName": "ソース名", "addSiteFeed": "サイトまたはフィードを追加", "sourcesWorldwide": "世界のおすすめソース", "sourcesWorldwideDetail": "国際的なニューススタンドを作るための便利な媒体をすばやく選べます。", "addOtherCountries": "他の国のソースも追加しますか？", "addOtherCountriesDetail": "選択済みのソースは保存されます。上で別の国を選ぶと、国際ニューススタンドを続けて作成できます。", "buildKiosk": "ニューススタンドを作成", "buildKioskDetail": "上部に表示するセクションを選択してください。ニュースは記事ごとに分類されます。", "customTab": "カスタムタブ", "tabName": "タブ名", "readyTitle": "ニューススタンドの準備ができました", "readyDetail": "これは初期設定です。後から設定でソースやタブを追加、削除、並べ替えできます。", "enterKiosk": "ニューススタンドへ", "sources": "ソース", "country": "国", "tabs": "タブ", "tabsHeading": "ニューススタンドのタブ", "newTab": "新しいタブ", "createTab": "タブを作成", "addSourcesAny": "任意の国からソースを追加", "countryHeadlines": "この国の主要ニュース", "updateHeading": "更新", "cacheInterval": "キャッシュ間隔", "clearCache": "キャッシュを消去", "repeatSetup": "初期設定をやり直す", "resetHeading": "リセット", "resetAll": "すべて削除して最初からやり直す", "resetDetail": "News のソース、タブ、キャッシュを削除し、初期設定を再度開きます。", "includedSources": "含まれるソース", "tabVisibility": "タブの表示", "tabVisibilityDetail": "設定を削除せずに非表示にできます。", "edit": "編集", "editTab": "タブを編集", "name": "名前", "activateTab": "タブを有効化", "deactivateTab": "タブを無効化", "deleteTab": "タブを削除", "active": "有効", "inactive": "無効", "availableSourcesFor": "{country}で利用可能なソース: {n}", "noPreconfiguredSources": "{country}には事前設定されたソースがありません。オンライン検索を使うか、その国の主要ニュースを追加してください。", "selectedSourcesSummary": "{countries}か国から{sources}件のソースを選択", "onlineSearchMinChars": "オンラインでソースを検索するには2文字以上入力してください。", "onlineSourcesAdded": "オンラインソースを結果に{n}件追加しました。", "onlineSourcesFound": "オンラインで{n}件のソースが見つかりました。", "noMoreSources": "他のオンラインソースは見つかりませんでした。", "onlineSearchUnavailable": "オンライン検索を利用できません。", "sourceAdded": "{name}を追加しました。", "sourceNotFound": "ソースが見つかりません。", "countryHeadlinesFailed": "その国の主要ニュースを追加できませんでした。", "selectAtLeastOneSource": "少なくとも1つのソースを選択してください。", "saveConfigFailed": "設定を保存できませんでした。", "alreadyPresent": "{name}はすでに追加されています。", "mustKeepActiveTab": "少なくとも1つのタブを有効にしておく必要があります。", "mustKeepTab": "少なくとも1つのタブを残す必要があります。", "resetFailed": "設定をリセットできませんでした。", "cacheCleared": "ニュースキャッシュを消去しました。", "tabUnavailable": "タブを利用できません", "saveTabFailed": "タブを保存できませんでした。", "deleteTabFailed": "タブを削除できませんでした。", "sourcesAvailable": "利用可能なソース: {n}", "noSourcesAvailable": "利用可能なソースはありません", "selected": "選択済み", "catAll": "すべて", "catPolitics": "政治", "catEconomy": "経済", "catSports": "スポーツ", "catGames": "ゲーム", "catMusic": "音楽", "catCinema": "映画・ドラマ", "catFashion": "ファッション", "catScience": "科学", "catHealth": "健康", "catComics": "コミック", "catTech": "テクノロジー", "catArt": "アート", "catTravel": "旅行", "catFood": "グルメ", "feedErrorsSummary": "{n}件のソースが応答しませんでした。その他のニュースは正常に読み込まれました。", "backendUnavailable": "News バックエンドが応答していません。", "enterSourceAddress": "サイトまたはフィードのアドレスを入力してください。", "unusableSource": "このアドレスから利用可能なソースを作成できませんでした。", "articleUrlMissing": "記事の URL がありません。", "invalidConfiguration": "設定が無効です。", "sourceUnreachable": "ソースに接続できませんでした" }, "zh": { "openKiosk": "打开报刊亭", "settings": "设置", "settingsDetail": "来源、标签页和报刊亭刷新设置", "refresh": "刷新", "back": "返回", "cancel": "取消", "close": "关闭", "retry": "重试", "continue": "继续", "add": "添加", "remove": "移除", "enable": "启用", "disable": "停用", "delete": "删除", "save": "保存", "saving": "正在保存…", "search": "在线搜索", "findFeed": "查找订阅源", "readSite": "在网站阅读", "loading": "加载中…", "updating": "刷新中…", "play": "播放", "pause": "暂停", "now": "刚刚", "yesterday": "昨天", "minutesAgo": "{n} 分钟前", "hoursAgo": "{n} 小时前", "daysAgo": "{n} 天前", "video": "视频", "minutesUnit": "分钟", "personalKiosk": "你的个人报刊亭", "personalKioskDetail": "选择国家、来源和分类。News 会整理内容，方便快速阅读和在报刊亭中浏览。", "configure": "设置 News", "noNews": "暂无新闻", "noNewsDetail": "请检查来源或刷新订阅源。", "noActiveTab": "没有启用的标签页", "emptyPage": "此页面暂时为空", "prepareKiosk": "正在准备报刊亭…", "prepareOnboarding": "正在准备…", "articleLoading": "正在加载文章…", "readerPartial": "此来源在阅读模式下只提供部分内容。你可以选择“在网站阅读”继续。", "readerUnavailable": "无法从此页面提取可读的文章正文。封面和现有信息仍会显示；你可以选择“在网站阅读”继续。", "setup": "设置", "startTitle": "你想从哪里开始？", "startDetail": "选择主要国家。之后无需更改此设置，也可以添加其他国家的来源和新闻。", "primaryCountry": "主要国家", "chooseSources": "选择来源", "chooseSourcesDetail": "选择国家、搜索媒体，或添加网站/订阅源。你可以在同一个报刊亭中自由混合不同国家的来源。", "sourceCountry": "来源国家", "sourceName": "来源名称", "addSiteFeed": "添加网站或订阅源", "sourcesWorldwide": "全球推荐来源", "sourcesWorldwideDetail": "快速选择适合构建国际报刊亭的常用媒体。", "addOtherCountries": "还要添加其他国家的来源吗？", "addOtherCountriesDetail": "已选择的来源会保留。请在上方选择另一个国家，继续构建国际报刊亭。", "buildKiosk": "构建报刊亭", "buildKioskDetail": "选择顶部显示的栏目。新闻会逐篇文章进行分类。", "customTab": "自定义标签页", "tabName": "标签页名称", "readyTitle": "报刊亭已准备就绪", "readyDetail": "这是初始设置。之后可以在设置中添加、删除和重新排序来源及标签页。", "enterKiosk": "进入报刊亭", "sources": "来源", "country": "国家", "tabs": "标签页", "tabsHeading": "报刊亭标签页", "newTab": "新标签页", "createTab": "创建标签页", "addSourcesAny": "添加任意国家的来源", "countryHeadlines": "该国主要新闻", "updateHeading": "刷新", "cacheInterval": "缓存间隔", "clearCache": "清除缓存", "repeatSetup": "重新进行初始设置", "resetHeading": "重置", "resetAll": "全部删除并重新开始", "resetDetail": "删除 News 的来源、标签页和缓存，然后重新打开初始设置。", "includedSources": "包含的来源", "tabVisibility": "标签页可见性", "tabVisibilityDetail": "可以隐藏标签页而不删除其设置。", "edit": "编辑", "editTab": "编辑标签页", "name": "名称", "activateTab": "启用标签页", "deactivateTab": "停用标签页", "deleteTab": "删除标签页", "active": "启用", "inactive": "停用", "availableSourcesFor": "{country} 有 {n} 个可用来源", "noPreconfiguredSources": "{country} 没有预配置来源：请使用在线搜索或添加该国主要新闻。", "selectedSourcesSummary": "已从 {countries} 个国家选择 {sources} 个来源", "onlineSearchMinChars": "在线搜索来源至少需要输入两个字符。", "onlineSourcesAdded": "已向结果添加 {n} 个在线来源。", "onlineSourcesFound": "在线找到 {n} 个来源。", "noMoreSources": "未找到其他在线来源。", "onlineSearchUnavailable": "在线搜索不可用。", "sourceAdded": "已添加 {name}。", "sourceNotFound": "未找到来源。", "countryHeadlinesFailed": "无法添加该国主要新闻。", "selectAtLeastOneSource": "请至少选择一个来源。", "saveConfigFailed": "无法保存配置。", "alreadyPresent": "{name} 已经存在。", "mustKeepActiveTab": "至少需要保留一个启用的标签页。", "mustKeepTab": "至少需要保留一个标签页。", "resetFailed": "无法重置配置。", "cacheCleared": "新闻缓存已清除。", "tabUnavailable": "标签页不可用", "saveTabFailed": "无法保存标签页。", "deleteTabFailed": "无法删除标签页。", "sourcesAvailable": "{n} 个来源可用", "noSourcesAvailable": "没有可用来源", "selected": "已选择", "catAll": "全部", "catPolitics": "政治", "catEconomy": "经济", "catSports": "体育", "catGames": "游戏", "catMusic": "音乐", "catCinema": "电影和剧集", "catFashion": "时尚", "catScience": "科学", "catHealth": "健康", "catComics": "漫画", "catTech": "科技", "catArt": "艺术", "catTravel": "旅行", "catFood": "美食", "feedErrorsSummary": "{n} 个来源未响应。其他新闻已正常加载。", "backendUnavailable": "News 后端没有响应。", "enterSourceAddress": "请输入网站或订阅源地址。", "unusableSource": "无法从此地址创建可用来源。", "articleUrlMissing": "缺少文章 URL。", "invalidConfiguration": "配置无效。", "sourceUnreachable": "无法连接到来源" } };
const NEWS_EXTRA_TRANSLATIONS = {
    it: { editSource: "MODIFICA FONTE", sourceSite: "Sito", sourceFeed: "Feed RSS/Atom", sourceStatus: "Stato della fonte", legendSelect: "Seleziona", legendBack: "Indietro", legendScroll: "Scorri", legendVideo: "Scorri tra i video di YouTube", legendTextSmall: "Testo −", legendTextLarge: "Testo +" },
    en: { editSource: "EDIT SOURCE", sourceSite: "Website", sourceFeed: "RSS/Atom feed", sourceStatus: "Source status", legendSelect: "Select", legendBack: "Back", legendScroll: "Scroll", legendVideo: "Browse YouTube videos", legendTextSmall: "Text −", legendTextLarge: "Text +" },
    es: { editSource: "EDITAR FUENTE", sourceSite: "Sitio web", sourceFeed: "Feed RSS/Atom", sourceStatus: "Estado de la fuente", legendSelect: "Seleccionar", legendBack: "Atrás", legendScroll: "Desplazar", legendVideo: "Desplazar entre vídeos de YouTube", legendTextSmall: "Texto −", legendTextLarge: "Texto +" },
    fr: { editSource: "MODIFIER LA SOURCE", sourceSite: "Site web", sourceFeed: "Flux RSS/Atom", sourceStatus: "État de la source", legendSelect: "Sélectionner", legendBack: "Retour", legendScroll: "Défiler", legendVideo: "Parcourir les vidéos YouTube", legendTextSmall: "Texte −", legendTextLarge: "Texte +" },
    de: { editSource: "QUELLE BEARBEITEN", sourceSite: "Website", sourceFeed: "RSS/Atom-Feed", sourceStatus: "Quellenstatus", legendSelect: "Auswählen", legendBack: "Zurück", legendScroll: "Scrollen", legendVideo: "Zwischen YouTube-Videos wechseln", legendTextSmall: "Text −", legendTextLarge: "Text +" },
    "pt-br": { editSource: "EDITAR FONTE", sourceSite: "Site", sourceFeed: "Feed RSS/Atom", sourceStatus: "Status da fonte", legendSelect: "Selecionar", legendBack: "Voltar", legendScroll: "Rolar", legendVideo: "Desplazar entre vídeos de YouTube", legendTextSmall: "Texto −", legendTextLarge: "Texto +" },
    ru: { editSource: "ИЗМЕНИТЬ ИСТОЧНИК", sourceSite: "Сайт", sourceFeed: "RSS/Atom-лента", sourceStatus: "Статус источника", legendSelect: "Выбрать", legendBack: "Назад", legendScroll: "Прокрутка", legendVideo: "Переключать видео YouTube", legendTextSmall: "Текст −", legendTextLarge: "Текст +" },
    ja: { editSource: "ソースを編集", sourceSite: "ウェブサイト", sourceFeed: "RSS/Atom フィード", sourceStatus: "ソースの状態", legendSelect: "選択", legendBack: "戻る", legendScroll: "スクロール", legendVideo: "YouTube 動画を切り替え", legendTextSmall: "文字 −", legendTextLarge: "文字 +" },
    zh: { editSource: "编辑来源", sourceSite: "网站", sourceFeed: "RSS/Atom 订阅源", sourceStatus: "来源状态", legendSelect: "选择", legendBack: "返回", legendScroll: "滚动", legendVideo: "切换 YouTube 视频", legendTextSmall: "文字 −", legendTextLarge: "文字 +" },
};
const NEWS_LOCALE_ALIASES = {
    italian: "it", it: "it", "it-it": "it",
    english: "en", en: "en", "en-us": "en", "en-gb": "en",
    spanish: "es", latam: "es", "spanish-latam": "es", es: "es", "es-es": "es", "es-mx": "es", "es-419": "es",
    french: "fr", fr: "fr", "fr-fr": "fr", "fr-ca": "fr",
    german: "de", de: "de", "de-de": "de",
    brazilian: "pt-br", pt: "pt-br", "pt-br": "pt-br",
    russian: "ru", ru: "ru", "ru-ru": "ru",
    japanese: "ja", ja: "ja", "ja-jp": "ja",
    schinese: "zh", "simplified-chinese": "zh", zh: "zh", "zh-cn": "zh", "zh-sg": "zh", "zh-hans": "zh"
};
function localeCandidates() {
    const values = [];
    const win = typeof window !== "undefined" ? window : {};
    const managers = [win.LocalizationManager, win.g_LocalizationManager, win.SteamLocalizationManager].filter(Boolean);
    managers.forEach((manager) => {
        [manager?.m_strLanguage, manager?.m_language, manager?.m_strCurrentLanguage, manager?.language].forEach((value) => values.push(value));
        ["GetLanguage", "GetCurrentLanguage"].forEach((method) => { try {
            const value = manager?.[method]?.();
            if (typeof value === "string")
                values.push(value);
        }
        catch { } });
    });
    [win.g_strLanguage, win.g_rgAppContextData?.language, document?.documentElement?.lang].forEach((value) => values.push(value));
    if (typeof navigator !== "undefined")
        values.push(...Array.from(navigator.languages ?? []), navigator.language);
    return values.map((value) => String(value ?? "").trim().toLowerCase().replaceAll("_", "-")).filter(Boolean);
}
function resolveNewsLocale(candidates = localeCandidates()) {
    for (const candidate of candidates) {
        const exact = NEWS_LOCALE_ALIASES[candidate];
        if (exact)
            return exact;
        const base = candidate.split("-")[0];
        const baseLocale = NEWS_LOCALE_ALIASES[base];
        if (baseLocale)
            return baseLocale;
    }
    return "en";
}
const CURRENT_LOCALE = resolveNewsLocale();
const CURRENT_LANGUAGE_TAG = { it: "it-IT", en: "en-US", es: "es-ES", fr: "fr-FR", de: "de-DE", "pt-br": "pt-BR", ru: "ru-RU", ja: "ja-JP", zh: "zh-CN" };
function tr(key, vars = {}) {
    let value = NEWS_EXTRA_TRANSLATIONS[CURRENT_LOCALE]?.[key] ?? NEWS_EXTRA_TRANSLATIONS.en[key] ?? NEWS_TRANSLATIONS[CURRENT_LOCALE]?.[key] ?? NEWS_TRANSLATIONS.en[key] ?? NEWS_TRANSLATIONS.it[key] ?? key;
    for (const [name, replacementValue] of Object.entries(vars))
        value = value.replaceAll(`{${name}}`, String(replacementValue));
    return value;
}
function localizeBackendError(error, fallbackKey = "loading") {
    const raw = String(error ?? "").trim();
    if (!raw)
        return tr(fallbackKey);
    const exact = {
        "Inserisci l'indirizzo del sito o del feed.": "enterSourceAddress",
        "Non sono riuscito a creare una fonte utilizzabile per questo indirizzo.": "unusableSource",
        "URL articolo mancante.": "articleUrlMissing",
        "Configurazione non valida.": "invalidConfiguration",
    };
    if (exact[raw])
        return tr(exact[raw]);
    const prefix = "Impossibile raggiungere la fonte:";
    if (raw.startsWith(prefix))
        return `${tr("sourceUnreachable")}: ${raw.slice(prefix.length).trim()}`;
    return raw;
}
let countryDisplayNames = null;
try {
    countryDisplayNames = new Intl.DisplayNames([CURRENT_LANGUAGE_TAG[CURRENT_LOCALE]], { type: "region" });
}
catch { }
function countryName(entry) {
    if (!entry)
        return "";
    try {
        return countryDisplayNames?.of(entry.code) || entry.name || entry.code;
    }
    catch {
        return entry.name || entry.code;
    }
}
let steamNavSoundManager = undefined;
function getSteamNavSoundManager() {
    if (steamNavSoundManager !== undefined)
        return steamNavSoundManager;
    try {
        steamNavSoundManager = findModuleExport?.((value) => value && typeof value.PlayNavSound === "function" && typeof value.RegisterCallbackOnPlaySound === "function") ?? null;
    }
    catch {
        steamNavSoundManager = null;
    }
    return steamNavSoundManager;
}
function playSteamBasicNavSound() { try {
    getSteamNavSoundManager()?.PlayNavSound?.(24);
}
catch { } }
function categoryLabel(category, fallback = "") {
    const map = { all: "catAll", politics: "catPolitics", economy: "catEconomy", sports: "catSports", games: "catGames", music: "catMusic", cinema: "catCinema", fashion: "catFashion", science: "catScience", health: "catHealth", comics: "catComics", tech: "catTech", art: "catArt", travel: "catTravel", food: "catFood" };
    return map[category] ? tr(map[category]) : fallback;
}
function displayTabName(tab) { if (!tab)
    return tr("catAll"); return tab.category ? categoryLabel(tab.category, tab.name) : tab.name; }
const PRESET_TABS = [
    ["all", tr("catAll")], ["politics", tr("catPolitics")], ["economy", tr("catEconomy")], ["sports", tr("catSports")],
    ["games", tr("catGames")], ["music", tr("catMusic")], ["cinema", tr("catCinema")], ["fashion", tr("catFashion")],
    ["science", tr("catScience")], ["health", tr("catHealth")], ["comics", tr("catComics")], ["tech", tr("catTech")],
    ["art", tr("catArt")], ["travel", tr("catTravel")], ["food", tr("catFood")],
];
const baseButton = {
    minHeight: 44,
    height: 44,
    padding: "0 14px",
    borderRadius: 10,
    fontSize: 15,
    color: "#fff",
};
function matchesAnyGamepadButton(button, ...candidates) {
    return candidates.some((candidate) => typeof candidate !== "undefined" && candidate === button);
}
function normalizeImageUrl(value) {
    return String(value || "").trim().replace(/[?#].*$/, "").replace(/\/+$/, "");
}
function imageIdentitySet(value) {
    const normalized = normalizeImageUrl(value);
    if (!normalized)
        return new Set();
    const variants = new Set([normalized]);
    try {
        const parsed = new URL(normalized, "https://example.invalid");
        const path = parsed.pathname.replace(/\/+/g, "/");
        const parts = path.split("/").filter(Boolean);
        if (path)
            variants.add(path);
        if (parts.length)
            variants.add(parts[parts.length - 1].toLowerCase());
        if (parts.length >= 2)
            variants.add(parts.slice(-2).join("/").toLowerCase());
    }
    catch { }
    return variants;
}
function imageLooksLikeHero(candidate, heroSources = []) {
    const current = imageIdentitySet(candidate);
    if (!current.size)
        return false;
    return heroSources.some((value) => {
        const hero = imageIdentitySet(value);
        if (!hero.size)
            return false;
        for (const a of current)
            for (const b of hero) {
                if (a === b || a.endsWith(b) || b.endsWith(a))
                    return true;
                if (a && b && (a.includes(b) || b.includes(a)))
                    return true;
            }
        return false;
    });
}
function callBackend(method, ...args) {
    // A disconnected Decky bridge can throw synchronously, not just reject. Keep
    // every UI .catch/finally path effective, and stop new requests after unload.
    try {
        if (newsDisposed)
            return Promise.reject(new Error("News has been unloaded"));
        return Promise.resolve(call(method, ...args));
    }
    catch (error) {
        return Promise.reject(error);
    }
}
function rpc(method, ...args) {
    const request = callBackend(method, ...args);
    if (method !== "save_config")
        return request;
    return request.then((value) => {
        if (newsDisposed)
            return value;
        if (value?.ok) {
            if (value?.config && bootstrapUiCache)
                bootstrapUiCache = { ...bootstrapUiCache, config: value.config };
            newsConfigGeneration += 1;
            newsUiCache.clear();
            imageEnrichmentInFlight.clear();
            allTabsPrefetchInFlight.clear();
            window.dispatchEvent(new CustomEvent(CONFIG_CHANGED_EVENT, { detail: value.config }));
        }
        return value;
    });
}
function saveConfigSilent(config) {
    // Update the in-memory bootstrap immediately so route remounts (especially
    // article -> Edicola Back) restore the exact active tab without waiting for a
    // fresh bootstrap RPC. The backend result then canonicalizes the cached copy.
    if (bootstrapUiCache)
        bootstrapUiCache = { ...bootstrapUiCache, config };
    return callBackend("save_config", config).then((value) => {
        if (value?.ok && value?.config && bootstrapUiCache)
            bootstrapUiCache = { ...bootstrapUiCache, config: value.config };
        return value;
    });
}
function formatAge(timestamp) {
    if (!timestamp)
        return "";
    const delta = Math.max(0, Math.floor(Date.now() / 1000 - timestamp));
    if (delta < 60)
        return tr("now");
    if (delta < 3600)
        return tr("minutesAgo", { n: Math.floor(delta / 60) });
    if (delta < 86400)
        return tr("hoursAgo", { n: Math.floor(delta / 3600) });
    if (delta < 172800)
        return tr("yesterday");
    return tr("daysAgo", { n: Math.floor(delta / 86400) });
}
function formatDate(timestamp) {
    if (!timestamp)
        return "";
    try {
        return new Date(timestamp * 1000).toLocaleString(CURRENT_LANGUAGE_TAG[CURRENT_LOCALE], { dateStyle: "medium", timeStyle: "short" });
    }
    catch {
        return "";
    }
}
function nextId(prefix) {
    return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}
function steamRouter() {
    // Steam exposes this store directly in the supplied September 2026 bundle.
    // It also avoids a hard dependency on DFL's historical module signature.
    return window.SteamUIStore ?? Router;
}
function steamWindows(store) {
    try {
        const windows = store?.SteamUIWindows;
        return Array.isArray(windows) ? windows : windows?.values ? Array.from(windows.values()) : [];
    }
    catch {
        return [];
    }
}
function mainWindow() {
    const router = steamRouter();
    const store = router?.WindowStore ?? Router?.WindowStore;
    const ready = (candidate) => {
        try {
            return candidate && typeof candidate.Navigate === "function" &&
                (typeof candidate.BCanNavigate !== "function" || candidate.BCanNavigate());
        }
        catch {
            return false;
        }
    };
    const main = store?.GamepadUIMainWindowInstance;
    if (ready(main))
        return main;
    const windows = steamWindows(store);
    const gamepad = windows.find((candidate) => {
        try {
            return candidate?.IsGamepadUIWindow?.() && ready(candidate);
        }
        catch {
            return false;
        }
    });
    if (gamepad)
        return gamepad;
    try {
        const focused = router?.GetFocusedWindowInstance?.();
        if (ready(focused))
            return focused;
    }
    catch { }
    return windows.find(ready);
}
let chromeObservers = [];
let chromeFrame = 0;
let suppressionLeaseCount = 0;
let suppressionReleaseTimer = 0;
const chromeRefreshTimers = new Set();
const transitionLeaseTimers = new Set();
const chromeSelectors = [
    "#header",
    '[class*="BasicFooter"]',
    '[class*="FooterLegend"]',
    '[class*="QuickAccessFooter"]',
    '[class*="GamepadFooter"]',
    '[class*="GamepadHeader"]',
    '[class*="HeaderStatus"]',
    '[class*="StatusIcons"]',
    '[class*="TopBar"]',
    '[data-news-fullscreen-chrome="true"]',
];
function fullscreenDocuments() {
    if (typeof document === "undefined")
        return [];
    const result = [];
    const add = (candidate) => {
        try {
            const doc = candidate;
            if (doc?.documentElement && !result.includes(doc))
                result.push(doc);
        }
        catch { }
    };
    const addWin = (candidate) => {
        if (!candidate)
            return;
        try {
            add(candidate.document);
        }
        catch { }
        try {
            add(candidate.window?.document);
        }
        catch { }
        try {
            add(candidate.m_Window?.document);
        }
        catch { }
        try {
            add(candidate.m_popup?.document);
        }
        catch { }
        try {
            add(candidate.BrowserWindow?.document);
        }
        catch { }
        try {
            add(candidate.GetWindow?.()?.document);
        }
        catch { }
    };
    add(document);
    try {
        add(window.top?.document);
    }
    catch { }
    try {
        add(window.parent?.document);
    }
    catch { }
    try {
        add(window.opener?.document);
    }
    catch { }
    const store = steamRouter()?.WindowStore ?? Router?.WindowStore;
    addWin(store?.GamepadUIMainWindowInstance);
    steamWindows(store).forEach(addWin);
    return result;
}
function chromeCss() {
    return `
    html.${ROOT_CLASS} #header,
    html.${ROOT_CLASS} [class*="BasicFooter"],
    html.${ROOT_CLASS} [class*="FooterLegend"],
    html.${ROOT_CLASS} [class*="QuickAccessFooter"],
    html.${ROOT_CLASS} [class*="GamepadFooter"],
    html.${ROOT_CLASS} [class*="GamepadHeader"],
    html.${ROOT_CLASS} [class*="HeaderStatus"],
    html.${ROOT_CLASS} [class*="StatusIcons"],
    html.${ROOT_CLASS} [class*="TopBar"],
    html.${ROOT_CLASS} [data-news-fullscreen-chrome="true"],
    body.${ROOT_CLASS} #header,
    body.${ROOT_CLASS} [class*="BasicFooter"],
    body.${ROOT_CLASS} [class*="FooterLegend"],
    body.${ROOT_CLASS} [class*="QuickAccessFooter"],
    body.${ROOT_CLASS} [class*="GamepadFooter"],
    body.${ROOT_CLASS} [class*="GamepadHeader"],
    body.${ROOT_CLASS} [class*="HeaderStatus"],
    body.${ROOT_CLASS} [class*="StatusIcons"],
    body.${ROOT_CLASS} [class*="TopBar"],
    body.${ROOT_CLASS} [data-news-fullscreen-chrome="true"] {
      display:none!important;
      opacity:0!important;
      visibility:hidden!important;
      pointer-events:none!important;
      transition:none!important;
      animation:none!important;
    }
  `;
}
function ensureChromeStyle(doc) {
    let style = doc.getElementById(CHROME_STYLE_ID);
    if (!style) {
        style = doc.createElement("style");
        style.id = CHROME_STYLE_ID;
        doc.head?.appendChild(style);
    }
    style.textContent = chromeCss();
}
function isVirtualKeyboardElement(element) {
    let current = element;
    for (let depth = 0; current && depth < 10; depth += 1, current = current.parentElement) {
        const className = typeof current.className === "string" ? current.className : "";
        const identity = `${current.id || ""} ${className} ${current.getAttribute("data-featuretarget") || ""} ${current.getAttribute("aria-label") || ""}`.toLowerCase();
        if (identity.includes("virtualkeyboard") || identity.includes("virtual-keyboard") ||
            identity.includes("onscreenkeyboard") || identity.includes("on-screen keyboard") ||
            identity.includes("keyboardmodal") || identity.includes("keyboard_modal"))
            return true;
    }
    return false;
}
const chromeInlineStyles = new Map();
function hideChromeElement(element) {
    if (!chromeInlineStyles.has(element)) {
        chromeInlineStyles.set(element, ["display", "opacity", "visibility", "pointer-events", "transition", "animation"]
            .map((name) => ({ name, value: element.style.getPropertyValue(name), priority: element.style.getPropertyPriority(name) })));
    }
    element.dataset.newsFullscreenChrome = "true";
    element.style.setProperty("display", "none", "important");
    element.style.setProperty("opacity", "0", "important");
    element.style.setProperty("visibility", "hidden", "important");
    element.style.setProperty("pointer-events", "none", "important");
    element.style.setProperty("transition", "none", "important");
    element.style.setProperty("animation", "none", "important");
}
function markChrome(doc) {
    if (!doc.documentElement.classList.contains(ROOT_CLASS))
        return;
    doc.querySelectorAll(chromeSelectors.join(",")).forEach((element) => {
        if (!element.closest(".newsFullscreenRoot") && !isVirtualKeyboardElement(element))
            hideChromeElement(element);
    });
    const targetWindow = doc.defaultView ?? window;
    const viewportWidth = targetWindow.innerWidth;
    const viewportHeight = targetWindow.innerHeight;
    doc.querySelectorAll("body *").forEach((element) => {
        if (element.closest(".newsFullscreenRoot") || element.dataset.newsFullscreenChrome === "true" || isVirtualKeyboardElement(element))
            return;
        const rect = element.getBoundingClientRect();
        if (rect.width < viewportWidth * .45 || rect.height <= 0 || rect.height > 190)
            return;
        const computed = targetWindow.getComputedStyle(element);
        if (!/^(fixed|absolute|sticky)$/.test(computed.position))
            return;
        const touchesTop = rect.top <= 12 && rect.bottom <= 194;
        const touchesBottom = rect.bottom >= viewportHeight - 12 && rect.top >= viewportHeight - 194;
        if (touchesTop || touchesBottom)
            hideChromeElement(element);
    });
}
function markAllChrome() {
    if (newsDisposed)
        return;
    fullscreenDocuments().forEach((doc) => {
        ensureChromeStyle(doc);
        doc.documentElement.classList.add(ROOT_CLASS);
        doc.body?.classList.add(ROOT_CLASS);
        markChrome(doc);
    });
}
function scheduleChromeMark() {
    if (chromeFrame)
        window.cancelAnimationFrame(chromeFrame);
    chromeFrame = window.requestAnimationFrame(() => {
        chromeFrame = 0;
        markAllChrome();
    });
}
function scheduleChromeBurst() {
    chromeRefreshTimers.forEach((timer) => window.clearTimeout(timer));
    chromeRefreshTimers.clear();
    [0, 40, 120, 280, 600, 1100].forEach((delay) => {
        const timer = window.setTimeout(() => {
            chromeRefreshTimers.delete(timer);
            markAllChrome();
        }, delay);
        chromeRefreshTimers.add(timer);
    });
}
function activateChromeSuppression() {
    if (typeof document === "undefined")
        return;
    markAllChrome();
    chromeObservers.forEach((observer) => observer.disconnect());
    chromeObservers = [];
    fullscreenDocuments().forEach((doc) => {
        if (!doc.body)
            return;
        const observer = new MutationObserver(scheduleChromeMark);
        observer.observe(doc.body, { childList: true, subtree: true });
        chromeObservers.push(observer);
    });
    scheduleChromeBurst();
}
function deactivateChromeSuppression() {
    if (typeof document === "undefined")
        return;
    chromeRefreshTimers.forEach((timer) => window.clearTimeout(timer));
    chromeRefreshTimers.clear();
    chromeObservers.forEach((observer) => observer.disconnect());
    chromeObservers = [];
    if (chromeFrame)
        window.cancelAnimationFrame(chromeFrame);
    chromeFrame = 0;
    fullscreenDocuments().forEach((doc) => {
        doc.documentElement.classList.remove(ROOT_CLASS);
        doc.body?.classList.remove(ROOT_CLASS);
    });
    chromeInlineStyles.forEach((properties, element) => {
        delete element.dataset.newsFullscreenChrome;
        properties.forEach(({ name, value, priority }) => {
            if (value)
                element.style.setProperty(name, value, priority);
            else
                element.style.removeProperty(name);
        });
    });
    chromeInlineStyles.clear();
}
function retainChromeSuppression() {
    suppressionLeaseCount += 1;
    if (suppressionReleaseTimer) {
        window.clearTimeout(suppressionReleaseTimer);
        suppressionReleaseTimer = 0;
    }
    activateChromeSuppression();
}
function releaseChromeSuppression() {
    suppressionLeaseCount = Math.max(0, suppressionLeaseCount - 1);
    if (suppressionLeaseCount > 0)
        return;
    if (suppressionReleaseTimer)
        window.clearTimeout(suppressionReleaseTimer);
    suppressionReleaseTimer = window.setTimeout(() => {
        suppressionReleaseTimer = 0;
        if (suppressionLeaseCount > 0)
            return;
        const stillMounted = fullscreenDocuments().some((doc) => Boolean(doc.querySelector(".newsFullscreenRoot")));
        if (!stillMounted)
            deactivateChromeSuppression();
    }, 650);
}
function holdChromeForTransition(duration = 1800) {
    retainChromeSuppression();
    const timer = window.setTimeout(() => {
        transitionLeaseTimers.delete(timer);
        releaseChromeSuppression();
    }, duration);
    transitionLeaseTimers.add(timer);
}
function forceRestoreChrome() {
    transitionLeaseTimers.forEach((timer) => window.clearTimeout(timer));
    transitionLeaseTimers.clear();
    if (suppressionReleaseTimer)
        window.clearTimeout(suppressionReleaseTimer);
    suppressionReleaseTimer = 0;
    suppressionLeaseCount = 0;
    deactivateChromeSuppression();
}
function useFullscreenChrome() {
    useLayoutEffect(() => {
        retainChromeSuppression();
        return () => releaseChromeSuppression();
    }, []);
}
function closeSideMenusAfterNavigation(win) {
    // Decky's Navigation contract requires closing AFTER navigating; closing first
    // can hide the Big Picture overlay during the route transition on Windows.
    try {
        if (typeof win?.MenuStore?.CloseSideMenus === "function")
            win.MenuStore.CloseSideMenus();
        else
            Navigation?.CloseSideMenus?.();
    }
    catch { }
}
function navigate(path) {
    if (newsDisposed)
        return;
    holdChromeForTransition();
    const win = mainWindow();
    try {
        if (typeof win?.Navigate === "function")
            win.Navigate(path);
        else if (typeof Navigation?.Navigate === "function")
            Navigation.Navigate(path);
        else
            throw new Error("Steam navigation is unavailable");
        closeSideMenusAfterNavigation(win);
        markAllChrome();
        queueMicrotask(markAllChrome);
        scheduleChromeMark();
    }
    catch (error) {
        forceRestoreChrome();
        console.warn("[News] Could not open route", path, error);
    }
}
function goBack() {
    const win = mainWindow();
    try {
        if (typeof win?.NavigateBack === "function")
            win.NavigateBack();
        else
            Navigation?.NavigateBack?.();
    }
    catch (error) {
        console.warn("[News] Could not navigate back", error);
        forceRestoreChrome();
    }
    [0, 60, 180, 420, 900].forEach((delay) => scheduleNewsTask(() => {
        const anyRoot = fullscreenDocuments().some((doc) => Boolean(doc.querySelector(".newsFullscreenRoot")));
        if (!anyRoot)
            forceRestoreChrome();
        else
            markAllChrome();
    }, delay));
}
function openWebsiteInSteam(url) {
    const value = String(url || "").trim();
    if (!/^https?:\/\//i.test(value))
        return;
    const win = mainWindow();
    try {
        // NavigateToSteamWeb is a WindowInstance method in the supplied Steam UI;
        // DFL's wrapper can exist but silently fail to find the correct window.
        if (typeof win?.NavigateToSteamWeb === "function") {
            win.NavigateToSteamWeb(value);
            closeSideMenusAfterNavigation(win);
            return;
        }
        if (typeof win?.Navigator?.SteamWeb === "function") {
            win.Navigator.SteamWeb(value);
            closeSideMenusAfterNavigation(win);
            return;
        }
    }
    catch { }
    const nav = Navigation;
    try {
        if (typeof nav?.NavigateToSteamWeb === "function") {
            nav.NavigateToSteamWeb(value);
            closeSideMenusAfterNavigation(win);
            return;
        }
    }
    catch { }
    try {
        if (typeof nav?.NavigateToExternalWeb === "function") {
            nav.NavigateToExternalWeb(value);
            return;
        }
    }
    catch { }
    void rpc("open_external_url", value).catch((error) => console.warn("[News] Could not open website", error));
}
function isMetadataOnly(item) {
    return item?.contentMode === "metadata_only";
}
function metadataNewsItem(item) {
    // Never revive a cover, full body or resolved/enriched URL from UI memory.
    return { id: item.id, title: item.title, url: item.url, sourceId: item.sourceId, source: item.source,
        country: item.country, published: item.published, publishedText: item.publishedText, excerpt: item.excerpt,
        type: "article", contentMode: "metadata_only" };
}
function openArticle(item) {
    if (isMetadataOnly(item)) {
        openWebsiteInSteam(item.url);
        return;
    }
    // Freeze the identity for this route. Use a resolved publisher URL when cover
    // enrichment already discovered it, but keep the feed item itself stable.
    window.__deckyNewsOpenItem = { ...stabilizeNewsItem(item), url: item.resolvedUrl || item.url };
    navigate(ARTICLE_ROUTE);
}
function useBootstrap() {
    const [bootstrap, setBootstrap] = useState(() => bootstrapUiCache);
    const [error, setError] = useState("");
    const reload = useCallback(async () => {
        try {
            setError("");
            if (!bootstrapLoadPromise) {
                let timeoutId = 0;
                const timeout = new Promise((_, reject) => {
                    timeoutId = window.setTimeout(() => reject(new Error(tr("backendUnavailable"))), 5000);
                });
                bootstrapLoadPromise = Promise.race([rpc("get_bootstrap"), timeout])
                    .then((value) => {
                    window.clearTimeout(timeoutId);
                    bootstrapUiCache = value;
                    return value;
                })
                    .finally(() => { window.clearTimeout(timeoutId); bootstrapLoadPromise = null; });
            }
            const value = await bootstrapLoadPromise;
            setBootstrap(value);
            return value;
        }
        catch (exc) {
            // A transient refresh failure must never erase a perfectly valid config
            // already in memory. Keep the current/last bootstrap visible and report
            // the error only if this is truly the first load.
            if (bootstrapUiCache)
                setBootstrap(bootstrapUiCache);
            else
                setBootstrap(null);
            setError(String(exc?.message ?? exc ?? tr("loading")));
            return bootstrapUiCache;
        }
    }, []);
    useEffect(() => {
        if (!bootstrapUiCache)
            void reload();
        else
            setBootstrap(bootstrapUiCache);
        const sync = (event) => {
            const detail = event?.detail;
            if (detail && bootstrapUiCache) {
                bootstrapUiCache = { ...bootstrapUiCache, config: detail };
                setBootstrap(bootstrapUiCache);
                return;
            }
            void reload();
        };
        window.addEventListener(CONFIG_CHANGED_EVENT, sync);
        return () => window.removeEventListener(CONFIG_CHANGED_EVENT, sync);
    }, [reload]);
    return { bootstrap, setBootstrap, error, reload };
}
const newsUiCache = new Map();
const imageEnrichmentInFlight = new Set();
let newsConfigGeneration = 0;
// Artwork survives route unmounts/refreshes in the frontend too. Backend image
// metadata is persistent; this map prevents a fresh raw feed item from visually
// erasing a cover that was already painted during the current plugin session.
const cardImageMemory = new Map();
const articleUiCache = new Map();
const ARTICLE_UI_CACHE_MS = 6 * 60 * 60 * 1000;
function newsItemKey(item) {
    return String(item?.id || item?.url || item?.title || "");
}
function newsItemMemoryKeys(item) {
    const keys = [
        String(item?.id || "").trim(),
        String(item?.resolvedUrl || "").trim(),
        String(item?.url || "").trim(),
        `${String(item?.sourceId || "").trim()}::${String(item?.title || "").trim()}`,
        `${String(item?.source || "").trim()}::${String(item?.title || "").trim()}`,
    ].filter(Boolean);
    return Array.from(new Set(keys));
}
function rememberCardImage(item, image) {
    if (isMetadataOnly(item)) {
        newsItemMemoryKeys(item).forEach((key) => cardImageMemory.delete(key));
        return;
    }
    const value = String(image || "").trim();
    if (!value)
        return;
    newsItemMemoryKeys(item).forEach((key) => cardImageMemory.set(key, value));
}
function recallCardImage(item) {
    if (isMetadataOnly(item))
        return "";
    for (const key of newsItemMemoryKeys(item)) {
        const value = String(cardImageMemory.get(key) || "").trim();
        if (value)
            return value;
    }
    return "";
}
function stabilizeNewsItem(item) {
    if (isMetadataOnly(item))
        return metadataNewsItem(item);
    const remembered = recallCardImage(item);
    const image = String(item?.image || remembered || "");
    if (image)
        rememberCardImage(item, image);
    return image === item.image ? item : { ...item, image };
}
function mergeNewsItemStable(existing, replacement) {
    if (isMetadataOnly(existing) || isMetadataOnly(replacement))
        return metadataNewsItem({ ...existing, ...replacement });
    const merged = { ...existing, ...replacement };
    // Empty/raw feed values are never allowed to erase enrichment already shown.
    // Keep the first successful cover stable for this cache revision as well.
    if (existing.image)
        merged.image = existing.image;
    if (existing.resolvedUrl)
        merged.resolvedUrl = existing.resolvedUrl;
    const remembered = recallCardImage(existing) || recallCardImage(replacement);
    if (!merged.image && remembered)
        merged.image = remembered;
    if (merged.image)
        rememberCardImage(merged, merged.image);
    return stabilizeNewsItem(merged);
}
function shuffledSourceOrder(sourceIds) {
    const values = Array.from(new Set(sourceIds));
    for (let index = values.length - 1; index > 0; index -= 1) {
        const swap = Math.floor(Math.random() * (index + 1));
        [values[index], values[swap]] = [values[swap], values[index]];
    }
    return values;
}
function mergeNewsSourceBatch(currentItems, sourceId, batch, limit) {
    const byKey = new Map(batch.map((item) => [newsItemKey(item), item]));
    const combined = currentItems.map((item) => {
        const replacement = byKey.get(newsItemKey(item));
        return replacement ? mergeNewsItemStable(item, replacement) : stabilizeNewsItem(item);
    });
    const seen = new Set(combined.map(newsItemKey));
    for (const item of batch) {
        const key = newsItemKey(item);
        if (!key || seen.has(key))
            continue;
        combined.push(item);
        seen.add(key);
        if (combined.length >= Math.max(1, limit))
            break;
    }
    return combined.slice(0, Math.max(1, limit));
}
function waitForProgressivePaint(ms = 12) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
}
function useNews(tabId, limit = 80, sourceIds = [], reserveFirstWaveSlots = false, enabled = true) {
    const cacheKey = `${tabId || "__all__"}:${limit}`;
    const sourceKey = sourceIds.join("|");
    const initial = newsUiCache.get(cacheKey);
    const [items, setItems] = useState((initial?.items ?? []).map(stabilizeNewsItem));
    const [loading, setLoading] = useState(enabled && !initial);
    const [errors, setErrors] = useState(initial?.errors ?? []);
    const activeCacheKeyRef = useRef(cacheKey);
    activeCacheKeyRef.current = cacheKey;
    const coverQueueRef = useRef(new Map());
    const coverMissCountRef = useRef(new Map());
    const coverPollActiveRef = useRef(false);
    const coverPollTimerRef = useRef(0);
    const coverPollGenerationRef = useRef(0);
    useEffect(() => {
        coverPollGenerationRef.current += 1;
        coverQueueRef.current.clear();
        coverMissCountRef.current.clear();
        coverPollActiveRef.current = false;
        if (coverPollTimerRef.current)
            window.clearTimeout(coverPollTimerRef.current);
        coverPollTimerRef.current = 0;
        return () => {
            coverPollGenerationRef.current += 1;
            if (coverPollTimerRef.current)
                window.clearTimeout(coverPollTimerRef.current);
            coverPollTimerRef.current = 0;
            coverPollActiveRef.current = false;
            coverQueueRef.current.clear();
            coverMissCountRef.current.clear();
        };
    }, [cacheKey]);
    const enrichMissingImages = useCallback((baseItems, baseErrors) => {
        if (newsDisposed)
            return;
        const missing = baseItems
            .map(stabilizeNewsItem)
            .filter((item) => !item.loadingPlaceholder && !isMetadataOnly(item) && item.type === "article" && !item.image && item.id);
        if (!missing.length)
            return;
        const queue = coverQueueRef.current;
        const newlyStarted = [];
        for (const candidate of missing) {
            queue.set(candidate.id, candidate);
            if (!imageEnrichmentInFlight.has(candidate.id)) {
                imageEnrichmentInFlight.add(candidate.id);
                newlyStarted.push(candidate);
            }
        }
        if (newlyStarted.length) {
            // The backend now has separate fast/slow cover pools. Keep the slow rendered
            // fallback budget deliberately small: all fast metadata jobs still start.
            void rpc("start_cover_enrichment", newlyStarted, newlyStarted.length).catch(() => { });
        }
        if (coverPollActiveRef.current)
            return;
        coverPollActiveRef.current = true;
        const generation = coverPollGenerationRef.current;
        const applyStatus = (status, candidates) => {
            const images = status?.images && typeof status.images === "object" ? status.images : {};
            const resolvedUrls = status?.resolvedUrls && typeof status.resolvedUrls === "object" ? status.resolvedUrls : {};
            const pending = new Set(Array.isArray(status?.pending) ? status.pending.map(String) : []);
            const current = newsUiCache.get(cacheKey);
            const sourceItems = current?.items ?? baseItems;
            let changed = false;
            // Cover failure must never remove an article. An unresolved publisher item
            // remains visible/clickable with the source fallback and can be retried by a
            // later refresh.
            const enriched = sourceItems.map((raw) => {
                const item = stabilizeNewsItem(raw);
                const image = String(images[item.id] || "");
                const resolvedUrl = String(resolvedUrls[item.id] || "");
                if (!image && !resolvedUrl)
                    return item;
                const nextImage = item.image || image;
                const nextResolved = item.resolvedUrl || resolvedUrl;
                if (image && !item.image)
                    rememberCardImage({ ...item, resolvedUrl }, image);
                if (nextImage === item.image && nextResolved === item.resolvedUrl)
                    return item;
                changed = true;
                return { ...item, image: nextImage, resolvedUrl: nextResolved };
            });
            if (changed) {
                const snapshot = { items: enriched, errors: current?.errors ?? baseErrors, at: current?.at ?? Date.now() };
                newsUiCache.set(cacheKey, snapshot);
                if (activeCacheKeyRef.current === cacheKey)
                    setItems(enriched);
            }
            const missCounts = coverMissCountRef.current;
            for (const candidate of candidates) {
                const image = String(images[candidate.id] || "");
                if (image) {
                    queue.delete(candidate.id);
                    missCounts.delete(candidate.id);
                    imageEnrichmentInFlight.delete(candidate.id);
                    continue;
                }
                if (pending.has(candidate.id)) {
                    missCounts.set(candidate.id, 0);
                    continue;
                }
                const misses = (missCounts.get(candidate.id) ?? 0) + 1;
                missCounts.set(candidate.id, misses);
                // Four cache-only misses after the backend says the item is no longer
                // pending are enough to stop polling it. A later refresh can retry it.
                if (misses >= 4) {
                    queue.delete(candidate.id);
                    missCounts.delete(candidate.id);
                    imageEnrichmentInFlight.delete(candidate.id);
                }
            }
        };
        let pollCount = 0;
        const poll = async () => {
            if (newsDisposed || generation !== coverPollGenerationRef.current)
                return;
            pollCount += 1;
            const candidates = Array.from(coverQueueRef.current.values());
            if (!candidates.length) {
                coverPollActiveRef.current = false;
                coverPollTimerRef.current = 0;
                return;
            }
            try {
                const status = await rpc("get_cached_covers", candidates);
                if (newsDisposed || generation !== coverPollGenerationRef.current)
                    return;
                applyStatus(status, candidates);
            }
            catch { }
            if (newsDisposed || generation !== coverPollGenerationRef.current)
                return;
            if (!coverQueueRef.current.size) {
                coverPollActiveRef.current = false;
                coverPollTimerRef.current = 0;
                return;
            }
            // Cover discovery itself continues at full backend concurrency. Polling the
            // cache less aggressively avoids rerendering the entire magazine grid 10+
            // times per second while the user is scrolling.
            const delay = pollCount < 6 ? 120 : pollCount < 24 ? 220 : 420;
            coverPollTimerRef.current = window.setTimeout(() => void poll(), delay);
        };
        coverPollTimerRef.current = window.setTimeout(() => void poll(), 30);
    }, [cacheKey]);
    const load = useCallback(async (force = false) => {
        if (!enabled || !tabId) {
            if (activeCacheKeyRef.current === cacheKey) {
                setLoading(false);
                setErrors([]);
            }
            return;
        }
        const cached = newsUiCache.get(cacheKey);
        setLoading(true);
        // Stable progressive source fan-out. Every publisher starts immediately,
        // but only ONE new story per completed source is appended during the first
        // wave. Nothing already visible is re-sorted upward, so the top of QAM and
        // Edicola never flashes while slower publishers arrive. Once all publishers
        // have answered, remaining stories are appended downward in randomized
        // source round-robin order (newest item of each source first, then second, etc.).
        if (sourceIds.length) {
            if (!cached) {
                newsUiCache.set(cacheKey, { items: [], errors: [], at: Date.now() });
                if (activeCacheKeyRef.current === cacheKey) {
                    setItems([]);
                    setErrors([]);
                }
            }
            const sourceOrder = shuffledSourceOrder(sourceIds);
            const sourceErrors = new Map();
            const sourceSnapshots = new Map();
            const sourceCursor = new Map();
            const firstWaveEmitted = new Set();
            let visibleItems = [...(cached?.items ?? [])].map(stabilizeNewsItem).slice(0, Math.max(1, limit));
            const useReservedSlots = reserveFirstWaveSlots && visibleItems.length === 0;
            if (useReservedSlots) {
                visibleItems = sourceOrder.slice(0, Math.max(1, limit)).map((sourceId) => ({
                    id: `__news-loading-${sourceId}`, title: "", url: "", sourceId, source: "", country: "", published: 0, type: "article", loadingPlaceholder: true,
                }));
            }
            const replaceReservedSlot = (sourceId, candidate) => {
                if (!useReservedSlots || !candidate)
                    return false;
                const index = visibleItems.findIndex((item) => item.loadingPlaceholder && item.sourceId === sourceId);
                if (index < 0)
                    return false;
                visibleItems = visibleItems.map((item, position) => position === index ? stabilizeNewsItem(candidate) : item);
                firstWaveEmitted.add(sourceId);
                publish();
                return true;
            };
            const publish = () => {
                const nextErrors = Array.from(sourceErrors.values()).flat();
                const snapshot = { items: visibleItems, errors: nextErrors, at: Date.now() };
                newsUiCache.set(cacheKey, snapshot);
                if (activeCacheKeyRef.current === cacheKey) {
                    setItems([...visibleItems]);
                    setErrors(nextErrors);
                }
                enrichMissingImages(visibleItems, nextErrors);
            };
            const takeNextUnseen = (sourceId) => {
                const batch = sourceSnapshots.get(sourceId) ?? [];
                let cursor = sourceCursor.get(sourceId) ?? 0;
                while (cursor < batch.length) {
                    const candidate = batch[cursor++];
                    sourceCursor.set(sourceId, cursor);
                    const key = newsItemKey(candidate);
                    if (key && !visibleItems.some((item) => newsItemKey(item) === key))
                        return stabilizeNewsItem(candidate);
                }
                sourceCursor.set(sourceId, cursor);
                return undefined;
            };
            const emitOneReadyFirstWave = () => {
                if (visibleItems.length >= limit)
                    return false;
                for (const sourceId of sourceOrder) {
                    if (firstWaveEmitted.has(sourceId) || !sourceSnapshots.has(sourceId))
                        continue;
                    firstWaveEmitted.add(sourceId);
                    const candidate = takeNextUnseen(sourceId);
                    if (!candidate)
                        continue;
                    visibleItems = [...visibleItems.filter((item) => !item.loadingPlaceholder), candidate].slice(0, limit);
                    publish();
                    return true;
                }
                return false;
            };
            const jobs = sourceOrder.map(async (sourceId) => {
                try {
                    const result = await rpc("get_news_source", tabId, sourceId, force, limit);
                    const batch = Array.isArray(result?.items) ? result.items : [];
                    const batchErrors = Array.isArray(result?.errors) ? result.errors : [];
                    sourceErrors.set(sourceId, batchErrors);
                    sourceSnapshots.set(sourceId, batch);
                    // Refresh data already visible IN PLACE, preserving its exact position.
                    // A source completion may contribute AT MOST one first-wave card. The
                    // randomized source priority decides which ready publisher contributes
                    // next, so completion speed cannot let a single publisher dominate.
                    const byKey = new Map(batch.map((item) => [newsItemKey(item), item]));
                    visibleItems = visibleItems.map((item) => {
                        if (item.loadingPlaceholder)
                            return item;
                        const replacement = byKey.get(newsItemKey(item));
                        return replacement ? mergeNewsItemStable(item, replacement) : stabilizeNewsItem(item);
                    });
                    if (useReservedSlots) {
                        const first = takeNextUnseen(sourceId);
                        if (!replaceReservedSlot(sourceId, first))
                            publish();
                    }
                    else if (!emitOneReadyFirstWave())
                        publish();
                }
                catch (exc) {
                    sourceErrors.set(sourceId, [{ source: "News", error: String(exc?.message ?? exc ?? tr("loading")) }]);
                    sourceSnapshots.set(sourceId, []);
                    publish();
                }
            });
            await Promise.allSettled(jobs);
            // Ensure every publisher gets its reserved first-wave position. A source
            // that returned no usable story leaves a temporary blank cell. After every
            // source has settled, fill those holes with the next round-robin stories in
            // place, so already-painted cards never jump to a new position.
            if (!useReservedSlots) {
                while (emitOneReadyFirstWave() && visibleItems.length < limit)
                    await waitForProgressivePaint(10);
            }
            else {
                const emptyIndexes = () => visibleItems.map((item, index) => item.loadingPlaceholder ? index : -1).filter((index) => index >= 0);
                for (const emptyIndex of emptyIndexes()) {
                    let fill;
                    for (const sourceId of sourceOrder) {
                        fill = takeNextUnseen(sourceId);
                        if (fill)
                            break;
                    }
                    if (!fill)
                        break;
                    visibleItems = visibleItems.map((item, index) => index === emptyIndex ? stabilizeNewsItem(fill) : item);
                    publish();
                    await waitForProgressivePaint(10);
                }
            }
            let addedInRound = true;
            while (addedInRound && visibleItems.filter((item) => !item.loadingPlaceholder).length < limit) {
                addedInRound = false;
                for (const sourceId of sourceOrder) {
                    const candidate = takeNextUnseen(sourceId);
                    if (!candidate)
                        continue;
                    visibleItems = [...visibleItems, candidate].slice(0, limit);
                    publish();
                    addedInRound = true;
                    await waitForProgressivePaint(10);
                    if (visibleItems.length >= limit)
                        break;
                }
            }
            if (activeCacheKeyRef.current === cacheKey)
                setLoading(false);
            return;
        }
        try {
            const result = await rpc("get_news", tabId, force, limit);
            let nextItems = Array.isArray(result?.items) ? result.items : [];
            const nextErrors = Array.isArray(result?.errors) ? result.errors : [];
            if (!force && nextItems.length === 0 && cached?.items?.length)
                nextItems = cached.items;
            newsUiCache.set(cacheKey, { items: nextItems, errors: nextErrors, at: Date.now() });
            if (activeCacheKeyRef.current === cacheKey) {
                setItems(nextItems);
                setErrors(nextErrors);
            }
            enrichMissingImages(nextItems, nextErrors);
        }
        catch (exc) {
            if (activeCacheKeyRef.current === cacheKey)
                setErrors([{ source: "News", error: String(exc?.message ?? exc ?? tr("loading")) }]);
        }
        finally {
            if (activeCacheKeyRef.current === cacheKey)
                setLoading(false);
        }
    }, [tabId, limit, cacheKey, sourceKey, enrichMissingImages, reserveFirstWaveSlots, enabled]);
    useEffect(() => {
        activeCacheKeyRef.current = cacheKey;
        if (!enabled || !tabId) {
            setItems([]);
            setErrors([]);
            setLoading(false);
            return;
        }
        const cached = newsUiCache.get(cacheKey);
        if (cached) {
            setItems(cached.items.map(stabilizeNewsItem));
            setErrors(cached.errors);
            setLoading(false);
            if (Date.now() - cached.at > 45000)
                void load(false);
            else
                enrichMissingImages(cached.items, cached.errors);
        }
        else {
            setItems([]);
            setErrors([]);
            setLoading(true);
            void load(false);
        }
        const sync = () => {
            // save_config invalidates shared caches before dispatching this event. The
            // new sourceKey/config render below owns the fresh request; never reload
            // from this listener's potentially stale closure.
        };
        window.addEventListener(CONFIG_CHANGED_EVENT, sync);
        return () => window.removeEventListener(CONFIG_CHANGED_EVENT, sync);
    }, [cacheKey, sourceKey, load, enrichMissingImages, enabled, tabId]);
    return { items, loading, errors, load };
}
const allTabsPrefetchInFlight = new Map();
function applyPrefetchedTabSnapshot(tabId, items, errors, limit = 120) {
    const stable = items.map(stabilizeNewsItem);
    stable.forEach((item) => { if (item.image)
        rememberCardImage(item, item.image); });
    newsUiCache.set(`${tabId}:${limit}`, { items: stable.slice(0, limit), errors, at: Date.now() });
    // QAM uses a smaller cache key. Populate it from the same all-tab pass so a
    // category switch there is warm too instead of triggering another cold load.
    newsUiCache.set(`${tabId}:30`, { items: stable.slice(0, 30), errors, at: Date.now() });
}
async function hydratePrefetchedCoverCaches(tabIds, limit = 120) {
    if (newsDisposed)
        return;
    const unique = new Map();
    for (const tabId of tabIds) {
        const snapshot = newsUiCache.get(`${tabId}:${limit}`);
        for (const item of snapshot?.items ?? []) {
            if (!item.loadingPlaceholder && !isMetadataOnly(item) && item.type === "article" && !item.image && item.id)
                unique.set(item.id, item);
        }
    }
    const missing = Array.from(unique.values());
    if (!missing.length)
        return;
    const chunks = [];
    for (let index = 0; index < missing.length; index += 140)
        chunks.push(missing.slice(index, index + 140));
    const statuses = await Promise.all(chunks.map((chunk) => rpc("get_cached_covers", chunk).catch(() => null)));
    const images = {};
    const resolvedUrls = {};
    for (const status of statuses) {
        if (status?.images && typeof status.images === "object")
            Object.assign(images, status.images);
        if (status?.resolvedUrls && typeof status.resolvedUrls === "object")
            Object.assign(resolvedUrls, status.resolvedUrls);
    }
    if (!Object.keys(images).length && !Object.keys(resolvedUrls).length)
        return;
    for (const tabId of tabIds) {
        const snapshot = newsUiCache.get(`${tabId}:${limit}`);
        if (!snapshot)
            continue;
        const enriched = snapshot.items.map((item) => {
            const image = item.image || String(images[item.id] || "");
            const resolvedUrl = item.resolvedUrl || String(resolvedUrls[item.id] || "");
            if (image)
                rememberCardImage({ ...item, resolvedUrl }, image);
            return image === item.image && resolvedUrl === item.resolvedUrl ? item : { ...item, image, resolvedUrl };
        });
        applyPrefetchedTabSnapshot(tabId, enriched, snapshot.errors, limit);
    }
}
async function prefetchNewsTabs(tabs, activeTabId, limit = 120) {
    if (newsDisposed)
        return;
    const enabledIds = tabs.filter((tab) => tab.enabled !== false).map((tab) => tab.id).filter(Boolean);
    if (!enabledIds.length)
        return;
    const tabSignature = tabs.filter((tab) => tab.enabled !== false).map((tab) => `${tab.id}:${tab.category || ""}:${(tab.sourceIds || []).join(",")}`).join("|");
    const key = `${tabSignature}::${activeTabId}::${limit}`;
    const generation = newsConfigGeneration;
    const existing = allTabsPrefetchInFlight.get(key);
    if (existing)
        return existing;
    const job = (async () => {
        try {
            const result = await rpc("prefetch_tabs", activeTabId, limit);
            if (generation !== newsConfigGeneration)
                return;
            const byTab = result?.tabs && typeof result.tabs === "object" ? result.tabs : {};
            const errors = Array.isArray(result?.errors) ? result.errors : [];
            for (const tabId of enabledIds) {
                // Never replace a live active-tab progressive snapshot with a background
                // bulk result. Every other tab can be made instantly switchable now.
                if (tabId === activeTabId)
                    continue;
                const items = Array.isArray(byTab[tabId]) ? byTab[tabId] : [];
                applyPrefetchedTabSnapshot(tabId, items, errors, limit);
            }
            // Cover workers keep running after the bulk tab result returns. Pull their
            // cache-only results into every hidden tab a few times, without any new
            // publisher/network fetch, so fallback cards disappear before tab entry.
            const backgroundIds = enabledIds.filter((id) => id !== activeTabId);
            if (backgroundIds.length) {
                const hydrateIfCurrent = () => { if (generation === newsConfigGeneration)
                    void hydratePrefetchedCoverCaches(backgroundIds, limit); };
                scheduleNewsTask(hydrateIfCurrent, 650);
                scheduleNewsTask(hydrateIfCurrent, 1800);
                scheduleNewsTask(hydrateIfCurrent, 5200);
                scheduleNewsTask(hydrateIfCurrent, 10000);
                scheduleNewsTask(hydrateIfCurrent, 20000);
                scheduleNewsTask(hydrateIfCurrent, 35000);
            }
        }
        catch { }
    })().finally(() => allTabsPrefetchInFlight.delete(key));
    allTabsPrefetchInFlight.set(key, job);
    return job;
}
async function prefetchNewsTab(tabId, limit = 120) {
    if (newsDisposed)
        return;
    const cacheKey = `${tabId || "__all__"}:${limit}`;
    if (!tabId)
        return;
    const warmCovers = (items) => {
        const missing = items.filter((item) => !item.loadingPlaceholder && !isMetadataOnly(item) && item.type === "article" && !item.image);
        if (missing.length)
            void rpc("start_cover_enrichment", missing, missing.length).catch(() => { });
    };
    const cached = newsUiCache.get(cacheKey);
    if (cached?.items?.length) {
        warmCovers(cached.items.map(stabilizeNewsItem));
        return;
    }
    try {
        const result = await rpc("get_news", tabId, false, limit);
        if (newsDisposed)
            return;
        const nextItems = (Array.isArray(result?.items) ? result.items : []).map(stabilizeNewsItem);
        const nextErrors = Array.isArray(result?.errors) ? result.errors : [];
        if (nextItems.length) {
            applyPrefetchedTabSnapshot(tabId, nextItems, nextErrors, limit);
            warmCovers(nextItems);
        }
    }
    catch { }
}
function magazineSpan(index, item) {
    const pattern = [
        [6, 2], [3, 1], [3, 1], [3, 1], [3, 1],
        [4, 1], [4, 1], [4, 1], [5, 2], [7, 2],
        [3, 1], [3, 1], [3, 1], [3, 1],
    ];
    let [w, h] = pattern[index % pattern.length];
    if (item.type === "video" && h === 1 && index % 4 === 0) {
        w = 6;
        h = 2;
    }
    return { w, h };
}
function computeMagazinePlacements(items) {
    const occupied = [];
    const ensureRow = (row) => { while (occupied.length <= row)
        occupied.push(Array(12).fill(false)); };
    const result = [];
    items.forEach((item, index) => {
        const { w, h } = magazineSpan(index, item);
        let y = 0;
        let x = 0;
        let placed = false;
        while (!placed && y < 1000) {
            for (let row = y; row < y + h; row += 1)
                ensureRow(row);
            for (x = 0; x <= 12 - w; x += 1) {
                let free = true;
                for (let row = y; row < y + h && free; row += 1) {
                    for (let col = x; col < x + w; col += 1) {
                        if (occupied[row][col]) {
                            free = false;
                            break;
                        }
                    }
                }
                if (!free)
                    continue;
                for (let row = y; row < y + h; row += 1)
                    for (let col = x; col < x + w; col += 1)
                        occupied[row][col] = true;
                placed = true;
                break;
            }
            if (!placed)
                y += 1;
        }
        result.push({ x, y, w, h, style: { gridColumn: `${x + 1} / span ${w}`, gridRow: `${y + 1} / span ${h}` } });
    });
    return result;
}
const edicolaScrollAnimations = new WeakMap();
function animateEdicolaScrollTo(container, targetTop, duration = 520) {
    const previousFrame = edicolaScrollAnimations.get(container);
    if (previousFrame)
        window.cancelAnimationFrame(previousFrame);
    const startTop = container.scrollTop;
    const delta = targetTop - startTop;
    if (Math.abs(delta) < 2)
        return;
    const started = performance.now();
    const ease = (t) => 1 - Math.pow(1 - t, 3);
    const frame = (now) => {
        const progress = Math.min(1, Math.max(0, (now - started) / duration));
        container.scrollTop = startTop + delta * ease(progress);
        if (progress < 1) {
            const nextFrame = window.requestAnimationFrame(frame);
            edicolaScrollAnimations.set(container, nextFrame);
        }
        else {
            edicolaScrollAnimations.delete(container);
        }
    };
    const firstFrame = window.requestAnimationFrame(frame);
    edicolaScrollAnimations.set(container, firstFrame);
}
function revealMagazineCardSmooth(card, duration = 520, centerVertically = false) {
    const container = card.closest?.(".newsEdicolaScroll");
    if (!container)
        return;
    const c = container.getBoundingClientRect();
    const r = card.getBoundingClientRect();
    const margin = 22;
    let target = container.scrollTop;
    if (centerVertically) {
        const cardCenter = (r.top + r.bottom) / 2;
        const viewportCenter = (c.top + c.bottom) / 2;
        target += cardCenter - viewportCenter;
    }
    else if (r.top < c.top + margin)
        target += r.top - (c.top + margin);
    else if (r.bottom > c.bottom - margin)
        target += r.bottom - (c.bottom - margin);
    target = Math.max(0, Math.min(target, Math.max(0, container.scrollHeight - container.clientHeight)));
    animateEdicolaScrollTo(container, target, duration);
}
function animateHorizontalScrollTo(container, targetLeft, duration = 600) {
    const startLeft = container.scrollLeft;
    const delta = targetLeft - startLeft;
    if (Math.abs(delta) < 2)
        return;
    const started = performance.now();
    const ease = (t) => 1 - Math.pow(1 - t, 3);
    const frame = (now) => {
        const progress = Math.min(1, Math.max(0, (now - started) / duration));
        container.scrollLeft = startLeft + delta * ease(progress);
        if (progress < 1)
            window.requestAnimationFrame(frame);
    };
    window.requestAnimationFrame(frame);
}
function revealHorizontalTabSmooth(tab, duration = 600) {
    const container = tab.closest?.(".newsEdicolaTabs");
    if (!container)
        return;
    const c = container.getBoundingClientRect();
    const r = tab.getBoundingClientRect();
    const margin = 12;
    let target = container.scrollLeft;
    if (r.left < c.left + margin)
        target += r.left - (c.left + margin);
    else if (r.right > c.right - margin)
        target += r.right - (c.right - margin);
    target = Math.max(0, Math.min(target, Math.max(0, container.scrollWidth - container.clientWidth)));
    animateHorizontalScrollTo(container, target, duration);
}
function focusAdjacentEdicolaTab(event, direction) {
    const current = event?.currentTarget;
    if (!current)
        return;
    const tabs = Array.from(current.ownerDocument.querySelectorAll(".newsEdicolaTabs .newsTabButton"))
        .filter((entry) => entry.offsetParent !== null);
    const index = tabs.indexOf(current);
    const target = tabs[index + (direction === "right" ? 1 : -1)];
    if (!target)
        return;
    event?.preventDefault?.();
    event?.stopPropagation?.();
    playSteamBasicNavSound();
    try {
        target.focus?.({ preventScroll: true });
    }
    catch {
        target.focus?.();
    }
    revealHorizontalTabSmooth(target, 600);
}
function focusDirectionalMagazineCard(event, direction) {
    const current = event?.currentTarget;
    if (!current)
        return;
    const origin = current.getBoundingClientRect();
    const ox = (origin.left + origin.right) / 2;
    const oy = (origin.top + origin.bottom) / 2;
    const cards = Array.from(current.ownerDocument.querySelectorAll(".newsMagazineCard"))
        .filter((card) => card !== current && card.offsetParent !== null);
    let best = null;
    let bestScore = Number.POSITIVE_INFINITY;
    for (const card of cards) {
        const rect = card.getBoundingClientRect();
        const cx = (rect.left + rect.right) / 2;
        const cy = (rect.top + rect.bottom) / 2;
        const horizontal = direction === "left" || direction === "right";
        const onSide = direction === "left" ? cx < ox - 2
            : direction === "right" ? cx > ox + 2
                : direction === "up" ? cy < oy - 2
                    : cy > oy + 2;
        if (!onSide)
            continue;
        const crossOverlap = horizontal
            ? Math.max(0, Math.min(origin.bottom, rect.bottom) - Math.max(origin.top, rect.top))
            : Math.max(0, Math.min(origin.right, rect.right) - Math.max(origin.left, rect.left));
        const crossMin = horizontal ? Math.min(origin.height, rect.height) : Math.min(origin.width, rect.width);
        const inBeam = crossOverlap >= Math.max(8, crossMin * .12);
        const primaryEdgeGap = direction === "left" ? Math.max(0, origin.left - rect.right)
            : direction === "right" ? Math.max(0, rect.left - origin.right)
                : direction === "up" ? Math.max(0, origin.top - rect.bottom)
                    : Math.max(0, rect.top - origin.bottom);
        const primaryCenter = horizontal ? Math.abs(cx - ox) : Math.abs(cy - oy);
        const crossCenter = horizontal ? Math.abs(cy - oy) : Math.abs(cx - ox);
        const crossGap = horizontal
            ? Math.max(rect.top - origin.bottom, origin.top - rect.bottom, 0)
            : Math.max(rect.left - origin.right, origin.left - rect.right, 0);
        // Edicola navigation is deliberately nearest-neighbour in both axes.  Large
        // mosaic tiles may span two rows, so beam overlap wins before diagonal jumps.
        const score = (inBeam ? 0 : 1000000)
            + primaryEdgeGap * 1000
            + primaryCenter * 7
            + crossGap * 80
            + crossCenter * (inBeam ? 3 : 12)
            - crossOverlap * 2;
        if (score < bestScore) {
            bestScore = score;
            best = card;
        }
    }
    if (best) {
        event?.preventDefault?.();
        event?.stopPropagation?.();
        playSteamBasicNavSound();
        try {
            best.focus?.({ preventScroll: true });
        }
        catch {
            best.focus?.();
        }
        revealMagazineCardSmooth(best, 460);
    }
}
function MediaEmbed({ block }) {
    const iframeRef = useRef(null);
    const [playing, setPlaying] = useState(false);
    const provider = String(block.provider || "");
    const controllable = provider === "youtube" || provider === "tiktok";
    const pointerInteractive = provider === "instagram" || provider === "facebook";
    const toggle = () => {
        if (!controllable)
            return;
        const next = !playing;
        if (provider === "youtube") {
            iframeRef.current?.contentWindow?.postMessage(JSON.stringify({ event: "command", func: next ? "playVideo" : "pauseVideo", args: [] }), "*");
        }
        else if (provider === "tiktok") {
            iframeRef.current?.contentWindow?.postMessage({ type: next ? "play" : "pause", value: undefined, "x-tiktok-player": true }, "*");
        }
        setPlaying(next);
    };
    const dimensions = provider === "youtube"
        ? { maxWidth: 850, height: "auto", aspectRatio: "16/9" }
        : provider === "tiktok"
            ? { maxWidth: 430, height: 720, aspectRatio: undefined }
            : provider === "instagram"
                ? { maxWidth: 560, height: 690, aspectRatio: undefined }
                : provider === "facebook"
                    ? { maxWidth: 560, height: 650, aspectRatio: undefined }
                    : provider === "x"
                        ? { maxWidth: 640, height: 350, aspectRatio: undefined }
                        : { maxWidth: 720, height: 520, aspectRatio: undefined };
    const shell = { position: "relative", width: "100%", maxWidth: dimensions.maxWidth, height: dimensions.height, aspectRatio: dimensions.aspectRatio, margin: "30px auto", overflow: "hidden", borderRadius: 14, background: provider === "x" || provider === "instagram" || provider === "facebook" ? "#fff" : "#08090b", border: "1px solid rgba(255,255,255,.12)" };
    if (provider === "x" && block.text)
        return SP_REACT.createElement("div", { className: "newsStaticMediaEmbed newsXCard", style: { width: "100%", maxWidth: 640, margin: "30px auto", padding: "22px 24px", borderRadius: 16, background: "#fff", color: "#111", border: "1px solid rgba(0,0,0,.12)", boxShadow: "0 12px 32px rgba(0,0,0,.16)", overflow: "hidden" } },
            SP_REACT.createElement("div", { style: { display: "flex", alignItems: "center", gap: 10, marginBottom: 14 } },
                SP_REACT.createElement("strong", { style: { fontSize: 20, color: "#111" } }, "\uD835\uDD4F"),
                SP_REACT.createElement("span", { style: { fontSize: 13, fontWeight: 700, color: "#222" } }, "X")),
            SP_REACT.createElement("div", { style: { fontSize: 18, lineHeight: 1.48, color: "#171717", whiteSpace: "pre-wrap" } }, block.text));
    const frame = SP_REACT.createElement("iframe", { ref: iframeRef, src: block.embedUrl, title: block.title || provider || "Contenuto incorporato", scrolling: "no", tabIndex: -1, allow: "autoplay; encrypted-media; picture-in-picture; fullscreen", style: { position: "absolute", inset: 0, width: "100%", height: "100%", border: 0, overflow: "hidden", pointerEvents: pointerInteractive ? "auto" : "none", background: provider === "x" || provider === "instagram" || provider === "facebook" ? "#fff" : "#000" } });
    if (!controllable)
        return SP_REACT.createElement("div", { className: "newsStaticMediaEmbed", style: shell }, frame);
    return (SP_REACT.createElement(DialogButton, { className: "newsMediaEmbed", "data-news-provider": provider, onClick: toggle, style: { ...shell, display: "block", padding: 0 } },
        frame,
        !playing ? SP_REACT.createElement("span", { className: "newsMediaEmbedPlay", style: { position: "absolute", left: "50%", top: "50%", transform: "translate(-50%,-50%)", width: 78, height: 78, borderRadius: 999, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,.78)", border: "2px solid rgba(255,255,255,.92)", boxShadow: "0 12px 36px rgba(0,0,0,.38)", fontSize: 32, fontWeight: 800, color: "#fff", paddingLeft: 5 } }, "\u25B6") : null));
}
function NewspaperIcon({ size = 20 }) {
    return SP_REACT.createElement("span", { "aria-hidden": "true", style: { fontSize: size, lineHeight: 1 } }, "\u25A4");
}
function Spinner({ size = 20, thickness = 2.4 }) {
    return SP_REACT.createElement("span", { className: "newsSpinner", "aria-hidden": "true", style: { display: "inline-block", boxSizing: "border-box", width: size, height: size, borderWidth: thickness, borderStyle: "solid", borderColor: "rgba(255,255,255,.22)", borderTopColor: "currentColor", borderRightColor: "currentColor", borderRadius: 999, color: "currentColor", verticalAlign: "middle", flex: "0 0 auto", animation: "newsSpin .72s linear infinite" } });
}
function EmptyState({ title, detail }) {
    return SP_REACT.createElement("div", { style: { padding: "28px 20px", textAlign: "center", opacity: .68 } },
        SP_REACT.createElement("strong", { style: { display: "block", fontSize: 18 } }, title),
        detail ? SP_REACT.createElement("span", { style: { display: "block", marginTop: 6, fontSize: 14 } }, detail) : null);
}
function validateRenderedImage(event, minWidth = 300, minHeight = 150) {
    const image = event?.currentTarget;
    if (!image)
        return;
    if ((image.naturalWidth || 0) < minWidth || (image.naturalHeight || 0) < minHeight)
        image.style.display = "none";
}
function hashedHue(value) {
    let hash = 0;
    for (let i = 0; i < value.length; i += 1)
        hash = (hash * 31 + value.charCodeAt(i)) >>> 0;
    return hash % 360;
}
function sourceLabelIdentity(source, url = "") {
    const host = (() => {
        try {
            return new URL(url).hostname.replace(/^www\./, "");
        }
        catch {
            return "";
        }
    })();
    const base = source || host || "News";
    const words = base.replace(/\.[a-z]{2,}$/i, "").split(/[^A-Za-zÀ-ÿ0-9]+/).filter(Boolean);
    const initials = (words[0]?.[0] || "N") + (words[1]?.[0] || words[0]?.[1] || "");
    const hue = hashedHue(host || base.toLowerCase());
    return { host, base, initials: initials.toUpperCase().slice(0, 2), hue };
}
function SourcePlaceholder({ source, url = "", compact = false, logo = "", favicon = "", color = "", preferFavicon = false }) {
    const identity = sourceLabelIdentity(source, url);
    // Article Reader placeholders must prefer the real publisher favicon. The old
    // non-compact path preferred logoUrl first, which is the bundled emergency
    // fallback and produced the odd "fallback inside a fallback" composition when
    // an article image was missing. Cards keep their existing behaviour.
    const brandImage = preferFavicon ? (favicon || logo) : (compact ? (favicon || logo) : (logo || favicon));
    // In the opened Reader the source mark is intentionally the raw publisher PNG:
    // no white tile, clipping, shadow or Google-wrapper styling around it. A Google
    // transport URL must never make an Il Post/Fanpage/etc. favicon look like a
    // nested app icon. Cards keep their established source-brand treatment.
    const rawReaderFavicon = preferFavicon && !!brandImage;
    const googleBrand = !rawReaderFavicon && (/google news|notizie principali/i.test(source) || (!String(source || "").trim() && /news\.google\./i.test(url)));
    const background = color
        ? `linear-gradient(135deg, ${color}, rgba(12,13,16,.96))`
        : `linear-gradient(135deg, hsla(${identity.hue},62%,47%,.96), hsla(${(identity.hue + 42) % 360},62%,29%,.98))`;
    return (SP_REACT.createElement("div", { className: "newsSourceFallback", style: { width: "100%", height: "100%", position: "relative", display: "flex", alignItems: "flex-start", justifyContent: "flex-start", padding: compact ? 5 : 14, background, color: "#fff" } },
        SP_REACT.createElement("div", { style: { width: compact ? 40 : 54, height: compact ? 40 : 54, borderRadius: rawReaderFavicon ? 0 : (googleBrand ? (compact ? 10 : 14) : 0), display: "flex", alignItems: "center", justifyContent: "center", overflow: rawReaderFavicon ? "visible" : "hidden", background: rawReaderFavicon ? "transparent" : (googleBrand ? "rgba(255,255,255,.97)" : "transparent"), boxShadow: rawReaderFavicon ? "none" : (googleBrand ? "0 8px 26px rgba(0,0,0,.20)" : "none"), flexShrink: 0 } },
            brandImage ? SP_REACT.createElement("img", { src: brandImage, alt: "", style: { width: rawReaderFavicon ? "100%" : (googleBrand ? "82%" : "100%"), height: rawReaderFavicon ? "100%" : (googleBrand ? "82%" : "100%"), objectFit: "contain", imageRendering: "auto", borderRadius: 0, background: "transparent", boxShadow: "none" }, onError: (event) => { const image = event.currentTarget; const backup = brandImage === favicon && logo && favicon !== logo ? logo : (brandImage === logo && favicon && logo !== favicon ? favicon : ""); if (backup && image.dataset.newsFallback !== "1") {
                    image.dataset.newsFallback = "1";
                    image.src = backup;
                    return;
                } image.style.display = "none"; const sibling = image.nextElementSibling; if (sibling)
                    sibling.style.display = "flex"; } }) : null,
            SP_REACT.createElement("span", { style: { display: brandImage ? "none" : "flex", color: "#1a1b1f", fontSize: compact ? 16 : 20, fontWeight: 850, lineHeight: 1 } }, identity.initials))));
}
function NewsImage({ src, alt = "", source = "", url = "", logo = "", favicon = "", color = "", objectFit = "cover", objectPosition = "center center", style = {}, minWidth = 300, minHeight = 150, fallbackCompact = false, preferFaviconFallback = false, cacheOnError = false, referer = "", blankWhenMissing = false, hideLoader = false, showFallbackWhileLoading = false, priority = false, eager = false }) {
    const [displaySrc, setDisplaySrc] = useState(src || "");
    const [state, setState] = useState(src ? "loading" : "error");
    const recoveryAttempted = useRef("");
    const lastGoodSrc = useRef(String(src || ""));
    useEffect(() => {
        const incoming = String(src || "").trim();
        recoveryAttempted.current = "";
        if (incoming) {
            if (incoming !== displaySrc) {
                setDisplaySrc(incoming);
                setState("loading");
            }
            else if (state === "error") {
                setState("loading");
            }
            return;
        }
        if (!displaySrc && !lastGoodSrc.current)
            setState("error");
    }, [src]);
    const fail = () => {
        const remote = String(displaySrc || "");
        const fallback = String(lastGoodSrc.current || "");
        if (cacheOnError && remote.startsWith("http") && recoveryAttempted.current !== remote) {
            recoveryAttempted.current = remote;
            void rpc("cache_image", remote, referer || url).then((result) => {
                const local = String(result?.url || "");
                if (local && local !== remote) {
                    setDisplaySrc(local);
                    setState("loading");
                }
                else if (fallback && fallback !== remote) {
                    setDisplaySrc(fallback);
                    setState("ready");
                }
                else {
                    lastGoodSrc.current = "";
                    setDisplaySrc("");
                    setState("error");
                }
            }).catch(() => {
                if (fallback && fallback !== remote) {
                    setDisplaySrc(fallback);
                    setState("ready");
                }
                else {
                    lastGoodSrc.current = "";
                    setDisplaySrc("");
                    setState("error");
                }
            });
            return;
        }
        if (fallback && fallback !== remote) {
            setDisplaySrc(fallback);
            setState("ready");
        }
        else {
            lastGoodSrc.current = "";
            setDisplaySrc("");
            setState("error");
        }
    };
    return (SP_REACT.createElement("div", { className: "newsImage", style: { position: "relative", width: "100%", height: "100%", overflow: "hidden", background: "rgba(255,255,255,.035)", ...style } },
        ((state === "error" || !displaySrc || (showFallbackWhileLoading && state === "loading")) && !blankWhenMissing) ? SP_REACT.createElement("div", { style: { position: "absolute", inset: 0, zIndex: 0 } },
            SP_REACT.createElement(SourcePlaceholder, { source: source, url: url, logo: logo, favicon: favicon, color: color, compact: fallbackCompact, preferFavicon: preferFaviconFallback })) : null,
        displaySrc ? SP_REACT.createElement("img", { src: displaySrc, alt: alt, loading: priority || eager ? "eager" : "lazy", fetchPriority: priority ? "high" : eager ? "low" : "auto", decoding: "async", onLoad: (event) => { const image = event?.currentTarget; if (!image || (image.naturalWidth || 0) < minWidth || (image.naturalHeight || 0) < minHeight)
                fail();
            else {
                lastGoodSrc.current = displaySrc;
                setState("ready");
            } }, onError: fail, style: { position: "absolute", inset: 0, zIndex: 1, width: "100%", height: "100%", objectFit, objectPosition, opacity: state === "ready" ? 1 : 0, transition: "opacity 120ms ease" } }) : null,
        state === "loading" && displaySrc && !hideLoader ? SP_REACT.createElement("div", { className: "newsImageLoader", style: { position: "absolute", inset: 0, zIndex: 2, display: "flex", alignItems: "center", justifyContent: "center", pointerEvents: "none" } },
            SP_REACT.createElement("span", { style: { display: "flex", width: 42, height: 42, alignItems: "center", justifyContent: "center", borderRadius: 999, background: "rgba(9,10,12,.74)", boxShadow: "0 8px 28px rgba(0,0,0,.30)", color: "rgba(255,255,255,.94)" } },
                SP_REACT.createElement(Spinner, { size: 24, thickness: 2.2 }))) : null));
}
function ArticleHeroImage({ primary, fallback, source, url, logo, favicon, color }) {
    // The card cover is the canonical visual for the opened article. The backend
    // Reader may discover another image while parsing complex publisher markup; use
    // that only when the card had no cover, never replace a known-good card image.
    const candidate = String(primary || fallback || "");
    return SP_REACT.createElement("div", { style: { position: "absolute", inset: 0, overflow: "hidden", background: "#111216" } },
        SP_REACT.createElement(NewsImage, { src: candidate, alt: "", source: source || "", url: url || "", logo: logo || "", favicon: favicon || "", color: color || "", objectFit: "cover", objectPosition: "center top", style: { position: "absolute", inset: 0, width: "100%", height: "100%" }, minWidth: 640, minHeight: 280, priority: true, eager: true, preferFaviconFallback: true, cacheOnError: true, referer: url || "" }));
}
function CountryDropdown({ countries, value, onChange, label = tr("country") }) {
    const [open, setOpen] = useState(false);
    const selected = countries.find((entry) => entry.code === value) ?? countries[0];
    const buttonRef = useRef(null);
    const [menuRect, setMenuRect] = useState(null);
    useLayoutEffect(() => {
        if (!open)
            return;
        const update = () => {
            const rect = buttonRef.current?.getBoundingClientRect();
            if (!rect)
                return;
            const top = rect.bottom + 6;
            const maxHeight = Math.max(260, Math.min(620, window.innerHeight - top - 18));
            setMenuRect({ left: rect.left, top, width: rect.width, maxHeight });
        };
        update();
        window.addEventListener("resize", update);
        window.addEventListener("scroll", update, true);
        return () => { window.removeEventListener("resize", update); window.removeEventListener("scroll", update, true); };
    }, [open]);
    return SP_REACT.createElement("div", { className: "newsCountryDropdown", style: { position: "relative", width: "100%", minWidth: 0, zIndex: open ? 6000 : 1, overflow: "visible" } },
        SP_REACT.createElement("span", { style: { display: "block", height: 18, margin: "0 0 4px 2px", fontSize: 12, opacity: .62, lineHeight: "18px" } }, label),
        SP_REACT.createElement(DialogButton, { ref: buttonRef, className: "newsCountryDropdownButton", style: { ...baseButton, width: "100%", height: 48, minHeight: 48, borderRadius: 10, textAlign: "left", background: "rgba(255,255,255,.055)", border: "1px solid rgba(255,255,255,.12)" }, onClick: () => setOpen(v => !v) },
            SP_REACT.createElement("span", { style: { display: "flex", width: "100%", alignItems: "center", justifyContent: "space-between", gap: 12 } },
                SP_REACT.createElement("strong", { style: { display: "block", minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" } }, countryName(selected) || value),
                SP_REACT.createElement("span", { style: { opacity: .7, fontSize: 14 } }, open ? "▲" : "▼"))),
        open && menuRect ? SP_REACT.createElement(Focusable, { className: "newsCountryDropdownMenu", "flow-children": "vertical", onCancel: () => setOpen(false), onCancelButton: () => setOpen(false), style: { position: "fixed", top: menuRect.top, left: menuRect.left, width: menuRect.width, maxHeight: menuRect.maxHeight, overflowY: "auto", overflowX: "hidden", padding: 8, borderRadius: 12, background: "rgba(17,18,22,.995)", border: "1px solid rgba(255,255,255,.18)", boxShadow: "0 28px 80px rgba(0,0,0,.68)", zIndex: 6500 } }, countries.map(entry => SP_REACT.createElement(DialogButton, { key: entry.code, className: "newsCountryOption", style: { ...baseButton, width: "100%", minWidth: 0, height: 44, minHeight: 44, marginBottom: 4, borderRadius: 9, textAlign: "left", background: entry.code === value ? "rgba(255,255,255,.13)" : "rgba(255,255,255,.035)" }, onFocus: (event) => event?.currentTarget?.scrollIntoView?.({ block: "nearest", behavior: "smooth" }), onClick: () => { onChange(entry.code); setOpen(false); } },
            SP_REACT.createElement("span", { style: { display: "flex", width: "100%", justifyContent: "space-between", gap: 10 } },
                SP_REACT.createElement("span", { style: { overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" } }, countryName(entry)),
                SP_REACT.createElement("span", { style: { opacity: .45 } }, entry.code))))) : null);
}
function NewsTextField({ label = "", style = {}, ...props }) {
    // Keep the native Decky TextField intact. Now Playing's Big Picture search
    // relies on the same controlled value/onChange shape; wrapping/re-styling the
    // internal input is what made virtual-keyboard text invisible in older builds.
    return SP_REACT.createElement("div", { className: "newsTextFieldHost", style: { width: "100%", minWidth: 0, ...style } },
        SP_REACT.createElement(TextField, { ...props, label: label, style: { width: "100%", minWidth: "100%" } }));
}
function FieldActionRow({ children, columns = "minmax(0,1fr) 160px", style = {} }) {
    return SP_REACT.createElement(Focusable, { className: "newsFieldActionRow", "flow-children": "horizontal", style: { display: "grid", gridTemplateColumns: columns, gap: 10, alignItems: "start", width: "100%", minWidth: 0, ...style } }, children);
}
function FieldActionButton({ children, ...props }) {
    return SP_REACT.createElement("div", { className: "newsFieldActionButtonHost", style: { display: "flex", flexDirection: "column", minWidth: 0, paddingTop: 22 } },
        SP_REACT.createElement(DialogButton, { ...props, style: { ...baseButton, height: 48, minHeight: 48, width: "100%", minWidth: 0, ...(props.style || {}) } }, children));
}
function useForcedWheelScroll(ref) {
    useEffect(() => {
        const target = ref.current;
        if (!target)
            return;
        const doc = target.ownerDocument;
        let desired = target.scrollTop;
        let frame = 0;
        let animating = false;
        const clamp = (value) => Math.max(0, Math.min(value, Math.max(0, target.scrollHeight - target.clientHeight)));
        const tick = () => {
            frame = 0;
            const diff = desired - target.scrollTop;
            if (Math.abs(diff) < .45) {
                target.scrollTop = desired;
                animating = false;
                return;
            }
            target.scrollTop += diff * .34;
            frame = window.requestAnimationFrame(tick);
        };
        const handler = (event) => {
            const node = event.target;
            if (node?.closest?.(".newsCountryDropdownMenu"))
                return;
            if (!target.contains(node) || Math.abs(event.deltaY) < 1)
                return;
            event.preventDefault();
            event.stopPropagation();
            if (!animating)
                desired = target.scrollTop;
            desired = clamp(desired + event.deltaY);
            animating = true;
            if (!frame)
                frame = window.requestAnimationFrame(tick);
        };
        const sync = () => { if (!animating)
            desired = target.scrollTop; };
        doc.addEventListener("wheel", handler, { capture: true, passive: false });
        target.addEventListener("scroll", sync, { passive: true });
        return () => {
            doc.removeEventListener("wheel", handler, true);
            target.removeEventListener("scroll", sync);
            if (frame)
                window.cancelAnimationFrame(frame);
        };
    }, [ref]);
}
function NewsQamCard({ item }) {
    const identity = sourceLabelIdentity(item.source, item.sourceSiteUrl || item.url);
    const googleBrand = /google news|notizie principali/i.test(item.source) || /news\.google\./i.test(item.sourceSiteUrl || "");
    return SP_REACT.createElement(DialogButton, { onClick: () => openArticle(item), style: { width: "100%", minHeight: 64, height: 64, padding: "6px 8px", marginBottom: 6, borderRadius: 9 } },
        SP_REACT.createElement("span", { style: { display: "grid", gridTemplateColumns: isMetadataOnly(item) ? "minmax(0,1fr)" : "52px minmax(0,1fr)", gap: 9, width: "100%", alignItems: "center", textAlign: "left" } },
            !isMetadataOnly(item) ? SP_REACT.createElement("span", { style: { width: 52, height: 52, borderRadius: googleBrand ? 9 : 0, overflow: "hidden", background: googleBrand ? "rgba(255,255,255,.92)" : "transparent", display: "flex", alignItems: "center", justifyContent: "center" } },
                item.sourceFavicon ? SP_REACT.createElement("img", { src: item.sourceFavicon, alt: "", style: { width: googleBrand ? 40 : 52, height: googleBrand ? 40 : 52, objectFit: "contain", imageRendering: "auto" }, onError: (e) => { const image = e.currentTarget; const backup = String(item.sourceLogo || ""); if (backup && backup !== item.sourceFavicon && image.dataset.newsFallback !== "1") {
                        image.dataset.newsFallback = "1";
                        image.src = backup;
                        return;
                    } image.style.display = "none"; const n = image.nextElementSibling; if (n)
                        n.style.display = "flex"; } }) : null,
                SP_REACT.createElement("span", { style: { display: item.sourceFavicon ? "none" : "flex", color: "#17181b", fontWeight: 850, fontSize: 16 } }, identity.initials)) : null,
            SP_REACT.createElement("span", { style: { minWidth: 0 } },
                SP_REACT.createElement("strong", { style: { display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden", fontSize: 13.5, lineHeight: 1.15 } }, item.title),
                SP_REACT.createElement("span", { style: { display: "block", marginTop: 4, fontSize: 10.5, opacity: .58, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" } },
                    item.source,
                    item.published ? ` · ${formatAge(item.published)}` : "",
                    item.type === "video" ? ` · ${tr("video")}` : ""))));
}
function tabSourceIds(config, tab) {
    if (!config)
        return [];
    const enabled = config.sources.filter((source) => source.enabled !== false).map((source) => source.id);
    if (!tab)
        return enabled;
    return (tab.sourceIds ?? []).filter((id) => enabled.includes(id));
}
function QamContent() {
    const { bootstrap, error, reload } = useBootstrap();
    const config = bootstrap?.config;
    const tabs = (config?.tabs ?? []).filter((tab) => tab.enabled !== false);
    const [activeTabId, setActiveTabId] = useState(() => config?.activeTabId || "");
    useEffect(() => {
        if (!config)
            return;
        const preferred = tabs.some((tab) => tab.id === config.activeTabId) ? config.activeTabId : tabs[0]?.id ?? "";
        setActiveTabId((current) => tabs.some((tab) => tab.id === current) ? current : preferred);
    }, [config?.activeTabId, config?.tabs]);
    const activeIndex = Math.max(0, tabs.findIndex((tab) => tab.id === activeTabId));
    const activeTab = tabs[activeIndex] ?? tabs[0];
    const activeSourceIds = tabSourceIds(config, activeTab);
    const { items, loading, load } = useNews(config?.onboardingComplete ? activeTab?.id ?? "" : "", 30, activeSourceIds, false, Boolean(config?.onboardingComplete && activeTab?.id));
    useEffect(() => {
        if (!config?.onboardingComplete || !tabs.length || !activeTab?.id)
            return;
        // Warm EVERY enabled tab together. Backend source single-flight guarantees a
        // publisher feed is not downloaded twice if the visible tab is loading too.
        const timer = window.setTimeout(() => void prefetchNewsTabs(tabs, activeTab.id, 120), 100);
        return () => window.clearTimeout(timer);
    }, [config?.onboardingComplete, tabs.map((tab) => `${tab.id}:${tab.category || ""}:${tab.enabled !== false}:${(tab.sourceIds || []).join(",")}`).join("|"), activeTab?.id]);
    const [refreshing, setRefreshing] = useState(false);
    const refreshCurrentTab = useCallback(async () => {
        if (!config || refreshing || !activeTab?.id)
            return;
        setRefreshing(true);
        try {
            // Manual refresh is deliberately scoped to the tab the user is looking at.
            // Hidden tabs keep their own cached state and are not force-refetched.
            await load(true);
        }
        finally {
            setRefreshing(false);
        }
    }, [config, load, refreshing, activeTab?.id]);
    const changeTab = (step) => {
        if (!config || !tabs.length)
            return;
        const index = (activeIndex + step + tabs.length) % tabs.length;
        const nextId = tabs[index].id;
        setActiveTabId(nextId);
        void saveConfigSilent({ ...config, activeTabId: nextId }).catch((error) => console.warn("[News] Could not save active tab", error));
    };
    if (!bootstrap) {
        if (error) {
            return (SP_REACT.createElement(PanelSection, null,
                SP_REACT.createElement(PanelSectionRow, null,
                    SP_REACT.createElement("div", { style: { width: "100%", padding: "10px 0 12px", textAlign: "center" } },
                        SP_REACT.createElement("strong", { style: { display: "block", fontSize: 16 } }, "News"),
                        SP_REACT.createElement("span", { style: { display: "block", margin: "7px 10px 12px", opacity: .62, fontSize: 11.5, lineHeight: 1.35 } }, error),
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: "100%" }, onClick: () => void reload() }, tr("retry"))))));
        }
        return SP_REACT.createElement(PanelSection, null,
            SP_REACT.createElement(PanelSectionRow, null,
                SP_REACT.createElement("div", { style: { padding: 14, textAlign: "center" } },
                    SP_REACT.createElement(Spinner, null),
                    " ",
                    tr("loading"))));
    }
    if (!config?.onboardingComplete) {
        return (SP_REACT.createElement(PanelSection, null,
            SP_REACT.createElement(PanelSectionRow, null,
                SP_REACT.createElement("div", { style: { width: "100%", padding: "8px 0 12px", textAlign: "center" } },
                    SP_REACT.createElement("div", { style: { fontSize: 34, marginBottom: 8 } }, "\u25A4"),
                    SP_REACT.createElement("strong", { style: { display: "block", fontSize: 18 } }, tr("personalKiosk")),
                    SP_REACT.createElement("span", { style: { display: "block", margin: "6px 14px 14px", opacity: .65, fontSize: 12.5, lineHeight: 1.35 } }, tr("personalKioskDetail")),
                    SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: "100%" }, onClick: () => navigate(ONBOARDING_ROUTE) }, tr("configure"))))));
    }
    return (SP_REACT.createElement(PanelSection, null,
        SP_REACT.createElement(PanelSectionRow, null,
            SP_REACT.createElement(Focusable, { "flow-children": "vertical", style: { width: "100%" } },
                SP_REACT.createElement("style", null, `
            @keyframes newsSpin { to { transform: rotate(360deg); } }
            .newsQamAction, .newsQamAction * { color:#fff!important; }
            .newsQamAction:hover, .newsQamAction:focus, .newsQamAction.gpfocus { background:#f5f5f5!important; color:#151619!important; border-color:#f5f5f5!important; box-shadow:0 0 0 2px rgba(255,255,255,.22)!important; }
            .newsQamAction:hover *, .newsQamAction:focus *, .newsQamAction.gpfocus * { color:#151619!important; }
          `),
                SP_REACT.createElement(DialogButton, { className: "newsQamAction", style: { ...baseButton, width: "100%", marginBottom: 8, fontWeight: 700 }, onClick: () => navigate(EDICOLA_ROUTE) },
                    SP_REACT.createElement("span", { style: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 } },
                        SP_REACT.createElement("span", { style: { fontSize: 18 } }, "\u25A4"),
                        SP_REACT.createElement("span", null, tr("openKiosk")))),
                tabs.length > 1 ? (SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "grid", gridTemplateColumns: "52px minmax(0,1fr) 52px", gap: 6, width: "100%", marginBottom: 8, alignItems: "stretch" } },
                    SP_REACT.createElement(DialogButton, { className: "newsQamAction", style: { ...baseButton, width: 52, minWidth: 52, padding: 0, fontSize: 22 }, onClick: () => changeTab(-1) }, "\u2039"),
                    SP_REACT.createElement("div", { style: { minWidth: 0, height: 44, display: "flex", alignItems: "center", justifyContent: "center", padding: "0 10px", borderRadius: 10, background: "rgba(255,255,255,.045)", fontSize: 14, fontWeight: 700, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" } }, displayTabName(activeTab)),
                    SP_REACT.createElement(DialogButton, { className: "newsQamAction", style: { ...baseButton, width: 52, minWidth: 52, padding: 0, fontSize: 22 }, onClick: () => changeTab(1) }, "\u203A"))) : SP_REACT.createElement("div", { style: { margin: "2px 4px 9px", fontSize: 12, fontWeight: 700, opacity: .6 } }, displayTabName(activeTab)),
                SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginBottom: 8 } },
                    SP_REACT.createElement(DialogButton, { className: "newsQamAction", style: { ...baseButton, minWidth: 0 }, onClick: () => void refreshCurrentTab() },
                        SP_REACT.createElement("span", { style: { display: "flex", alignItems: "center", justifyContent: "center" } }, refreshing ? SP_REACT.createElement(Spinner, { size: 19, thickness: 2.2 }) : SP_REACT.createElement("span", { style: { fontSize: 20, lineHeight: 1 } }, "\u21BB"))),
                    SP_REACT.createElement(DialogButton, { className: "newsQamAction", style: { ...baseButton, minWidth: 0 }, onClick: () => navigate(SETTINGS_ROUTE) },
                        SP_REACT.createElement("span", { style: { fontSize: 18 } }, "\u2699"))),
                loading && !items.length ? SP_REACT.createElement("div", { style: { padding: 16, textAlign: "center", opacity: .65 } },
                    SP_REACT.createElement(Spinner, null),
                    " ",
                    tr("updating")) : null,
                items.slice(0, 30).map((item) => SP_REACT.createElement(NewsQamCard, { key: item.id, item: item })),
                !loading && !items.length ? SP_REACT.createElement(EmptyState, { title: tr("noNews"), detail: tabs.length ? tr("noNewsDetail") : tr("noActiveTab") }) : null))));
}
const ArticleCard = memo(function ArticleCard({ item, index, placement }) {
    const large = placement.h > 1 || placement.w >= 6;
    if (item.loadingPlaceholder)
        return SP_REACT.createElement("div", { className: "newsMagazinePlaceholder", "aria-hidden": "true", style: { ...placement.style, position: "relative", minWidth: 0, minHeight: 0, height: "100%", borderRadius: 12, background: "rgba(255,255,255,.018)", border: "1px solid rgba(255,255,255,.025)", display: "flex", alignItems: "center", justifyContent: "center" } },
            SP_REACT.createElement("span", { style: { display: "flex", width: 42, height: 42, alignItems: "center", justifyContent: "center", borderRadius: 999, background: "rgba(9,10,12,.74)", boxShadow: "0 8px 28px rgba(0,0,0,.30)", color: "rgba(255,255,255,.94)" } },
                SP_REACT.createElement(Spinner, { size: 24, thickness: 2.2 })));
    return (SP_REACT.createElement(DialogButton, { className: "newsMagazineCard", "data-news-x": placement.x, "data-news-y": placement.y, "data-news-w": placement.w, "data-news-h": placement.h, style: { ...placement.style, position: "relative", minWidth: 0, minHeight: 0, height: "100%", padding: 0, overflow: "hidden", borderRadius: 12, background: "rgba(255,255,255,.055)" }, onButtonDown: (event) => {
            const button = event?.detail?.button;
            if (button === GamepadButton.DIR_LEFT)
                focusDirectionalMagazineCard(event, "left");
            else if (button === GamepadButton.DIR_RIGHT)
                focusDirectionalMagazineCard(event, "right");
            else if (button === GamepadButton.DIR_UP)
                focusDirectionalMagazineCard(event, "up");
            else if (button === GamepadButton.DIR_DOWN)
                focusDirectionalMagazineCard(event, "down");
        }, onClick: () => openArticle(item) },
        !isMetadataOnly(item) ? SP_REACT.createElement(NewsImage, { src: item.image, source: item.source, url: item.sourceSiteUrl || item.url, logo: item.sourceLogo, favicon: item.sourceFavicon, color: item.sourceColor, objectFit: "cover", objectPosition: "center top", style: { position: "absolute", inset: 0, zIndex: 0 }, minWidth: 320, minHeight: 160, fallbackCompact: true, showFallbackWhileLoading: true, cacheOnError: true, referer: item.resolvedUrl || item.url, priority: index < 16, eager: true }) : null,
        SP_REACT.createElement("span", { style: { position: "absolute", inset: 0, zIndex: 2, display: "block", pointerEvents: "none", background: "linear-gradient(to top, rgba(4,5,8,.98) 0%, rgba(4,5,8,.76) 35%, rgba(4,5,8,.10) 77%)" } }),
        item.type === "video" ? SP_REACT.createElement("span", { style: { position: "absolute", zIndex: 4, top: 12, right: 12, width: 30, height: 30, display: "flex", alignItems: "center", justifyContent: "center", borderRadius: 999, background: "rgba(0,0,0,.72)", fontSize: 14 } }, "\u25B6") : null,
        SP_REACT.createElement("span", { style: { position: "absolute", zIndex: 3, left: large ? 18 : 12, right: large ? 18 : 12, bottom: large ? 16 : 11, textAlign: "left", pointerEvents: "none" } },
            SP_REACT.createElement("strong", { style: { display: "-webkit-box", WebkitLineClamp: large ? 3 : 2, WebkitBoxOrient: "vertical", overflow: "hidden", fontSize: large ? 24 : 16, lineHeight: 1.14, paddingBottom: ".10em", letterSpacing: "-.018em", color: "#fff", textShadow: "0 2px 12px rgba(0,0,0,.70)" } }, item.title),
            isMetadataOnly(item) && item.excerpt ? SP_REACT.createElement("span", { style: { display: "-webkit-box", WebkitLineClamp: large ? 4 : 2, WebkitBoxOrient: "vertical", overflow: "hidden", marginTop: 12, fontSize: large ? 17 : 13, lineHeight: 1.45, color: "rgba(255,255,255,.78)" } }, item.excerpt) : null,
            SP_REACT.createElement("span", { style: { display: "block", marginTop: 6, fontSize: large ? 12 : 10.5, color: "rgba(255,255,255,.76)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" } },
                item.source,
                item.published ? ` · ${formatAge(item.published)}` : ""))));
}, (previous, next) => previous.item === next.item
    && previous.index === next.index
    && previous.placement.x === next.placement.x
    && previous.placement.y === next.placement.y
    && previous.placement.w === next.placement.w
    && previous.placement.h === next.placement.h);
function firstVisibleNewsFocusable(root) {
    const selector = 'button:not([disabled]),input:not([disabled]),textarea:not([disabled]),select:not([disabled]),[role="button"],[tabindex]:not([tabindex="-1"])';
    return Array.from(root.querySelectorAll(selector)).find((element) => element.offsetParent !== null && getComputedStyle(element).visibility !== "hidden") ?? null;
}
function useFullscreenFocusContainment(rootRef) {
    useLayoutEffect(() => {
        const root = rootRef.current;
        if (!root)
            return;
        const doc = root.ownerDocument;
        let lastInside = null;
        let restoring = false;
        let disposed = false;
        let focusFrame = 0;
        const owner = doc.defaultView ?? window;
        const focusFallback = () => {
            if (restoring || disposed)
                return;
            restoring = true;
            focusFrame = owner.requestAnimationFrame(() => {
                if (disposed || !root.isConnected)
                    return;
                const fallback = lastInside && root.contains(lastInside) && lastInside.offsetParent !== null ? lastInside : firstVisibleNewsFocusable(root);
                fallback?.focus?.();
                restoring = false;
            });
        };
        const onFocusIn = (event) => {
            const target = event.target;
            if (!target)
                return;
            if (root.contains(target)) {
                lastInside = target;
                return;
            }
            if (isVirtualKeyboardElement(target))
                return;
            focusFallback();
        };
        doc.addEventListener("focusin", onFocusIn, true);
        const timer = window.setTimeout(() => {
            const active = doc.activeElement;
            if (!active || (!root.contains(active) && !isVirtualKeyboardElement(active)))
                focusFallback();
        }, 60);
        return () => {
            disposed = true;
            owner.cancelAnimationFrame(focusFrame);
            window.clearTimeout(timer);
            doc.removeEventListener("focusin", onFocusIn, true);
        };
    }, []);
}
function FullscreenShell({ children, className = "", style = {} }) {
    useFullscreenChrome();
    const rootRef = useRef(null);
    useFullscreenFocusContainment(rootRef);
    return (SP_REACT.createElement("div", { ref: rootRef, className: `newsFullscreenRoot ${className}`, style: { position: "fixed", inset: 0, width: "100vw", height: "100vh", zIndex: 10, background: "radial-gradient(circle at 50% -20%,#303238 0%,#1e2024 36%,#121316 100%)", color: "#f5f5f5", overflow: "hidden", fontFamily: "inherit", ...style } },
        children,
        SP_REACT.createElement("style", null, `
        @keyframes newsSpin { to { transform: rotate(360deg); } }
        @keyframes newsTabPulse { from { box-shadow:0 0 0 1px rgba(255,255,255,.18),0 0 12px rgba(255,255,255,.05); } to { box-shadow:0 0 0 2px rgba(255,255,255,.48),0 0 28px rgba(255,255,255,.18); } }
        .newsSpinner { display:inline-block; box-sizing:border-box; border-style:solid; border-color:rgba(255,255,255,.24); border-top-color:currentColor; border-right-color:currentColor; border-radius:999px; vertical-align:middle; flex:0 0 auto; animation:newsSpin .72s linear infinite; }
        .newsFullscreenRoot, .newsFullscreenRoot * { box-sizing:border-box; }
        .newsTextFieldHost { position:relative; z-index:1; overflow:visible; }
        .newsFieldActionRow { overflow:visible; }

        .newsFullscreenRoot button, .newsFullscreenRoot button *, .newsFullscreenRoot [role="button"], .newsFullscreenRoot [role="button"] * { color:#fff!important; }
        .newsFullscreenRoot button { transition:background 120ms ease,border-color 120ms ease,box-shadow 120ms ease,opacity 120ms ease,color 120ms ease!important; }
        .newsFullscreenRoot button:not(.newsMagazineCard):not(.newsMediaEmbed):hover, .newsFullscreenRoot button:not(.newsMagazineCard):not(.newsMediaEmbed):focus, .newsFullscreenRoot button:not(.newsMagazineCard):not(.newsMediaEmbed).gpfocus { color:#111216!important; background:rgba(255,255,255,.96)!important; border-color:rgba(255,255,255,.96)!important; box-shadow:0 0 0 2px rgba(255,255,255,.22),0 0 26px rgba(255,255,255,.14)!important; }
        .newsFullscreenRoot button:not(.newsMagazineCard):not(.newsMediaEmbed):focus *, .newsFullscreenRoot button:not(.newsMagazineCard):not(.newsMediaEmbed).gpfocus *, .newsFullscreenRoot button:not(.newsMagazineCard):not(.newsMediaEmbed):hover * { color:#111216!important; }
        .newsMediaEmbed:hover, .newsMediaEmbed:focus, .newsMediaEmbed.gpfocus { outline:3px solid rgba(255,255,255,.95)!important; outline-offset:3px; box-shadow:0 18px 48px rgba(0,0,0,.38)!important; transform:none!important; }
        .newsMediaEmbed:hover *, .newsMediaEmbed:focus *, .newsMediaEmbed.gpfocus * { color:#fff!important; }
        .newsMagazineCard { transition:transform 150ms cubic-bezier(.2,.8,.2,1),box-shadow 150ms ease,outline-color 120ms ease!important; }
        .newsMagazineCard:hover, .newsMagazineCard:focus, .newsMagazineCard.gpfocus { outline:3px solid rgba(255,255,255,.96)!important; outline-offset:3px; transform:scale(1.012); z-index:5; box-shadow:0 15px 42px rgba(0,0,0,.36)!important; }
        .newsMagazineCard:hover *, .newsMagazineCard:focus *, .newsMagazineCard.gpfocus * { color:#fff!important; }
        .newsTabButton, .newsTabButton * { color:#fff!important; }
        .newsTabButton { border:1px solid rgba(255,255,255,.08)!important; background:rgba(255,255,255,.025)!important; }
        .newsTabButton:hover, .newsTabButton:focus, .newsTabButton.gpfocus { opacity:1!important; background:rgba(255,255,255,.96)!important; border-color:rgba(255,255,255,.96)!important; box-shadow:0 0 0 2px rgba(255,255,255,.22),0 0 26px rgba(255,255,255,.13)!important; transform:none!important; }
        .newsTabButton:hover *, .newsTabButton:focus *, .newsTabButton.gpfocus * { color:#111216!important; }
        .newsTabButton.newsTabActive { opacity:1!important; background:rgba(255,255,255,.10)!important; border-color:rgba(255,255,255,.24)!important; }
        .newsTabButton.newsTabActive:focus, .newsTabButton.newsTabActive.gpfocus { animation:newsTabPulse .75s ease-in-out alternate infinite; }
        .newsCountryDropdownButton:focus, .newsCountryDropdownButton.gpfocus, .newsCountryOption:focus, .newsCountryOption.gpfocus { box-shadow:0 0 0 2px rgba(255,255,255,.38),0 0 22px rgba(255,255,255,.10)!important; }
        .newsSettingsScroll::-webkit-scrollbar,.newsOnboardingScroll::-webkit-scrollbar{width:8px}.newsSettingsScroll::-webkit-scrollbar-thumb,.newsOnboardingScroll::-webkit-scrollbar-thumb{background:rgba(255,255,255,.18);border-radius:999px}
        .newsReaderScroll::-webkit-scrollbar, .newsEdicolaScroll::-webkit-scrollbar, .newsCountryDropdown [style*="overflow-y"]::-webkit-scrollbar { width:8px; }
        .newsReaderScroll::-webkit-scrollbar-thumb, .newsEdicolaScroll::-webkit-scrollbar-thumb, .newsCountryDropdown [style*="overflow-y"]::-webkit-scrollbar-thumb { background:rgba(255,255,255,.18); border-radius:20px; }
        body > [class*="virtualkeyboard"], body > [class*="VirtualKeyboard"], body [class*="virtualkeyboard_Keyboard"], body [class*="VirtualKeyboard_Keyboard"] { z-index:2147483647!important; visibility:visible!important; opacity:1!important; pointer-events:auto!important; }
      `)));
}
function EdicolaRoute() {
    const { bootstrap } = useBootstrap();
    const config = bootstrap?.config;
    const tabs = (config?.tabs ?? []).filter((tab) => tab.enabled !== false);
    const [activeTabId, setActiveTabId] = useState(() => config?.activeTabId || "");
    const scrollRef = useRef(null);
    const toolbarRefreshRef = useRef(null);
    const activeTabRef = useRef(null);
    useForcedWheelScroll(scrollRef);
    useEffect(() => {
        if (!config)
            return;
        const preferred = tabs.some((tab) => tab.id === config.activeTabId) ? config.activeTabId : tabs[0]?.id ?? "";
        setActiveTabId((current) => tabs.some((tab) => tab.id === current) ? current : preferred);
    }, [config?.activeTabId, config?.tabs]);
    const active = tabs.find((tab) => tab.id === activeTabId) ?? tabs[0];
    const activeSourceIds = tabSourceIds(config, active);
    const { items, loading, errors, load } = useNews(active?.id ?? "", 120, activeSourceIds, true, Boolean(config?.onboardingComplete && active?.id));
    const placements = useMemo(() => computeMagazinePlacements(items), [items]);
    useEffect(() => {
        if (!tabs.length || !active?.id)
            return;
        const timer = window.setTimeout(() => void prefetchNewsTabs(tabs, active.id, 120), 100);
        return () => window.clearTimeout(timer);
    }, [tabs.map((tab) => `${tab.id}:${tab.category || ""}:${tab.enabled !== false}:${(tab.sourceIds || []).join(",")}`).join("|"), active?.id]);
    const chooseTab = useCallback((tab) => {
        if (!config || tab.id === active?.id)
            return;
        const activate = () => {
            setActiveTabId(tab.id);
            scrollRef.current?.scrollTo?.({ top: 0, left: 0, behavior: "auto" });
            void saveConfigSilent({ ...config, activeTabId: tab.id }).catch((error) => console.warn("[News] Could not save active tab", error));
        };
        // Switch immediately. If this tab is not cached, useNews paints each source
        // as it arrives instead of holding the old tab until a full prefetch completes.
        activate();
    }, [config, active?.id]);
    const cycleTab = useCallback((step) => {
        if (!tabs.length)
            return;
        const index = Math.max(0, tabs.findIndex((tab) => tab.id === active?.id));
        chooseTab(tabs[(index + step + tabs.length) % tabs.length]);
    }, [tabs, active?.id, chooseTab]);
    useEffect(() => {
        if (!active?.id)
            return;
        window.requestAnimationFrame(() => {
            const node = activeTabRef.current;
            if (node)
                revealHorizontalTabSmooth(node, 600);
        });
    }, [active?.id]);
    const handleRootButtonDown = useCallback((event) => {
        const button = event?.detail?.button;
        if (button !== GamepadButton.BUMPER_LEFT && button !== GamepadButton.BUMPER_RIGHT)
            return;
        event?.preventDefault?.();
        event?.stopPropagation?.();
        cycleTab(button === GamepadButton.BUMPER_RIGHT ? 1 : -1);
    }, [cycleTab]);
    if (!bootstrap) {
        return (SP_REACT.createElement(FullscreenShell, null,
            SP_REACT.createElement(Focusable, { onCancel: goBack, onCancelButton: goBack, style: { width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" } },
                SP_REACT.createElement("div", { style: { display: "flex", alignItems: "center", gap: 12, fontSize: 20, opacity: .68 } },
                    SP_REACT.createElement(Spinner, null),
                    " ",
                    SP_REACT.createElement("span", null, tr("prepareKiosk"))))));
    }
    return (SP_REACT.createElement(FullscreenShell, null,
        SP_REACT.createElement(Focusable, { "flow-children": "vertical", onButtonDown: handleRootButtonDown, onCancel: goBack, onCancelButton: goBack, style: { width: "100%", height: "100%" } },
            SP_REACT.createElement("header", { style: { height: 158, padding: "26px 52px 0", boxSizing: "border-box", background: "linear-gradient(to bottom,rgba(0,0,0,.2),transparent)" } },
                SP_REACT.createElement("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between" } },
                    SP_REACT.createElement("h1", { style: { margin: 0, fontSize: 33, lineHeight: 1, fontWeight: 720, letterSpacing: "-.02em" } }, "News"),
                    SP_REACT.createElement(Focusable, { className: "newsEdicolaToolbar", "flow-children": "horizontal", onButtonDown: (event) => {
                            const button = event?.detail?.button;
                            if (button === GamepadButton.DIR_UP) {
                                event?.preventDefault?.();
                                event?.stopPropagation?.();
                                return;
                            }
                            if (button === GamepadButton.DIR_DOWN && activeTabRef.current) {
                                event?.preventDefault?.();
                                event?.stopPropagation?.();
                                activeTabRef.current.focus?.();
                            }
                        }, style: { display: "flex", gap: 8 } },
                        SP_REACT.createElement(DialogButton, { ref: toolbarRefreshRef, className: "newsToolbarRefresh newsToolbarButton", style: { ...baseButton, width: 46, minWidth: 46, padding: 0 }, onButtonDown: (event) => { if (event?.detail?.button === GamepadButton.DIR_DOWN && activeTabRef.current) {
                                event.preventDefault?.();
                                event.stopPropagation?.();
                                activeTabRef.current.focus?.();
                            } }, onClick: () => void load(true), title: tr("refresh") }, loading ? SP_REACT.createElement(Spinner, { size: 20, thickness: 2.2 }) : "↻"),
                        SP_REACT.createElement(DialogButton, { className: "newsToolbarButton", style: { ...baseButton, width: 46, minWidth: 46, padding: 0 }, onButtonDown: (event) => { if (event?.detail?.button === GamepadButton.DIR_DOWN && activeTabRef.current) {
                                event.preventDefault?.();
                                event.stopPropagation?.();
                                activeTabRef.current.focus?.();
                            } }, onClick: () => navigate(SETTINGS_ROUTE), title: tr("settings") }, "\u2699"),
                        SP_REACT.createElement(DialogButton, { className: "newsToolbarButton", style: { ...baseButton, width: 92, minWidth: 92 }, onButtonDown: (event) => { if (event?.detail?.button === GamepadButton.DIR_DOWN && activeTabRef.current) {
                                event.preventDefault?.();
                                event.stopPropagation?.();
                                activeTabRef.current.focus?.();
                            } }, onClick: goBack }, tr("back")))),
                SP_REACT.createElement(Focusable, { className: "newsEdicolaTabs", "flow-children": "horizontal", onButtonDown: (event) => {
                        const button = event?.detail?.button;
                        if (button === GamepadButton.DIR_UP && toolbarRefreshRef.current) {
                            event?.preventDefault?.();
                            event?.stopPropagation?.();
                            toolbarRefreshRef.current.focus?.();
                        }
                    }, style: { display: "flex", flexWrap: "nowrap", gap: 9, marginTop: 23, overflowX: "auto", overflowY: "hidden", padding: "3px 3px 7px", scrollPaddingInline: 6, scrollBehavior: "auto" } }, tabs.map((tab) => {
                    const selected = tab.id === active?.id;
                    return SP_REACT.createElement(DialogButton, { ref: selected ? activeTabRef : undefined, key: tab.id, className: `newsTabButton${selected ? " newsTabActive" : ""}`, onButtonDown: (event) => { const button = event?.detail?.button; if (button === GamepadButton.DIR_UP && toolbarRefreshRef.current) {
                            event.preventDefault?.();
                            event.stopPropagation?.();
                            toolbarRefreshRef.current.focus?.();
                            return;
                        } if (button === GamepadButton.DIR_LEFT)
                            focusAdjacentEdicolaTab(event, "left");
                        else if (button === GamepadButton.DIR_RIGHT)
                            focusAdjacentEdicolaTab(event, "right"); }, onFocus: (event) => revealHorizontalTabSmooth(event?.currentTarget, 600), style: { flex: "0 0 auto", minWidth: "max-content", width: "auto", height: 40, padding: "0 16px", borderRadius: 9, opacity: selected ? 1 : .58, fontSize: 17, fontWeight: selected ? 680 : 520 }, onClick: () => chooseTab(tab) }, displayTabName(tab));
                }))),
            SP_REACT.createElement("div", { ref: scrollRef, className: "newsEdicolaScroll", style: { height: "calc(100% - 158px)", overflowY: "auto", overflowX: "hidden", overscrollBehavior: "contain", scrollBehavior: "auto", scrollbarGutter: "stable", padding: "24px 52px 54px", boxSizing: "border-box" } },
                !tabs.length ? SP_REACT.createElement(EmptyState, { title: tr("noActiveTab"), detail: tr("noNewsDetail") }) : null,
                loading && !items.length ? SP_REACT.createElement("div", { style: { height: 260, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, opacity: .68 } },
                    SP_REACT.createElement(Spinner, null),
                    "\u00A0 ",
                    tr("prepareKiosk")) : null,
                !loading && tabs.length && !items.length ? SP_REACT.createElement(EmptyState, { title: tr("emptyPage"), detail: tr("noNewsDetail") }) : null,
                items.length ? (SP_REACT.createElement(Focusable, { "flow-children": "grid", style: { display: "grid", gridTemplateColumns: "repeat(12,minmax(0,1fr))", gridAutoRows: 154, gap: 12, width: "100%" } }, items.map((item, index) => SP_REACT.createElement(ArticleCard, { key: `${item.id}-${index}`, item: item, index: index, placement: placements[index] })))) : null,
                errors.length ? SP_REACT.createElement("div", { style: { marginTop: 24, padding: 14, borderRadius: 10, background: "rgba(255,180,80,.08)", fontSize: 12, opacity: .75 } }, tr("feedErrorsSummary", { n: errors.length })) : null))));
}
const CONTROLLER_ICONS = {
    a: "https://upload.wikimedia.org/wikipedia/commons/c/c6/Xbox_A_button_%28B%2BW%29.svg",
    b: "https://upload.wikimedia.org/wikipedia/commons/0/05/Xbox_B_button_%28B%2BW%29.svg",
    dpadDown: "https://upload.wikimedia.org/wikipedia/commons/e/e3/Xbox_D-pad_%28D%29.svg",
    dpadUp: "https://upload.wikimedia.org/wikipedia/commons/6/60/Xbox_D-pad_%28U%29.svg",
    lb: "https://upload.wikimedia.org/wikipedia/commons/b/b1/Xbox_LB_bumper.svg",
    rb: "https://upload.wikimedia.org/wikipedia/commons/d/d0/Xbox_RB_bumper.svg",
    view: "https://upload.wikimedia.org/wikipedia/commons/c/cc/Xbox_View_button.svg",
    menu: "https://upload.wikimedia.org/wikipedia/commons/e/e5/Xbox_Menu_button.svg",
};
function ControllerSvg({ src, size = 24 }) {
    return SP_REACT.createElement("img", { src: src, alt: "", loading: "eager", decoding: "async", style: { width: size, height: size, objectFit: "contain", display: "block", filter: "brightness(0) invert(1)", opacity: .98 } });
}
function ControllerLegendIcon({ type }) {
    if (type === "scroll")
        return SP_REACT.createElement("span", { style: { display: "inline-flex", alignItems: "center", gap: 1 } },
            SP_REACT.createElement(ControllerSvg, { src: CONTROLLER_ICONS.dpadUp, size: 23 }),
            SP_REACT.createElement(ControllerSvg, { src: CONTROLLER_ICONS.dpadDown, size: 23 }));
    if (type === "video")
        return SP_REACT.createElement("span", { style: { display: "inline-flex", alignItems: "center", gap: 2 } },
            SP_REACT.createElement(ControllerSvg, { src: CONTROLLER_ICONS.lb, size: 25 }),
            SP_REACT.createElement(ControllerSvg, { src: CONTROLLER_ICONS.rb, size: 25 }));
    return SP_REACT.createElement(ControllerSvg, { src: CONTROLLER_ICONS[type], size: 26 });
}
function ReaderLegendHint({ glyph, label, wide = false }) {
    return SP_REACT.createElement("span", { style: { display: "inline-flex", alignItems: "center", gap: 6, whiteSpace: "nowrap", opacity: .94, minWidth: wide ? 0 : undefined } },
        SP_REACT.createElement("span", { style: { display: "inline-flex", alignItems: "center", justifyContent: "center", minWidth: wide ? 54 : 28, height: 28 } }, glyph),
        SP_REACT.createElement("span", { style: { fontSize: 9.5, lineHeight: 1.05, color: "rgba(255,255,255,.92)", fontWeight: 560 } }, label));
}
function MetadataArticlePreview({ item }) {
    return SP_REACT.createElement(FullscreenShell, { style: { background: "#111216" } },
        SP_REACT.createElement(Focusable, { "flow-children": "vertical", onCancel: goBack, onCancelButton: goBack, style: { height: "100%", boxSizing: "border-box", padding: "44px 64px", display: "flex", flexDirection: "column", gap: 24 } },
            SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 140 }, onClick: goBack }, tr("back")),
            SP_REACT.createElement("div", { style: { maxWidth: 960, margin: "auto 0", textAlign: "left" } },
                SP_REACT.createElement("div", { style: { fontSize: 16, opacity: .7, marginBottom: 16 } },
                    item.source,
                    item.published ? ` · ${formatDate(item.published)}` : ""),
                SP_REACT.createElement("h1", { style: { fontSize: "clamp(32px,4vw,54px)", lineHeight: 1.18, margin: "0 0 24px" } }, item.title),
                item.excerpt ? SP_REACT.createElement("p", { style: { fontSize: 22, lineHeight: 1.5, maxWidth: 840 } }, item.excerpt) : null,
                SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 260, marginTop: 20 }, onClick: () => openWebsiteInSteam(item.url) }, tr("readSite")))));
}
function ArticleRoute() {
    const item = window.__deckyNewsOpenItem;
    return item && isMetadataOnly(item) ? SP_REACT.createElement(MetadataArticlePreview, { item: metadataNewsItem(item) }) : SP_REACT.createElement(ReaderArticleRoute, null);
}
function ReaderArticleRoute() {
    const item = window.__deckyNewsOpenItem;
    const cachedArticle = item?.url ? articleUiCache.get(item.url) : undefined;
    const cachedFresh = Boolean(cachedArticle && Date.now() - cachedArticle.at < ARTICLE_UI_CACHE_MS);
    const [article, setArticle] = useState(cachedFresh ? cachedArticle.article : null);
    const [loading, setLoading] = useState(!cachedFresh);
    const [fontScale, setFontScale] = useState(1);
    const readerRef = useRef(null);
    useForcedWheelScroll(readerRef);
    const requestSequenceRef = useRef(0);
    const readerHoldDirectionRef = useRef(0);
    const readerHoldTimerRef = useRef(0);
    const readerHoldFrameRef = useRef(0);
    const readerHoldLastFrameRef = useRef(0);
    useEffect(() => {
        let alive = true;
        const sequence = ++requestSequenceRef.current;
        const requested = item ? { ...item } : undefined;
        if (!requested?.url) {
            setArticle(null);
            setLoading(false);
            return;
        }
        const uiCached = articleUiCache.get(requested.url);
        const hasUiCached = Boolean(uiCached && Date.now() - uiCached.at < ARTICLE_UI_CACHE_MS);
        if (hasUiCached) {
            setArticle(uiCached.article);
            setLoading(false);
        }
        else {
            setArticle(null);
            setLoading(true);
        }
        const stillCurrent = () => {
            const current = window.__deckyNewsOpenItem;
            return alive && sequence === requestSequenceRef.current && current?.id === requested.id && current?.url === requested.url;
        };
        void rpc("get_article", requested.url, requested)
            .then((value) => { if (stillCurrent()) {
            setArticle(value);
            articleUiCache.set(requested.url, { article: value, at: Date.now() });
            if (value?.url)
                articleUiCache.set(value.url, { article: value, at: Date.now() });
        } })
            .catch((exc) => { if (stillCurrent())
            setArticle({ ok: false, error: String(exc?.message ?? exc) }); })
            .finally(() => { if (stillCurrent() && !hasUiCached)
            setLoading(false); });
        return () => { alive = false; };
    }, [item?.id, item?.url]);
    const scrollReaderStep = useCallback((direction) => {
        const node = readerRef.current;
        if (!node)
            return;
        // Let Chromium's native/compositor smooth-scroll path own the animation. This
        // avoids JS writing scrollTop on every frame and tracks 120 Hz displays much
        // better. The step is intentionally modest so reading position is not lost.
        const step = Math.max(280, node.clientHeight * .40);
        const maxTop = Math.max(0, node.scrollHeight - node.clientHeight);
        const targetTop = Math.max(0, Math.min(maxTop, node.scrollTop + direction * step));
        try {
            node.scrollTo({ top: targetTop, behavior: "smooth" });
        }
        catch {
            node.scrollTop = targetTop;
        }
    }, []);
    const stopReaderContinuousScroll = useCallback(() => {
        if (readerHoldTimerRef.current)
            window.clearTimeout(readerHoldTimerRef.current);
        if (readerHoldFrameRef.current)
            window.cancelAnimationFrame(readerHoldFrameRef.current);
        readerHoldTimerRef.current = 0;
        readerHoldFrameRef.current = 0;
        readerHoldLastFrameRef.current = 0;
        readerHoldDirectionRef.current = 0;
    }, []);
    const startReaderDirectionalScroll = useCallback((direction) => {
        if (readerHoldDirectionRef.current === direction)
            return;
        stopReaderContinuousScroll();
        // A quick tap keeps the existing short native smooth step. Holding the
        // direction for a moment seamlessly transitions to continuous 120-Hz-friendly
        // requestAnimationFrame scrolling until the button/key is released.
        scrollReaderStep(direction);
        readerHoldDirectionRef.current = direction;
        readerHoldTimerRef.current = window.setTimeout(() => {
            if (readerHoldDirectionRef.current !== direction)
                return;
            const node = readerRef.current;
            if (!node)
                return;
            try {
                node.scrollTo({ top: node.scrollTop, behavior: "auto" });
            }
            catch { }
            readerHoldLastFrameRef.current = performance.now();
            const tick = (now) => {
                if (readerHoldDirectionRef.current !== direction)
                    return;
                const current = readerRef.current;
                if (!current)
                    return;
                const previous = readerHoldLastFrameRef.current || now;
                const deltaSeconds = Math.max(0, Math.min(.04, (now - previous) / 1000));
                readerHoldLastFrameRef.current = now;
                const maxTop = Math.max(0, current.scrollHeight - current.clientHeight);
                const speed = Math.max(520, current.clientHeight * .68);
                const nextTop = Math.max(0, Math.min(maxTop, current.scrollTop + direction * speed * deltaSeconds));
                current.scrollTop = nextTop;
                readerHoldFrameRef.current = window.requestAnimationFrame(tick);
            };
            readerHoldFrameRef.current = window.requestAnimationFrame(tick);
        }, 260);
    }, [scrollReaderStep, stopReaderContinuousScroll]);
    const cancelReaderScroll = useCallback(() => {
        stopReaderContinuousScroll();
        const node = readerRef.current;
        if (!node)
            return;
        // A synchronous no-op scroll cancels an in-flight native smooth scroll before
        // leaving the Reader route.
        try {
            node.scrollTo({ top: node.scrollTop, behavior: "auto" });
        }
        catch { /* nothing to cancel */ }
    }, [stopReaderContinuousScroll]);
    useEffect(() => {
        const node = readerRef.current;
        const doc = node?.ownerDocument;
        if (!node || !doc)
            return;
        const onKeyDown = (event) => {
            if (event.key !== "ArrowDown" && event.key !== "ArrowUp")
                return;
            const active = doc.activeElement;
            if (active && !node.contains(active) && !active.closest?.(".newsReaderSite") && !active.closest?.(".newsMediaEmbed"))
                return;
            event.preventDefault();
            if (event.repeat)
                return;
            startReaderDirectionalScroll(event.key === "ArrowDown" ? 1 : -1);
        };
        const onKeyUp = (event) => {
            if (event.key !== "ArrowDown" && event.key !== "ArrowUp")
                return;
            event.preventDefault();
            stopReaderContinuousScroll();
        };
        doc.addEventListener("keydown", onKeyDown, true);
        doc.addEventListener("keyup", onKeyUp, true);
        return () => {
            doc.removeEventListener("keydown", onKeyDown, true);
            doc.removeEventListener("keyup", onKeyUp, true);
            stopReaderContinuousScroll();
        };
    }, [startReaderDirectionalScroll, stopReaderContinuousScroll]);
    const focusReaderSite = useCallback(() => {
        const siteButton = readerRef.current?.ownerDocument.querySelector(".newsReaderSite");
        siteButton?.focus?.();
    }, []);
    const focusYoutubeByStep = useCallback((step) => {
        const doc = readerRef.current?.ownerDocument;
        const reader = readerRef.current;
        if (!doc || !reader)
            return false;
        const videos = Array.from(doc.querySelectorAll('.newsMediaEmbed[data-news-provider="youtube"]'))
            .filter((element) => element.offsetParent !== null);
        if (!videos.length)
            return false;
        const activeElement = doc.activeElement;
        const activeIndex = videos.findIndex((video) => Boolean(activeElement && (video === activeElement || video.contains(activeElement))));
        let targetIndex = -1;
        if (activeIndex >= 0)
            targetIndex = activeIndex + step;
        else if (activeElement?.closest?.(".newsReaderSite") && step < 0)
            targetIndex = videos.length - 1;
        else {
            const readerRect = reader.getBoundingClientRect();
            const viewportCenter = (readerRect.top + readerRect.bottom) / 2;
            const centers = videos.map((video) => { const rect = video.getBoundingClientRect(); return (rect.top + rect.bottom) / 2; });
            if (step > 0) {
                targetIndex = centers.findIndex((center) => center >= viewportCenter - 20);
                if (targetIndex < 0)
                    targetIndex = videos.length - 1;
            }
            else {
                for (let index = centers.length - 1; index >= 0; index -= 1) {
                    if (centers[index] <= viewportCenter + 20) {
                        targetIndex = index;
                        break;
                    }
                }
                if (targetIndex < 0)
                    targetIndex = 0;
            }
        }
        if (targetIndex < 0 || targetIndex >= videos.length)
            return false;
        const target = videos[targetIndex];
        try {
            target.focus?.({ preventScroll: true });
        }
        catch {
            target.focus?.();
        }
        const rr = reader.getBoundingClientRect();
        const trr = target.getBoundingClientRect();
        const targetTop = Math.max(0, Math.min(reader.scrollTop + (trr.top + trr.bottom) / 2 - (rr.top + rr.bottom) / 2, reader.scrollHeight - reader.clientHeight));
        const start = reader.scrollTop;
        const delta = targetTop - start;
        const started = performance.now();
        const animate = (now) => {
            const t = Math.min(1, (now - started) / 360);
            const eased = t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
            reader.scrollTop = start + delta * eased;
            if (t < 1)
                window.requestAnimationFrame(animate);
        };
        window.requestAnimationFrame(animate);
        playSteamBasicNavSound();
        return true;
    }, []);
    const handleReaderButton = useCallback((event) => {
        const button = event?.detail?.button;
        const gp = GamepadButton;
        const fontDown = matchesAnyGamepadButton(button, gp.BACK, gp.SELECT, gp.VIEW, gp.BUTTON_SELECT);
        // Steam's OPTIONS is the Y/triangle action (4), not Start/Menu (14).
        const fontUp = matchesAnyGamepadButton(button, gp.START, gp.MENU, gp.BUTTON_START);
        if (fontDown || fontUp) {
            event?.preventDefault?.();
            event?.stopPropagation?.();
            setFontScale((current) => Math.max(.78, Math.min(1.42, current + (fontUp ? .08 : -.08))));
            return;
        }
        if (button === GamepadButton.BUMPER_LEFT || button === GamepadButton.BUMPER_RIGHT) {
            event?.preventDefault?.();
            event?.stopPropagation?.();
            focusYoutubeByStep(button === GamepadButton.BUMPER_RIGHT ? 1 : -1);
            return;
        }
        if (button === GamepadButton.DIR_RIGHT) {
            event?.preventDefault?.();
            event?.stopPropagation?.();
            focusReaderSite();
            return;
        }
        if (button === GamepadButton.DIR_DOWN || button === GamepadButton.DIR_UP) {
            event?.preventDefault?.();
            event?.stopPropagation?.();
            startReaderDirectionalScroll(button === GamepadButton.DIR_DOWN ? 1 : -1);
        }
    }, [focusReaderSite, focusYoutubeByStep, startReaderDirectionalScroll]);
    const handleReaderButtonUp = useCallback((event) => {
        const button = event?.detail?.button;
        if (button !== GamepadButton.DIR_DOWN && button !== GamepadButton.DIR_UP)
            return;
        event?.preventDefault?.();
        event?.stopPropagation?.();
        stopReaderContinuousScroll();
    }, [stopReaderContinuousScroll]);
    if (article?.contentMode === "metadata_only" && item)
        return SP_REACT.createElement(MetadataArticlePreview, { item: metadataNewsItem(item) });
    const title = article?.title || item?.title || "Articolo";
    const articleHero = article?.hero || "";
    const hero = item?.image || articleHero || "";
    const published = article?.published || item?.published || 0;
    const embed = article?.embedUrl || item?.embedUrl || "";
    const blocks = article?.blocks ?? [];
    let skippedFirstHeroLikeImage = false;
    const heroSources = [hero, item?.image || "", articleHero, article?.hero || ""];
    const bodyBlocks = blocks.filter((block) => {
        if (block.type !== "image" || !block.url)
            return true;
        if (!skippedFirstHeroLikeImage && imageLooksLikeHero(block.url, heroSources)) {
            skippedFirstHeroLikeImage = true;
            return false;
        }
        return true;
    });
    return (SP_REACT.createElement(FullscreenShell, { style: { background: "#111216" } },
        SP_REACT.createElement(Focusable, { "flow-children": "vertical", onButtonDown: handleReaderButton, onButtonUp: handleReaderButtonUp, onCancel: () => { cancelReaderScroll(); goBack(); }, onCancelButton: () => { cancelReaderScroll(); goBack(); }, style: { width: "100%", height: "100%" } },
            SP_REACT.createElement("div", { className: "newsReaderBottomBar", style: { position: "absolute", left: 0, right: 0, bottom: 0, height: 88, zIndex: 8, pointerEvents: "none", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 18, padding: "16px 34px 12px", background: "linear-gradient(to top, rgba(17,18,22,.96) 0%, rgba(17,18,22,.88) 26%, rgba(17,18,22,.64) 56%, rgba(17,18,22,.28) 78%, rgba(17,18,22,0) 100%)" } },
                SP_REACT.createElement("div", { style: { display: "flex", alignItems: "center", gap: 10, minWidth: 0, maxWidth: "calc(100% - 220px)", overflow: "hidden", paddingTop: 4 } },
                    SP_REACT.createElement(ReaderLegendHint, { glyph: SP_REACT.createElement(ControllerLegendIcon, { type: "a" }), label: tr("legendSelect") }),
                    SP_REACT.createElement(ReaderLegendHint, { glyph: SP_REACT.createElement(ControllerLegendIcon, { type: "b" }), label: tr("legendBack") }),
                    SP_REACT.createElement(ReaderLegendHint, { glyph: SP_REACT.createElement(ControllerLegendIcon, { type: "scroll" }), label: tr("legendScroll") }),
                    SP_REACT.createElement(ReaderLegendHint, { glyph: SP_REACT.createElement(ControllerLegendIcon, { type: "video" }), label: tr("legendVideo"), wide: true }),
                    SP_REACT.createElement(ReaderLegendHint, { glyph: SP_REACT.createElement(ControllerLegendIcon, { type: "view" }), label: tr("legendTextSmall") }),
                    SP_REACT.createElement(ReaderLegendHint, { glyph: SP_REACT.createElement(ControllerLegendIcon, { type: "menu" }), label: tr("legendTextLarge") })),
                SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "flex", justifyContent: "flex-end", pointerEvents: "none", paddingTop: 6, flex: "0 0 auto" } },
                    SP_REACT.createElement(DialogButton, { className: "newsReaderSite", style: { ...baseButton, width: 154, pointerEvents: "auto", background: "rgba(20,20,22,.92)", backdropFilter: "blur(14px)", boxShadow: "0 10px 34px rgba(0,0,0,.42)" }, onClick: () => openWebsiteInSteam(article?.url || item?.resolvedUrl || item?.url || "") }, tr("readSite")))),
            SP_REACT.createElement("div", { ref: readerRef, className: "newsReaderScroll", style: { width: "100%", height: "100%", overflowY: "auto", overflowX: "hidden", overscrollBehavior: "contain", boxSizing: "border-box", paddingBottom: 152, scrollBehavior: "auto" } },
                SP_REACT.createElement("section", { style: { position: "relative", height: "min(82vh,860px)", minHeight: 620, overflow: "hidden", background: "#111216" } },
                    SP_REACT.createElement(ArticleHeroImage, { primary: item?.image || "", fallback: articleHero, source: item?.source || "", url: article?.url || item?.url || item?.sourceSiteUrl || "", logo: item?.sourceLogo, favicon: item?.sourceFavicon, color: item?.sourceColor }),
                    SP_REACT.createElement("span", { style: { position: "absolute", inset: 0, zIndex: 1, pointerEvents: "none", background: "linear-gradient(to bottom,rgba(17,18,22,.00) 0%,rgba(17,18,22,.05) 30%,rgba(17,18,22,.34) 62%,rgba(17,18,22,.88) 84%,#111216 100%)" } }),
                    SP_REACT.createElement("div", { style: { position: "absolute", zIndex: 2, left: "50%", bottom: 2, transform: "translateX(-50%)", width: "min(900px,calc(100% - 360px))", textAlign: "left" } },
                        SP_REACT.createElement("div", { style: { fontSize: 13, opacity: .82, marginBottom: 10, textShadow: "0 2px 12px rgba(0,0,0,.55)" } },
                            item?.source ?? "",
                            published ? ` · ${formatDate(published)}` : "",
                            article?.author ? ` · ${article.author}` : ""),
                        SP_REACT.createElement("h1", { style: { margin: 0, fontSize: "clamp(38px,4.35vw,62px)", lineHeight: 1.18, paddingBottom: ".16em", letterSpacing: "-.038em", fontWeight: 730, textShadow: "0 3px 22px rgba(0,0,0,.58)", whiteSpace: "normal", overflow: "visible", textOverflow: "clip" } }, title))),
                SP_REACT.createElement("main", { style: { width: "min(820px,calc(100% - 380px))", margin: "0 auto", position: "relative", zIndex: 2, paddingTop: 30 } },
                    article?.description ? SP_REACT.createElement("p", { style: { margin: "0 0 30px", fontSize: 20 * fontScale, lineHeight: 1.48, opacity: .78 } }, article.description) : null,
                    loading ? SP_REACT.createElement("div", { style: { padding: "42px 0", display: "flex", alignItems: "center", gap: 12, fontSize: 18, opacity: .72 } },
                        SP_REACT.createElement(Spinner, { size: 24 }),
                        " ",
                        SP_REACT.createElement("span", null, tr("articleLoading"))) : null,
                    embed ? SP_REACT.createElement(MediaEmbed, { block: { type: "embed", provider: "youtube", embedUrl: embed, url: item?.videoUrl || item?.url, title: "YouTube" } }) : null,
                    !loading && article?.ok && article.readerAvailable ? SP_REACT.createElement("div", { style: { marginTop: article?.description ? 8 : 0 } }, bodyBlocks.map((block, index) => {
                        if (block.type === "embed" && block.embedUrl)
                            return SP_REACT.createElement(MediaEmbed, { key: `embed-${index}`, block: block });
                        if (block.type === "image" && block.url)
                            return SP_REACT.createElement(NewsImage, { key: index, src: block.url, alt: block.alt || "", source: item?.source || "", url: item?.sourceSiteUrl || article?.url || item?.url || "", logo: item?.sourceLogo, favicon: item?.sourceFavicon, color: item?.sourceColor, objectFit: "contain", objectPosition: "center top", style: { display: "block", width: "100%", height: "min(72vh,780px)", margin: "32px 0", borderRadius: 10, background: "rgba(255,255,255,.025)" }, minWidth: 720, minHeight: 320, preferFaviconFallback: true, cacheOnError: true, referer: article?.url || item?.url || "" });
                        if (block.type === "heading")
                            return SP_REACT.createElement("h2", { key: index, style: { margin: "34px 0 12px", fontSize: 29 * fontScale, lineHeight: 1.15 } }, block.text);
                        if (block.type === "quote")
                            return SP_REACT.createElement("blockquote", { key: index, style: { margin: "26px 0", padding: "5px 0 5px 20px", borderLeft: "4px solid rgba(255,255,255,.4)", fontSize: 22 * fontScale, lineHeight: 1.55, opacity: .78 } }, block.text);
                        return SP_REACT.createElement("p", { key: index, style: { margin: "0 0 21px", fontSize: 21 * fontScale, lineHeight: 1.62, letterSpacing: "-.006em", color: "rgba(255,255,255,.91)" } }, block.text);
                    })) : null,
                    !loading && article?.ok && article.readerAvailable && article.readerPartial ? SP_REACT.createElement("div", { style: { marginTop: 24, padding: "14px 16px", borderRadius: 10, background: "rgba(255,255,255,.045)", border: "1px solid rgba(255,255,255,.08)", fontSize: 14, lineHeight: 1.45, opacity: .76 } }, tr("readerPartial")) : null,
                    !loading && article?.ok && !article.readerAvailable ? SP_REACT.createElement("div", { style: { marginTop: 34, padding: 22, borderRadius: 12, background: "rgba(255,255,255,.05)", fontSize: 17, lineHeight: 1.45 } }, tr("readerUnavailable")) : null,
                    !loading && article && !article.ok ? SP_REACT.createElement("div", { style: { marginTop: 34, padding: 22, borderRadius: 12, background: "rgba(255,90,90,.08)", fontSize: 16 } }, article.error || tr("readerUnavailable")) : null,
                    SP_REACT.createElement("div", { style: { height: 70 } }))))));
}
function StepHeader({ step, total, title, detail }) {
    return SP_REACT.createElement("div", { style: { marginBottom: 24 } },
        SP_REACT.createElement("div", { style: { fontSize: 12, opacity: .48, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 8 } },
            tr("setup"),
            " \u00B7 ",
            step,
            "/",
            total),
        SP_REACT.createElement("h1", { style: { margin: 0, fontSize: 38, letterSpacing: "-.025em" } }, title),
        SP_REACT.createElement("p", { style: { margin: "8px 0 0", fontSize: 16, opacity: .65, lineHeight: 1.45, maxWidth: 760 } }, detail));
}
function OnboardingRoute() {
    const { bootstrap, error, reload } = useBootstrap();
    const [step, setStep] = useState(1);
    const [country, setCountry] = useState("IT");
    const [sourceCountry, setSourceCountry] = useState("IT");
    const [sourceQuery, setSourceQuery] = useState("");
    const [catalog, setCatalog] = useState([]);
    const [onlineSearching, setOnlineSearching] = useState(false);
    const [selected, setSelected] = useState({});
    const [globalSuggestions, setGlobalSuggestions] = useState([]);
    const [presetTabs, setPresetTabs] = useState({ all: true });
    const [customTabs, setCustomTabs] = useState([]);
    const [customTabName, setCustomTabName] = useState("");
    const [manualUrl, setManualUrl] = useState("");
    const [discovering, setDiscovering] = useState(false);
    const [message, setMessage] = useState("");
    const initialized = useRef(false);
    const onboardingScrollRef = useRef(null);
    useForcedWheelScroll(onboardingScrollRef);
    useEffect(() => {
        if (!bootstrap || initialized.current)
            return;
        initialized.current = true;
        setCountry(bootstrap.config.country || "IT");
        setSourceCountry(bootstrap.config.country || "IT");
        if (window.__deckyNewsReconfigure && bootstrap.config.sources?.length) {
            const map = {};
            bootstrap.config.sources.forEach((source) => { map[source.id] = source; });
            setSelected(map);
            const presets = {};
            bootstrap.config.tabs.forEach((tab) => {
                const byCategory = tab.category ? PRESET_TABS.find(([key]) => key === tab.category) : undefined;
                const byName = PRESET_TABS.find(([, label]) => label.toLowerCase() === tab.name.toLowerCase());
                const match = byCategory ?? byName;
                if (match)
                    presets[match[0]] = true;
                else
                    setCustomTabs((current) => current.includes(tab.name) ? current : [...current, tab.name]);
            });
            if (!Object.keys(presets).length)
                presets.all = true;
            setPresetTabs(presets);
        }
    }, [bootstrap]);
    useEffect(() => {
        let alive = true;
        void rpc("search_sources", sourceCountry, sourceQuery).then((result) => { if (alive)
            setCatalog(result?.sources ?? []); }).catch(() => { if (alive)
            setCatalog([]); });
        return () => { alive = false; };
    }, [sourceCountry, sourceQuery]);
    useEffect(() => {
        let alive = true;
        void rpc("search_global_sources").then((result) => {
            if (alive)
                setGlobalSuggestions(Array.isArray(result?.sources) ? result.sources : []);
        }).catch(() => { if (alive)
            setGlobalSuggestions([]); });
        return () => { alive = false; };
    }, []);
    const countries = bootstrap?.countries ?? [];
    const selectedSources = Object.values(selected);
    const availableTags = useMemo(() => new Set(selectedSources.flatMap((source) => source.tags || [])), [selectedSources]);
    const toggleSource = (source) => setSelected((current) => {
        const next = { ...current };
        if (next[source.id])
            delete next[source.id];
        else
            next[source.id] = source;
        return next;
    });
    const searchOnline = async () => {
        const query = sourceQuery.trim();
        if (query.length < 2) {
            setMessage(tr("onlineSearchMinChars"));
            return;
        }
        setOnlineSearching(true);
        setMessage("");
        try {
            const result = await rpc("search_online_sources", sourceCountry, query);
            if (result?.ok) {
                const merged = new Map();
                catalog.forEach((source) => merged.set(source.id, source));
                (result.sources ?? []).forEach((source) => merged.set(source.id, source));
                setCatalog(Array.from(merged.values()));
                setMessage((result.sources ?? []).length ? tr("onlineSourcesAdded", { n: result.sources.length }) : tr("noMoreSources"));
            }
            else
                setMessage(localizeBackendError(result?.error, "onlineSearchUnavailable"));
        }
        catch (exc) {
            setMessage(String(exc?.message ?? exc));
        }
        finally {
            setOnlineSearching(false);
        }
    };
    const discover = async () => {
        if (!manualUrl.trim())
            return;
        setDiscovering(true);
        setMessage("");
        try {
            const result = await rpc("discover_source", manualUrl.trim(), sourceCountry, "");
            if (result?.ok && result.source) {
                setSelected((current) => ({ ...current, [result.source.id]: result.source }));
                setManualUrl("");
                setMessage(tr("sourceAdded", { name: result.source.name }));
            }
            else
                setMessage(localizeBackendError(result?.error, "sourceNotFound"));
        }
        catch (exc) {
            setMessage(String(exc?.message ?? exc));
        }
        finally {
            setDiscovering(false);
        }
    };
    const addCountryHeadlines = async () => {
        setDiscovering(true);
        setMessage("");
        try {
            const result = await rpc("make_country_source", sourceCountry);
            if (result?.ok && result.source) {
                setSelected((current) => ({ ...current, [result.source.id]: result.source }));
                setMessage(tr("sourceAdded", { name: result.source.name }));
            }
            else
                setMessage(localizeBackendError(result?.error, "countryHeadlinesFailed"));
        }
        catch (exc) {
            setMessage(String(exc?.message ?? exc));
        }
        finally {
            setDiscovering(false);
        }
    };
    const addSuggestedSource = (source) => {
        setSelected((current) => ({ ...current, [source.id]: source }));
        setMessage(tr("sourceAdded", { name: source.name }));
    };
    const finish = async () => {
        const sources = selectedSources;
        if (!sources.length) {
            setMessage(tr("selectAtLeastOneSource"));
            setStep(2);
            return;
        }
        const tabs = [];
        PRESET_TABS.forEach(([key, label]) => {
            if (!presetTabs[key])
                return;
            const sourceIds = sources.map((source) => source.id);
            if (sourceIds.length)
                tabs.push({ id: key === "all" ? "all" : `preset-${key}`, name: label, sourceIds, category: key });
        });
        customTabs.forEach((name) => tabs.push({ id: nextId("tab"), name, sourceIds: sources.map((source) => source.id) }));
        if (!tabs.length)
            tabs.push({ id: "all", name: tr("catAll"), sourceIds: sources.map((source) => source.id), category: "all" });
        const old = bootstrap?.config;
        const config = {
            version: 1,
            onboardingComplete: true,
            country,
            language: CURRENT_LANGUAGE_TAG[CURRENT_LOCALE],
            refreshMinutes: old?.refreshMinutes || 15,
            sources,
            tabs,
            activeTabId: tabs[0].id,
        };
        const result = await rpc("save_config", config);
        if (result?.ok) {
            window.__deckyNewsReconfigure = false;
            // Remove onboarding from the navigation stack before opening the Edicola.
            // This way B/Back returns to the QAM (or to Settings when reconfiguring) instead
            // of reopening the completed wizard.
            goBack();
            scheduleNewsTask(() => navigate(EDICOLA_ROUTE), 180);
        }
        else
            setMessage(localizeBackendError(result?.error, "saveConfigFailed"));
    };
    if (!bootstrap)
        return (SP_REACT.createElement(FullscreenShell, null,
            SP_REACT.createElement(Focusable, { "flow-children": "vertical", style: { height: "100%", display: "flex", alignItems: "center", justifyContent: "center", padding: 40, boxSizing: "border-box" } }, error ? SP_REACT.createElement(SP_REACT.Fragment, null,
                SP_REACT.createElement("strong", { style: { fontSize: 24 } }, "News"),
                SP_REACT.createElement("span", { style: { marginTop: 10, maxWidth: 620, textAlign: "center", opacity: .65 } }, error),
                SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "flex", gap: 10, marginTop: 20 } },
                    SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 130 }, onClick: () => void reload() }, tr("retry")),
                    SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 130 }, onClick: goBack }, tr("back")))) : SP_REACT.createElement("div", { style: { fontSize: 20 } },
                SP_REACT.createElement(Spinner, null),
                "\u00A0 ",
                tr("prepareOnboarding")))));
    return (SP_REACT.createElement(FullscreenShell, null,
        SP_REACT.createElement(Focusable, { "flow-children": "vertical", style: { width: "100%", height: "100%", boxSizing: "border-box", position: "relative", overflow: "hidden" } },
            SP_REACT.createElement("div", { style: { position: "absolute", top: 34, left: 54, right: 54, zIndex: 50, display: "flex", justifyContent: "space-between", alignItems: "center" } },
                SP_REACT.createElement("strong", { style: { fontSize: 20 } }, "News"),
                SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 110 }, onClick: goBack }, tr("cancel"))),
            SP_REACT.createElement("div", { ref: onboardingScrollRef, className: "newsOnboardingScroll", style: { position: "absolute", top: 104, bottom: 106, left: 54, right: 54, overflowY: "auto", overflowX: "hidden", paddingRight: 10, paddingBottom: 40, overscrollBehavior: "contain" } },
                step === 1 ? SP_REACT.createElement(SP_REACT.Fragment, null,
                    SP_REACT.createElement(StepHeader, { step: 1, total: 4, title: tr("startTitle"), detail: tr("startDetail") }),
                    SP_REACT.createElement("div", { style: { width: "min(620px,100%)" } },
                        SP_REACT.createElement(CountryDropdown, { countries: countries, value: country, onChange: (code) => { setCountry(code); setSourceCountry(code); }, label: tr("primaryCountry") }))) : null,
                step === 2 ? SP_REACT.createElement(SP_REACT.Fragment, null,
                    SP_REACT.createElement(StepHeader, { step: 2, total: 4, title: tr("chooseSources"), detail: tr("chooseSourcesDetail") }),
                    SP_REACT.createElement(FieldActionRow, { columns: "220px minmax(0,1fr) 170px" },
                        SP_REACT.createElement(CountryDropdown, { countries: countries, value: sourceCountry, onChange: (code) => { setSourceCountry(code); setSourceQuery(""); setMessage(""); }, label: tr("sourceCountry") }),
                        SP_REACT.createElement(NewsTextField, { label: tr("sourceName"), value: sourceQuery, onChange: (value) => setSourceQuery(typeof value === "string" ? value : String(value?.target?.value ?? "")) }),
                        SP_REACT.createElement(FieldActionButton, { disabled: sourceQuery.trim().length < 2 || onlineSearching, onClick: () => void searchOnline() }, onlineSearching ? SP_REACT.createElement(Spinner, { size: 18 }) : tr("search"))),
                    SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, margin: "11px 0 10px" } },
                        SP_REACT.createElement("div", { style: { fontSize: 13, opacity: .62 } }, catalog.length ? tr("availableSourcesFor", { n: catalog.length, country: countryName(countries.find((entry) => entry.code === sourceCountry)) || sourceCountry }) : tr("noPreconfiguredSources", { country: countryName(countries.find((entry) => entry.code === sourceCountry)) || sourceCountry })),
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 220, minWidth: 220, height: 40, minHeight: 40 }, disabled: discovering, onClick: () => void addCountryHeadlines() },
                            "\uFF0B ",
                            tr("countryHeadlines"))),
                    SP_REACT.createElement("div", { style: { margin: "0 2px 8px", fontSize: 12.5, opacity: .52, textAlign: "right" } }, tr("selectedSourcesSummary", { sources: selectedSources.length, countries: new Set(selectedSources.map((source) => source.country)).size })),
                    selectedSources.length ? SP_REACT.createElement("div", { style: { marginBottom: 14, padding: 16, borderRadius: 12, background: "rgba(255,255,255,.045)" } },
                        SP_REACT.createElement("strong", { style: { display: "block", marginBottom: 7 } }, tr("addOtherCountries")),
                        SP_REACT.createElement("span", { style: { display: "block", fontSize: 12.5, opacity: .68, lineHeight: 1.45 } }, tr("addOtherCountriesDetail")),
                        SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "flex", flexWrap: "wrap", gap: 7, marginTop: 11 } }, ["US", "GB", "FR", "DE", "ES", "JP"].map((code) => SP_REACT.createElement(DialogButton, { key: code, style: { ...baseButton, width: "auto", height: 38, minHeight: 38 }, onClick: () => { setSourceCountry(code); setSourceQuery(""); setMessage(""); } }, countryName(countries.find((entry) => entry.code === code)) || code)))) : null,
                    catalog.length ? SP_REACT.createElement(Focusable, { "flow-children": "grid", style: { display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 8 } }, catalog.map((source) => {
                        const active = Boolean(selected[source.id]);
                        return SP_REACT.createElement(DialogButton, { key: source.id, style: { ...baseButton, minWidth: 0, height: 58, opacity: active ? 1 : .62, border: active ? "2px solid #fff" : "2px solid transparent" }, onClick: () => toggleSource(source) },
                            SP_REACT.createElement("span", { style: { display: "flex", alignItems: "center", width: "100%", gap: 10, textAlign: "left" } },
                                SP_REACT.createElement("span", { style: { width: 28, height: 28, borderRadius: 7, background: "rgba(255,255,255,.08)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 } }, active ? "✓" : "▤"),
                                SP_REACT.createElement("span", { style: { minWidth: 0 } },
                                    SP_REACT.createElement("strong", { style: { display: "block", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" } }, source.name),
                                    SP_REACT.createElement("span", { style: { display: "block", fontSize: 11, opacity: .52, marginTop: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" } }, source.siteUrl?.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "")))));
                    })) : null,
                    globalSuggestions.length ? SP_REACT.createElement("div", { style: { marginTop: 18, padding: 16, borderRadius: 12, background: "rgba(255,255,255,.045)" } },
                        SP_REACT.createElement("strong", { style: { display: "block", marginBottom: 8 } }, tr("sourcesWorldwide")),
                        SP_REACT.createElement("span", { style: { display: "block", fontSize: 12.5, opacity: .66, marginBottom: 10 } }, tr("sourcesWorldwideDetail")),
                        SP_REACT.createElement(Focusable, { "flow-children": "grid", style: { display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 8 } }, globalSuggestions.map((source) => {
                            const active = Boolean(selected[source.id]);
                            const countryLabel = countryName(countries.find((entry) => entry.code === source.country)) || source.country;
                            return SP_REACT.createElement(DialogButton, { key: source.id, style: { ...baseButton, minWidth: 0, height: 58, opacity: active ? 1 : .82, border: active ? "2px solid #fff" : "2px solid transparent" }, onClick: () => active ? toggleSource(source) : addSuggestedSource(source) },
                                SP_REACT.createElement("span", { style: { display: "flex", justifyContent: "space-between", width: "100%", gap: 10, textAlign: "left" } },
                                    SP_REACT.createElement("span", { style: { minWidth: 0 } },
                                        SP_REACT.createElement("strong", { style: { display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" } }, source.name),
                                        SP_REACT.createElement("span", { style: { display: "block", marginTop: 2, fontSize: 11, opacity: .54 } }, countryLabel)),
                                    SP_REACT.createElement("span", { style: { opacity: .55 } }, active ? "✓" : "＋")));
                        }))) : null,
                    SP_REACT.createElement("div", { style: { marginTop: 22, padding: 16, borderRadius: 12, background: "rgba(255,255,255,.045)" } },
                        SP_REACT.createElement("strong", { style: { display: "block", marginBottom: 8 } }, tr("addSiteFeed")),
                        SP_REACT.createElement(FieldActionRow, { columns: "minmax(0,1fr) 170px" },
                            SP_REACT.createElement(NewsTextField, { label: tr("addSiteFeed"), value: manualUrl, onChange: (value) => setManualUrl(typeof value === "string" ? value : String(value?.target?.value ?? "")) }),
                            SP_REACT.createElement(FieldActionButton, { disabled: !manualUrl.trim() || discovering, onClick: () => void discover() }, discovering ? SP_REACT.createElement(Spinner, { size: 18 }) : tr("findFeed"))),
                        message ? SP_REACT.createElement("div", { style: { marginTop: 8, fontSize: 12.5, opacity: .72 } }, message) : null)) : null,
                step === 3 ? SP_REACT.createElement(SP_REACT.Fragment, null,
                    SP_REACT.createElement(StepHeader, { step: 3, total: 4, title: tr("buildKiosk"), detail: tr("buildKioskDetail") }),
                    SP_REACT.createElement(Focusable, { "flow-children": "grid", style: { display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 9 } }, PRESET_TABS.map(([key, label]) => {
                        const available = true;
                        const active = Boolean(presetTabs[key]);
                        return SP_REACT.createElement(DialogButton, { key: key, style: { ...baseButton, minWidth: 0, height: 54, opacity: active ? 1 : .55, border: active ? "2px solid #fff" : "2px solid transparent" }, onClick: () => setPresetTabs((current) => ({ ...current, [key]: !current[key] })) },
                            SP_REACT.createElement("span", { style: { display: "flex", justifyContent: "space-between", width: "100%" } },
                                SP_REACT.createElement("span", null, label),
                                SP_REACT.createElement("span", null, active ? "✓" : "")));
                    })),
                    SP_REACT.createElement("div", { style: { marginTop: 20, padding: 16, borderRadius: 12, background: "rgba(255,255,255,.045)" } },
                        SP_REACT.createElement("strong", { style: { display: "block", marginBottom: 8 } }, tr("customTab")),
                        SP_REACT.createElement(FieldActionRow, { columns: "minmax(0,1fr) 160px" },
                            SP_REACT.createElement(NewsTextField, { label: tr("tabName"), value: customTabName, onChange: (value) => setCustomTabName(typeof value === "string" ? value : String(value?.target?.value ?? "")) }),
                            SP_REACT.createElement(FieldActionButton, { disabled: !customTabName.trim(), onClick: () => { const name = customTabName.trim(); if (name && !customTabs.includes(name))
                                    setCustomTabs(current => [...current, name]); setCustomTabName(""); } }, tr("add"))),
                        customTabs.length ? SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "flex", flexWrap: "wrap", gap: 7, marginTop: 10 } }, customTabs.map((name) => SP_REACT.createElement(DialogButton, { key: name, style: { ...baseButton, width: "auto", height: 38 }, onClick: () => setCustomTabs((current) => current.filter((value) => value !== name)) },
                            name,
                            " \u00D7"))) : null)) : null,
                step === 4 ? SP_REACT.createElement(SP_REACT.Fragment, null,
                    SP_REACT.createElement(StepHeader, { step: 4, total: 4, title: tr("readyTitle"), detail: tr("readyDetail") }),
                    SP_REACT.createElement("div", { style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 } },
                        SP_REACT.createElement("div", { style: { padding: 18, borderRadius: 12, background: "rgba(255,255,255,.05)" } },
                            SP_REACT.createElement("span", { style: { display: "block", fontSize: 12, opacity: .52 } }, tr("country").toUpperCase()),
                            SP_REACT.createElement("strong", { style: { display: "block", marginTop: 4, fontSize: 22 } }, countryName(countries.find((entry) => entry.code === country)) || country)),
                        SP_REACT.createElement("div", { style: { padding: 18, borderRadius: 12, background: "rgba(255,255,255,.05)" } },
                            SP_REACT.createElement("span", { style: { display: "block", fontSize: 12, opacity: .52 } }, tr("sources").toUpperCase()),
                            SP_REACT.createElement("strong", { style: { display: "block", marginTop: 4, fontSize: 22 } }, selectedSources.length))),
                    SP_REACT.createElement("div", { style: { marginTop: 12, padding: 18, borderRadius: 12, background: "rgba(255,255,255,.05)" } },
                        SP_REACT.createElement("span", { style: { display: "block", fontSize: 12, opacity: .52, marginBottom: 10 } }, tr("tabs").toUpperCase()),
                        SP_REACT.createElement("div", { style: { display: "flex", flexWrap: "wrap", gap: 8 } },
                            PRESET_TABS.filter(([key]) => presetTabs[key]).map(([key, label]) => SP_REACT.createElement("span", { key: key, style: { padding: "7px 11px", borderRadius: 8, background: "rgba(255,255,255,.08)" } }, label)),
                            customTabs.map((name) => SP_REACT.createElement("span", { key: name, style: { padding: "7px 11px", borderRadius: 8, background: "rgba(255,255,255,.08)" } }, name)))),
                    message ? SP_REACT.createElement("div", { style: { marginTop: 14, opacity: .72 } }, message) : null) : null),
            SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { position: "absolute", left: 54, right: 54, bottom: 34, zIndex: 50, display: "flex", justifyContent: "space-between", gap: 10 } },
                SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 130 }, disabled: step === 1, onClick: () => setStep(value => Math.max(1, value - 1)) },
                    "\u2190 ",
                    tr("back")),
                step < 4 ? SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 150, fontWeight: 700 }, disabled: step === 2 && selectedSources.length === 0, onClick: () => { setMessage(""); setStep(value => Math.min(4, value + 1)); } },
                    tr("continue"),
                    " \u2192") : SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 190, fontWeight: 700 }, onClick: () => void finish() }, tr("enterKiosk"))))));
}
function saveAndSet(config, setBootstrap, bootstrap) {
    return rpc("save_config", config).then((result) => {
        if (result?.ok)
            setBootstrap({ ...bootstrap, config: result.config });
        return result;
    });
}
function SettingsRoute() {
    const { bootstrap, setBootstrap } = useBootstrap();
    const [sourceUrl, setSourceUrl] = useState("");
    const [catalogCountry, setCatalogCountry] = useState("");
    const [catalogQuery, setCatalogQuery] = useState("");
    const [catalogResults, setCatalogResults] = useState([]);
    const [onlineCatalogBusy, setOnlineCatalogBusy] = useState(false);
    const [newTabName, setNewTabName] = useState("");
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState("");
    const settingsScrollRef = useRef(null);
    useForcedWheelScroll(settingsScrollRef);
    const config = bootstrap?.config;
    const countries = bootstrap?.countries ?? [];
    const searchCountry = (catalogCountry || config?.country || "IT").toUpperCase();
    useEffect(() => {
        if (config && !catalogCountry)
            setCatalogCountry(config.country || "IT");
    }, [config?.country]);
    useEffect(() => {
        let alive = true;
        if (!config)
            return () => { alive = false; };
        void rpc("search_sources", searchCountry, catalogQuery).then((result) => {
            if (!alive)
                return;
            const existing = new Set(config.sources.map((source) => source.id));
            setCatalogResults((result?.sources ?? []).filter((source) => !existing.has(source.id)).slice(0, 20));
        }).catch(() => { if (alive)
            setCatalogResults([]); });
        return () => { alive = false; };
    }, [searchCountry, catalogQuery, config?.sources.length]);
    if (!bootstrap || !config)
        return SP_REACT.createElement(FullscreenShell, null,
            SP_REACT.createElement("div", { style: { height: "100%", display: "flex", alignItems: "center", justifyContent: "center" } },
                SP_REACT.createElement(Spinner, null),
                "\u00A0 ",
                tr("loading")));
    const persist = async (next) => { setBusy(true); try {
        await saveAndSet(next, setBootstrap, bootstrap);
    }
    finally {
        setBusy(false);
    } };
    const normalizedActiveTab = (tabs, activeId = config.activeTabId) => {
        const active = tabs.find((tab) => tab.id === activeId && tab.enabled !== false) ?? tabs.find((tab) => tab.enabled !== false) ?? tabs[0];
        return active?.id ?? "";
    };
    const removeSource = async (source) => {
        const sources = config.sources.filter((value) => value.id !== source.id);
        const tabs = config.tabs.map((tab) => ({ ...tab, sourceIds: tab.sourceIds.filter((id) => id !== source.id) }));
        await persist({ ...config, sources, tabs });
    };
    const toggleSource = async (source) => {
        await persist({ ...config, sources: config.sources.map((value) => value.id === source.id ? { ...value, enabled: value.enabled === false } : value) });
    };
    const addSource = async () => {
        if (!sourceUrl.trim())
            return;
        setBusy(true);
        setMessage("");
        try {
            const result = await rpc("discover_source", sourceUrl.trim(), searchCountry, "");
            if (result?.ok && result.source) {
                const source = result.source;
                const exists = config.sources.some((value) => value.id === source.id);
                const sources = exists ? config.sources : [...config.sources, source];
                const tabs = config.tabs.map((tab, index) => index === 0 ? { ...tab, sourceIds: Array.from(new Set([...tab.sourceIds, source.id])) } : tab);
                const saved = await rpc("save_config", { ...config, sources, tabs });
                if (saved?.ok)
                    setBootstrap({ ...bootstrap, config: saved.config });
                setSourceUrl("");
                setMessage(tr("sourceAdded", { name: source.name }));
            }
            else
                setMessage(localizeBackendError(result?.error, "sourceNotFound"));
        }
        finally {
            setBusy(false);
        }
    };
    const addCountryHeadlines = async () => {
        setBusy(true);
        setMessage("");
        try {
            const result = await rpc("make_country_source", searchCountry);
            if (result?.ok && result.source) {
                const source = result.source;
                if (config.sources.some((value) => value.id === source.id)) {
                    setMessage(tr("alreadyPresent", { name: source.name }));
                    return;
                }
                const sources = [...config.sources, source];
                const tabs = config.tabs.map((tab, index) => index === 0 ? { ...tab, sourceIds: Array.from(new Set([...tab.sourceIds, source.id])) } : tab);
                const saved = await rpc("save_config", { ...config, sources, tabs });
                if (saved?.ok)
                    setBootstrap({ ...bootstrap, config: saved.config });
                setMessage(tr("sourceAdded", { name: source.name }));
            }
            else
                setMessage(localizeBackendError(result?.error, "countryHeadlinesFailed"));
        }
        finally {
            setBusy(false);
        }
    };
    const searchOnlineCatalog = async () => {
        if (catalogQuery.trim().length < 2) {
            setMessage(tr("onlineSearchMinChars"));
            return;
        }
        setOnlineCatalogBusy(true);
        setMessage("");
        try {
            const result = await rpc("search_online_sources", searchCountry, catalogQuery.trim());
            if (result?.ok) {
                const existing = new Set(config.sources.map((source) => source.id));
                const merged = new Map();
                catalogResults.forEach((source) => { if (!existing.has(source.id))
                    merged.set(source.id, source); });
                (result.sources ?? []).forEach((source) => { if (!existing.has(source.id))
                    merged.set(source.id, source); });
                setCatalogResults(Array.from(merged.values()).slice(0, 30));
                setMessage((result.sources ?? []).length ? tr("onlineSourcesFound", { n: result.sources.length }) : tr("noMoreSources"));
            }
            else
                setMessage(localizeBackendError(result?.error, "onlineSearchUnavailable"));
        }
        catch (exc) {
            setMessage(String(exc?.message ?? exc));
        }
        finally {
            setOnlineCatalogBusy(false);
        }
    };
    const addCatalogSource = async (source) => {
        if (config.sources.some((value) => value.id === source.id))
            return;
        const sources = [...config.sources, source];
        const tabs = config.tabs.map((tab, index) => index === 0 ? { ...tab, sourceIds: Array.from(new Set([...tab.sourceIds, source.id])) } : tab);
        await persist({ ...config, sources, tabs });
        setMessage(tr("sourceAdded", { name: source.name }));
    };
    const addTab = async () => {
        const name = newTabName.trim();
        if (!name)
            return;
        await persist({ ...config, tabs: [...config.tabs, { id: nextId("tab"), name, sourceIds: [], enabled: true }] });
        setNewTabName("");
    };
    const moveTab = async (index, step) => {
        const nextIndex = index + step;
        if (nextIndex < 0 || nextIndex >= config.tabs.length)
            return;
        const tabs = [...config.tabs];
        const [tab] = tabs.splice(index, 1);
        tabs.splice(nextIndex, 0, tab);
        await persist({ ...config, tabs });
    };
    const toggleTab = async (tab) => {
        const currentlyEnabled = tab.enabled !== false;
        if (currentlyEnabled && config.tabs.filter((value) => value.enabled !== false).length <= 1) {
            setMessage(tr("mustKeepActiveTab"));
            return;
        }
        const tabs = config.tabs.map((value) => value.id === tab.id ? { ...value, enabled: !currentlyEnabled } : value);
        await persist({ ...config, tabs, activeTabId: normalizedActiveTab(tabs, config.activeTabId) });
    };
    const removeTab = async (tab) => {
        if (config.tabs.length <= 1) {
            setMessage(tr("mustKeepTab"));
            return;
        }
        const tabs = config.tabs.filter((value) => value.id !== tab.id);
        await persist({ ...config, tabs, activeTabId: normalizedActiveTab(tabs, config.activeTabId === tab.id ? "" : config.activeTabId) });
    };
    const editTab = (tab) => { window.__deckyNewsTabEditor = { tab, config }; navigate(TAB_EDITOR_ROUTE); };
    const editSource = (source) => { window.__deckyNewsSourceEditor = { source, config }; navigate(SOURCE_EDITOR_ROUTE); };
    const resetAll = async () => {
        if (busy)
            return;
        setBusy(true);
        setMessage("");
        try {
            const result = await rpc("reset_config");
            if (!result?.ok) {
                setMessage(localizeBackendError(result?.error, "resetFailed"));
                return;
            }
            newsUiCache.clear();
            window.__deckyNewsReconfigure = undefined;
            navigate(ONBOARDING_ROUTE);
        }
        finally {
            setBusy(false);
        }
    };
    return (SP_REACT.createElement(FullscreenShell, null,
        SP_REACT.createElement(Focusable, { "flow-children": "vertical", onCancel: goBack, onCancelButton: goBack, style: { height: "100%", minHeight: 0, boxSizing: "border-box", padding: "30px 50px", display: "flex", flexDirection: "column", overflow: "hidden" } },
            SP_REACT.createElement("div", { style: { display: "flex", flex: "0 0 auto", justifyContent: "space-between", alignItems: "center", marginBottom: 22 } },
                SP_REACT.createElement("div", null,
                    SP_REACT.createElement("h1", { style: { margin: 0, fontSize: 35 } }, tr("settings")),
                    SP_REACT.createElement("span", { style: { display: "block", marginTop: 5, opacity: .55, fontSize: 13 } }, tr("settingsDetail"))),
                SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 100 }, onClick: goBack }, tr("close"))),
            SP_REACT.createElement("div", { ref: settingsScrollRef, className: "newsSettingsScroll", style: { flex: "1 1 auto", minHeight: 0, overflowY: "auto", overflowX: "hidden", overscrollBehavior: "contain", paddingRight: 8, paddingBottom: 54, WebkitOverflowScrolling: "touch" } },
                SP_REACT.createElement("section", { style: { marginBottom: 26 } },
                    SP_REACT.createElement("h2", { style: { fontSize: 19, margin: "0 0 10px" } }, tr("tabsHeading")),
                    SP_REACT.createElement(Focusable, { "flow-children": "vertical", style: { display: "flex", flexDirection: "column", gap: 7 } }, config.tabs.map((tab, index) => SP_REACT.createElement(Focusable, { key: tab.id, "flow-children": "horizontal", style: { display: "grid", gridTemplateColumns: "minmax(0,1fr) 92px 92px 48px 48px", gap: 6 } },
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton, minWidth: 0, textAlign: "left", opacity: tab.enabled === false ? .48 : 1 }, onButtonDown: (event) => { const gp = GamepadButton; if (matchesAnyGamepadButton(event?.detail?.button, gp.A, gp.BUTTON_A, gp.OK, gp.ACCEPT)) {
                                event?.preventDefault?.();
                                event?.stopPropagation?.();
                                editTab(tab);
                            } }, onClick: () => editTab(tab) },
                            SP_REACT.createElement("span", { style: { display: "flex", justifyContent: "space-between", width: "100%", gap: 10 } },
                                SP_REACT.createElement("strong", null, displayTabName(tab)),
                                SP_REACT.createElement("span", { style: { opacity: .5 } },
                                    tab.sourceIds.length,
                                    " ",
                                    tr("sources"),
                                    " \u00B7 ",
                                    tr("edit")))),
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 92, minWidth: 92 }, disabled: busy, onClick: () => void toggleTab(tab) }, tab.enabled === false ? tr("enable") : tr("disable")),
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 92, minWidth: 92 }, disabled: busy || config.tabs.length <= 1, onClick: () => void removeTab(tab) },
                            " ",
                            tr("delete")),
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 48, minWidth: 48, padding: 0 }, disabled: index === 0 || busy, onClick: () => void moveTab(index, -1) }, "\u2191"),
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 48, minWidth: 48, padding: 0 }, disabled: index === config.tabs.length - 1 || busy, onClick: () => void moveTab(index, 1) }, "\u2193")))),
                    SP_REACT.createElement(FieldActionRow, { columns: "minmax(0,1fr) 150px", style: { marginTop: 9 } },
                        SP_REACT.createElement(NewsTextField, { label: tr("newTab"), value: newTabName, onChange: (value) => setNewTabName(typeof value === "string" ? value : String(value?.target?.value ?? "")) }),
                        SP_REACT.createElement(FieldActionButton, { disabled: !newTabName.trim() || busy, onClick: () => void addTab() }, tr("createTab")))),
                SP_REACT.createElement("section", { style: { marginBottom: 26 } },
                    SP_REACT.createElement("h2", { style: { fontSize: 19, margin: "0 0 10px" } }, tr("sources")),
                    SP_REACT.createElement(Focusable, { "flow-children": "vertical", style: { display: "flex", flexDirection: "column", gap: 7 } }, config.sources.map((source) => SP_REACT.createElement(Focusable, { key: source.id, "flow-children": "horizontal", style: { display: "grid", gridTemplateColumns: "minmax(0,1fr) 100px 100px", gap: 6 } },
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton, minWidth: 0, opacity: source.enabled === false ? .48 : 1 }, disabled: busy, onClick: () => editSource(source) },
                            SP_REACT.createElement("span", { style: { display: "flex", justifyContent: "space-between", gap: 10, width: "100%", textAlign: "left" } },
                                SP_REACT.createElement("span", { style: { overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" } },
                                    SP_REACT.createElement("strong", null, source.name),
                                    SP_REACT.createElement("span", { style: { opacity: .45, marginLeft: 8 } }, countryName(countries.find((entry) => entry.code === source.country)) || source.country)),
                                SP_REACT.createElement("span", { style: { opacity: .55 } }, tr("edit")))),
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 100, minWidth: 100 }, disabled: busy, onClick: () => void toggleSource(source) }, source.enabled === false ? tr("enable") : tr("disable")),
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 100, minWidth: 100 }, disabled: busy, onClick: () => void removeSource(source) },
                            " ",
                            tr("remove"))))),
                    SP_REACT.createElement("div", { style: { marginTop: 12, padding: 14, borderRadius: 12, background: "rgba(255,255,255,.04)" } },
                        SP_REACT.createElement("strong", { style: { display: "block", marginBottom: 8 } }, tr("addSourcesAny")),
                        SP_REACT.createElement(FieldActionRow, { columns: "220px minmax(0,1fr) 170px" },
                            SP_REACT.createElement(CountryDropdown, { countries: countries, value: searchCountry, onChange: (code) => { setCatalogCountry(code); setCatalogQuery(""); setMessage(""); }, label: tr("sourceCountry") }),
                            SP_REACT.createElement(NewsTextField, { label: tr("sourceName"), value: catalogQuery, onChange: (value) => setCatalogQuery(typeof value === "string" ? value : String(value?.target?.value ?? "")) }),
                            SP_REACT.createElement(FieldActionButton, { disabled: catalogQuery.trim().length < 2 || onlineCatalogBusy, onClick: () => void searchOnlineCatalog() }, onlineCatalogBusy ? SP_REACT.createElement(Spinner, { size: 18 }) : tr("search"))),
                        SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "grid", gridTemplateColumns: "220px minmax(0,1fr) 170px", gap: 10, alignItems: "center", marginTop: 9 } },
                            SP_REACT.createElement("span", { style: { gridColumn: "1 / span 2", fontSize: 12.5, opacity: .55 } }, catalogResults.length ? `${catalogResults.length} ${tr("sources")}` : tr("chooseSourcesDetail")),
                            SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: "100%", minWidth: 0, height: 48, minHeight: 48 }, disabled: busy, onClick: () => void addCountryHeadlines() },
                                "\uFF0B ",
                                tr("countryHeadlines"))),
                        catalogResults.length ? SP_REACT.createElement(Focusable, { "flow-children": "grid", style: { display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 7, marginTop: 9 } }, catalogResults.map((source) => SP_REACT.createElement(DialogButton, { key: source.id, style: { ...baseButton, minWidth: 0, height: 50 }, disabled: busy, onClick: () => void addCatalogSource(source) },
                            SP_REACT.createElement("span", { style: { display: "flex", justifyContent: "space-between", width: "100%", gap: 8 } },
                                SP_REACT.createElement("span", { style: { overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" } }, source.name),
                                SP_REACT.createElement("span", { style: { opacity: .5 } }, "\uFF0B"))))) : null),
                    SP_REACT.createElement("div", { style: { marginTop: 10, padding: 14, borderRadius: 12, background: "rgba(255,255,255,.04)" } },
                        SP_REACT.createElement(FieldActionRow, { columns: "minmax(0,1fr) 170px" },
                            SP_REACT.createElement(NewsTextField, { label: tr("addSiteFeed"), value: sourceUrl, onChange: (value) => setSourceUrl(typeof value === "string" ? value : String(value?.target?.value ?? "")) }),
                            SP_REACT.createElement(FieldActionButton, { disabled: !sourceUrl.trim() || busy, onClick: () => void addSource() }, busy ? SP_REACT.createElement(Spinner, { size: 18 }) : tr("add"))),
                        message ? SP_REACT.createElement("div", { style: { marginTop: 7, fontSize: 12, opacity: .7 } }, message) : null)),
                SP_REACT.createElement("section", { style: { marginBottom: 26 } },
                    SP_REACT.createElement("h2", { style: { fontSize: 19, margin: "0 0 10px" } }, tr("updateHeading")),
                    SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "grid", gridTemplateColumns: "minmax(0,1fr) 68px 68px", gap: 6 } },
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton, minWidth: 0 } },
                            SP_REACT.createElement("span", { style: { display: "flex", justifyContent: "space-between", width: "100%" } },
                                SP_REACT.createElement("span", null, tr("cacheInterval")),
                                SP_REACT.createElement("strong", null,
                                    config.refreshMinutes,
                                    " ",
                                    tr("minutesUnit")))),
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 68, minWidth: 68 }, disabled: busy || config.refreshMinutes <= 5, onClick: () => void persist({ ...config, refreshMinutes: Math.max(5, config.refreshMinutes - 5) }) }, "\u2212"),
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 68, minWidth: 68 }, disabled: busy || config.refreshMinutes >= 180, onClick: () => void persist({ ...config, refreshMinutes: Math.min(180, config.refreshMinutes + 5) }) }, "+")),
                    SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 7, marginTop: 8 } },
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton }, onClick: () => void rpc("clear_cache").then(() => { newsUiCache.clear(); setMessage(tr("cacheCleared")); }).catch((error) => setMessage(String(error?.message ?? error))) },
                            " ",
                            tr("clearCache")),
                        SP_REACT.createElement(DialogButton, { style: { ...baseButton }, onClick: () => { window.__deckyNewsReconfigure = true; navigate(ONBOARDING_ROUTE); } },
                            " ",
                            tr("repeatSetup")))),
                SP_REACT.createElement("section", { style: { marginTop: 30, paddingTop: 22, borderTop: "1px solid rgba(255,255,255,.10)" } },
                    SP_REACT.createElement("h2", { style: { fontSize: 19, margin: "0 0 8px" } }, tr("resetHeading")),
                    SP_REACT.createElement("p", { style: { margin: "0 0 12px", fontSize: 13, lineHeight: 1.45, opacity: .58 } }, tr("resetDetail")),
                    SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: "100%", minHeight: 50, height: 50, background: "rgba(190,55,55,.20)", border: "1px solid rgba(255,110,110,.22)" }, disabled: busy, onClick: () => void resetAll() },
                        " ",
                        tr("resetAll")))))));
}
function SourceEditorRoute() {
    const state = window.__deckyNewsSourceEditor;
    const { bootstrap } = useBootstrap();
    const source = state?.source;
    const config = state?.config;
    const countries = bootstrap?.countries ?? [];
    const [name, setName] = useState(source?.name ?? "");
    const [country, setCountry] = useState((source?.country || config?.country || "IT").toUpperCase());
    const [siteUrl, setSiteUrl] = useState(source?.siteUrl ?? "");
    const [feedUrl, setFeedUrl] = useState(source?.feedUrl ?? "");
    const [enabled, setEnabled] = useState(source?.enabled !== false);
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState("");
    const scrollRef = useRef(null);
    useForcedWheelScroll(scrollRef);
    if (!source || !config)
        return SP_REACT.createElement(FullscreenShell, null,
            SP_REACT.createElement("div", { style: { padding: 50 } },
                SP_REACT.createElement(DialogButton, { style: baseButton, onClick: goBack }, tr("back")),
                SP_REACT.createElement(EmptyState, { title: tr("sourceNotFound") })));
    const save = async () => {
        const nextName = name.trim();
        if (!nextName) {
            setMessage(tr("sourceName"));
            return;
        }
        setBusy(true);
        setMessage("");
        try {
            const normalizedSite = siteUrl.trim();
            const normalizedFeed = feedUrl.trim();
            const identityChanged = normalizedSite !== (source.siteUrl || "");
            const edited = {
                ...source,
                name: nextName,
                country: country.toUpperCase(),
                siteUrl: normalizedSite,
                feedUrl: normalizedFeed,
                enabled,
                ...(identityChanged ? { faviconUrl: "", logoUrl: "" } : {}),
            };
            const nextConfig = { ...config, sources: config.sources.map((value) => value.id === source.id ? edited : value) };
            const result = await rpc("save_config", nextConfig);
            if (!result?.ok) {
                setMessage(localizeBackendError(result?.error, "saveConfigFailed"));
                return;
            }
            newsUiCache.clear();
            window.__deckyNewsSourceEditor = undefined;
            goBack();
        }
        catch (exc) {
            setMessage(String(exc?.message ?? exc));
        }
        finally {
            setBusy(false);
        }
    };
    return (SP_REACT.createElement(FullscreenShell, null,
        SP_REACT.createElement(Focusable, { "flow-children": "vertical", onCancel: goBack, onCancelButton: goBack, style: { height: "100%", boxSizing: "border-box", padding: "34px 54px", display: "flex", flexDirection: "column" } },
            SP_REACT.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 } },
                SP_REACT.createElement("div", null,
                    SP_REACT.createElement("span", { style: { fontSize: 12, opacity: .5 } }, tr("editSource")),
                    SP_REACT.createElement("h1", { style: { margin: "5px 0 0", fontSize: 34 } }, source.name)),
                SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 100 }, onClick: goBack }, tr("cancel"))),
            SP_REACT.createElement("div", { ref: scrollRef, className: "newsSettingsScroll", style: { flex: 1, minHeight: 0, overflowY: "auto", overflowX: "hidden", paddingRight: 8, paddingBottom: 34 } },
                SP_REACT.createElement(NewsTextField, { label: tr("sourceName"), value: name, onChange: (value) => setName(typeof value === "string" ? value : String(value?.target?.value ?? "")), style: { width: "100%" } }),
                SP_REACT.createElement("div", { style: { marginTop: 12 } },
                    SP_REACT.createElement(CountryDropdown, { countries: countries, value: country, onChange: setCountry, label: tr("sourceCountry") })),
                SP_REACT.createElement("div", { style: { marginTop: 12 } },
                    SP_REACT.createElement(NewsTextField, { label: tr("sourceSite"), value: siteUrl, onChange: (value) => setSiteUrl(typeof value === "string" ? value : String(value?.target?.value ?? "")), style: { width: "100%" } })),
                SP_REACT.createElement("div", { style: { marginTop: 12 } },
                    SP_REACT.createElement(NewsTextField, { label: tr("sourceFeed"), value: feedUrl, onChange: (value) => setFeedUrl(typeof value === "string" ? value : String(value?.target?.value ?? "")), style: { width: "100%" } })),
                SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "grid", gridTemplateColumns: "minmax(0,1fr) 170px", alignItems: "center", gap: 8, marginTop: 12, padding: 12, borderRadius: 11, background: "rgba(255,255,255,.045)" } },
                    SP_REACT.createElement("div", null,
                        SP_REACT.createElement("strong", { style: { display: "block" } }, tr("sourceStatus")),
                        SP_REACT.createElement("span", { style: { display: "block", marginTop: 3, fontSize: 12, opacity: .55 } }, enabled ? tr("active") : tr("inactive"))),
                    SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 170 }, onClick: () => setEnabled((value) => !value) }, enabled ? tr("disable") : tr("enable")))),
            message ? SP_REACT.createElement("div", { style: { marginTop: 8, fontSize: 12.5, opacity: .75 } }, message) : null,
            SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 16 } },
                SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 160, fontWeight: 700 }, disabled: busy || !name.trim(), onClick: () => void save() }, busy ? tr("saving") : tr("save"))))));
}
function TabEditorRoute() {
    const state = window.__deckyNewsTabEditor;
    const { bootstrap } = useBootstrap();
    const [name, setName] = useState(state?.tab.name ?? "");
    const [enabled, setEnabled] = useState(state?.tab.enabled !== false);
    const [selectedIds, setSelectedIds] = useState(() => Object.fromEntries((state?.tab.sourceIds ?? []).map((id) => [id, true])));
    const [workingSources, setWorkingSources] = useState(() => state?.config.sources ?? []);
    const [sourceCountry, setSourceCountry] = useState((state?.config.country || "IT").toUpperCase());
    const [sourceQuery, setSourceQuery] = useState("");
    const [catalogResults, setCatalogResults] = useState([]);
    const [onlineBusy, setOnlineBusy] = useState(false);
    const [manualUrl, setManualUrl] = useState("");
    const [discovering, setDiscovering] = useState(false);
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState("");
    const tabEditorScrollRef = useRef(null);
    useForcedWheelScroll(tabEditorScrollRef);
    const countries = bootstrap?.countries ?? [];
    useEffect(() => {
        let alive = true;
        void rpc("search_sources", sourceCountry, sourceQuery).then((result) => {
            if (!alive)
                return;
            const current = new Set(workingSources.map((source) => source.id));
            setCatalogResults((result?.sources ?? []).filter((source) => !current.has(source.id)).slice(0, 30));
        }).catch(() => { if (alive)
            setCatalogResults([]); });
        return () => { alive = false; };
    }, [sourceCountry, sourceQuery, workingSources]);
    if (!state)
        return SP_REACT.createElement(FullscreenShell, null,
            SP_REACT.createElement("div", { style: { padding: 50 } },
                SP_REACT.createElement(DialogButton, { style: baseButton, onClick: goBack }, tr("back")),
                SP_REACT.createElement(EmptyState, { title: tr("tabUnavailable") })));
    const { config, tab } = state;
    const normalizeActive = (tabs, preferred) => {
        const activeIds = tabs.filter((value) => value.enabled !== false).map((value) => value.id);
        return activeIds.includes(preferred) ? preferred : activeIds[0] ?? tabs[0]?.id ?? "";
    };
    const includeSource = (source) => {
        setWorkingSources((current) => current.some((value) => value.id === source.id) ? current : [...current, source]);
        setSelectedIds((current) => ({ ...current, [source.id]: true }));
        setCatalogResults((current) => current.filter((value) => value.id !== source.id));
        setMessage(tr("sourceAdded", { name: source.name }));
    };
    const searchOnline = async () => {
        const query = sourceQuery.trim();
        if (query.length < 2) {
            setMessage(tr("onlineSearchMinChars"));
            return;
        }
        setOnlineBusy(true);
        setMessage("");
        try {
            const result = await rpc("search_online_sources", sourceCountry, query);
            if (result?.ok) {
                const current = new Set(workingSources.map((source) => source.id));
                const merged = new Map();
                catalogResults.forEach((source) => merged.set(source.id, source));
                (result.sources ?? []).forEach((source) => { if (!current.has(source.id))
                    merged.set(source.id, source); });
                setCatalogResults(Array.from(merged.values()).slice(0, 40));
                setMessage((result.sources ?? []).length ? tr("onlineSourcesAdded", { n: result.sources.length }) : tr("noMoreSources"));
            }
            else
                setMessage(localizeBackendError(result?.error, "onlineSearchUnavailable"));
        }
        catch (exc) {
            setMessage(String(exc?.message ?? exc));
        }
        finally {
            setOnlineBusy(false);
        }
    };
    const discover = async () => {
        if (!manualUrl.trim()) {
            setMessage(tr("enterSourceAddress"));
            return;
        }
        setDiscovering(true);
        setMessage("");
        try {
            const result = await rpc("discover_source", manualUrl.trim(), sourceCountry, "");
            if (result?.ok && result.source) {
                includeSource(result.source);
                setManualUrl("");
            }
            else
                setMessage(localizeBackendError(result?.error, "sourceNotFound"));
        }
        catch (exc) {
            setMessage(String(exc?.message ?? exc));
        }
        finally {
            setDiscovering(false);
        }
    };
    const save = async () => {
        if (!enabled && tab.enabled !== false && config.tabs.filter((value) => value.id !== tab.id && value.enabled !== false).length === 0) {
            setMessage(tr("mustKeepActiveTab"));
            return;
        }
        setBusy(true);
        setMessage("");
        const selectedSourceIds = workingSources.filter((source) => selectedIds[source.id]).map((source) => source.id);
        const tabs = config.tabs.map((value) => value.id === tab.id ? {
            ...value,
            name: name.trim() || value.name,
            enabled,
            sourceIds: selectedSourceIds,
        } : value);
        const result = await rpc("save_config", { ...config, sources: workingSources, tabs, activeTabId: normalizeActive(tabs, config.activeTabId) });
        setBusy(false);
        if (result?.ok) {
            window.__deckyNewsTabEditor = undefined;
            goBack();
        }
        else
            setMessage(localizeBackendError(result?.error, "saveTabFailed"));
    };
    const remove = async () => {
        if (config.tabs.length <= 1) {
            setMessage(tr("mustKeepTab"));
            return;
        }
        setBusy(true);
        setMessage("");
        const tabs = config.tabs.filter((value) => value.id !== tab.id);
        const result = await rpc("save_config", { ...config, sources: workingSources, tabs, activeTabId: normalizeActive(tabs, config.activeTabId === tab.id ? "" : config.activeTabId) });
        setBusy(false);
        if (result?.ok) {
            window.__deckyNewsTabEditor = undefined;
            goBack();
        }
        else
            setMessage(localizeBackendError(result?.error, "deleteTabFailed"));
    };
    return (SP_REACT.createElement(FullscreenShell, null,
        SP_REACT.createElement(Focusable, { "flow-children": "vertical", onCancel: goBack, onCancelButton: goBack, style: { height: "100%", boxSizing: "border-box", padding: "34px 54px" } },
            SP_REACT.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 } },
                SP_REACT.createElement("div", null,
                    SP_REACT.createElement("span", { style: { fontSize: 12, opacity: .5 } }, tr("editTab")),
                    SP_REACT.createElement("h1", { style: { margin: "5px 0 0", fontSize: 34 } }, displayTabName(tab))),
                SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 100 }, onClick: goBack }, tr("cancel"))),
            SP_REACT.createElement("div", { ref: tabEditorScrollRef, style: { flex: 1, minHeight: 0, overflowY: "auto", overflowX: "hidden", paddingRight: 6 } },
                SP_REACT.createElement(NewsTextField, { label: tr("name"), value: name, onChange: (value) => setName(typeof value === "string" ? value : String(value?.target?.value ?? "")), style: { width: "100%" } }),
                SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "grid", gridTemplateColumns: "minmax(0,1fr) 170px", alignItems: "center", gap: 8, marginTop: 12, padding: 12, borderRadius: 11, background: "rgba(255,255,255,.045)" } },
                    SP_REACT.createElement("div", null,
                        SP_REACT.createElement("strong", { style: { display: "block" } }, tr("tabVisibility")),
                        SP_REACT.createElement("span", { style: { display: "block", marginTop: 3, fontSize: 12, opacity: .55 } }, tr("tabVisibilityDetail"))),
                    SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 170 }, onClick: () => setEnabled((value) => !value) }, enabled ? tr("deactivateTab") : tr("activateTab"))),
                SP_REACT.createElement("h2", { style: { fontSize: 18, margin: "22px 0 10px" } }, tr("includedSources")),
                workingSources.length ? SP_REACT.createElement(Focusable, { "flow-children": "grid", style: { display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 8 } }, workingSources.map((source) => {
                    const active = Boolean(selectedIds[source.id]);
                    return SP_REACT.createElement(DialogButton, { key: source.id, style: { ...baseButton, minWidth: 0, height: 54, opacity: active ? 1 : .48, border: active ? "2px solid #fff" : "2px solid transparent" }, onClick: () => setSelectedIds((current) => ({ ...current, [source.id]: !current[source.id] })) },
                        SP_REACT.createElement("span", { style: { display: "flex", justifyContent: "space-between", width: "100%", gap: 8 } },
                            SP_REACT.createElement("span", { style: { overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" } }, source.name),
                            SP_REACT.createElement("span", null, active ? "✓" : "")));
                })) : SP_REACT.createElement("div", { style: { padding: "15px 16px", borderRadius: 10, background: "rgba(255,255,255,.04)", opacity: .68 } }, tr("noSourcesAvailable")),
                SP_REACT.createElement("h2", { style: { fontSize: 18, margin: "26px 0 10px" } }, tr("addSourcesAny")),
                SP_REACT.createElement(FieldActionRow, { columns: "220px minmax(0,1fr) 160px", style: { gap: 8 } },
                    SP_REACT.createElement(CountryDropdown, { countries: countries, value: sourceCountry, onChange: (code) => { setSourceCountry(code); setSourceQuery(""); setMessage(""); }, label: tr("sourceCountry") }),
                    SP_REACT.createElement(NewsTextField, { label: tr("sourceName"), value: sourceQuery, onChange: (value) => setSourceQuery(typeof value === "string" ? value : String(value?.target?.value ?? "")), style: { width: "100%" } }),
                    SP_REACT.createElement(FieldActionButton, { disabled: onlineBusy || sourceQuery.trim().length < 2, onClick: () => void searchOnline() }, onlineBusy ? tr("loading") : tr("search"))),
                catalogResults.length ? SP_REACT.createElement(Focusable, { "flow-children": "grid", style: { display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 8, marginTop: 10 } }, catalogResults.map((source) => SP_REACT.createElement(DialogButton, { key: `add-${source.id}`, style: { ...baseButton, minWidth: 0, height: 54 }, onClick: () => includeSource(source) },
                    SP_REACT.createElement("span", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", gap: 8 } },
                        SP_REACT.createElement("span", { style: { overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" } }, source.name),
                        SP_REACT.createElement("strong", { style: { fontSize: 18 } }, "\uFF0B"))))) : null,
                SP_REACT.createElement(FieldActionRow, { columns: "minmax(0,1fr) 180px", style: { marginTop: 12 } },
                    SP_REACT.createElement(NewsTextField, { label: tr("addSiteFeed"), value: manualUrl, onChange: (value) => setManualUrl(typeof value === "string" ? value : String(value?.target?.value ?? "")) }),
                    SP_REACT.createElement(FieldActionButton, { disabled: discovering || !manualUrl.trim(), onClick: () => void discover() }, discovering ? tr("loading") : tr("add")))),
            message ? SP_REACT.createElement("div", { style: { marginTop: 8, fontSize: 12.5, opacity: .75 } }, message) : null,
            SP_REACT.createElement(Focusable, { "flow-children": "horizontal", style: { display: "flex", justifyContent: "space-between", gap: 10, marginTop: 16 } },
                SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 150, opacity: config.tabs.length <= 1 ? .35 : 1 }, disabled: busy || config.tabs.length <= 1, onClick: () => void remove() }, tr("deleteTab")),
                SP_REACT.createElement(DialogButton, { style: { ...baseButton, width: 160, fontWeight: 700 }, disabled: busy || !name.trim(), onClick: () => void save() }, busy ? tr("saving") : tr("save"))))));
}
function NewsTitle() {
    return SP_REACT.createElement("div", { title: "News", "aria-label": "News", style: { display: "flex", alignItems: "center", justifyContent: "flex-end", width: "100%", height: 34, paddingRight: 8, boxSizing: "border-box" } },
        SP_REACT.createElement(NewspaperIcon, { size: 20 }));
}
export default definePlugin(() => {
    newsDisposed = false;
    routerHook.addRoute(EDICOLA_ROUTE, EdicolaRoute);
    routerHook.addRoute(ARTICLE_ROUTE, ArticleRoute);
    routerHook.addRoute(ONBOARDING_ROUTE, OnboardingRoute);
    routerHook.addRoute(SETTINGS_ROUTE, SettingsRoute);
    routerHook.addRoute(SOURCE_EDITOR_ROUTE, SourceEditorRoute);
    routerHook.addRoute(TAB_EDITOR_ROUTE, TabEditorRoute);
    return {
        name: "News",
        titleView: SP_REACT.createElement(NewsTitle, null),
        content: SP_REACT.createElement(QamContent, null),
        icon: SP_REACT.createElement(NewspaperIcon, { size: 18 }),
        onDismount() {
            newsDisposed = true;
            newsConfigGeneration += 1;
            backgroundUiTimers.forEach((timer) => window.clearTimeout(timer));
            backgroundUiTimers.clear();
            forceRestoreChrome();
            fullscreenDocuments().forEach((doc) => doc.getElementById(CHROME_STYLE_ID)?.remove());
            bootstrapUiCache = null;
            bootstrapLoadPromise = null;
            newsUiCache.clear();
            articleUiCache.clear();
            cardImageMemory.clear();
            imageEnrichmentInFlight.clear();
            allTabsPrefetchInFlight.clear();
            routerHook.removeRoute(EDICOLA_ROUTE);
            routerHook.removeRoute(ARTICLE_ROUTE);
            routerHook.removeRoute(ONBOARDING_ROUTE);
            routerHook.removeRoute(SETTINGS_ROUTE);
            routerHook.removeRoute(SOURCE_EDITOR_ROUTE);
            routerHook.removeRoute(TAB_EDITOR_ROUTE);
        },
    };
});

<div align="center">

# News

### Le notizie diventano un'Edicola da sfogliare con il controller.

Titoli rapidi nel QAM e un lettore a schermo intero che trasforma fonti RSS, siti e canali in un magazine personale per Steam Big Picture.

[![Release](https://img.shields.io/github/v/release/LoZazaMastro/News?style=for-the-badge&label=Release&labelColor=111111&color=ffffff)](https://github.com/LoZazaMastro/News/releases/latest)
[![Licenza MIT](https://img.shields.io/badge/Licenza-MIT-ffffff?style=for-the-badge&labelColor=111111)](LICENSE)

</div>

## Informazione, senza uscire da Gaming Mode

News usa il menu rapido per gli aggiornamenti immediati e una **Edicola** a schermo intero per la lettura. Il layout cambia in base ai contenuti, come una rivista, e ogni elemento resta raggiungibile tramite la navigazione nativa di Decky.

- titoli recenti direttamente nel QAM;
- Edicola full-screen con layout dinamico e navigazione a quattro direzioni;
- tab dedicate a politica, sport, videogiochi, musica, cinema, fumetti, arte, viaggi, cucina o categorie personali;
- fonti differenti per ogni tab, mescolabili anche fra più Paesi;
- categorie rinominabili, riordinabili, disattivabili o eliminabili;
- catalogo iniziale per Paese, ricerca online degli editori e aggiunta manuale di siti o feed RSS/Atom;
- Reader che estrae testo e immagini pubblici quando possibile;
- schede video e contenuti incorporati supportati per YouTube e alcuni link social;
- cache locale e intervallo di aggiornamento configurabile;
- nessuna chiave API richiesta per le normali fonti RSS/Atom.

La classificazione avviene sul singolo articolo: una pubblicazione generalista può alimentare contemporaneamente più sezioni senza essere forzata in un'unica categoria.

## Primo avvio

L'onboarding guida nella scelta di:

1. Paese;
2. fonti;
3. tab e categorie dell'Edicola;
4. riepilogo finale.

Puoi ripeterlo dalle impostazioni. La configurazione esistente resta attiva finché il nuovo percorso non viene completato e confermato.

## Fonti e modalità Reader

Puoi incollare la home page di una testata, un feed RSS/Atom diretto oppure un canale YouTube riconoscibile. Se un sito non espone feed pubblici, blocca l'accesso automatico o non offre un articolo estraibile, News mantiene anteprima e collegamento **Apri sul sito**: non aggira paywall o limitazioni della fonte.

Le immagini vengono cercate nella pagina, nei dati strutturati e nel corpo dell'articolo, scartando icone, avatar e loghi troppo piccoli. Gli asset risolti vengono memorizzati in locale per evitare richieste e caricamenti ripetuti durante la navigazione.

## Lingue

News segue automaticamente la lingua di Steam. Sono incluse traduzioni per italiano, inglese, spagnolo, francese, tedesco, portoghese brasiliano, russo, giapponese e cinese semplificato; le lingue non disponibili usano l'inglese.

## Installazione

Puoi installare e aggiornare News dal Plugin Store di [Playhub](https://github.com/LoZazaMastro/Playhub), oppure scaricare lo ZIP dall'[ultima release](https://github.com/LoZazaMastro/News/releases/latest) e installarlo da **Decky → Impostazioni → Sviluppatore → Installa plugin da ZIP**.

Il core non dipende da helper esclusivi di Windows ed è progettato per funzionare anche sulle installazioni Linux supportate da Decky.

## Sviluppo

```bash
npm install
npm run validate:translations
npm run build
python -m py_compile main.py
```

Il frontend e le traduzioni sono in `src/`; scoperta delle fonti, download, Reader e cache sono gestiti da `main.py`.

## Licenza

News è distribuito con licenza [MIT](LICENSE). I contenuti visualizzati restano di proprietà delle rispettive fonti.

<div align="center">

Creato e mantenuto da **[LoZazaMastro](https://github.com/LoZazaMastro)**.

</div>

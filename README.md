# 言葉 Kotoba Travel

**Impara il giapponese attraverso viaggi, cucina, cultura e quiz.**
App desktop gratuita per Windows e Linux — nessuna connessione richiesta.

[![Release](https://img.shields.io/github/v/release/Rigel899/KOTOBA-TRAVEL?label=versione&color=c0392b)](https://github.com/Rigel899/KOTOBA-TRAVEL/releases/latest)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078d4?logo=windows)](https://github.com/Rigel899/KOTOBA-TRAVEL/releases/latest)
[![Linux](https://img.shields.io/badge/Linux-x86__64-e67e22?logo=linux&logoColor=white)](https://github.com/Rigel899/KOTOBA-TRAVEL/releases/latest)
[![License](https://img.shields.io/badge/licenza-MIT-6c757d)](LICENSE)

---

## Scarica

| Sistema | File | Note |
| --- | --- | --- |
| **Windows 10 / 11** | `kotoba-travel-windows.zip` | Estrai ed esegui `KotobaTravel.exe` |
| **Linux x86\_64** | `kotoba-travel-linux.tar.gz` | Estrai, `chmod +x KotobaTravel`, avvia |

➡️ **[Vai all'ultima release](https://github.com/Rigel899/KOTOBA-TRAVEL/releases/latest)**

---

## Cosa trovi nell'app

- **Quiz** — Hiragana, Katakana, Kanji, Vocabolario, Grammatica, Prova Kotoba
- **Esplora** — luoghi, musei, cucina tipica con storia e ricette
- **Cultura** — lingua, società, tradizioni, storia del Giappone
- **Dojo** — sessioni di studio intensive per kana e kanji
- **Progressi** — statistiche, achievement, storico sessioni
- **Profili locali** — più utenti sullo stesso PC, dati salvati offline

---

## Installazione

### Windows

1. Scarica `kotoba-travel-windows.zip` dalla [release](https://github.com/Rigel899/KOTOBA-TRAVEL/releases/latest)
2. Estrai la cartella
3. Avvia `KotobaTravel.exe`

### Linux

1. Scarica `kotoba-travel-linux.tar.gz` dalla [release](https://github.com/Rigel899/KOTOBA-TRAVEL/releases/latest)
2. Estrai: `tar -xzf kotoba-travel-linux.tar.gz`
3. Rendi eseguibile: `chmod +x KotobaTravel`
4. Avvia: `./KotobaTravel`

---

## Note tecniche

- I profili locali vengono salvati fuori dalla cartella dell'app:
  - Windows: `%APPDATA%\KotobaTravel\`
  - Linux: `~/.local/share/KotobaTravel/`
- Le password sono salvate come hash PBKDF2, mai in chiaro
- I profili sono firmati con HMAC per rilevare modifiche accidentali
- Nessun dato viene inviato a server esterni

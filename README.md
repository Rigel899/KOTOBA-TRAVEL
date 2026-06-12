# Kotoba Travel

Applicazione desktop Flet per studiare giapponese attraverso viaggio, cucina, cultura e quiz.

## Avvio sviluppo

```powershell
python .\run.py
```

## Dati utente

I profili locali non stanno nel progetto: su Windows vengono salvati in `%APPDATA%\KotobaTravel\profiles`.

## Sicurezza locale

Le password e le risposte di recupero sono salvate come hash PBKDF2, non in chiaro. Gli export profilo escludono password, risposte di recupero e firma interna.

I profili locali sono firmati con HMAC per rilevare modifiche manuali accidentali o grossolane. Questa protezione e tamper-evident, non anti-cheat forte: su una app offline l'utente controlla comunque il proprio computer e il codice dell'app.

I nomi utente sono case-insensitive: `Mario`, `MARIO` e `mario` indicano lo stesso account locale.

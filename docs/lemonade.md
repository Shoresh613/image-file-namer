# Lemonade med Gemma 4 31B MTP

Projektet använder nu Lemonades OpenAI-kompatibla API med modellen
`Gemma-4-31B-it-MTP-GGUF`. Tesseract hämtar OCR-text och modellen får
bildens originalbyte följt av OCR-text och instruktionen att svara med högst
15 nyckelord. Ingen bildskalning eller omkomprimering görs.

Filnamnet byggs enbart av datumet och dessa nyckelord. OCR-texten används för
modellens analys och datumtolkning; spaCy-termer läggs inte till. Nyckelord och
delar i bindestrecksord får stor begynnelsebokstav och sätts ihop utan mellanrum:
`ambition-sverige sverige-först riksdagen` blir
`20260923AmbitionSverigeFörstRiksdagen.jpg`.
Varje ord behålls bara första gången det förekommer, även inne i
bindestrecksord och oavsett versaler/gemener. `screenshot` utesluts alltid.
Ordningen från modellen behålls. Hela nyckelord som inte ryms inom
filnamnsgränsen hoppas över, och ord i exkluderingslistan filtreras fortfarande.

Installera och starta [Lemonade](https://lemonade-server.ai/), och kör:

```bash
lemonade pull Gemma-4-31B-it-MTP-GGUF
lemonade status
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python main.py --skip-setup
```

Om spaCy-modellen saknas: kör `./.venv/bin/python -m spacy download en_core_web_sm`.
Tesseract behöver språkpaketen `eng`, `swe` och `deu` (se README).

Scriptet laddar modellen automatiskt via Lemonades `/load`-API innan
batchbearbetningen börjar, med `--batch-size 2048 --ubatch-size 2048`.
Det förebygger den observerade kraschen `non-causal attention requires
n_ubatch >= n_tokens` vid bildanalys. API-användning laddar på samma sätt
modellen före första bildanropet. Lemonade-servern behöver redan vara igång.

## Konfiguration

| Miljövariabel | Standard | Användning |
| --- | --- | --- |
| `LEMONADE_BASE_URL` | `http://localhost:13305/api/v1` | API-basadress inklusive prefix |
| `LEMONADE_MODEL` | `Gemma-4-31B-it-MTP-GGUF` | Modell-ID i Lemonade |
| `LEMONADE_API_KEY` | tom | Bearer-nyckel om servern kräver autentisering |
| `LEMONADE_LLAMACPP_ARGS` | `--batch-size 2048 --ubatch-size 2048` | Laddningsargument för llama.cpp |
| `LEMONADE_TIMEOUT_SECONDS` | `300` | Timeout per anrop, inklusive modelladdning |

Sampling använder temperatur 0, top-k 20, top-p 0,9 och högst 64 output-token.
Anropet begär avstängt tänkande genom `chat_template_kwargs.enable_thinking=false`.
Tillfälliga anslutningsfel och HTTP 408/429/5xx får högst två nya försök.
Fel som saknad modell eller ogiltig bild rapporteras direkt.

Kontextstorlek, MTP och GPU-backend hanteras av Lemonade. Kontrollera
`lemonade status` och serverloggen för en faktisk GPU-körning. Den tidigare
Ollama-kontrollen av `size_vram` används inte; klienten verifierar inte
modellens GPU-residens. Ändra laddningsalternativ i Lemonade vid behov,
till exempel `lemonade load Gemma-4-31B-it-MTP-GGUF --ctx-size 65536`.

## Referenser

- [Lemonades modeller](https://lemonade-server.ai/docs/models.html)
- [API och bildformat](https://lemonade-server.ai/docs/api/openai/)

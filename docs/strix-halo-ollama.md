# Säker Ollama-körning på AMD Strix Halo (Linux)

Projektet begär nu full modell-offload (`num_gpu=-1`), håller modellen laddad i
GPU-minnet i 24 timmar och stoppar körningen om `ollama ps` inte visar att minst
98 % av modellens byte ligger i GPU-minnet. `num_gpu=1` betyder **ett
modellager**, inte en GPU, och får därför inte användas här.

Strix Halo har delat minne: det som Ollama visar som VRAM är reserverat/hanterat
GPU-minne i systemets RAM. En full-offload-modell kan fortfarande använda lite
CPU för tokenisering, I/O och schemaläggning; målet som går att garantera är att
alla modellager körs på GPU, inte att CPU-användningen bokstavligen blir 0 %.

## 1. Installera ROCm-varianten av Ollama

Använd aktuell Ollama samt AMD:s ROCm 7-drivrutin. Ollamas officiella Linux-guide
anger både ROCm 7 och det separata ROCm-paketet:

```bash
curl -fsSL https://ollama.com/download/ollama-linux-amd64-rocm.tar.zst \
  | sudo tar x -C /usr
```

Säkerställ också att tjänstanvändaren får åtkomst till AMD-enheterna:

```bash
sudo usermod -aG render,video ollama
```

Logga ut/in eller starta om efter gruppändringen.

## 2. Lås Ollama till ROCm för gfx1151

Strix Halo / Radeon 8060S är `gfx1151`. Skapa en systemd-override:

```bash
sudo systemctl edit ollama
```

Lägg in följande och spara:

```ini
[Service]
Environment="HSA_OVERRIDE_GFX_VERSION=11.5.1"
Environment="OLLAMA_KEEP_ALIVE=-1"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_DEBUG=1"
```

Starta därefter om tjänsten:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Sätt **inte** `OLLAMA_VULKAN=1` eller `HIP_VISIBLE_DEVICES=-1` i denna
konfiguration. ROCm är den avsedda vägen för Strix Halo; den senare variabeln
stänger av HIP/ROCm-GPU:n helt.

## 3. Verifiera före och under en körning

I en terminal:

```bash
sudo journalctl -fu ollama
```

När modellen laddas ska loggen innehålla `library=ROCm`, `compute=gfx1151` och
`offloaded X/X layers to GPU`. Kontrollera sedan:

```bash
ollama ps
```

Kolumnen `PROCESSOR` ska vara `100% GPU`. Om den visar `CPU` eller en mix ska
du inte köra batchen: minska i första hand kontexten, stäng minneskrävande
program och starta om Ollama.

Projektets `gemma4:31b-gpu` har redan en Modelfile med `num_ctx 262144` och
`num_gpu 999`. Klienten begär i stället **64k** som säker standard, vilket ger
plats för en högupplöst bild, dess vision-token och OCR-text utan att
okontrollerat ta hela Strix Halos delade minne. Pixelmått kan inte direkt
översättas till kontexttoken eftersom visionkodaren först komprimerar bilden.

Höj försiktigt vid behov, exempelvis till 128k:

```bash
OLLAMA_NUM_CTX=131072 ./.venv/bin/python main.py --skip-setup
```

På Strix Halo är för stor kontext den vanligaste orsaken till att den delade
minnesbudgeten spricker. För att medvetet tillåta CPU/partial-offload (inte
rekommenderat) kan kontrollen stängas av temporärt med
`OLLAMA_REQUIRE_FULL_GPU=0`.

## Källor

- [Ollama: GPU-stöd för AMD/ROCm](https://docs.ollama.com/gpu)
- [Ollama: Linux- och systemd-installation](https://docs.ollama.com/linux)
- [Ollama: felsökning av AMD GPU-detektering](https://docs.ollama.com/troubleshooting)
- [Strix Halo gfx1151 – verifierad ROCm-konfiguration](https://github.com/ollama/ollama/issues/14855)

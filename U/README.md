# pTp — Phrase to Playlist

Type a phrase like *"rainy Sunday morning, warm coffee, no plans"* and get back a playlist: a title, a short description, and real songs — each with its artist and a one-line reason it fits. Every track links to Spotify and YouTube search, and can play a 30-second preview right inside the app.

Works with any OpenAI-compatible provider (including free ones), runs entirely on your machine, and has no dependencies.

![black and white, compact UI](https://img.shields.io/badge/UI-monochrome-black)

**English** · [فارسی](README.fa.md)

## Contents

- [Quick start](#quick-start)
- [Features](#features)
- [Setup](#setup)
- [Themes](#themes)
- [Song previews](#song-previews)
- [Use it on your iPhone](#use-it-on-your-iphone)
- [Hosting it 24/7](#hosting-it-247)
- [Build the executables](#build-the-executables)
- [Project layout](#project-layout)
- [Troubleshooting](#troubleshooting)

## Quick start

**Option 1 — download it (Windows)**

1. Grab `PhraseToPlaylistDesktop.exe` (clean window, no console) or `PhraseToPlaylist.exe` (console + browser) from [Releases](https://github.com/3000S-HTTP/pTp/releases).
2. Run it. Your browser opens by itself.

**Option 2 — run from source (any OS)**

```bash
python server.py
```

The console prints the exact URL — normally `http://localhost:8000/playlist.html`. Python 3 is the only requirement; the server uses the standard library only.

**Then, either way:**

1. Open **AI Settings** and paste at least one API key. Leave **API base URL** as `/proxy` unless you know you need something else.
2. Type a phrase and click **Generate playlist**.

## Features

- **Playlist from a phrase** — a mood or moment becomes a titled playlist with a description, real tracks, artists, and a short reason each song fits.
- **Any OpenAI-compatible provider** — OpenAI, Groq, OpenRouter, Google Gemini, Together, Ollama, LM Studio, tokenharbor, and others (see [Setup](#setup)).
- **Multiple API keys with failover** — keys are tried in order and the app rotates to the next one automatically on a bad key, rate limit, or server error.
- **30-second previews** — a ▶ button on every track plays a clip, matched by title and artist so it never plays the wrong song (see [Song previews](#song-previews)).
- **Installable themes** — Monochrome, Liquid Glass, Ocean, Sunset, and Neon, each in light and dark (see [Themes](#themes)).
- **Works on your phone** — the server prints a LAN URL you can open on any device on the same Wi-Fi.
- **Runs anywhere** — one Python file with no dependencies, or a Windows `.exe` (console or desktop app).
- **Built to survive messy models** — a built-in CORS proxy for providers that block browsers, and a forgiving JSON parser that handles markdown fences, single quotes, unquoted keys, trailing commas, wrapper objects, and plain-text track lists.

## Setup

Open **AI Settings** in the app:

| Field | What to put there |
| --- | --- |
| **API keys** | One or more keys for your provider. Stored in this browser only (`localStorage`) — never on the server. Each row has an enable checkbox, Show/Hide, and Delete. |
| **API base URL** | `/proxy` (the default) routes through the built-in proxy, which is what makes providers work in Safari, Chrome, and mobile browsers. Use a full URL such as `https://api.openai.com/v1` only if that provider allows browser CORS requests. |
| **Model** | The model name your provider expects. |

Your key is sent only to the provider you configure, in the request itself. There is no analytics and no third-party backend.

### Provider examples

| Provider | Base URL | Example model |
| --- | --- | --- |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| OpenRouter | `https://openrouter.ai/api/v1` | `meta-llama/llama.3.3-70b-instruct:free` |
| Google Gemini (OpenAI compatibility) | `https://generativelanguage.googleapis.com/v1beta/openai` | `gemini-2.0-flash` |
| Ollama (local, no key) | `http://localhost:11434/v1` | `llama3.1` |
| tokenharbor | `https://tokenharbor.ai/v1` | `deepseek-v4.1-flash:free` |

## Themes

Click **Themes ▸** in the footer to open the theme manager.

- **Install** — under *Browse themes*, click **Install** on the one you want. It moves to *Your themes* and applies immediately.
- **Switch** — click a card under *Your themes*. The active card is outlined.
- **Uninstall** — click **Uninstall** on its card. Removing the active theme falls back to Monochrome, which is always installed and cannot be removed.
- **Light / dark** — click **Dark / Light** in the footer. Every theme ships both variants.

| Theme | What it looks like |
| --- | --- |
| Monochrome | The original black & white — the default, always installed |
| Liquid Glass | Frosted translucent panels over a violet-to-indigo gradient |
| Ocean | Teal-to-navy gradient with deep sea blues |
| Sunset | Orange-to-violet gradient in warm dusk colors |
| Neon | Pastel light / near-black dark with magenta and cyan glow |

Your installed themes and the active choice are saved in this browser (`localStorage`, key `phrase-playlist-themes-v1`). Nothing is sent to the server.

## Song previews

Every track row has a **▶ Preview** button that plays a 30-second clip:

1. It searches Apple's public [iTunes Search API](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/) for `title + artist` — no API key, and it works straight from the browser.
2. Results are scored by title/artist similarity. Only a score of 0.55 or higher plays; otherwise the status line says *No preview found* instead of playing the wrong song.
3. One shared player: press again to pause, again to resume. Generating a new playlist stops playback.

Each lookup is cached after the first click, so replaying is instant and costs no extra requests. Previews need an internet connection — the Spotify and YouTube links work regardless.

## Use it on your iPhone

1. Start the server on your computer (the exe or `python server.py`).
2. Put your computer and phone on the **same network** (same Wi-Fi).
3. In the console, find the "Phone / tablet" URL, e.g. `http://192.168.1.100:8000/playlist.html`.
4. Open it in Safari, then Share → **Add to Home Screen** for an app-like icon.
5. If it does not load, allow the app through your firewall, or check both devices are on the same subnet — VPNs and Hyper-V adapters often get in the way.

## Hosting it 24/7

The app itself is free; only the AI provider can cost money:

- **Local and free forever** — run [Ollama](https://ollama.com), set the base URL to `http://localhost:11434/v1` and use any placeholder key. No internet, no cost, no rate limits — your computer just has to be on.
- **Free API tiers** — Google Gemini and Groq both have generous free tiers, and OpenRouter lists models ending in `:free`. Free tiers have rate limits and can change, so treat them as best-effort, not guaranteed capacity.
- **Free hosting** — deploy `server.py` to Railway, Render, Fly.io, or Cloudflare Workers (free tiers sleep or have quotas), or keep it on a home machine or Raspberry Pi, then point the base URL at a provider with a free tier.

There is no fully unpaid, unlimited, guaranteed-24/7 hosted AI. The closest combination is **local Ollama plus this app on a device that stays on**.

### Deploy to Railway

The app is a single dependency-free Python file, so it deploys as-is: Railway sets `PORT`, the server honors it, binds `0.0.0.0`, skips browser auto-open when hosted, and exposes `GET /healthz`.

1. Push the repository to GitHub.
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** and pick the repository.
3. If asked for a root directory, set it to `U` — the folder containing `server.py`.
4. `Procfile` and `railway.json` supply the start command (`python server.py`) and the health check (`/healthz`); Railway detects Python automatically.
5. Open the generated URL (`https://<your-app>.up.railway.app`) — it redirects to `playlist.html`.
6. Add your key in **AI Settings** and keep the base URL as `/proxy`.

Optional variables (Railway → Variables):

| Variable | Purpose |
| --- | --- |
| `UPSTREAM_BASE` | Change the default upstream API, e.g. `https://api.openai.com/v1`. |
| `NO_BROWSER` | Set to `1` to never auto-open a browser (automatic when hosted). |

Hosting notes:

- The site is public — anyone with the URL can open the UI. Keys live in each visitor's own `localStorage` and are never stored server-side, so nobody can see yours, though the proxy does forward whatever key the visitor supplies.
- Railway's trial credit expires; an always-on service needs a paid plan. For a $0 always-on setup, run the app on your own device instead.

## Build the executables

Run these from the `U/` folder. Both write to `U/dist/`.

**Console/server exe** — runs the local server and opens your default browser:

```bash
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --onefile --name "PhraseToPlaylist" --add-data "playlist.html;." --console server.py
```

**Desktop app** — opens in its own native window instead of a browser tab, with no console window:

```bash
python -m pip install pyinstaller pywebview pythonnet
python -m PyInstaller --noconfirm --onefile --windowed --name "PhraseToPlaylistDesktop" --add-data "playlist.html;." --hidden-import server --collect-all webview --collect-all pythonnet --collect-all clr_loader desktop/app.py
```

The desktop app uses `desktop/app.py` to embed the UI with **WebView2** (the Edge Chromium runtime) via pywebview. Windows 10/11 only; WebView2 is preinstalled on current Windows — if the window is blank, install the WebView2 Runtime from Microsoft.

## Project layout

Paths are relative to the repository root:

```
README.md            this document
U/                   the app folder (Railway deploys this directory)
U/playlist.html      the entire UI — HTML, CSS and JavaScript in one file
U/server.py          static server + API proxy, standard library only
U/desktop/app.py     WebView2 wrapper for the Windows desktop app
U/Procfile           Railway start command
U/railway.json       Railway build settings and health check
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `Failed to fetch` | You opened the file directly (`file://`). Run `python server.py` or the exe and use the `http://localhost:...` URL it prints. |
| `Failed to fetch` with a direct provider URL | That provider does not allow browser CORS. Use the default `/proxy` base URL instead. |
| `401` / key rejected | The key is invalid or disabled. Rotate it with your provider, or re-enable it in **AI Settings**. |
| `502` proxy error | Transient upstream failure — the proxy retries three times. Try again or switch keys. |
| `Could not parse ... JSON` | Open the **Raw model response** panel to see what came back; if it recurs, switch to a model that follows JSON instructions better. |
| **▶ Preview** says *No preview found* | The song is not in the iTunes catalogue, or the title/artist differed too much. The Spotify and YouTube links still work. |
| Installed theme disappeared | Themes are stored in `localStorage`, so clearing site data removes them. Reinstall from *Browse themes*. |

## License

MIT. Use it, change it, ship it.

# pTp — Phrase to Playlist

Turn a phrase like *"rainy Sunday morning, warm coffee, no plans"* into a curated playlist using any OpenAI-compatible AI API.

Describe a mood, a moment, or a vibe and the app asks an AI model to return real songs with artists and a short reason each one fits. Every track links out to Spotify and YouTube search.

![black and white, compact UI](https://img.shields.io/badge/UI-monochrome-black)

## Features

- **Phrase to playlist** — natural-language prompt becomes a titled playlist with a description.
- **Any OpenAI-compatible API** — OpenAI, Groq, OpenRouter, Google Gemini (compatibility endpoint), Together, Ollama, LM Studio, tokenharbor, and more.
- **Multiple API keys** — add two or more keys; they are tried in order and the app rotates to the next enabled key automatically when one fails (bad key, rate limit, server error).
- **Local proxy built in** — many providers do not send CORS headers, so the browser cannot call them directly. The bundled proxy forwards `/proxy/*` to the upstream API and adds CORS, so the UI works in Safari, Chrome, and mobile browsers.
- **Works on your iPhone** — the server binds to your LAN and prints a URL you can open on your phone.
- **Forgiving JSON parser** — handles markdown fences, single quotes, unquoted keys, trailing commas, wrapper objects, and plain-text track lists.
- **Monochrome compact UI** — black and white, light and dark.
- **Single-file executable** — build a standalone `.exe` with PyInstaller.

## Quick start

### Option A — run the executable (Windows)

1. Run `dist\PhraseToPlaylist.exe`.
2. Your browser opens automatically. The console prints the local and LAN URLs.
3. Open **AI Settings**, paste one or more API keys, set the base URL and model, then click **Generate playlist**.

### Option B — run from source

```bash
python server.py
```

Then open `http://localhost:8000/playlist.html`.

No dependencies are required — `server.py` only uses the Python standard library.

## Using it on your iPhone

1. Start the server on your computer (exe or `python server.py`).
2. Make sure both the computer and the iPhone are on the **same network** (Wi-Fi or the router both are connected to).
3. In the console, find the "Phone / tablet" URL, for example `http://192.168.1.100:8000/playlist.html`.
4. Open that URL in Safari. Use Share → **Add to Home Screen** for an app-like icon.
5. If it does not load, allow the app through your firewall, or check that your computer and phone are on the same subnet (VPNs and Hyper-V adapters can interfere).

## Configuration

Open **AI Settings** in the app:

| Field | Meaning |
| --- | --- |
| **API keys** | One or more keys. Stored only in your browser's `localStorage`. Each row has an enable checkbox, Show/Hide, and Delete. |
| **API base URL** | `/proxy` (default) routes through the built-in proxy. For direct calls use a full URL such as `https://api.openai.com/v1`. |
| **Model** | The model name for your provider. |

Keys never leave your machine except in the request to the provider you configure. There is no analytics and no third-party backend.

### Provider examples

| Provider | Base URL | Example model |
| --- | --- | --- |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| OpenRouter | `https://openrouter.ai/api/v1` | `meta-llama/llama-3.3-70b-instruct:free` |
| Google Gemini (OpenAI compatibility) | `https://generativelanguage.googleapis.com/v1beta/openai` | `gemini-2.0-flash` |
| Ollama (local, no key) | `http://localhost:11434/v1` | `llama3.1` |
| tokenharbor | `https://tokenharbor.ai/v1` | `deepseek-v4.1-flash:free` |

When you use a direct URL instead of `/proxy`, the provider must allow browser CORS requests.

## Free and low-cost options

The app is free; you only choose what powers the AI:

- **Fully local and free forever** — run [Ollama](https://ollama.com) and set the base URL to `http://localhost:11434/v1` with any key placeholder. No internet, no cost, no rate limits. Requires your computer to be on.
- **Free API tiers** — Google Gemini and Groq both have generous free tiers; OpenRouter lists models ending in `:free`. Free tiers have rate limits and can change, so they are not a guarantee of 24/7 capacity.
- **Free hosting for 24/7** — to run unattended, host `server.py` on a free platform such as Cloudflare Workers, Render, Railway, or Fly.io (free tiers sleep or have quotas), or keep it running on a home machine or Raspberry Pi. Point the base URL at a provider with a free tier.

There is no fully unpaid, unlimited, guaranteed-24/7 hosted AI. The closest combination is **local Ollama + this app on an always-on device**.

## Deploy to Railway

The app is a single Python file with no dependencies, so it deploys as-is. Railway sets a `PORT` environment variable and the server already honors it, binds `0.0.0.0`, skips browser auto-open when hosted, and exposes `GET /healthz`.

1. Push this folder to a GitHub repo (already done for `pTp`).
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
3. Pick the repo. If Railway asks for the root directory, set it to `U` (the folder that contains `server.py`).
4. Railway detects Python via Nixpacks. The included `Procfile` and `railway.json` set the start command (`python server.py`) and health check (`/healthz`).
5. Once deployed, open the generated URL (`https://<your-app>.up.railway.app` — it redirects to `playlist.html`).
6. Enter your API key in **AI Settings** on the site. The base URL stays `/proxy`.

Optional environment variables (Railway → Variables):

| Variable | Purpose |
| --- | --- |
| `UPSTREAM_BASE` | Change the default upstream API, e.g. `https://api.openai.com/v1`. |
| `NO_BROWSER` | Set to `1` to never auto-open a browser (also automatic when hosted). |

Important notes for hosting:

- The page is served over HTTPS, which browsers require for reliable behavior, but it is **public**. Anyone with the URL can open the UI. Since keys live in each visitor's browser `localStorage` and are not stored on the server, nobody can see your key — but the proxy does forward whatever key a visitor supplies.
- Railway's free trial credit runs out; a permanently running service needs a paid plan. For a truly $0 always-on setup, run the app on your own device instead.

## Telegram bot

`bot.py` is a Telegram bot version. Type a phrase and it replies with the playlist name and every track as regular chat messages, each with official Spotify / YouTube / YouTube Music links. It sends links only — it does not download or send audio. If anything fails, the bot reports the reason in the chat.

### Create the bot

1. Open Telegram, message [@BotFather](https://t.me/BotFather), send `/newbot`, follow the prompts.
2. Copy the bot token it gives you.

### Run it locally

```bash
set TELEGRAM_BOT_TOKEN=123456:ABC...
set API_KEY=your-provider-key
python bot.py
```

### Deploy as a Railway service

1. In the same Railway project, click **New** → **GitHub Repo** → pick the repo again (create a second service).
2. Set the root directory to `U/bot` (not `U` — the bot folder has its own start command).
3. Leave the start command as-is; `bot/railway.json` and `bot/Procfile` already run `python bot.py`.
4. Add **Variables**:
   - `TELEGRAM_BOT_TOKEN` — from BotFather.
   - `API_KEY` — your provider key.
   - `UPSTREAM_BASE` — optional, defaults to `https://tokenharbor.ai/v1`.
   - `MODEL` — optional, defaults to `deepseek-v4.1-flash:free`.
   - `TRACKS` — optional, default `20`.
5. Deploy. Send your bot a phrase on Telegram to test.

The bot does not need a public port or health check — it uses long polling.

## Build the executable

```bash
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --onefile --name "PhraseToPlaylist" --add-data "playlist.html;." --console server.py
```

The result is `dist/PhraseToPlaylist.exe`.

## Project layout

```
playlist.html   the entire UI (HTML, CSS, JS)
server.py       static server + API proxy, auto-opens the browser
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `Failed to fetch` | You opened the file directly (`file://`). Run `python server.py` or the exe and use `http://localhost:...`. |
| `Failed to fetch` with a direct provider URL | The provider does not allow browser CORS. Use the default `/proxy` base URL instead. |
| `401` / key rejected | The key is invalid or disabled. Rotate it with your provider. |
| `502` proxy error | Transient upstream failure. The proxy retries three times; try again or switch keys. |
| `Could not parse ... JSON` | Open the **Raw model response** panel and, if needed, switch to a model that follows JSON instructions better. |
| Button stuck on `Curating...` | Update to the current version; this was fixed. |

## License

MIT. Use it, change it, ship it.
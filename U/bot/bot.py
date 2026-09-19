import os
import re
import sys
import json
import time
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
API_KEY = os.environ.get("API_KEY", "").strip()
BASE_URL = os.environ.get("UPSTREAM_BASE", "https://tokenharbor.ai/v1").rstrip("/")
MODEL = os.environ.get("MODEL", "deepseek-v4.1-flash:free")
TRACKS = os.environ.get("TRACKS", "20")

TG = "https://api.telegram.org/bot%s" % BOT_TOKEN


def http_json(url, payload=None, headers=None, timeout=120):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def strip_html(text):
    text = re.sub(r"<[^>]+>", "", text)
    return (text.replace("&amp;", "&").replace("&lt;", "<")
            .replace("&gt;", ">").replace("&quot;", '"'))


def send_message(chat_id, text, parse_mode=None, reply_markup=None):
    for chunk in split_message(text, 4000):
        payload = {"chat_id": chat_id, "text": chunk, "disable_web_page_preview": True}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            http_json(TG + "/sendMessage", payload)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:500]
            sys.stderr.write("sendMessage failed: HTTP %s %s\n" % (e.code, body))
            if parse_mode:
                payload.pop("parse_mode", None)
                payload["text"] = strip_html(chunk)
                try:
                    http_json(TG + "/sendMessage", payload)
                except Exception as e2:
                    sys.stderr.write("plain fallback failed: %s\n" % e2)
        except Exception as e:
            sys.stderr.write("sendMessage failed: %s\n" % e)


def split_message(text, limit):
    if len(text) <= limit:
        return [text]
    parts = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > limit:
            parts.append(current)
            current = line
        else:
            current = current + "\n" + line if current else line
    if current:
        parts.append(current)
    return parts


def escape_html(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def track_urls(track):
    query = urllib.parse.quote((str(track.get("title") or "") + " " + str(track.get("artist") or "")).strip())
    return {
        "youtube": "https://www.youtube.com/results?search_query=" + query,
        "youtube_music": "https://music.youtube.com/search?q=" + query,
        "spotify": "https://open.spotify.com/search/" + query,
    }


def enrich(playlist):
    for track in playlist["tracks"]:
        track["links"] = track_urls(track)
    return playlist


def build_prompt(phrase, count):
    return "\n".join([
        "You are a music curator. Build a playlist for this request:",
        '"%s"' % phrase,
        "",
        "Constraints:",
        "- Exactly %s tracks." % count,
        "- Use real, existing songs with correct artist names.",
        "- Avoid repeating the same artist more than twice.",
        "",
        "Return ONLY valid JSON with this exact shape, no markdown, no commentary:",
        '{"name":"<catchy playlist title>","description":"<one sentence about the vibe>","tracks":[{"title":"<song>","artist":"<artist>","why":"<max 12 words on why it fits>"}]}',
    ])


def sanitize(strv):
    return (strv.lstrip("\uFEFF")
            .replace("\u201c", '"').replace("\u201d", '"')
            .replace("\u2018", "'").replace("\u2019", "'")
            .replace(",]", "]").replace(",}", "}"))


def repair(strv):
    out = []
    in_str = False
    quote = ""
    i = 0
    while i < len(strv):
        ch = strv[i]
        if in_str:
            if ch == "\\":
                out.append(ch + (strv[i + 1] if i + 1 < len(strv) else ""))
                i += 2
                continue
            if ch == quote:
                in_str = False
                out.append('"')
            elif ch == '"':
                out.append('\\"')
            elif ch == "\n":
                out.append("\\n")
            elif ch != "\r":
                out.append(ch)
        else:
            if ch in ('"', "'"):
                in_str = True
                quote = ch
                out.append('"')
            else:
                out.append(ch)
        i += 1
    text = "".join(out)
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', text)
    text = re.sub(r",\s*([}\]])", r"\1", text)
    text = re.sub(r"\bNaN\b", "null", text)
    text = re.sub(r"\bNone\b", "null", text)
    text = re.sub(r"\bTrue\b", "true", text)
    text = re.sub(r"\bFalse\b", "false", text)
    return text


def parse_loose(text):
    for attempt in (text, sanitize(text), repair(text), repair(sanitize(text))):
        try:
            return json.loads(attempt)
        except Exception:
            pass
    return None


def extract_json(text):
    if not text:
        raise ValueError("empty response")
    cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", text.strip())
    cleaned = re.sub(r"```\s*$", "", cleaned).strip()

    direct = parse_loose(cleaned)
    if direct:
        return direct

    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        sliced = parse_loose(cleaned[start:end + 1])
        if sliced:
            return sliced

    a, b = cleaned.find("["), cleaned.rfind("]")
    if a != -1 and b > a:
        arr = parse_loose(cleaned[a:b + 1])
        if isinstance(arr, list):
            return {"name": "Your playlist", "description": "", "tracks": arr}

    raise ValueError("could not parse JSON: %s" % cleaned[:300])


def normalize(value):
    if not value:
        return None
    if isinstance(value, list):
        value = {"name": "Your playlist", "description": "", "tracks": value}
    for key in ("playlist", "result", "data", "response"):
        if isinstance(value.get(key), (dict, list)):
            nested = normalize(value[key])
            if nested:
                return nested
    if not value.get("tracks") and value.get("songs"):
        value["tracks"] = value["songs"]
    tracks = value.get("tracks")
    if not isinstance(tracks, list):
        return None
    clean = []
    for track in tracks:
        if isinstance(track, str):
            clean.append({"title": track, "artist": "", "why": ""})
            continue
        if not isinstance(track, dict):
            continue
        title = str(track.get("title") or track.get("name") or track.get("song") or track.get("track") or "").strip()
        artist = str(track.get("artist") or track.get("by") or track.get("artist_name") or "").strip()
        why = str(track.get("why") or track.get("reason") or track.get("note") or "").strip()
        if title:
            clean.append({"title": title, "artist": artist, "why": why})
    if not clean:
        return None
    value["tracks"] = clean
    return value


def generate(phrase):
    body = {
        "model": MODEL,
        "temperature": 0.85,
        "max_tokens": 4000,
        "messages": [
            {"role": "system", "content": "You are a concise music curator. Reply with a single valid JSON object and nothing else."},
            {"role": "user", "content": build_prompt(phrase, TRACKS)},
        ],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + API_KEY,
        "Accept": "application/json",
        "User-Agent": "PhraseToPlaylistBot/1.0",
    }
    last = None
    for attempt in range(3):
        try:
            data = http_json(BASE_URL + "/chat/completions", body, headers)
            choice = (data.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            content = message.get("content") or message.get("reasoning_content") or choice.get("text") or ""
            if isinstance(content, list):
                content = "".join(p.get("text", "") if isinstance(p, dict) else "" for p in content)
            if not str(content).strip():
                raise ValueError("model returned an empty response")
            return normalize(extract_json(str(content)))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            last = "API %d: %s" % (e.code, detail)
            if e.code < 500:
                break
        except Exception as e:
            last = "%s: %s" % (type(e).__name__, e)
        time.sleep(1 + attempt)
    raise RuntimeError(last or "generation failed")


HELP = (
    "Send me a phrase and I'll build a playlist.\n\n"
    "Example:\n"
    "rainy Sunday morning, warm coffee, no plans\n\n"
    "I reply with the playlist name and every track, each with "
    "official Spotify / YouTube / YouTube Music links."
)


def handle(chat_id, text):
    phrase = text.strip()
    print("handle: chat=%s phrase=%r" % (chat_id, phrase[:80]))
    if not phrase:
        send_message(chat_id, "Send me a phrase and I'll build a playlist.")
        return
    if phrase in ("/start", "/help", "help"):
        send_message(chat_id, HELP)
        return

    send_message(chat_id, "Building your playlist for: %s" % phrase)

    try:
        playlist = generate(phrase)
    except Exception as e:
        sys.stderr.write("generate failed: %s\n" % e)
        send_message(chat_id, "Sorry, that failed.\n\nReason: %s" % e)
        return
    if playlist:
        print("handle: got playlist '%s' with %d tracks" % (playlist.get("name"), len(playlist.get("tracks") or [])))
    else:
        print("handle: model returned no usable playlist")

    if not playlist:
        send_message(chat_id, "The model did not return a usable playlist. Try rephrasing your phrase.")
        return

    try:
        enrich(playlist)
        name = playlist.get("name") or "Your playlist"
        desc = playlist.get("description") or ""
        tracks = playlist["tracks"]

        lines = ["<b>%s</b>" % escape_html(name)]
        if desc:
            lines.append(escape_html(desc))
        lines.append("")
        for i, track in enumerate(tracks):
            links = track.get("links", {})
            lines.append("<b>%d. %s</b> — %s" % (
                i + 1,
                escape_html(track.get("artist") or "Unknown artist"),
                escape_html(track.get("title") or "Untitled"),
            ))
            if track.get("why"):
                lines.append("<i>%s</i>" % escape_html(track["why"]))
            lines.append('<a href="%s">Spotify</a> | <a href="%s">YouTube</a> | <a href="%s">YouTube Music</a>' % (
                links.get("spotify", ""),
                links.get("youtube", ""),
                links.get("youtube_music", ""),
            ))
            lines.append("")
        send_message(chat_id, "\n".join(lines), parse_mode="HTML")
    except Exception as e:
        sys.stderr.write("render failed: %s\n" % e)
        send_message(chat_id, "I built the playlist but could not format it.\n\nReason: %s" % e)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"ok"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", "8080"))
    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    except OSError as e:
        sys.stderr.write("health server could not bind port %d: %s\n" % (port, e))
        return
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print("Health server listening on /healthz (port %d)." % port)


def main():
    if not BOT_TOKEN:
        sys.exit("TELEGRAM_BOT_TOKEN is not set.")
    if not API_KEY:
        sys.exit("API_KEY is not set.")
    print("Bot started. Upstream %s, model %s" % (BASE_URL, MODEL))
    start_health_server()
    try:
        me = http_json(TG + "/getMe").get("result", {})
        print("Bot identity: @%s (%s). Message THIS bot." % (me.get("username"), me.get("first_name")))
    except urllib.error.HTTPError as e:
        sys.stderr.write("getMe failed: HTTP %s %s\n" % (e.code, e.read().decode("utf-8", "replace")[:300]))
    except Exception as e:
        sys.stderr.write("getMe failed: %s\n" % e)
    try:
        http_json(TG + "/deleteWebhook", {"drop_pending_updates": True})
        print("Webhook cleared; using long polling.")
    except urllib.error.HTTPError as e:
        sys.stderr.write("deleteWebhook failed: HTTP %s %s\n" % (e.code, e.read().decode("utf-8", "replace")[:300]))
    except Exception as e:
        sys.stderr.write("deleteWebhook failed: %s\n" % e)
    offset = None
    while True:
        try:
            params = {"timeout": 50}
            if offset is not None:
                params["offset"] = offset
            url = TG + "/getUpdates?" + urllib.parse.urlencode(params)
            data = http_json(url, timeout=60)
            updates = data.get("result", [])
            if updates:
                print("received %d update(s)" % len(updates))
            for update in updates:
                offset = update["update_id"] + 1
                message = update.get("message") or update.get("edited_message")
                if not message:
                    continue
                chat_id = message["chat"]["id"]
                text = message.get("text")
                if text:
                    try:
                        handle(chat_id, text)
                    except Exception as e:
                        sys.stderr.write("handle failed: %s\n" % e)
                        send_message(chat_id, "Unexpected error while handling that message.\n\nReason: %s" % e)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            sys.stderr.write("polling HTTP %s: %s\n" % (e.code, body))
            if e.code == 409:
                sys.stderr.write(
                    "409 Conflict: another process is polling this bot token "
                    "(duplicate service or webhook). Waiting...\n")
                try:
                    http_json(TG + "/deleteWebhook", {"drop_pending_updates": False})
                except Exception:
                    pass
                time.sleep(5)
                continue
            time.sleep(3)
        except Exception as e:
            sys.stderr.write("polling error: %s: %s\n" % (type(e).__name__, e))
            time.sleep(3)


if __name__ == "__main__":
    main()
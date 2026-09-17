import os
import sys
import json
import socket
import threading
import urllib.error
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

TARGET = os.environ.get("UPSTREAM_BASE", "https://tokenharbor.ai/v1").rstrip("/")
PORT = int(os.environ.get("PORT", "8000"))


def resource_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


ROOT = resource_dir()


def find_free_port(start):
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start


def candidate_ips():
    ips = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.append(info[4][0])
    except Exception:
        pass
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
    except Exception:
        pass

    seen = []
    for ip in ips:
        if not ip or ip.startswith("127.") or ip.startswith("169.254.") or ip in seen:
            continue
        seen.append(ip)

    def rank(ip):
        if ip.startswith("192.168."):
            return 0
        if ip.startswith("10."):
            return 1
        if ip.startswith("172."):
            return 3
        return 2

    return sorted(seen, key=rank)

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Max-Age": "86400",
}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _cors(self):
        for key, value in CORS.items():
            self.send_header(key, value)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _proxy(self, method):
        path = self.path[len("/proxy"):].split("?", 1)[0]
        if not path.startswith("/"):
            path = "/" + path
        url = TARGET + path

        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None

        headers = {}
        if self.headers.get("Authorization"):
            headers["Authorization"] = self.headers["Authorization"]
        if self.headers.get("Content-Type"):
            headers["Content-Type"] = self.headers["Content-Type"]
        headers["Accept"] = "application/json"

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                status = resp.status
                payload = resp.read()
                content_type = resp.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as e:
            status = e.code
            payload = e.read()
            content_type = e.headers.get("Content-Type", "application/json")
        except Exception as e:
            status = 502
            payload = json.dumps({"error": {"message": "Proxy could not reach %s: %s" % (url, e)}}).encode()
            content_type = "application/json"

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self._cors()
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path.startswith("/proxy"):
            self._proxy("GET")
        elif self.path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/playlist.html")
            self.end_headers()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/proxy"):
            self._proxy("POST")
        else:
            self.send_error(405, "Only /proxy/* accepts POST")


def main():
    port = find_free_port(PORT)
    local_url = "http://localhost:%d/playlist.html" % port
    ips = candidate_ips()
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print("Phrase to Playlist")
    print("Serving   %s" % ROOT)
    print("Proxying  /proxy/* -> %s" % TARGET)
    print("")
    print("  This computer : %s" % local_url)
    print("  Phone / tablet (same Wi-Fi), try one of:")
    if ips:
        for ip in ips:
            print("      http://%s:%d/playlist.html" % (ip, port))
    else:
        print("      (no LAN IP found — connect to Wi-Fi or Ethernet)")
    print("")
    print("On your iPhone: same Wi-Fi network, open one of the URLs above in Safari.")
    print("If none load, allow 'PhraseToPlaylist' through Windows Firewall.")
    print("Press Ctrl+C to stop.")
    threading.Timer(0.8, lambda: webbrowser.open(local_url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
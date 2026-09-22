import os
import sys
import time
import urllib.request
import webview

if getattr(sys, "frozen", False):
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, BASE_DIR)
import server as backend

APP_NAME = "Phrase to Playlist"


def wait_until_ready(port, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/healthz" % port, timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.15)
    return False


def main():
    port = backend.run_local(0, "127.0.0.1")
    if not wait_until_ready(port):
        raise SystemExit("Local server did not start.")

    window = webview.create_window(
        APP_NAME,
        "http://127.0.0.1:%d/playlist.html" % port,
        width=760,
        height=900,
        min_size=(420, 560),
    )
    webview.start()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Local static dev server for the Nova Analytics site.

Mirrors Vercel's `cleanUrls: true` behaviour so local previews match
production: a request for `/login` is served from `web/login.html`, and a bare
`/` is served from `web/index.html`. Not used in production — Vercel serves the
`web/` directory directly.

Usage:  python devserver.py [port]   (default port 4321)
"""
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 4321


class CleanUrlHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def translate_path(self, path):
        local = super().translate_path(path)
        # If the path has no extension and isn't an existing dir/file, try .html
        if not os.path.exists(local) and not os.path.splitext(local)[1]:
            if os.path.isfile(local + ".html"):
                return local + ".html"
        return local

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    with ThreadingHTTPServer(("127.0.0.1", PORT), CleanUrlHandler) as httpd:
        print(f"Nova Analytics dev server -> http://127.0.0.1:{PORT}")
        httpd.serve_forever()

#!/usr/bin/env python3

import argparse
from dataclasses import dataclass
import http.server
import sys

from pathlib import Path

import requests

parser = argparse.ArgumentParser(description='WMTS proxy for French tourist map')
parser.add_argument("upstream_url")
parser.add_argument("self_url")
parser.add_argument("--referer")
parser.add_argument("--user-agent")
args = parser.parse_args()

cache_dir = Path("cache")

@dataclass
class CacheEntry:
    url: str
    content_type: str
    contents: bytes


class Cache:
    def __init__(self, base_dir):
        self.base_dir = base_dir

        base_dir.mkdir(parents=True, exist_ok=True)

    def put(self, e: CacheEntry):
        local_path = self.to_path(e.url, e.content_type)

        if local_path is not None:
            with open(local_path, "wb") as f:
                f.write(e.contents)

    def try_get(self, url) -> CacheEntry:
        if "FORMAT=image/jpeg" in url:
            content_type = "image/jpeg"
        elif "FORMAT=image/png" in url:
            content_type = "image/png"
        else:
            return None

        local_path = self.to_path(url, content_type)

        if local_path is not None and local_path.is_file():
            with open(local_path, "rb") as f:
                return CacheEntry(url=url, content_type=content_type, contents=f.read())

        return None

    def to_path(self, url: str, content_type: str) -> Path:
        if content_type == "image/jpeg":
            return self.base_dir / (url.replace("/", "_").replace("&", "_") + ".jpg")
        elif content_type == "image/png":
            return self.base_dir / (url.replace("/", "_").replace("&", "_") + ".png")
        else:
            # TODO: better logging
            print(f"WARNING: wtf {content_type}")
            return None


cache = Cache(cache_dir)


class MyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        http.server.BaseHTTPRequestHandler.__init__(self, request, client_address, server)
        self.timeout = 10

    def do_GET(self):
        if self.path.startswith("/?SERVICE=WMTS&REQUEST="):
            self.proxy(self.path[2:])    # drop initial "/?"
        else:
            raise Exception(f"Unhandled request GET {self.path}")

    def proxy(self, arglist):
        e = cache.try_get(arglist)

        if e is not None:
            self.serve(e)
            return

        full_url = args.upstream_url + "?" + arglist

        headers = {}

        if args.referer is not None:
            headers["Referer"] = args.referer

        if args.user_agent is not None:
            headers["User-Agent"] = args.user_agent

        r = requests.get(full_url, headers=headers)

        # pass errors through (this might not be right for 30x status)
        if r.status_code != 200:
            self.send_response(r.status_code)

            for key, value in r.headers.items():
                # only selected headers
                if key in ["Content-Type"]:
                    self.send_header(key, value)

            self.end_headers()

        e = CacheEntry(url=arglist,
                       content_type=r.headers["Content-Type"],
                       contents=r.content)
        self.serve(e)
        cache.put(e)

    def serve(self, e: CacheEntry):
        self.send_response(200)
        self.send_header("Content-Type", e.content_type)
        self.end_headers()

        if "&REQUEST=GetCapabilities" in e.url:
            # URL fix-up needed
            fixed_up_content = e.contents.replace(args.upstream_url.encode(), args.self_url.encode())
            self.wfile.write(fixed_up_content)
        else:
            self.wfile.write(e.contents)

def run(server_class=http.server.ThreadingHTTPServer, handler_class=MyHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    print('Listening on port', server_address[1])
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

run()

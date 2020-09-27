# wmts-proxy
A very simple caching proxy for the Web Map Tile Service protocol

What it can do:

- Forward requests to an upstream server
- Cache JPEG & PNG tiles
- Optionally spoof Referer and User-Agent headers

Usage:

    pip3 install requests
    ./wmts-proxy.py <upstream> <self-url> <additional options>

e.g.

    ./wmts-proxy.py "https://example.com/wmts" \
                    "http://localhost:8000/" \
                    --referer "https://example.com/map/"

Then, you would use the following URL in QGIS: http://localhost:8000/?SERVICE=WMTS&REQUEST=GetCapabilities

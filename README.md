# wmts-proxy
A very simple caching proxy for the Web Map Tile Service protocol

Example usage:

    ./wmts-proxy.py "https://example.com/wmts" \
                    "http://localhost:8000/" \
                    --referer "https://example.com/map/"

Then, you would use the following URL in QGIS: http://localhost:8000/?SERVICE=WMTS&REQUEST=GetCapabilities

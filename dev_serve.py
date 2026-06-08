#!/usr/bin/env python3
"""
dev_serve.py — local development server for the WLC High Bay dashboard.

Usage:
    python3 dev_serve.py            # rebuild index.html then serve
    python3 dev_serve.py --port 5500
    python3 dev_serve.py --no-rebuild   # skip HTML rebuild, just serve

The script finds a free port automatically if the default is busy.
Open the printed URL in your browser.  Ctrl-C to stop.
Rerun whenever you edit chart_interactions.js.
"""

import argparse
import os
import socket
import sys
import http.server
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def find_free_port(preferred):
    """Return preferred port if free, otherwise the next free port."""
    for port in range(preferred, preferred + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue
    raise RuntimeError('No free port found near', preferred)


def rebuild():
    """Regenerate index.html from the current data files + chart_interactions.js."""
    sys.path.insert(0, BASE_DIR)
    import particle_plus as pp

    csv_path    = pp.ARCHIVE_CSV if os.path.exists(pp.ARCHIVE_CSV) else pp.LIVE_CSV
    output_path = os.path.join(BASE_DIR, 'index.html')

    print(f'[dev] Rebuilding index.html from {os.path.basename(csv_path)} …')
    ok = pp.generate_dashboard_html(csv_path, output_path)
    if ok:
        print('[dev] index.html rebuilt.')
    else:
        print('[dev] WARNING: rebuild returned False — check logs above.')


def serve(port):
    os.chdir(BASE_DIR)

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass   # silence all request logs; errors still go to stderr

        def log_error(self, fmt, *args):
            super().log_error(fmt, *args)

    actual_port = find_free_port(port)
    if actual_port != port:
        print(f'[dev] Port {port} busy — using {actual_port} instead.')

    httpd = http.server.HTTPServer(('127.0.0.1', actual_port), QuietHandler)
    url = f'http://localhost:{actual_port}'
    print(f'[dev] Dashboard → {url}')
    print('[dev] Ctrl-C to stop.  Re-run to pick up JS changes.')

    # Confirm the socket is really bound before opening the browser
    webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n[dev] Stopped.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',       type=int, default=5500,
                        help='Preferred port (default: 5500)')
    parser.add_argument('--no-rebuild', action='store_true',
                        help='Skip HTML rebuild, just serve the existing index.html')
    args = parser.parse_args()

    if not args.no_rebuild:
        rebuild()

    serve(args.port)

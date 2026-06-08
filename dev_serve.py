#!/usr/bin/env python3
"""
dev_serve.py — local development server for the WLC High Bay dashboard.

Usage:
    python3 dev_serve.py          # rebuild index.html then serve on http://localhost:8080
    python3 dev_serve.py --port 9000
    python3 dev_serve.py --no-rebuild   # skip HTML rebuild, just serve

Open http://localhost:8080 in your browser.  Ctrl-C to stop.
Rerun the script whenever you edit chart_interactions.js or particle_plus.py.
"""

import argparse
import os
import sys
import threading
import http.server
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def rebuild():
    """Regenerate index.html from the current data files + chart_interactions.js."""
    sys.path.insert(0, BASE_DIR)
    import particle_plus as pp

    csv_path    = pp.ARCHIVE_CSV if os.path.exists(pp.ARCHIVE_CSV) else pp.LIVE_CSV
    output_path = os.path.join(BASE_DIR, 'index.html')

    print(f'[dev_serve] Rebuilding index.html from {os.path.basename(csv_path)} …')
    ok = pp.generate_dashboard_html(csv_path, output_path)
    if ok:
        print('[dev_serve] index.html rebuilt successfully.')
    else:
        print('[dev_serve] WARNING: HTML rebuild returned False — check particle_plus.py logs.')

def serve(port):
    os.chdir(BASE_DIR)
    handler = http.server.SimpleHTTPRequestHandler

    class QuietHandler(handler):
        def log_message(self, fmt, *args):
            # Only show non-200 responses to keep the terminal clean
            if args and str(args[1]) not in ('200', '304'):
                super().log_message(fmt, *args)

    server = http.server.HTTPServer(('', port), QuietHandler)
    url = f'http://localhost:{port}'
    print(f'[dev_serve] Serving on {url}  (Ctrl-C to stop)')

    # Open the browser after a short delay so the server is up
    def _open():
        import time; time.sleep(0.4)
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n[dev_serve] Stopped.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',       type=int, default=8080)
    parser.add_argument('--no-rebuild', action='store_true',
                        help='Skip HTML rebuild, just serve the existing index.html')
    args = parser.parse_args()

    if not args.no_rebuild:
        rebuild()

    serve(args.port)

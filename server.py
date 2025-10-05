#!/usr/bin/env python3
"""
Multi-threaded HTTP Server
Supports:
- GET/HEAD requests for HTML, PNG, JPEG, TXT files
- POST /upload for JSON data
- Thread pool with connection queue
- Path traversal protection
- Host header validation
- Keep-alive connections with timeout and max requests
- Proper HTTP response codes and headers
- Timestamped logging
"""

import os
import sys
import socket
import threading
import queue
import json
import time
import random
import string
from datetime import datetime
from email.utils import formatdate

# ---------------------- Config ----------------------
HOST = "127.0.0.1"
PORT = 8080
POOL_SIZE = 10
LISTEN_BACKLOG = 50
CONN_TIMEOUT = 30
MAX_REQUESTS_PER_CONN = 100
MAX_HEADER_SIZE = 8192
RESOURCES_DIR = "resources"
UPLOADS_DIR = os.path.join(RESOURCES_DIR, "uploads")
QUEUE_MAXSIZE = 200
RETRY_AFTER = 5

os.makedirs(RESOURCES_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ---------------------- Utilities ----------------------
def http_date_now():
    return formatdate(timeval=None, usegmt=True)

def random_id(n=4):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

def safe_path(base, path):
    """Prevent directory traversal attacks"""
    target = os.path.realpath(os.path.join(base, path.lstrip("/")))
    if not target.startswith(os.path.realpath(base)):
        return None
    return target

def log(msg):
    """Timestamped log with thread name"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] [{threading.current_thread().name}] {msg}")

def build_response(status, reason, headers=None, body=b""):
    status_line = f"HTTP/1.1 {status} {reason}\r\n"
    header_lines = ""
    if headers:
        for k, v in headers.items():
            header_lines += f"{k}: {v}\r\n"
    return (status_line + header_lines + "\r\n").encode() + body

# ---------------------- Thread Pool ----------------------
class WorkerPool:
    def __init__(self, size):
        self.queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
        self.size = size
        for i in range(size):
            t = threading.Thread(target=self.worker, daemon=True, name=f"Worker-{i+1}")
            t.start()

    def worker(self):
        while True:
            client_sock, addr = self.queue.get()
            if client_sock is None:
                break
            try:
                handle_connection(client_sock, addr)
            except Exception as e:
                log(f"Error: {e}")
            finally:
                self.queue.task_done()

    def submit(self, client_sock, addr):
        try:
            self.queue.put_nowait((client_sock, addr))
            return True
        except queue.Full:
            return False

pool = None  # initialized in main

# ---------------------- Request Handling ----------------------
def recv_headers(sock):
    data = b""
    while b"\r\n\r\n" not in data and len(data) < MAX_HEADER_SIZE:
        try:
            chunk = sock.recv(1024)
        except socket.timeout:
            break
        if not chunk:
            break
        data += chunk
    return data

def parse_headers(data):
    try:
        text = data.decode("iso-8859-1")
        lines = text.split("\r\n")
        request_line = lines[0]
        headers = {}
        for line in lines[1:]:
            if ": " in line:
                k, v = line.split(": ", 1)
                headers[k.strip()] = v.strip()
        return request_line, headers
    except:
        return None, None

# ---------------------- Connection Handler ----------------------
def handle_connection(sock, addr):
    log(f"Connection from {addr}")
    sock.settimeout(CONN_TIMEOUT)
    requests_handled = 0
    last_activity = time.time()

    while requests_handled < MAX_REQUESTS_PER_CONN:
        raw = recv_headers(sock)
        if not raw:
            break

        last_activity = time.time()

        request_line, headers = parse_headers(raw)
        if not request_line or "Host" not in headers:
            resp = build_response(400, "Bad Request", {"Date": http_date_now(), "Connection": "close"}, b"400 Bad Request")
            sock.sendall(resp)
            break

        host = headers.get("Host")
        if host not in (f"{HOST}:{PORT}", f"localhost:{PORT}"):
            resp = build_response(403, "Forbidden", {"Date": http_date_now(), "Connection": "close"}, b"403 Forbidden")
            sock.sendall(resp)
            break

        parts = request_line.split()
        if len(parts) < 3:
            resp = build_response(400, "Bad Request", {"Date": http_date_now(), "Connection": "close"}, b"400 Bad Request")
            sock.sendall(resp)
            break

        method, path, version = parts
        keep_alive = version == "HTTP/1.1" and headers.get("Connection", "").lower() != "close"

        if ".." in path or path.startswith("/../") or path.startswith("//"):
            resp = build_response(403, "Forbidden", {"Date": http_date_now(), "Connection": "close"}, b"403 Forbidden")
            sock.sendall(resp)
            break

        if method in ("GET", "HEAD"):
            handle_get_head(sock, path, keep_alive, method)
        elif method == "POST":
            handle_post(sock, path, headers, raw.split(b"\r\n\r\n",1)[1] if b"\r\n\r\n" in raw else b"", keep_alive)
        else:
            resp = build_response(405, "Method Not Allowed", {"Date": http_date_now(), "Connection": "close"}, b"405 Method Not Allowed")
            sock.sendall(resp)
            break

        requests_handled += 1
        if not keep_alive:
            break

        # Check idle timeout
        if time.time() - last_activity > CONN_TIMEOUT:
            break

    sock.close()
    log(f"Connection closed {addr}")

# ---------------------- GET/HEAD ----------------------
def handle_get_head(sock, path, keep_alive, method):
    if path == "/":
        path = "/index.html"

    filepath = safe_path(RESOURCES_DIR, path)
    if not filepath or os.path.isdir(filepath):
        resp = build_response(403, "Forbidden", {"Date": http_date_now(), "Connection": "close"}, b"403 Forbidden")
        sock.sendall(resp)
        return

    ext = os.path.splitext(filepath)[1].lower()

    # Check for unsupported file types BEFORE checking if the file exists
    if ext not in (".html", ".png", ".jpg", ".jpeg", ".txt"):
        resp = build_response(415, "Unsupported Media Type", {"Date": http_date_now(), "Connection": "close"}, b"415 Unsupported Media Type")
        sock.sendall(resp)
        return

    # Now check if the file actually exists
    if not os.path.exists(filepath):
        resp = build_response(404, "Not Found", {"Date": http_date_now(), "Connection": "close"}, b"404 Not Found")
        sock.sendall(resp)
        return

    # ✅ Serve HTML file
    if ext == ".html":
        with open(filepath, "rb") as f:
            body = f.read()
        headers = {
            "Date": http_date_now(),
            "Content-Type": "text/html; charset=utf-8",
            "Content-Length": str(len(body)),
            "Connection": "keep-alive" if keep_alive else "close",
            "Keep-Alive": "timeout=30, max=100" if keep_alive else ""
        }
        sock.sendall(build_response(200, "OK", headers, body if method == "GET" else b""))
        log(f"Served HTML: {path} ({len(body)} bytes)")

    # ✅ Serve supported binary files
    elif ext in (".png", ".jpg", ".jpeg", ".txt"):
        filesize = os.path.getsize(filepath)
        headers = {
            "Date": http_date_now(),
            "Content-Type": "application/octet-stream",
            "Content-Disposition": f'attachment; filename="{os.path.basename(filepath)}"',
            "Content-Length": str(filesize),
            "Connection": "keep-alive" if keep_alive else "close",
            "Keep-Alive": "timeout=30, max=100" if keep_alive else ""
        }
        sock.sendall(build_response(200, "OK", headers))
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sock.sendall(chunk)
        log(f"Sent binary file: {path} ({filesize} bytes)")

# ---------------------- POST /upload ----------------------
def handle_post(sock, path, headers, body, keep_alive):
    if path != "/upload" or "application/json" not in headers.get("Content-Type", ""):
        resp = build_response(415, "Unsupported Media Type", {"Date": http_date_now(), "Connection": "close"}, b"415 Unsupported Media Type")
        sock.sendall(resp)
        return

    content_length = int(headers.get("Content-Length", "0"))
    data = body
    while len(data) < content_length:
        data += sock.recv(4096)

    try:
        json_data = json.loads(data.decode("utf-8"))
    except:
        resp = build_response(400, "Bad Request", {"Date": http_date_now(), "Connection": "close"}, b"400 Bad Request: Invalid JSON")
        sock.sendall(resp)
        return

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"upload_{timestamp}_{random_id()}.json"
    filepath = os.path.join(UPLOADS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    resp_body = json.dumps({
        "status": "success",
        "message": "File created successfully",
        "filepath": f"/uploads/{filename}"
    }).encode()
    headers_out = {
        "Date": http_date_now(),
        "Content-Type": "application/json",
        "Content-Length": str(len(resp_body)),
        "Connection": "keep-alive" if keep_alive else "close",
        "Keep-Alive": "timeout=30, max=100" if keep_alive else ""
    }
    sock.sendall(build_response(201, "Created", headers_out, resp_body))
    log(f"Created JSON upload: {filename} ({len(resp_body)} bytes)")

# ---------------------- Main ----------------------
def run_server(host, port, pool_size):
    global pool
    pool = WorkerPool(pool_size)
    log(f"HTTP Server started on {host}:{port}")
    log(f"Thread pool size: {pool_size}")
    log(f"Serving files from '{RESOURCES_DIR}' directory")
    log("Press Ctrl+C to stop the server")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(LISTEN_BACKLOG)
        while True:
            try:
                client_sock, addr = s.accept()
                submitted = pool.submit(client_sock, addr)
                if not submitted:
                    resp = build_response(
                        503,
                        "Service Unavailable",
                        {"Date": http_date_now(), "Retry-After": str(RETRY_AFTER), "Connection":"close"},
                        b"503 Service Unavailable"
                    )
                    client_sock.sendall(resp)
                    client_sock.close()
            except KeyboardInterrupt:
                log("Server shutting down...")
                break

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else PORT
    pool_size = int(sys.argv[3]) if len(sys.argv) > 3 else POOL_SIZE
    run_server(host, port, pool_size)

# Multi-threaded HTTP Server (Python) 

A fully functional multi-threaded HTTP server built from scratch in Python. This server demonstrates core concepts of networking, concurrency, and HTTP protocol design, while supporting static file serving, JSON uploads, and persistent connections.

---

## Features

✅ **GET / HEAD Support**

* Serves static files (`.html`, `.txt`, `.png`, `.jpg`, `.jpeg`) from `resources/`
* Protects against directory traversal attacks
* Returns appropriate `Content-Type`, `Content-Length`, and `Connection` headers

✅ **POST /upload**

* Accepts JSON via POST requests (`Content-Type: application/json`)
* Saves each upload to `resources/uploads/` as a `.json` file
* Returns a success message with the saved file path

✅ **Thread Pool**

* Fixed-size pool of worker threads for concurrent clients
* Connection queue supports up to 200 pending connections
* Returns `503 Service Unavailable` if queue is full

✅ **Connection Handling**

* Supports persistent connections (keep-alive) with configurable timeout and request limits
* Validates `Host` headers to prevent spoofing
* Enforces connection timeouts and maximum header size

✅ **Robust Error Handling**

* Gracefully handles `400`, `403`, `404`, `405`, `415`, and `503` response codes
* Logs all activity with timestamps and thread names

---

## Directory Structure

```
project_root/
│
├── server.py             # Main HTTP server script
├── resources/            # Root folder for static files
│   ├── index.html        # Default home page
│   ├── uploads/          # JSON uploads from POST /upload
│   ├── images/           # Image files (.png, .jpg, .jpeg)
│   └── text/             # Text files (.txt)
└── README.md             # Project documentation
```

---

## Prerequisites

* Python 3.8+ installed
* Basic knowledge of terminal commands

---

## Running the Server

```bash
python3 server.py
```

Server runs at `http://127.0.0.1:8080/` by default.

---

## Supported Endpoints

| Method | Path                              | Description                                   |
| ------ | --------------------------------- | --------------------------------------------- |
| GET    | `/` or `/index.html`              | Serves the main HTML page                     |
| GET    | `/file.txt` or `/images/file.jpg` | Serves a file from `resources/`               |
| HEAD   | `/file.ext`                       | Returns only headers (no body)                |
| POST   | `/upload`                         | Accepts JSON data and saves as a `.json` file |

---

## Example Requests

**GET Request**

```bash
curl http://127.0.0.1:8080/
```

**HEAD Request**

```bash
curl -I http://127.0.0.1:8080/index.html
```

**POST JSON Upload**

```bash
curl -X POST http://127.0.0.1:8080/upload \
-H "Content-Type: application/json" \
-d '{"name": "Ridaa", "project": "HTTP Server"}'
```

**Response**

```json
{
  "status": "success",
  "message": "File created successfully",
  "filepath": "/uploads/upload_20251005_145623_ab3d.json"
}
```

Uploaded JSON files are saved in `resources/uploads/` with unique timestamped filenames.

---

## Key Concepts Demonstrated

* **Socket Programming** – Handling TCP connections and data transfer
* **Thread Pool** – Efficient concurrency using worker threads
* **Keep-Alive** – Persistent HTTP connections with timeouts
* **Header Parsing** – Manual decoding of HTTP headers and request lines
* **Security** – Path traversal prevention, host validation, and size limits
* **HTTP Protocol** – Implementation of request parsing and response formatting

---

## HTTP Response Codes

| Code | Meaning                                                     |
| ---- | ----------------------------------------------------------- |
| 200  | OK – Successful GET/HEAD request                            |
| 201  | Created – Successful JSON upload                            |
| 400  | Bad Request – Invalid or malformed request                  |
| 403  | Forbidden – Unauthorized path or invalid host               |
| 404  | Not Found – File does not exist                             |
| 405  | Method Not Allowed – Unsupported HTTP method                |
| 415  | Unsupported Media Type – File type/content type not allowed |
| 503  | Service Unavailable – Thread pool/queue full                |

---

## Example Log Output

```
[2025-10-05 14:45:10] [Worker-3] Connection from ('127.0.0.1', 52644)
[2025-10-05 14:45:10] [Worker-3] Served HTML: /index.html (324 bytes)
[2025-10-05 14:45:15] [Worker-5] Created JSON upload: upload_20251005_144515_k8df.json (118 bytes)
[2025-10-05 14:45:20] [Worker-2] Connection closed ('127.0.0.1', 52644)
```

---

## Testing Suggestions

* Open your browser → Visit `http://127.0.0.1:8080/`
* If Chrome is used then the text and image files will be downloaded automatically
* Upload JSON using `curl` or Postman
* Access unsupported paths → Expect `403` or `415` responses
* Send multiple concurrent requests → Observe thread logs in the console

---

## Author

**Ridaa Mahrooz**
Built for a Networking / Operating Systems assignment demonstrating multithreading and HTTP fundamentals.


🧩 Multi-threaded HTTP Server (Python)
📖 Overview

This project implements a fully functional multi-threaded HTTP server built from scratch using Python sockets and thread pooling.
It is designed to serve static files, handle JSON uploads, support HTTP/1.1 keep-alive connections, and demonstrate core networking, concurrency, and protocol design principles.

⚙️ Features

✅ GET / HEAD Support

Serves static files (.html, .txt, .png, .jpg, .jpeg) from the resources/ directory

Protects against directory traversal attacks

Sends appropriate Content-Type, Content-Length, and Connection headers

✅ POST /upload

Accepts JSON data via POST requests (Content-Type: application/json)

Saves each upload into resources/uploads/ as a .json file

Returns a success message with a file path

✅ Thread Pool

Uses a fixed-size pool of worker threads for concurrent client handling

Supports connection queuing (up to 200 pending connections)

Returns 503 Service Unavailable if the queue is full

✅ Connection Handling

Supports persistent connections (keep-alive) with timeout and request limits

Validates Host headers to prevent spoofing

Enforces connection timeouts and maximum header size

✅ Robust Error Handling

Handles 400, 403, 404, 405, 415, and 503 response codes gracefully

Logs all activity with timestamps and thread names

🗂️ Directory Structure
project_root/
│
├── server.py                 # Main HTTP server script
├── resources/                # Root folder for static files
│   ├── index.html            # Default home page
│   ├── uploads/              # Directory for POST /upload JSON files
│   ├── images                # image files
│   └── text                  # text files
└── README.md                 # Project documentation

🚀 How to Run
1️⃣ Prerequisites

Python 3.8+ installed

Basic knowledge of terminal commands

2️⃣ Start the Server
python3 server.py

🌐 Supported Endpoints
GET / or /index.html

Serves the main HTML file.
Example:

curl http://127.0.0.1:8080/

GET /file.txt

Serves a text or binary file from resources/.

HEAD /file.jpeg

Returns only headers (no body).

If opened in chrome then it downloads the image or text file.

POST /upload

Uploads JSON data and saves it as a .json file.

Example:

curl -X POST http://127.0.0.1:8080/upload \
     -H "Content-Type: application/json" \
     -d '{"name": "Ridaa", "project": "HTTP Server"}'

Response:
{
  "status": "success",
  "message": "File created successfully",
  "filepath": "/uploads/upload_20251005_145623_ab3d.json"
}

🧠 Key Concepts Demonstrated

    Concept	                                      Description
Socket Programming	          Low-level handling of TCP connections and data transfer
Thread Pool	                  Efficient concurrency using a fixed number of worker threads
Keep-Alive	                  Persistent HTTP connections with configurable timeouts
Header Parsing	              Manual decoding of HTTP headers and request lines
Security	                  Path traversal prevention, host validation, size limits
HTTP Protocol	              Implementation of request parsing and response formatting

🧩 HTTP Response Codes Used
   Code	                            Meaning
200 OK	                      Successful GET/HEAD
201 Created	                  Successful JSON upload
400 Bad Request	              Invalid or malformed request
403 Forbidden	              Unauthorized path or invalid host
404 Not Found	              File does not exist
405 Method Not Allowed	      Unsupported HTTP method
415 Unsupported Media Type	  File type or content type not allowed
503 Service Unavailable	      Thread pool/queue full

🧾 Example Log Output
[2025-10-05 14:45:10] [Worker-3] Connection from ('127.0.0.1', 52644)
[2025-10-05 14:45:10] [Worker-3] Served HTML: /index.html (324 bytes)
[2025-10-05 14:45:15] [Worker-5] Created JSON upload: upload_20251005_144515_k8df.json (118 bytes)
[2025-10-05 14:45:20] [Worker-2] Connection closed ('127.0.0.1', 52644)

🧰 Configuration Parameters
  Variable	                       Description	                   Default
HOST	                            Server IP	                  127.0.0.1
PORT	                            Port number	                    8080
POOL_SIZE	                        Number of worker threads	     10
LISTEN_BACKLOG	                    Max pending connections	         50
CONN_TIMEOUT	                    Connection idle timeout	        30 sec
MAX_REQUESTS_PER_CONN	            Max requests per connection	     100
RESOURCES_DIR	                    Static files directory	        resources/
UPLOADS_DIR	                        Uploads directory	            resources/uploads/


🧪 Testing Suggestions

Open your browser → Visit http://127.0.0.1:8080/

Upload JSON using curl or Postman

Try unsupported paths → expect 403 or 415

Test multiple concurrent requests → observe thread logs

🧑‍💻 Author

Ridaa Mahrooz
Built for the Networking / Operating Systems assignment demonstrating multithreading and HTTP fundamentals.
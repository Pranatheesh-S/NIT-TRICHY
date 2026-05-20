# Network Traffic Interception System - Workflow Summary

This document outlines the architecture and execution workflow of the modular Python-based network traffic interception and monitoring system.

## 1. System Architecture

The system is composed of three primary network components and a suite of inspection tools:

*   **Client (`client/client.py`)**: A simulation script that initiates an HTTP `POST` request to upload a file to a designated server. It connects to the Proxy instead of the Server directly to demonstrate interception.
*   **Server (`server/server.py`)**: A simple backend server listening for incoming file uploads. It parses HTTP requests, extracts the payload, and saves the file to the local `data/` directory.
*   **Proxy (`proxy/proxy.py`)**: The core "Man-in-the-Middle" (MITM) component. It intercepts the client's connection, forwards traffic bidirectionally between the client and the server, and routes the data through the inspection modules.

### Core Inspection Modules
*   **Packet Inspector (`core/packet_inspector.py`)**: Analyzes raw packet data in transit. It detects anomalies like excessively large payloads or repeated rapid requests.
*   **HTTP Analyzer (`core/http_analyzer.py`)**: Parses the intercepted packet to extract HTTP headers, methods (`GET`, `POST`, etc.), and routing paths. It specifically flags `POST`/`PUT` requests that may contain file uploads.
*   **File Extractor (`core/file_extractor.py`)**: Scans payloads for recognized file signatures (magic bytes for PNG, JPG, PDF, ZIP, etc.). If a match is found, it extracts and saves a copy of the file to the `intercepted_files/` directory.

### Monitoring & Logging
*   **Traffic Monitor & Dashboard (`dashboard.py`)**: A Rich-based CLI dashboard that provides real-time statistics on active sessions, total requests, upload/download speeds, and total bytes transferred.
*   **Logger (`monitoring/logger.py`)**: Records events, HTTP requests, file extractions, and suspicious activities.

---

## 2. Execution Workflow

The operational flow of a typical file interception scenario proceeds as follows:

### Step 1: Initialization
1.  **Start the Server**: The server is initialized (`python server/server.py`) and begins listening for incoming connections on the designated `SERVER_PORT`.
2.  **Start the Proxy**: The proxy is launched (`python proxy/proxy.py`). It binds to `PROXY_PORT`, initializes the `Dashboard` for live metrics, and waits for client connections.

### Step 2: Client Connection & Interception
3.  **Run the Client**: The client is executed to upload a file, but directed to connect to the Proxy (`python client/client.py <file_path> --port <PROXY_PORT>`).
4.  **Session Creation**: The Proxy accepts the client connection, logs an "intercepted" event, creates a new session via the `SessionManager`, and establishes a secondary connection to the actual Server.

### Step 3: Traffic Forwarding & Analysis
5.  **Bidirectional Forwarding**: Two threads are spawned in the Proxy to handle simultaneous Client-to-Server and Server-to-Client communication.
6.  **Packet Inspection**: As data flows from the Client to the Server:
    *   The `Traffic Monitor` tallies the bytes uploaded.
    *   The `Packet Inspector` scans the raw byte stream.
7.  **HTTP Parsing & Extraction**:
    *   The `HTTP Analyzer` processes the HTTP headers. Recognizing a `POST` request with a payload, it triggers the `File Extractor`.
    *   The `File Extractor` identifies the file type using magic bytes (e.g., `\x89PNG` for a PNG file), extracts the binary data, and saves a duplicate copy into the `intercepted_files/` directory.

### Step 4: Server Reception & Completion
8.  **Server Processing**: The Server receives the forwarded (and already inspected) traffic from the Proxy. It parses the HTTP headers, reads the file data, and saves it into the `data/` directory.
9.  **Response Handling**: The Server responds with an `HTTP 200 OK` message, which travels back through the Proxy to the Client. The `Traffic Monitor` updates the download statistics.
10. **Termination**: The transfer completes. The Client closes its connection, which signals the Proxy to terminate the forwarding threads and close the session.

## 3. Data Storage
*   **Original File**: Uploaded by the client, received and saved by the server in `./data/`.
*   **Intercepted File**: Copied mid-transit by the proxy's `file_extractor` and saved in `./intercepted_files/`.

import socket
import threading
import os
import sys
import ssl

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import SERVER_HOST, HTTPS_SERVER_PORT, DATA_DIR, BUFFER_SIZE, SERVER_CERT, SERVER_KEY
from utils.helpers import format_bytes, get_timestamp
from rich.console import Console

console = Console()

def handle_client(client_socket, client_address):
    ip, port = client_address
    timestamp = get_timestamp()
    console.print(f"[green][{timestamp}][/green] Secure connection accepted from {ip}:{port}")
    
    try:
        # Read HTTP request headers
        request_data = client_socket.recv(BUFFER_SIZE)
        if not request_data:
            console.print(f"[red][{get_timestamp()}][/red] Failed to receive data from {ip}")
            return
            
        header_end = request_data.find(b'\r\n\r\n')
        if header_end == -1:
            console.print(f"[red][{get_timestamp()}][/red] Invalid HTTP request from {ip}")
            return
            
        headers_raw = request_data[:header_end].decode('utf-8', errors='ignore')
        initial_body = request_data[header_end+4:]
        
        headers = {}
        for line in headers_raw.split('\r\n')[1:]:
            if ': ' in line:
                k, v = line.split(': ', 1)
                headers[k.lower()] = v
                
        filename = headers.get('filename', f"secure_unknown_{get_timestamp().replace(':', '-').replace(' ', '_')}.dat")
        try:
            filesize = int(headers.get('content-length', 0))
        except ValueError:
            filesize = 0
            
        filepath = os.path.join(DATA_DIR, os.path.basename(filename))
        bytes_received = len(initial_body)
        
        with open(filepath, 'wb') as f:
            if initial_body:
                f.write(initial_body)
                
            while filesize > 0 and bytes_received < filesize:
                chunk = client_socket.recv(BUFFER_SIZE)
                if not chunk:
                    break
                f.write(chunk)
                bytes_received += len(chunk)
                
        # Send HTTP response
        response = "HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
        client_socket.sendall(response.encode('utf-8'))
                    
        timestamp_end = get_timestamp()
        status = "Success" if (filesize == 0 or bytes_received == filesize) else "Partial/Failed"
        
        console.print(f"--- Secure Transfer Details ---")
        console.print(f"Client IP: {ip}")
        console.print(f"Connection Time: {timestamp}")
        console.print(f"File Name: {filename}")
        console.print(f"File Size: {format_bytes(bytes_received)}")
        console.print(f"Status: {status}")
        console.print(f"-------------------------------")
        
    except Exception as e:
        console.print(f"[red]Error handling secure client {ip}: {str(e)}[/red]")
    finally:
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        client_socket.close()

def start_https_server(host=SERVER_HOST, port=HTTPS_SERVER_PORT):
    # Configure TLS 1.3
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    # Use standard modern ciphers enabling ECDHE
    context.set_ciphers('HIGH:!aNULL:!eNULL:!MD5')
    
    try:
        context.load_cert_chain(certfile=SERVER_CERT, keyfile=SERVER_KEY)
    except FileNotFoundError:
        console.print(f"[red]Certificates not found at {SERVER_CERT}. Run cert_gen.py first.[/red]")
        sys.exit(1)
        
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    
    # Wrap socket with SSL Context
    secure_server = context.wrap_socket(server, server_side=True)
    
    console.print(f"[bold blue]HTTPS Server listening securely on {host}:{port}[/bold blue]")
    
    try:
        while True:
            try:
                client_socket, client_address = secure_server.accept()
                client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
                client_thread.start()
            except ssl.SSLError as e:
                console.print(f"[yellow]SSL Error during accept: {e}[/yellow]")
    except KeyboardInterrupt:
        console.print("[yellow]HTTPS Server shutting down...[/yellow]")
    finally:
        secure_server.close()

if __name__ == "__main__":
    start_https_server()

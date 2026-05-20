import socket
import threading
import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import SERVER_HOST, SERVER_PORT, DATA_DIR, BUFFER_SIZE
from utils.helpers import format_bytes, get_timestamp
from rich.console import Console

console = Console()

def handle_client(client_socket, client_address):
    ip, port = client_address
    timestamp = get_timestamp()
    console.print(f"[green][{timestamp}][/green] Connection accepted from {ip}:{port}")
    
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
                
        filename = headers.get('filename', f"unknown_{get_timestamp().replace(':', '-').replace(' ', '_')}.dat")
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
        
        # Log to console
        console.print(f"--- Transfer Details ---")
        console.print(f"Client IP: {ip}")
        console.print(f"Connection Time: {timestamp}")
        console.print(f"File Name: {filename}")
        console.print(f"File Size: {format_bytes(bytes_received)}")
        console.print(f"Status: {status}")
        console.print(f"------------------------")
        
    except Exception as e:
        console.print(f"[red]Error handling client {ip}: {str(e)}[/red]")
    finally:
        client_socket.close()

def start_server(host=SERVER_HOST, port=SERVER_PORT):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    console.print(f"[bold blue]Server listening on {host}:{port}[/bold blue]")
    
    try:
        while True:
            client_socket, client_address = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()
    except KeyboardInterrupt:
        console.print("[yellow]Server shutting down...[/yellow]")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()

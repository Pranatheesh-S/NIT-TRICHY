import socket
import sys
import os
import argparse
import ssl

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import PROXY_HOST, HTTPS_PROXY_PORT, BUFFER_SIZE
from rich.console import Console
from rich.progress import Progress

console = Console()

def upload_secure_file(filepath, host=PROXY_HOST, port=HTTPS_PROXY_PORT):
    if not os.path.exists(filepath):
        console.print(f"[red]Error: File {filepath} does not exist.[/red]")
        return
        
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    
    # Configure TLS 1.3 Client Context (ignore self-signed cert verification)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Wrap socket in TLS
        secure_client = context.wrap_socket(client, server_hostname=host)
        secure_client.connect((host, port))
        
        # Build HTTP POST Request
        request = (
            f"POST /upload HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Filename: {filename}\r\n"
            f"Content-Length: {filesize}\r\n"
            f"\r\n"
        )
        
        secure_client.sendall(request.encode('utf-8'))
        
        # Upload file with progress bar
        with Progress() as progress:
            task = progress.add_task(f"[green]Securely uploading {filename}...", total=filesize)
            
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    secure_client.sendall(chunk)
                    progress.update(task, advance=len(chunk))
                    
        # Wait for response
        response = secure_client.recv(BUFFER_SIZE)
        console.print(f"\n[bold green]Server Response:[/bold green]\n{response.decode('utf-8')}")
        
    except Exception as e:
        console.print(f"[red]Connection error: {e}[/red]")
    finally:
        try:
            secure_client.close()
        except Exception:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Secure HTTPS Client for File Upload")
    parser.add_argument("file", help="Path to the file to upload")
    parser.add_argument("--host", default=PROXY_HOST, help="Proxy host to connect to")
    parser.add_argument("--port", type=int, default=HTTPS_PROXY_PORT, help="Proxy HTTPS port")
    
    args = parser.parse_args()
    upload_secure_file(args.file, args.host, args.port)

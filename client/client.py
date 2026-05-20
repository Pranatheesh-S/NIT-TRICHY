import socket
import os
import sys
import time

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import SERVER_HOST, SERVER_PORT, BUFFER_SIZE
from utils.helpers import format_bytes, get_timestamp
from rich.console import Console
from rich.progress import Progress

console = Console()

def send_file(filepath, host=SERVER_HOST, port=SERVER_PORT):
    if not os.path.exists(filepath):
        console.print(f"[red]Error: File {filepath} does not exist.[/red]")
        return

    filesize = os.path.getsize(filepath)
    filename = os.path.basename(filepath)
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        console.print(f"[cyan]Connecting to {host}:{port}...[/cyan]")
        client_socket.connect((host, port))
        
        # Traffic Monitoring logs (Phase 1 req)
        source_ip, source_port = client_socket.getsockname()
        dest_ip, dest_port = client_socket.getpeername()
        
        console.print("\n[bold]Traffic Monitor (Outgoing Connection)[/bold]")
        console.print(f"Source: {source_ip}:{source_port}")
        console.print(f"Destination: {dest_ip}:{dest_port}")
        console.print("-" * 30)
        
        # Send HTTP Headers
        headers = (
            f"POST /upload HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Filename: {filename}\r\n"
            f"Content-Length: {filesize}\r\n"
            f"Content-Type: application/octet-stream\r\n"
            f"\r\n"
        )
        client_socket.sendall(headers.encode('utf-8'))
        
        bytes_sent = 0
        
        # Display progress
        with Progress() as progress:
            task = progress.add_task(f"[green]Uploading {filename}...", total=filesize)
            
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    client_socket.sendall(chunk)
                    bytes_sent += len(chunk)
                    progress.update(task, advance=len(chunk))
                    
        # Wait for HTTP response
        response = client_socket.recv(4096).decode('utf-8')
        if "200 OK" not in response:
            console.print(f"[red]Server error: {response.splitlines()[0] if response else 'No response'}[/red]")
            return
                    
        console.print(f"\n[bold green]Transfer Complete![/bold green]")
        console.print(f"Bytes Transferred: {format_bytes(bytes_sent)}")
        console.print(f"Status: Success")
        
    except ConnectionRefusedError:
        console.print(f"[red]Connection refused. Is the server running on {host}:{port}?[/red]")
    except Exception as e:
        console.print(f"[red]Error during transfer: {str(e)}[/red]")
        console.print(f"Status: Failed")
    finally:
        client_socket.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Send a file to the server.")
    parser.add_argument("file", help="Path to the file to send")
    parser.add_argument("--host", default=SERVER_HOST, help="Server IP address")
    parser.add_argument("--port", type=int, default=SERVER_PORT, help="Server port")
    
    args = parser.parse_args()
    send_file(args.file, args.host, args.port)

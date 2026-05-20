import socket
import threading
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import PROXY_HOST, PROXY_PORT, SERVER_HOST, SERVER_PORT, BUFFER_SIZE
from session_manager import session_manager
from monitoring.traffic_monitor import monitor
from monitoring.logger import log_event
from core.packet_inspector import packet_inspector
from rich.console import Console

console = Console()

def forward_client_to_server(client_socket, server_socket, session):
    try:
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
                
            monitor.add_bytes_up(len(data))
            
            # Inspect packet
            inspected_data = packet_inspector.inspect(data, session.client_ip)
            
            # Forward data
            server_socket.sendall(inspected_data)
            
    except Exception as e:
        log_event("ERROR", f"Client to Server error: {e}")
    finally:
        client_socket.close()
        server_socket.close()

def forward_server_to_client(server_socket, client_socket, session):
    try:
        while True:
            data = server_socket.recv(BUFFER_SIZE)
            if not data:
                break
                
            monitor.add_bytes_down(len(data))
            
            # Forward data
            client_socket.sendall(data)
            
    except Exception as e:
        log_event("ERROR", f"Server to Client error: {e}")
    finally:
        client_socket.close()
        server_socket.close()

def handle_proxy_client(client_socket, client_address):
    ip, port = client_address
    console.print(f"[bold red]Connection intercepted![/bold red] from {ip}:{port}")
    
    session = session_manager.create_session(ip, port)
    monitor.increment_requests()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.connect((SERVER_HOST, SERVER_PORT))
        
        # Start bidirectional forwarding threads
        c2s_thread = threading.Thread(target=forward_client_to_server, args=(client_socket, server_socket, session))
        s2c_thread = threading.Thread(target=forward_server_to_client, args=(server_socket, client_socket, session))
        
        c2s_thread.start()
        s2c_thread.start()
        
        c2s_thread.join()
        s2c_thread.join()
        
    except Exception as e:
        console.print(f"[red]Failed to connect to actual server: {e}[/red]")
        client_socket.close()
    finally:
        session_manager.end_session(session.session_id)

def start_proxy(host=PROXY_HOST, port=PROXY_PORT, use_dashboard=True):
    if use_dashboard:
        from dashboard import run_dashboard
        dash_thread = threading.Thread(target=run_dashboard, daemon=True)
        dash_thread.start()
        
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.bind((host, port))
    proxy.listen(10)
    console.print(f"[bold green]Proxy listening on {host}:{port}[/bold green]")
    
    try:
        while True:
            client_socket, client_address = proxy.accept()
            client_thread = threading.Thread(target=handle_proxy_client, args=(client_socket, client_address))
            client_thread.start()
    except KeyboardInterrupt:
        console.print("[yellow]Proxy shutting down...[/yellow]")
    finally:
        proxy.close()

if __name__ == "__main__":
    start_proxy()

import socket
import threading
import sys
import os
import ssl

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import PROXY_HOST, HTTPS_PROXY_PORT, SERVER_HOST, HTTPS_SERVER_PORT, BUFFER_SIZE, PROXY_CERT, PROXY_KEY
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
            
            # Inspect plaintext data
            inspected_data = packet_inspector.inspect(data, session.client_ip)
            
            # Forward data
            server_socket.sendall(inspected_data)
            
    except Exception as e:
        log_event("ERROR", f"HTTPS Client to Server error: {e}")
    finally:
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            server_socket.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
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
        log_event("ERROR", f"HTTPS Server to Client error: {e}")
    finally:
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            server_socket.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        client_socket.close()
        server_socket.close()

def handle_https_proxy_client(client_socket, client_address, proxy_context):
    ip, port = client_address
    console.print(f"[bold red]Secure connection intercepted![/bold red] from {ip}:{port}")
    
    # 1. SSL Termination (Proxy acting as server to the client)
    try:
        secure_client_socket = proxy_context.wrap_socket(client_socket, server_side=True)
    except Exception as e:
        console.print(f"[red]SSL handshake failed with client {ip}: {e}[/red]")
        client_socket.close()
        return

    session = session_manager.create_session(ip, port)
    monitor.increment_requests()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.connect((SERVER_HOST, HTTPS_SERVER_PORT))
        
        # 2. SSL Initiation (Proxy acting as client to the actual server)
        server_context = ssl.create_default_context()
        server_context.check_hostname = False
        server_context.verify_mode = ssl.CERT_NONE
        server_context.minimum_version = ssl.TLSVersion.TLSv1_3
        
        secure_server_socket = server_context.wrap_socket(server_socket, server_hostname=SERVER_HOST)
        
        # Start bidirectional forwarding threads
        c2s_thread = threading.Thread(target=forward_client_to_server, args=(secure_client_socket, secure_server_socket, session))
        s2c_thread = threading.Thread(target=forward_server_to_client, args=(secure_server_socket, secure_client_socket, session))
        
        c2s_thread.start()
        s2c_thread.start()
        
        c2s_thread.join()
        s2c_thread.join()
        
    except Exception as e:
        console.print(f"[red]Failed to connect to actual HTTPS server: {e}[/red]")
        secure_client_socket.close()
    finally:
        session_manager.end_session(session.session_id)

def start_https_proxy(host=PROXY_HOST, port=HTTPS_PROXY_PORT, use_dashboard=True):
    if use_dashboard:
        from dashboard import run_dashboard
        dash_thread = threading.Thread(target=run_dashboard, daemon=True)
        dash_thread.start()
        
    # Configure Proxy Context
    proxy_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    proxy_context.minimum_version = ssl.TLSVersion.TLSv1_3
    proxy_context.set_ciphers('HIGH:!aNULL:!eNULL:!MD5')
    
    try:
        proxy_context.load_cert_chain(certfile=PROXY_CERT, keyfile=PROXY_KEY)
    except FileNotFoundError:
        console.print(f"[red]Certificates not found at {PROXY_CERT}. Run cert_gen.py first.[/red]")
        sys.exit(1)
        
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.bind((host, port))
    proxy.listen(10)
    console.print(f"[bold green]HTTPS Proxy listening on {host}:{port}[/bold green]")
    
    try:
        while True:
            client_socket, client_address = proxy.accept()
            client_thread = threading.Thread(target=handle_https_proxy_client, args=(client_socket, client_address, proxy_context))
            client_thread.start()
    except KeyboardInterrupt:
        console.print("[yellow]HTTPS Proxy shutting down...[/yellow]")
    finally:
        proxy.close()

if __name__ == "__main__":
    start_https_proxy()

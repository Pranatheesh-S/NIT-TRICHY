import socket
import threading
import sys
import os
import re
import ssl

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import PROXY_HOST, FTPS_PROXY_PORT, SERVER_HOST, FTPS_SERVER_PORT, BUFFER_SIZE, PROXY_CERT, PROXY_KEY
from core.file_extractor import analyze_payload_for_files
from monitoring.logger import log_event
from rich.console import Console

console = Console()

class FTPSDataProxy(threading.Thread):
    def __init__(self, server_ip, server_port, client_ip, proxy_context, server_context):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_ip = client_ip
        self.proxy_context = proxy_context
        self.server_context = server_context
        
        self.proxy_data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy_data_socket.bind((PROXY_HOST, 0))
        self.proxy_data_socket.listen(1)
        self.listen_port = self.proxy_data_socket.getsockname()[1]
        
    def run(self):
        try:
            self.proxy_data_socket.settimeout(10)
            client_socket, addr = self.proxy_data_socket.accept()
            console.print(f"[dim cyan]Secure data connection intercepted from {addr}[/dim cyan]")
            
            # Wrap client connection
            secure_client_socket = self.proxy_context.wrap_socket(client_socket, server_side=True)
            
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((self.server_ip, self.server_port))
            
            # Wrap server connection
            secure_server_socket = self.server_context.wrap_socket(server_socket, server_hostname=SERVER_HOST)
            
            def s2c():
                try:
                    while True:
                        data = secure_server_socket.recv(BUFFER_SIZE)
                        if not data: break
                        secure_client_socket.sendall(data)
                except: pass
                
            def c2s():
                try:
                    full_payload = b""
                    while True:
                        data = secure_client_socket.recv(BUFFER_SIZE)
                        if not data: break
                        full_payload += data
                        secure_server_socket.sendall(data)
                    
                    try:
                        secure_server_socket.shutdown(socket.SHUT_WR)
                    except:
                        pass
                        
                    if full_payload:
                        file_type = analyze_payload_for_files(full_payload)
                        if file_type:
                            log_event("FTPS_FILE", f"Extracted {file_type} via FTPS Data channel")
                except Exception as e: 
                    console.print(f"[red]Error in Data C2S: {e}[/red]")
            
            t1 = threading.Thread(target=s2c)
            t2 = threading.Thread(target=c2s)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            
            secure_client_socket.close()
            secure_server_socket.close()
            
        except Exception as e:
            console.print(f"[red]FTPS Data Proxy Error: {e}[/red]")
        finally:
            self.proxy_data_socket.close()


def handle_ftps_client(client_socket, client_address, proxy_context, server_context):
    ip, port = client_address
    console.print(f"[bold red]FTPS Connection intercepted![/bold red] from {ip}:{port}")
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.connect((SERVER_HOST, FTPS_SERVER_PORT))
        
        state = {"tls_active": False}
        client_sock_ref = [client_socket]
        server_sock_ref = [server_socket]

        def forward_c2s():
            try:
                while True:
                    data = client_sock_ref[0].recv(BUFFER_SIZE)
                    if not data: break
                    if not state["tls_active"]:
                        cmd = data.decode('utf-8', errors='ignore').strip()
                        log_event("FTPS_CMD", cmd)
                    server_sock_ref[0].sendall(data)
            except: pass
            
        def forward_s2c():
            try:
                while True:
                    data = server_sock_ref[0].recv(BUFFER_SIZE)
                    if not data: break
                    
                    if not state["tls_active"]:
                        decoded = data.decode('utf-8', errors='ignore')
                        # Check if AUTH TLS response is successful
                        if "234" in decoded and "AUTH TLS" in decoded:
                            client_sock_ref[0].sendall(data)
                            console.print("[yellow]AUTH TLS successful, switching to secure mode...[/yellow]")
                            
                            # Upgrade sockets to TLS
                            client_sock_ref[0] = proxy_context.wrap_socket(client_sock_ref[0], server_side=True)
                            server_sock_ref[0] = server_context.wrap_socket(server_sock_ref[0], server_hostname=SERVER_HOST)
                            state["tls_active"] = True
                            continue
                            
                        # Intercept PASV response in plaintext (if it's somehow not TLS, though usually it is)
                        pasv_match = re.search(r'227 .*?\((\d+,\d+,\d+,\d+),(\d+),(\d+)\)', decoded)
                        if pasv_match:
                            ip_str = pasv_match.group(1).replace(',', '.')
                            p1, p2 = int(pasv_match.group(2)), int(pasv_match.group(3))
                            server_data_port = (p1 * 256) + p2
                            
                            data_proxy = FTPSDataProxy(ip_str, server_data_port, ip, proxy_context, server_context)
                            data_proxy.start()
                            
                            proxy_p1 = data_proxy.listen_port // 256
                            proxy_p2 = data_proxy.listen_port % 256
                            new_response = f"227 Entering Passive Mode (127,0,0,1,{proxy_p1},{proxy_p2}).\r\n".encode('utf-8')
                            client_sock_ref[0].sendall(new_response)
                            continue

                    else:
                        # Once TLS is active, we must decode the decrypted stream to find PASV
                        decoded = data.decode('utf-8', errors='ignore')
                        pasv_match = re.search(r'227 .*?\((\d+,\d+,\d+,\d+),(\d+),(\d+)\)', decoded)
                        if pasv_match:
                            ip_str = pasv_match.group(1).replace(',', '.')
                            p1, p2 = int(pasv_match.group(2)), int(pasv_match.group(3))
                            server_data_port = (p1 * 256) + p2
                            
                            console.print(f"[yellow]Intercepted SECURE PASV response for port {server_data_port}[/yellow]")
                            
                            data_proxy = FTPSDataProxy(ip_str, server_data_port, ip, proxy_context, server_context)
                            data_proxy.start()
                            
                            proxy_p1 = data_proxy.listen_port // 256
                            proxy_p2 = data_proxy.listen_port % 256
                            
                            new_response = f"227 Entering Passive Mode (127,0,0,1,{proxy_p1},{proxy_p2}).\r\n".encode('utf-8')
                            client_sock_ref[0].sendall(new_response)
                            continue

                    client_sock_ref[0].sendall(data)
            except Exception as e:
                console.print(f"[red]Error forwarding FTPS S2C: {e}[/red]")
                
        c2s_thread = threading.Thread(target=forward_c2s)
        s2c_thread = threading.Thread(target=forward_s2c)
        c2s_thread.start()
        s2c_thread.start()
        c2s_thread.join()
        s2c_thread.join()
        
    except Exception as e:
        console.print(f"[red]FTPS Proxy connection error: {e}[/red]")
    finally:
        client_sock_ref[0].close()
        server_sock_ref[0].close()


def start_ftps_proxy(host=PROXY_HOST, port=FTPS_PROXY_PORT):
    proxy_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    proxy_context.minimum_version = ssl.TLSVersion.TLSv1_3
    proxy_context.set_ciphers('HIGH:!aNULL:!eNULL:!MD5')
    
    try:
        proxy_context.load_cert_chain(certfile=PROXY_CERT, keyfile=PROXY_KEY)
    except FileNotFoundError:
        console.print(f"[red]Certificates not found at {PROXY_CERT}. Run cert_gen.py first.[/red]")
        sys.exit(1)
        
    server_context = ssl.create_default_context()
    server_context.check_hostname = False
    server_context.verify_mode = ssl.CERT_NONE
    server_context.minimum_version = ssl.TLSVersion.TLSv1_3

    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.bind((host, port))
    proxy.listen(5)
    console.print(f"[bold green]FTPS Control Proxy listening on {host}:{port}[/bold green]")
    
    try:
        while True:
            client_socket, client_address = proxy.accept()
            threading.Thread(target=handle_ftps_client, args=(client_socket, client_address, proxy_context, server_context)).start()
    except KeyboardInterrupt:
        console.print("[yellow]FTPS Proxy shutting down...[/yellow]")
    finally:
        proxy.close()

if __name__ == "__main__":
    start_ftps_proxy()

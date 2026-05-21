import socket
import threading
import sys
import os
import re
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import PROXY_HOST, FTP_PROXY_PORT, SERVER_HOST, FTP_SERVER_PORT, BUFFER_SIZE
from core.file_extractor import analyze_payload_for_files
from monitoring.logger import log_event
from rich.console import Console

console = Console()

class FTPDataProxy(threading.Thread):
    def __init__(self, server_ip, server_port, client_ip):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_ip = client_ip
        
        # Listen for the client's data connection
        self.proxy_data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy_data_socket.bind((PROXY_HOST, 0)) # OS assigns random port
        self.proxy_data_socket.listen(1)
        self.listen_port = self.proxy_data_socket.getsockname()[1]
        
    def run(self):
        try:
            # Wait for client to connect to our data proxy
            self.proxy_data_socket.settimeout(10)
            client_socket, addr = self.proxy_data_socket.accept()
            console.print(f"[dim cyan]Data connection intercepted from {addr}[/dim cyan]")
            
            # Connect to the actual FTP server's data port
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((self.server_ip, self.server_port))
            
            # Thread for Server -> Client data (download)
            def s2c():
                try:
                    while True:
                        data = server_socket.recv(BUFFER_SIZE)
                        if not data: break
                        client_socket.sendall(data)
                except: pass
                
            # Thread for Client -> Server data (upload)
            def c2s():
                try:
                    # Buffer for extraction (in case file is small enough or chunked)
                    full_payload = b""
                    while True:
                        data = client_socket.recv(BUFFER_SIZE)
                        if not data: break
                        full_payload += data
                        
                        # Forward immediately
                        server_socket.sendall(data)
                    
                    # Notify server that upload is complete
                    try:
                        server_socket.shutdown(socket.SHUT_WR)
                    except:
                        pass
                        
                    # Once transfer is done, try to extract file from payload
                    if full_payload:
                        file_type = analyze_payload_for_files(full_payload)
                        if file_type:
                            log_event("FTP_FILE", f"Extracted {file_type} via FTP Data channel")
                except Exception as e: 
                    console.print(f"[red]Error in Data C2S: {e}[/red]")
            
            t1 = threading.Thread(target=s2c)
            t2 = threading.Thread(target=c2s)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            
            client_socket.close()
            server_socket.close()
            
        except Exception as e:
            console.print(f"[red]Data Proxy Error: {e}[/red]")
        finally:
            self.proxy_data_socket.close()

def handle_ftp_client(client_socket, client_address):
    ip, port = client_address
    console.print(f"[bold red]FTP Connection intercepted![/bold red] from {ip}:{port}")
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.connect((SERVER_HOST, FTP_SERVER_PORT))
        
        def forward_c2s():
            try:
                while True:
                    data = client_socket.recv(BUFFER_SIZE)
                    if not data: break
                    log_event("FTP_CMD", data.decode('utf-8', errors='ignore').strip())
                    server_socket.sendall(data)
            except: pass
            
        def forward_s2c():
            try:
                while True:
                    data = server_socket.recv(BUFFER_SIZE)
                    if not data: break
                    
                    decoded = data.decode('utf-8', errors='ignore')
                    
                    # Intercept PASV response
                    # Format: 227 Entering Passive Mode (127,0,0,1,213,99).
                    pasv_match = re.search(r'227 .*?\((\d+,\d+,\d+,\d+),(\d+),(\d+)\)', decoded)
                    if pasv_match:
                        ip_str = pasv_match.group(1).replace(',', '.')
                        p1, p2 = int(pasv_match.group(2)), int(pasv_match.group(3))
                        server_data_port = (p1 * 256) + p2
                        
                        console.print(f"[yellow]Intercepted PASV response for port {server_data_port}[/yellow]")
                        
                        # Spin up data proxy
                        data_proxy = FTPDataProxy(ip_str, server_data_port, ip)
                        data_proxy.start()
                        
                        # Rewrite response
                        # Our data proxy is on 127.0.0.1
                        proxy_p1 = data_proxy.listen_port // 256
                        proxy_p2 = data_proxy.listen_port % 256
                        
                        new_response = f"227 Entering Passive Mode (127,0,0,1,{proxy_p1},{proxy_p2}).\r\n".encode('utf-8')
                        console.print(f"[green]Rewritten PASV response for proxy port {data_proxy.listen_port}[/green]")
                        
                        client_socket.sendall(new_response)
                    else:
                        client_socket.sendall(data)
            except Exception as e:
                console.print(f"[red]Error forwarding S2C: {e}[/red]")
                
        c2s_thread = threading.Thread(target=forward_c2s)
        s2c_thread = threading.Thread(target=forward_s2c)
        c2s_thread.start()
        s2c_thread.start()
        c2s_thread.join()
        s2c_thread.join()
        
    except Exception as e:
        console.print(f"[red]FTP Proxy connection error: {e}[/red]")
    finally:
        client_socket.close()
        server_socket.close()

def start_ftp_proxy(host=PROXY_HOST, port=FTP_PROXY_PORT):
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.bind((host, port))
    proxy.listen(5)
    console.print(f"[bold green]FTP Control Proxy listening on {host}:{port}[/bold green]")
    
    try:
        while True:
            client_socket, client_address = proxy.accept()
            threading.Thread(target=handle_ftp_client, args=(client_socket, client_address)).start()
    except KeyboardInterrupt:
        console.print("[yellow]FTP Proxy shutting down...[/yellow]")
    finally:
        proxy.close()

if __name__ == "__main__":
    start_ftp_proxy()

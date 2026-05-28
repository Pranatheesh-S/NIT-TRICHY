import ftplib
import os
import argparse
import sys
import ssl

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import PROXY_HOST, FTPS_PROXY_PORT
from rich.console import Console

console = Console()

def secure_upload_ftp(filepath, host=PROXY_HOST, port=FTPS_PROXY_PORT):
    if not os.path.exists(filepath):
        console.print(f"[red]Error: File {filepath} does not exist.[/red]")
        return
        
    filename = os.path.basename(filepath)
    
    try:
        # Create a custom SSL context to ignore self-signed certificates and enforce TLS 1.3
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        
        console.print(f"[cyan]Connecting securely to FTPS Proxy at {host}:{port}...[/cyan]")
        ftp = ftplib.FTP_TLS(context=context)
        ftp.connect(host, port)
        
        # Log in
        ftp.login("user", "12345")
        
        # Upgrade data connection to TLS (PROT P)
        ftp.prot_p()
        
        console.print(f"[cyan]Securely uploading {filename}...[/cyan]")
        with open(filepath, 'rb') as f:
            ftp.storbinary(f'STOR {filename}', f)
            
        console.print("[bold green]Upload complete![/bold green]")
        
        ftp.quit()
    except Exception as e:
        console.print(f"[red]FTPS Upload failed: {e}[/red]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Secure FTPS Client for File Upload")
    parser.add_argument("file", help="Path to the file to upload")
    parser.add_argument("--host", default=PROXY_HOST, help="Proxy host to connect to")
    parser.add_argument("--port", type=int, default=FTPS_PROXY_PORT, help="Proxy FTPS port")
    
    args = parser.parse_args()
    secure_upload_ftp(args.file, args.host, args.port)

import ftplib
import os
import sys
import time

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import PROXY_HOST, FTP_PROXY_PORT
from rich.console import Console
from rich.progress import Progress

console = Console()

def upload_file_ftp(filepath, host=PROXY_HOST, port=FTP_PROXY_PORT):
    if not os.path.exists(filepath):
        console.print(f"[red]Error: File {filepath} does not exist.[/red]")
        return

    filename = os.path.basename(filepath)
    
    try:
        console.print(f"[cyan]Connecting to FTP Proxy {host}:{port}...[/cyan]")
        ftp = ftplib.FTP()
        ftp.connect(host, port)
        
        # Login with our dummy credentials
        console.print("[cyan]Logging in as 'user'...[/cyan]")
        ftp.login("user", "12345")
        
        filesize = os.path.getsize(filepath)
        
        console.print(f"[bold]Uploading {filename} via FTP...[/bold]")
        with open(filepath, 'rb') as f:
            # We use STOR command for upload
            ftp.storbinary(f'STOR {filename}', f)
            
        console.print(f"\n[bold green]FTP Transfer Complete![/bold green]")
        
        ftp.quit()
    except ConnectionRefusedError:
        console.print(f"[red]Connection refused. Is the FTP proxy running on {host}:{port}?[/red]")
    except ftplib.all_errors as e:
        console.print(f"[red]FTP Error: {str(e)}[/red]")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Upload a file via FTP.")
    parser.add_argument("file", help="Path to the file to send")
    parser.add_argument("--host", default=PROXY_HOST, help="FTP Proxy IP address")
    parser.add_argument("--port", type=int, default=FTP_PROXY_PORT, help="FTP Proxy port")
    
    args = parser.parse_args()
    upload_file_ftp(args.file, args.host, args.port)

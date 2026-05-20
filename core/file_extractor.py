import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import INTERCEPTED_DIR
from utils.helpers import get_timestamp
from monitoring.logger import log_event
from rich.console import Console

console = Console()

FILE_SIGNATURES = {
    b'\x89PNG\r\n\x1a\n': 'png',
    b'\xff\xd8\xff': 'jpg',
    b'%PDF-': 'pdf',
    b'PK\x03\x04': 'zip', # Covers docx, xlsx, pptx, zip
    b'GIF89a': 'gif',
    b'GIF87a': 'gif',
    b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1': 'doc',
}

def analyze_payload_for_files(payload, content_type=""):
    """
    Attempts to identify file signatures in the payload or extracts
    based on multipart/form-data.
    """
    detected_type = "unknown"
    
    # Check magic bytes for known types
    for sig, ext in FILE_SIGNATURES.items():
        if sig in payload:
            detected_type = ext
            break
            
    # Simple text detection (heuristic)
    if detected_type == "unknown" and b'Content-Type: text/plain' in payload:
        detected_type = "txt"
        
    if detected_type != "unknown":
        save_extracted_file(payload, detected_type)
        return detected_type
        
    return None

def save_extracted_file(data, ext):
    timestamp = get_timestamp().replace(':', '-').replace(' ', '_')
    filename = f"intercepted_{timestamp}.{ext}"
    filepath = os.path.join(INTERCEPTED_DIR, filename)
    
    try:
        with open(filepath, 'wb') as f:
            f.write(data)
        log_event("FILE_EXTRACTED", f"Extracted {ext} file: {filename}")
        console.print(f"[bold green]File Extracted:[/bold green] {filename}")
    except Exception as e:
        log_event("ERROR", f"Failed to save extracted file: {e}")

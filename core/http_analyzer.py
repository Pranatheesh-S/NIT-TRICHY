from core.file_extractor import analyze_payload_for_files
from monitoring.logger import log_event
from rich.console import Console

console = Console()

class HTTPAnalyzer:
    def __init__(self):
        pass
        
    def analyze_packet(self, data: bytes):
        """
        Analyzes a packet for HTTP requests.
        Returns a dict of info if HTTP, else None.
        """
        try:
            # We just do basic text parsing for headers
            header_end = data.find(b'\r\n\r\n')
            if header_end == -1:
                return None
                
            headers_raw = data[:header_end].decode('utf-8', errors='ignore')
            payload = data[header_end+4:]
            
            lines = headers_raw.split('\r\n')
            if not lines:
                return None
                
            first_line = lines[0]
            parts = first_line.split(' ')
            if len(parts) >= 3 and parts[0] in ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']:
                method = parts[0]
                path = parts[1]
                
                # Extract headers into dict
                headers = {}
                for line in lines[1:]:
                    if ': ' in line:
                        k, v = line.split(': ', 1)
                        headers[k.lower()] = v
                        
                content_type = headers.get('content-type', '')
                
                log_event("HTTP_REQ", f"{method} {path}")
                
                # Check for files
                if method in ['POST', 'PUT']:
                    if 'multipart/form-data' in content_type or len(payload) > 0:
                        file_type = analyze_payload_for_files(payload, content_type)
                        if file_type:
                            log_event("HTTP_FILE", f"Detected uploaded file of type: {file_type}")
                            
                return {
                    'method': method,
                    'path': path,
                    'headers': headers,
                    'payload_len': len(payload)
                }
        except Exception as e:
            log_event("ERROR", f"HTTP parsing failed: {e}")
            
        return None

http_analyzer = HTTPAnalyzer()

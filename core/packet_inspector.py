from core.http_analyzer import http_analyzer
from monitoring.logger import log_event
import time

class PacketInspector:
    def __init__(self):
        self.request_counts = {}
        
    def inspect(self, data: bytes, client_ip: str):
        """
        Inspects raw packet data.
        Returns unmodified data (could be modified if Scapy was used).
        """
        # Analyze HTTP
        result = http_analyzer.analyze_packet(data)
        
        if result:
            # Check for large upload
            if result['payload_len'] > 1024 * 1024: # > 1MB
                log_event("SUSPICIOUS", f"Large HTTP payload detected from {client_ip}: {result['payload_len']} bytes")
                
            # Check for repeated requests
            current_time = time.time()
            if client_ip not in self.request_counts:
                self.request_counts[client_ip] = []
                
            # Clean up old timestamps (older than 10 seconds)
            self.request_counts[client_ip] = [t for t in self.request_counts[client_ip] if current_time - t < 10]
            self.request_counts[client_ip].append(current_time)
            
            if len(self.request_counts[client_ip]) > 50:
                log_event("SUSPICIOUS", f"Repeated requests detected from {client_ip} (>50 in 10s)")
                
        return data

packet_inspector = PacketInspector()

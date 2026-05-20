import uuid
from typing import Dict
from monitoring.logger import log_event
from monitoring.traffic_monitor import monitor

class Session:
    def __init__(self, client_ip, client_port):
        self.session_id = str(uuid.uuid4())[:8]
        self.client_ip = client_ip
        self.client_port = client_port
        self.status = "ACTIVE"
        
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        
    def create_session(self, client_ip, client_port) -> Session:
        session = Session(client_ip, client_port)
        self.sessions[session.session_id] = session
        log_event("SESSION_START", f"Session {session.session_id} started for {client_ip}:{client_port}")
        monitor.update_sessions(1)
        return session
        
    def end_session(self, session_id):
        if session_id in self.sessions:
            self.sessions[session_id].status = "CLOSED"
            log_event("SESSION_END", f"Session {session_id} closed")
            monitor.update_sessions(-1)

session_manager = SessionManager()

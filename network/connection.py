import socket  # Für die Internetverbindung
import json  # Zum Verpacken von Nachrichten

class NetworkHandler:
    def __init__(self, port):
        # Speichert den Port 
        self.port = port
        
        # Erstellt ein UDP-Socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Bindet den Socket an localhost und Port
        self.socket.bind(('localhost', port))
    
    def send_message(self, message, target_port):
        try:
            # Verpackt die Nachricht als JSON 
            # und schickt sie an den Ziel-Port
            self.socket.sendto(
                json.dumps(message).encode(),
                ('localhost', target_port))
        except Exception as e:
            print(f"Send error: {e}")

    def receive(self):
        # Wartet auf eine Nachricht (max. 1024 Zeichen groß)
        data, _ = self.socket.recvfrom(1024)
        
        # Öffnet JSON und gibt den Inhalt zurück
        return json.loads(data.decode())
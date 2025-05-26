import threading  # Damit wir mehrere Dinge gleichzeitig machen können
from utils import config_loader  # Unser Config-Leser
from network.connection import NetworkHandler  # Unser Netzwerk-Handler

def user_input_loop(network, config):
    while True:  # Endlosschleife
        # Fragt nach einer Nachricht
        msg = input("Schreibe eine Nachricht: ")
        
        # Wenn der Benutzer "exit" eingibt: Schleife beenden
        if msg.lower() == 'exit':
            break
            
        # Schickt die Nachricht an den nächsten Port (+1)
        network.send_message({
            'von': config['user']['name'],  # Absender
            'text': msg  # Nachrichtentext
        }, config['user']['port'] + 1)

def message_listener(network):
    while True:  # Immer wieder
        # Wartet auf eine Nachricht
        data = network.receive()
        
        # Zeigt die Nachricht an
        print(f"\nReceived: {data['von']}: {data['text']}\n> ", end="")

def main():
    print("Startet chat...")  # Startnachricht
    
    # Lädt die Konfiguration
    config = config_loader.load_config()
    if not config:  # Falls keine Konfiguration da ist
        return  # Programm beenden
    
    # Erstellt den Netzwerk-Handler mit unserem Port
    network = NetworkHandler(config['user']['port'])
    
    # Startet einen Hintergrund-Thread für den Empfang
    threading.Thread(
        target=message_listener,  # Was der Thread machen soll
        args=(network,),  # Was er braucht
        daemon=True  # Wird beendet wenn Hauptprogramm endet
    ).start()
    
    # Startet die Hauptschleife für Benutzereingaben
    user_input_loop(network, config)

if __name__ == "__main__":
    main()  # Startet das Programm
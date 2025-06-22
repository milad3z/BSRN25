#!/usr/bin/env python3
## @file main.py
# @brief Haupt-Einstiegspunkt der P2P-Chat-Anwendung.

import multiprocessing
import sys
import time
import os
import tempfile
from user_interface import UserInterface
from network.network_handler import NetworkHandler
from network.discovery import DiscoveryService
from utils.config_loader import load_config

def network_process(config, from_ui_queue, to_ui_queue):
    """! Prozess für die Netzwerkkommunikation.
    """
    network_handler = NetworkHandler(config, from_ui_queue, to_ui_queue)
    while network_handler.running:
        try:
            time.sleep(0.1)
        except (KeyboardInterrupt, SystemExit):
            network_handler.shutdown()
            break

def discovery_process(config):
    """! Prozess für den Discovery-Dienst.
    """
    lock_file_path = os.path.join(tempfile.gettempdir(), 'p2p_chat_discovery.lock')
    if os.path.exists(lock_file_path):
        # Lock-Datei existiert, also läuft bereits ein anderer Discovery-Dienst.
        return

    with open(lock_file_path, 'w') as f:
        f.write(str(os.getpid()))

    try:
        discovery_service = DiscoveryService(config)
        discovery_service.start()
        while True:
            try:
                time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                discovery_service.stop()
                break
    finally:
        os.remove(lock_file_path)


def main():
    """! Hauptfunktion der Anwendung.
    
    Diese Funktion initialisiert die Anwendung, lädt die Konfiguration,
    startet die Netzwerk- und Discovery-Komponenten in separaten Prozessen
    und führt die Benutzeroberfläche im Hauptprozess aus.
    """
    # Konfiguration laden
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.toml"
    config = load_config(config_file)
    if not config:
        print("Fehler: Konfiguration konnte nicht geladen werden.")
        sys.exit(1)

    # Queues für die Interprozesskommunikation erstellen
    ui_to_network_queue = multiprocessing.Queue()
    network_to_ui_queue = multiprocessing.Queue()

    # Hintergrundprozesse erstellen
    network = multiprocessing.Process(target=network_process, args=(config, ui_to_network_queue, network_to_ui_queue))
    network.daemon = True
    
    processes = [network]

    if config.get('discovery', {}).get('enabled', False):
        discovery = multiprocessing.Process(target=discovery_process, args=(config,))
        discovery.daemon = True
        processes.append(discovery)

    # Prozesse starten
    for p in processes:
        p.start()

    # Benutzeroberfläche im Hauptprozess starten
    ui = UserInterface(ui_to_network_queue, network_to_ui_queue)
    ui.show_welcome_banner()
    
    try:
        # Die UI-Schleife wird im Hauptthread ausgeführt
        ui.handle_input()
    except KeyboardInterrupt:
        print("\nProgramm wird beendet...")
    finally:
        # Alle Prozesse beenden
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join()
        print("Alle Prozesse wurden beendet.")
        sys.exit(0)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
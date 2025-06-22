#!/usr/bin/env python3
## @file discovery.py
# @brief Implementiert den Discovery-Dienst für die P2P-Chat-Anwendung.

import time

class DiscoveryService:
    """! Der DiscoveryService ist für das Auffinden anderer Peers im Netzwerk zuständig.
    """
    def __init__(self, config):
        """! Initialisiert den Discovery-Dienst.
        @param config Die Konfiguration der Anwendung.
        """
        self.config = config
        self.running = True

    def start(self):
        """! Startet den Discovery-Dienst.
        """
        print("Discovery-Dienst gestartet.")
        while self.running:
            time.sleep(10)

    def stop(self):
        """! Stoppt den Discovery-Dienst.
        """
        self.running = False
        print("Discovery-Dienst gestoppt.")
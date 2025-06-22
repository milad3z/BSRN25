# BSRN25
# P2P-Chat-Programm

Dies ist ein Peer-to-Peer-Chat-Programm, das es Benutzern ermoeglicht, über ein lokales Netzwerk miteinander zu kommunizieren.

## Teammitglieder und Verantwortlichkeiten

In Diesem Projekt wurde die Arbeit wie folgt aufgeteilt:

*   **Taha**: Projektleitung & Hauptprogramm (`main.py`)
    *   Verantwortlich fuer den Haupteinstiegspunkt der Anwendung, die Prozessverwaltung und die Interprozesskommunikation.

*   **Simon**: Benutzeroberflaeche (`user_interface.py`)
    *   Verantwortlich fuer die Kommandozeilenschnittstelle, die Verarbeitung von Benutzereingaben und die Anzeige von Nachrichten.

*   **Milad**: Netzwerkprotokoll & Hilfsfunktionen (`utils/protocol.py`, `network/network_handler.py`)
    *   Verantwortlich fuer die Implementierung des "Simple Local Chat Protocol" (SLCP) und der protokollbezogenen Hilfsfunktionen.

*   **Matin**: Netzwerkkommunikation & Discovery (`network/network_handler.py`, `network/discovery.py`)
    *   Verantwortlich fuer die Low-Level-Netzwerkkommunikation, die Socket-Verwaltung und den Discovery-Dienst
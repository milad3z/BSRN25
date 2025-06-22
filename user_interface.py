#!/usr/bin/env python3
## @file user_interface.py
# @brief Benutzeroberfläche für die P2P-Chat-Anwendung.

import threading
import sys
from utils.protocol import escape

class UserInterface:
    """! Die UserInterface-Klasse ist für die Interaktion mit dem Benutzer zuständig.
    """
    def __init__(self, to_network_queue, from_network_queue):
        """! Initialisiert die Benutzeroberfläche.
        @param to_network_queue Die Queue zum Senden von Befehlen an den Netzwerk-Prozess.
        @param from_network_queue Die Queue zum Empfangen von Nachrichten vom Netzwerk-Prozess.
        """
        self.to_network_queue = to_network_queue
        self.from_network_queue = from_network_queue
        self.running = True
        
        self.output_thread = threading.Thread(target=self.handle_output)
        self.output_thread.daemon = True
        self.output_thread.start()

    def show_welcome_banner(self):
        """! Zeigt ein Willkommensbanner mit grundlegenden Befehlen an.
        """
        print("\n=== Peer-to-Peer Chat ===")
        print("Befehle: /join <Gruppe>, msg <Nutzer> <Text>, who, exit, /help")
        print("Standardnachrichten werden an die aktuelle Gruppe gesendet.\n")

    def handle_input(self):
        """! Verarbeitet die Benutzereingaben in der Hauptschleife.
        """
        while self.running:
            try:
                user_input = input("> ")
                if user_input.strip():
                    self.process_command(user_input)
            except (EOFError, KeyboardInterrupt):
                self.running = False
                self.to_network_queue.put(("shutdown", []))
                break

    def handle_output(self):
        """! Verarbeitet die Netzwerkausgaben.
        """
        while self.running:
            try:
                message = self.from_network_queue.get()
                if message is None:
                    break
                print(f"\n{message}\n> ", end="", flush=True)
            except (EOFError, KeyboardInterrupt):
                self.running = False
                break

    def process_command(self, user_input):
        """! Verarbeitet die eingegebenen Befehle.
        @param user_input Der vom Benutzer eingegebene Text.
        """
        parts = user_input.split()
        command = parts[0].lower()
        args = parts[1:]

        if command.startswith('/'):
            command = command[1:]
            if command == "help":
                print("Verfügbare Befehle: /join <Gruppe>, /leave <Gruppe>, /switch <Gruppe>, /groups, msg <Nutzer> <Text>, who [Gruppe], list [Gruppe], img <handle> <size>, exit, /help")
            elif command == "join":
                if len(args) == 1:
                    self.to_network_queue.put(("join_group", [args[0]]))
                else:
                    print("Verwendung: /join <Gruppe>")
            elif command == "leave":
                if len(args) == 1:
                    self.to_network_queue.put(("leave_group", [args[0]]))
                else:
                    print("Verwendung: /leave <Gruppe>")
            elif command == "switch":
                if len(args) == 1:
                    self.to_network_queue.put(("switch_active_group", [args[0]]))
                else:
                    print("Verwendung: /switch <Gruppe>")
            elif command == "groups":
                self.to_network_queue.put(("list_groups", []))
            else:
                print(f"Unbekannter Befehl: /{command}")
        elif command == "msg":
            if len(args) >= 2:
                handle = args[0]
                text = " ".join(args[1:])
                self.to_network_queue.put(("send_message", [handle, escape(text)]))
            else:
                print("Verwendung: msg <Nutzer> <Text>")
        elif command == "who":
            group = args[0] if args else None
            self.to_network_queue.put(("who", [group]))
        elif command == "list":
            group = args[0] if args else None
            self.to_network_queue.put(("list_users", [group]))
        elif command == "img":
            if len(args) == 2:
                self.to_network_queue.put(("send_image", [args[0], args[1]]))
            else:
                print("Verwendung: img <handle> <size>")
        elif command == "exit":
            self.running = False
            self.to_network_queue.put(("shutdown", []))
            print("Programm wird beendet...")
            sys.exit(0)
        else:
            self.to_network_queue.put(("send_group_message", [user_input]))
## @file network_handler.py
# @brief Implementiert die Kernlogik der Netzwerkkommunikation.

import socket
import time
import os
from threading import Thread
from utils.protocol import parse_message, unescape

class NetworkHandler:
    def __init__(self, config, from_ui_queue, to_ui_queue):
        self.config = config
        self.from_ui_queue = from_ui_queue
        self.to_ui_queue = to_ui_queue
        self.running = True
        self.image_transfer_info = {}
        self.handle = self.config['user']['handle']
        self.port = self.config['user']['port']
        self.broadcast_port = self.config['user'].get('whoisport', 4000)
        self.broadcast_address = '255.255.255.255'
        
        self.groups = ['default']
        self.active_group = 'default'
        self.users_by_group = {'default': {}} # {Gruppe: {Handle: (IP, Port)}}

        self.unicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.unicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.unicast_socket.bind(('0.0.0.0', self.port))

        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.bind(('0.0.0.0', self.broadcast_port))

        self.unicast_listener = Thread(target=self._listen_unicast)
        self.unicast_listener.daemon = True
        self.unicast_listener.start()

        self.broadcast_listener = Thread(target=self._listen_broadcast)
        self.broadcast_listener.daemon = True
        self.broadcast_listener.start()
        
        self.ui_listener_thread = Thread(target=self._listen_to_ui)
        self.ui_listener_thread.daemon = True
        self.ui_listener_thread.start()

        self.join_group('default')

    def _listen_to_ui(self):
        while self.running:
            try:
                command, args = self.from_ui_queue.get()
                if hasattr(self, command):
                    getattr(self, command)(*args)
            except Exception as e:
                self.to_ui_queue.put(f"Fehler im Netzwerk-Handler: {e}")

    def _listen_unicast(self):
        while self.running:
            try:
                data, addr = self.unicast_socket.recvfrom(65535)
                if addr in self.image_transfer_info:
                    size, handle = self.image_transfer_info.pop(addr)
                    if len(data) == size:
                        self._save_image(data, handle)
                    else:
                        self.to_ui_queue.put(f"Bildempfang von {handle} fehlgeschlagen: Größen stimmen nicht überein (erwartet: {size}, erhalten: {len(data)}).")
                else:
                    message = data.decode('utf-8').strip()
                    self._handle_unicast_message(message, addr)
            except OSError:
                if self.running:
                    break
            except Exception as e:
                if self.running:
                    self.to_ui_queue.put(f"Unicast-Fehler: {e}")

    def _listen_broadcast(self):
        while self.running:
            try:
                data, addr = self.broadcast_socket.recvfrom(512)
                message = data.decode('utf-8').strip()
                self._handle_broadcast_message(message, addr)
            except OSError:
                if self.running:
                    break
            except Exception as e:
                if self.running:
                    self.to_ui_queue.put(f"Broadcast-Fehler: {e}")

    def _handle_unicast_message(self, message, addr):
        parts = parse_message(message)
        command = parts[0]
        args = parts[1:]

        if command == "MSG":
            if len(args) == 2:
                sender, text = args
                self.to_ui_queue.put(f"[{sender} -> mir]: {unescape(text)}")
        
        elif command == "IMG":
            if len(args) == 2:
                sender, size_str = args
                try:
                    size = int(size_str)
                    self.image_transfer_info[addr] = (size, sender)
                    self.to_ui_queue.put(f"Eingehendes Bild von {sender} ({size} bytes). Warte auf Daten...")
                except (ValueError, IndexError):
                    self.to_ui_queue.put(f"Ungültige IMG-Nachricht empfangen: {message}")

        elif command == "KNOWUSERS":
            if len(args) >= 1:
                group = args[0]
                users = args[1:]
                if group in self.users_by_group:
                    for i in range(0, len(users), 3):
                        handle, ip, port = users[i], users[i+1], int(users[i+2])
                        if handle != self.handle:
                            self.users_by_group[group][handle] = (ip, int(port))
                    self.to_ui_queue.put(f"Bekannte Benutzer in Gruppe '{group}' aktualisiert: {list(self.users_by_group[group].keys())}")


    def _handle_broadcast_message(self, message, addr):
        parts = parse_message(message)
        command = parts[0]
        args = parts[1:]
        
        if command == "JOIN":
            if len(args) == 4:
                group, handle, ip, port_str = args
                try:
                    port = int(port_str)
                    if handle != self.handle:
                        if group not in self.users_by_group:
                            self.users_by_group[group] = {}
                        self.users_by_group[group][handle] = (ip, port)
                        self.to_ui_queue.put(f"{handle} ist Gruppe '{group}' beigetreten.")
                except (ValueError, IndexError):
                    pass
        
        elif command == "LEAVE":
            if len(args) == 2:
                group, handle = args
                if group in self.users_by_group and handle in self.users_by_group[group]:
                    del self.users_by_group[group][handle]
                    self.to_ui_queue.put(f"{handle} hat Gruppe '{group}' verlassen.")

        elif command == "GMSG":
            if len(args) >= 3:
                group, sender, text = args[0], args[1], " ".join(args[2:])
                if group in self.groups and sender != self.handle:
                    self.to_ui_queue.put(f"[{group}] {sender}: {unescape(text)}")

        elif command == "WHO":
            if len(args) == 3:
                group, sender_handle, sender_port_str = args
                try:
                    sender_port = int(sender_port_str)
                    sender_ip = addr[0]
                    if group in self.users_by_group:
                        know_users_parts = [group]
                        for handle, (user_ip, user_port) in self.users_by_group[group].items():
                            know_users_parts.extend([handle, user_ip, str(user_port)])
                        
                        know_users_parts.extend([self.handle, self.get_local_ip(), str(self.port)])

                        know_users_msg = f"KNOWUSERS {' '.join(know_users_parts)}"
                        self.unicast_socket.sendto(know_users_msg.encode('utf-8'), (sender_ip, sender_port))
                except (ValueError, IndexError):
                    pass


    def who(self, group_name=None):
        group = group_name if group_name else self.active_group
        msg = f"WHO {group} {self.handle} {self.port}"
        self.broadcast_socket.sendto(msg.encode('utf-8'), (self.broadcast_address, self.broadcast_port))
        self.to_ui_queue.put(f"WHO-Anfrage für Gruppe '{group}' gesendet.")

    def join_group(self, group_name):
        if group_name in self.groups:
            self.active_group = group_name
            self.to_ui_queue.put(f"Du bist bereits in Gruppe '{group_name}'. Sie ist jetzt aktiv.")
            return

        self.groups.append(group_name)
        self.users_by_group[group_name] = {}
        self.active_group = group_name
        join_msg = f"JOIN {group_name} {self.handle} {self.get_local_ip()} {self.port}"
        self.broadcast_socket.sendto(join_msg.encode('utf-8'), (self.broadcast_address, self.broadcast_port))
        self.to_ui_queue.put(f"Gruppe '{group_name}' beigetreten.")

    def leave_group(self, group_name):
        if group_name not in self.groups:
            self.to_ui_queue.put(f"Du bist nicht in Gruppe '{group_name}'.")
            return
        
        leave_msg = f"LEAVE {group_name} {self.handle}"
        self.broadcast_socket.sendto(leave_msg.encode('utf-8'), (self.broadcast_address, self.broadcast_port))
        
        if group_name in self.users_by_group:
            for handle, (ip, port) in self.users_by_group[group_name].items():
                self.unicast_socket.sendto(leave_msg.encode('utf-8'), (ip, port))
        
        self.groups.remove(group_name)
        del self.users_by_group[group_name]

        if self.active_group == group_name:
            self.active_group = 'default' if 'default' in self.groups else (self.groups[0] if self.groups else None)
        
        self.to_ui_queue.put(f"Gruppe '{group_name}' verlassen.")


    def send_message(self, handle, text):
        user_info = None
        target_ip, target_port = None, None
        for group in self.users_by_group.values():
            if handle in group:
                target_ip, target_port = group[handle]
                break
        
        if target_ip and target_port:
            msg = f"MSG {self.handle} {text}"
            self.unicast_socket.sendto(msg.encode('utf-8'), (target_ip, target_port))
        else:
            self.to_ui_queue.put(f"Nutzer '{handle}' nicht gefunden. 'who' ausführen, um die Benutzerliste zu aktualisieren.")

    def send_group_message(self, text):
        if not self.active_group:
            self.to_ui_queue.put("Keine aktive Gruppe ausgewählt. Mit /join <gruppe> beitreten.")
            return
        msg = f"GMSG {self.active_group} {self.handle} {text}"
        self.broadcast_socket.sendto(msg.encode('utf-8'), (self.broadcast_address, self.broadcast_port))

    def shutdown(self):
        for group in self.groups:
            self.leave_group(group)
        self.running = False
        try:
            self.unicast_socket.close()
            self.broadcast_socket.close()
        except Exception:
            pass

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # Muss nicht erreichbar sein
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def list_users(self, group_name=None):
        group = group_name if group_name else self.active_group
        if group not in self.users_by_group:
            self.to_ui_queue.put(f"Unbekannte Gruppe: {group}")
            return
            
        users = self.users_by_group[group]
        if not users:
            user_list = "- Niemand sonst online."
        else:
            user_list = "\n".join([f"- {handle}" for handle in users])
        self.to_ui_queue.put(f"Benutzer in Gruppe '{group}':\n{user_list}")

    def switch_active_group(self, group_name):
        if group_name in self.groups:
            self.active_group = group_name
            self.to_ui_queue.put(f"Aktive Gruppe ist jetzt '{group_name}'.")
        else:
            self.to_ui_queue.put(f"Du bist nicht in Gruppe '{group_name}'.")

    def list_groups(self):
        if not self.groups:
            group_list = "- Keine"
        else:
            group_list = "\n".join([f"- {group}{' (aktiv)' if group == self.active_group else ''}" for group in self.groups])
        self.to_ui_queue.put(f"Beigetretene Gruppen:\n{group_list}")

    def send_image(self, handle, size_str):
        user_info = None
        for group in self.users_by_group.values():
            if handle in group:
                user_info = group[handle]
                break

        if not user_info:
            self.to_ui_queue.put(f"Nutzer '{handle}' nicht gefunden.")
            return

        try:
            size = int(size_str)
            if size <= 0:
                self.to_ui_queue.put("Größe muss positiv sein.")
                return
        except ValueError:
            self.to_ui_queue.put(f"Ungültige Größe: {size_str}")
            return

        try:
            binary_data = os.urandom(size)
            ip, port = user_info
            img_command = f"IMG {self.handle} {size}"
            self.unicast_socket.sendto(img_command.encode('utf-8'), (ip, port))
            time.sleep(0.1)
            self.unicast_socket.sendto(binary_data, (ip, port))
            self.to_ui_queue.put(f"Binärdaten an {handle} gesendet ({size} bytes).")
        except Exception as e:
            self.to_ui_queue.put(f"Fehler beim Senden der Binärdaten: {e}")
        
    def _save_image(self, data, sender):
        try:
            image_path = self.config.get('user', {}).get('imagepath', 'received_images')
            if not os.path.exists(image_path):
                os.makedirs(image_path)
            timestamp = int(time.time())
            filename = f"{image_path}/from_{sender}_{timestamp}.bin"
            with open(filename, 'wb') as f:
                f.write(data)
            self.to_ui_queue.put(f"Binärdaten von {sender} empfangen und als '{filename}' gespeichert.")
        except Exception as e:
            self.to_ui_queue.put(f"Fehler beim Speichern des Bildes: {e}")

import toml  # Bibliothek für TOML-Dateien
from pathlib import Path  # Für Dateipfade

def load_config():
    try:
        # Findet den Pfad zur config.toml
        config_path = Path(__file__).parent.parent / "config.toml"
        
        # Öffnet die Datei im Lesemodus ('r' = read)
        with open(config_path, "r") as tomlDatei:
            # Lädt die TOML-Datei und gibt sie zurück
            return toml.load(tomlDatei)
    except Exception as e:
        print(f"Config error: {e}")
        return None  # Nichts zurückgeben
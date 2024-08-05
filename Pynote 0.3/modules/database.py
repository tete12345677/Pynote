import json
import os

user_dir = os.path.expanduser("~")
data_dir = os.path.join(user_dir, "FastNotes")
os.makedirs(data_dir, exist_ok=True)

DATA_FILE = os.path.join(data_dir, 'data.json')

def load_notes():
    if not os.path.exists(DATA_FILE):
        print("El archivo de datos no existe.")
        return []

    try:
        with open(DATA_FILE, 'r') as file:
            notes = json.load(file)
            print(f"Notas cargadas: {notes}")
            return notes
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error al cargar notas: {e}")
        return []

def save_notes(notes):
    try:
        with open(DATA_FILE, 'w') as file:
            json.dump(notes, file, indent=4)
            print(f"Notas guardadas: {notes}")  # Asegúrate de que esta línea se ejecute
    except IOError as e:
        print(f"Error al guardar notas: {e}")
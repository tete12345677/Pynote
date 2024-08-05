import json
import os

user_dir = os.path.expanduser("~")
data_dir = os.path.join(user_dir, "FastNotes")
os.makedirs(data_dir, exist_ok=True)

DATA_FILE = os.path.join(data_dir, 'data.json')

def load_notes():
    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, 'r') as file:
        return json.load(file)

def save_notes(notes):
    with open(DATA_FILE, 'w') as file:
        json.dump(notes, file, indent=4)
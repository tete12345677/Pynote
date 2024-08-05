import json
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'data.json')

def load_notes():
    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, 'r') as file:
        return json.load(file)

def save_notes(notes):
    with open(DATA_FILE, 'w') as file:
        json.dump(notes, file, indent=4)
import os
import tkinter as tk
from tkinter import messagebox, simpledialog, colorchooser
import yaml
from modules.database import load_notes, save_notes

def load_config():
    config_path = os.path.join("data", "config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"No se encuentra el archivo de configuración: {config_path}")
    
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

class NotesApp:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.apply_theme(self.config['window']['theme'])
        self.root.title(self.config['window']['title'])
        self.root.geometry(self.config['window']['size'])
        try:
            self.root.iconbitmap("icon.ico")
        except tk.TclError as e:
            print("Error al cargar el icono:", e)

        self.notes = load_notes()
        self.current_note_index = None

        # Frame para la lista de notas
        self.notes_list_frame = tk.Frame(root)
        self.notes_list_frame.pack(fill=tk.BOTH, expand=True)

        # Botón para agregar nota
        self.add_button = tk.Button(self.notes_list_frame, text="+", command=self.add_note)
        self.add_button.pack(fill=tk.X)

        # Listbox para mostrar las notas
        self.notes_listbox = tk.Listbox(self.notes_list_frame)
        self.notes_listbox.pack(fill=tk.BOTH, expand=True)
        self.notes_listbox.bind("<<ListboxSelect>>", self.open_note_editor)

        self.load_notes_list()

        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def apply_theme(self, theme):
        if theme == "dark":
            self.root.tk_setPalette(background="#2e2e2e", foreground="#ffffff", activeBackground="#3e3e3e", activeForeground="#ffffff")
        else:
            self.root.tk_setPalette(background="#ffffff", foreground="#000000", activeBackground="#e0e0e0", activeForeground="#000000")

    def load_notes_list(self):
        self.notes_listbox.delete(0, tk.END)
        for i, note in enumerate(self.notes):
            self.notes_listbox.insert(tk.END, f"{i+1}. {note['title']}")
            self.notes_listbox.itemconfig(i, {'bg': note.get('color', 'white')})

    def add_note(self):
        title = simpledialog.askstring("New Note", "Enter note title:")
        if title:
            self.notes.append({"title": title, "content": "", "color": "white"})
            self.load_notes_list()
            save_notes(self.notes)  # Guardar notas inmediatamente después de agregar

    def open_note_editor(self, event):
        selection = self.notes_listbox.curselection()
        if not selection:
            return

        self.current_note_index = selection[0]
        note = self.notes[self.current_note_index]

        editor_window = tk.Toplevel(self.root)
        editor_window.title(note["title"])
        editor_window.geometry(self.config['editor']['size'])
        self.apply_theme_to_editor(editor_window, self.config['window']['theme'])

        note_text = tk.Text(editor_window, wrap=tk.WORD, font=self.config['editor']['font'])
        note_text.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        note_text.insert(tk.END, note["content"])
        note_text.configure(bg=note.get("color", "white"))

        editor_window.grid_rowconfigure(0, weight=1)
        editor_window.grid_columnconfigure(0, weight=1)

        def save_note():
            self.notes[self.current_note_index]["content"] = note_text.get(1.0, tk.END).strip()
            self.notes[self.current_note_index]["color"] = note_text.cget("bg")
            save_notes(self.notes)
            self.load_notes_list()
            editor_window.destroy()
            messagebox.showinfo("Success", "Note saved successfully")

        def delete_note():
            if messagebox.askyesno("Delete Note", "Are you sure you want to delete this note?"):
                del self.notes[self.current_note_index]
                self.load_notes_list()
                save_notes(self.notes)
                editor_window.destroy()
                messagebox.showinfo("Success", "Note deleted successfully")

        def choose_color():
            color = colorchooser.askcolor()[1]
            if color:
                note_text.configure(bg=color)

        # Crear y empaquetar los botones usando grid
        save_button = tk.Button(editor_window, text="Save", command=save_note)
        save_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        delete_button = tk.Button(editor_window, text="Delete", command=delete_note)
        delete_button.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        color_button = tk.Button(editor_window, text="Choose Color", command=choose_color)
        color_button.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        editor_window.protocol("WM_DELETE_WINDOW", save_note)

    def apply_theme_to_editor(self, window, theme):
        if theme == "dark":
            window.configure(bg="#2e2e2e")
            for child in window.winfo_children():
                child.configure(bg="#2e2e2e", fg="#ffffff", activebackground="#3e3e3e", activeforeground="#ffffff")
        else:
            window.configure(bg="#ffffff")
            for child in window.winfo_children():
                child.configure(bg="#ffffff", fg="#000000", activebackground="#e0e0e0", activeforeground="#000000")

    def on_closing(self):
        save_notes(self.notes)
        self.root.destroy()

if __name__ == "__main__":
    try:
        config = load_config()
        root = tk.Tk()
        app = NotesApp(root, config)
        root.mainloop()
    except FileNotFoundError as e:
        print(e)
        messagebox.showerror("Error", f"Error: {e}")

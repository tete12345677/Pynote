import tkinter as tk
from tkinter import messagebox, simpledialog, colorchooser
from modules.database import load_notes, save_notes

class NotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fast Notes")
        self.root.geometry("800x600")
        try:
            self.root.iconbitmap("icon.ico")
        except tk.TclError as e:
            print("Error al cargar el icono:", e)

        self.notes = load_notes()
        self.current_note_index = None
        self.unsaved_changes = False

        # Create frames for layout
        self.left_frame = tk.Frame(root, width=200)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.right_frame = tk.Frame(root)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Add button
        self.add_button = tk.Button(self.left_frame, text="+", command=self.add_note)
        self.add_button.pack(fill=tk.X)

        # Notes listbox
        self.notes_listbox = tk.Listbox(self.left_frame)
        self.notes_listbox.pack(fill=tk.BOTH, expand=True)
        self.notes_listbox.bind("<<ListboxSelect>>", self.show_note)

        self.load_notes_list()

        # Note editor and save button
        self.note_text = tk.Text(self.right_frame, wrap=tk.WORD, font=("Helvetica", 12))
        self.note_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.note_text.bind("<<Modified>>", self.on_text_modified)

        self.save_button = tk.Button(self.right_frame, text="Save", command=self.save_note)
        self.save_button.pack(fill=tk.X, padx=5, pady=5)

        self.delete_button = tk.Button(self.right_frame, text="Delete", command=self.delete_note)
        self.delete_button.pack(fill=tk.X, padx=5, pady=5)

        self.color_button = tk.Button(self.right_frame, text="Choose Color", command=self.choose_color)
        self.color_button.pack(fill=tk.X, padx=5, pady=5)

        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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

    def show_note(self, event):
        if not self.notes_listbox.curselection():
            return

        if self.unsaved_changes:
            self.prompt_save_changes()

        self.current_note_index = self.notes_listbox.curselection()[0]
        note = self.notes[self.current_note_index]
        self.note_text.delete(1.0, tk.END)
        self.note_text.insert(tk.END, note["content"])
        self.note_text.configure(bg=note.get("color", "white"))
        self.unsaved_changes = False

    def save_note(self):
        if self.current_note_index is not None:
            self.notes[self.current_note_index]["content"] = self.note_text.get(1.0, tk.END).strip()
            self.notes[self.current_note_index]["color"] = self.note_text.cget("bg")
            save_notes(self.notes)
            self.unsaved_changes = False
            messagebox.showinfo("Success", "Note saved successfully")

    def delete_note(self):
        if self.current_note_index is not None:
            del self.notes[self.current_note_index]
            self.load_notes_list()
            self.note_text.delete(1.0, tk.END)
            self.current_note_index = None
            save_notes(self.notes)
            self.unsaved_changes = False
            messagebox.showinfo("Success", "Note deleted successfully")

    def choose_color(self):
        color = colorchooser.askcolor()[1]
        if color and self.current_note_index is not None:
            self.note_text.configure(bg=color)
            self.unsaved_changes = True

    def on_text_modified(self, event):
        self.unsaved_changes = True
        self.note_text.edit_modified(False)

    def prompt_save_changes(self):
        if messagebox.askyesno("Save Changes", "You have unsaved changes. Do you want to save them?"):
            self.save_note()
        else:
            self.unsaved_changes = False

    def on_closing(self):
        if self.unsaved_changes:
            self.prompt_save_changes()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = NotesApp(root)
    root.mainloop()
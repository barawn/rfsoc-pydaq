import tkinter as tk
from typing import Callable

class submitButton:
    def __init__(self,
                 parent: tk.Frame,
                 label_text,
                 placeholder_text,
                 submit_command: Callable,
                 index: int,
                 Auto=False):
        
        self.parent=parent

        self.frame = tk.Frame(self.parent)
        
        self.label =tk.Label(self.frame, text=label_text)
        self.label.grid(row = 0, column=0)
        
        vcmd = self.frame.register(self.validate)
        
        if Auto:
            self.Auto = Auto
            self.entry = tk.Entry(self.frame, width=12, validate="key", validatecommand=(vcmd, '%P'))
        else:
            self.entry = tk.Entry(self.frame, width=12)
        self.entry.insert(0, placeholder_text)
        self.entry.grid(row = 0, column=1)
        self.entry.bind("<Return>", lambda event: submit_command())
        
        self.submit_button = tk.Button(self.frame, text="Submit", command=submit_command)
        self.submit_button.grid(row = 0, column=2)

        self.frame.grid(row=0, column=index)

    def validate(self, new_text):
        if not new_text:
            self.input = None
            return True
        try:
            input = int(new_text)
            if self.Auto[0] <= input <= self.Auto[1]:
                self.input = input
                return True
            else:
                return False
        except ValueError:
            return False
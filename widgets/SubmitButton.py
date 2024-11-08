import tkinter as tk
from typing import Callable

class submitButton(tk.Frame):
    """
    So this is a template for a submit button GUI widget

    Label, Entry Field, Submit Button (tied to enter/return key)

    Input:
    Parent frame, most likely the submit frame
    label_text, what the submit value will do
    placeholder_text, should be the current/default value for the option we are changing
    submit_command, this should be a submit<Something>Value in the appropriate Daq Class, basically what actually does the work in changing stuff
    index, Only here for the grid system
    Auto, Should be an array of 2 elements which are bounds to limit the users input. Enitrely optional. Mainly put in to ensure the sample number can't be set to crash the whole thing
    """
    def __init__(self,
                 parent: tk.Frame,
                 label_text,
                 placeholder_text,
                 submit_command: Callable,
                 Auto=False):
        
        self.parent=parent

        super().__init__(self.parent)
        
        self.label =tk.Label(self, text=label_text)
        self.label.grid(row = 0, column=0)
        
        vcmd = self.register(self.validate)
        
        if Auto:
            self.Auto = Auto
            self.entry = tk.Entry(self, width=12, validate="key", validatecommand=(vcmd, '%P'))
        else:
            self.entry = tk.Entry(self, width=12)
        self.entry.insert(0, placeholder_text)
        self.entry.grid(row = 0, column=1)
        self.entry.bind("<Return>", lambda event: submit_command())
        
        self.submit_button = tk.Button(self, text="Submit", command=submit_command)
        self.submit_button.grid(row = 0, column=2)

    def get_value(self):
        return self.entry.get()

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
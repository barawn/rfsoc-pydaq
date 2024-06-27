import tkinter as tk
import threading
import time

class TaskManager:
    def __init__(self, root, input_text, job):
        self.root = root
        self.task_running = False
        self.task_thread = None
        self.input_text = input_text
        self.job = job
        
        self.toggle_button = tk.Button(root, text=f"Start {self.input_text}", command=self.toggle_task)
        self.toggle_button.grid(row=0, column=10)

    def toggle_task(self):
        if self.task_running:
            self.job(False)
            self.toggle_button.config(text=f"Start {self.input_text}")
            self.task_running = False
        else:
            self.job(True)
            self.toggle_button.config(text=f"Stop {self.input_text}")
            self.task_running = True
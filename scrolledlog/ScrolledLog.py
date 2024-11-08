import logging
import queue
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk, VERTICAL, HORIZONTAL, N, S, E, W, END

# Example from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
# (https://stackoverflow.com/questions/13318742/python-logging-to-tkinter-text-widget) is not thread safe!
# See https://stackoverflow.com/questions/43909849/tkinter-python-crashes-on-new-thread-trying-to-log-on-main-thread

# This was reorganized to make it a widget.
class ScrolledLog(ScrolledText):
    
    class QueueHandler(logging.Handler):
        def __init__(self, log_queue):
            super().__init__()
            self.log_queue = log_queue

        def emit(self, record):
            self.log_queue.put(record)

    def __init__(self, frame, logger, height=8, width = 10):
        self.frame = frame
        self.logger = logger
        super().__init__(frame, state='disabled', height=height, width=width)        
        self.grid(row=0, column=0, sticky=(N, S, W, E))
        self.configure(font='TkFixedFont')
        self.tag_config('INFO', foreground='black')
        self.tag_config('DEBUG', foreground='gray')
        self.tag_config('WARNING', foreground='orange')
        self.tag_config('ERROR', foreground='red')
        self.tag_config('CRITICAL', foreground='red', underline=1)

        self.log_queue = queue.Queue()
        self.queue_handler = self.QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        self.queue_handler.setFormatter(formatter)
        self.logger.addHandler(self.queue_handler)
        self.frame.after(100, self.poll_log_queue)

    def display(self, record):
        msg = self.queue_handler.format(record)
        self.configure(state='normal')
        self.insert(END, msg+'\n', record.levelname)
        self.configure(state='disabled')
        self.yview(END)

    def poll_log_queue(self):
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.frame.after(100, self.poll_log_queue)

#%%
import tkinter as tk
from tkinter import ttk
import asx

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill='both', expand=True)
        self.create_widgets()
        self.style = tk.ttk.Style()
        self.style.configure("BW.TLabel", foreground="blue", background="white")

    def create_widgets(self):
        self.disclaimer = tk.ttk.Label(text="ASX Chart Data may be delayed by up to 3 trading days."
                                        , style="BW.TLabel", anchor="center")
        self.disclaimer.pack(side="top", fill='x')
        self.intro = tk.Label(self, text = "Select an option:\n")
        self.intro.pack(side="top")
        self.update = tk.Button(self, text = "Update SQL Database",
                                command = self.update_database)
        self.update.pack(side="top",fill='x', padx=5, pady=5)

        self.msg = tk.Label(self, text = "ASX ticker:")
        self.msg.pack(side='left',padx=5,pady=5)
        self.ticker = tk.Entry(self)
        self.ticker.pack(side='left',fill='x',padx=5,pady=5)
        self.plot = tk.Button(self, text="Graph ticker",
                              command = self.plot_ticker)
        self.plot.pack(side='left',fill='x',padx=5,pady=5)

        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=self.master.destroy)
        self.quit.pack(side="bottom", padx=5, pady=5)

    def update_database(self):
        asx.update_csv_database()
    def plot_ticker(self):
        asx_code = self.ticker.get()
        asx.plotting_tool(asx_code)

root = tk.Tk()
root.title("Bob Equity Tracker Tool")
root.geometry('350x200')
app = Application(master=root)
app.mainloop()

#%%

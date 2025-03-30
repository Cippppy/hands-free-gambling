import tkinter as tk
from casino_state import CasinoState
from games.black_jack import BarbieBlackjackApp
from games.roulette import BarbieRouletteApp
from games.slot_machine import BarbieSlotsApp
from voice_listener import *

class BarbieCasinoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Barbie Casino 💖")
        self.geometry("1000x700")
        self.configure(bg="#FFB6C1")

        self.state = CasinoState()
        self.current_frame = None
        self.current_screen = "main"

        self.voice_listener = VoiceCommandListener(
            get_context=self.get_current_screen,
            context_handlers={
                "main": self.handle_main_voice,
                "blackjack": lambda cmd: self.current_frame.handle_voice_command(cmd),
                "roulette": lambda cmd: self.current_frame.handle_voice_command(cmd),
                "slots": lambda cmd: self.current_frame.handle_voice_command(cmd),
            }
        )
        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}")

        self.show_main_menu()

    def get_current_screen(self):
        return self.current_screen

    def show_main_menu(self):
        self.clear_current_frame()
        self.current_screen = "main"

        frame = tk.Frame(self, bg="#FFB6C1")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="👑 Welcome to Barbie Casino 👑", font=("Comic Sans MS", 30),
                 fg="#DDA0DD", bg="#FFB6C1").pack(pady=24)

        games = {
            "🎀 Blackjack": self.launch_blackjack,
            "🎡 Roulette": self.launch_roulette,
            "🎰 Slot Machine": self.launch_slots
        }

        for name, func in games.items():
            tk.Button(frame, text=name, font=("Helvetica", 20),
                      bg="#FF69B4", fg="white", width=15,
                      command=func).pack(pady=15)

        self.voice_button = tk.Button(frame, text="🎙️ Toggle Voice Mode", font=("Helvetica", 14),
                                      bg="#FFD700", fg="black", command=self.toggle_voice_mode)
        self.voice_button.pack(pady=10)

        self.current_frame = frame
        self.update_voice_button_text()

    def toggle_voice_mode(self):
        if self.voice_listener.running:
            self.voice_listener.stop()
            self.voice_button.config(text="🎙️ Start Voice Mode")
        else:
            self.voice_listener.start()
            self.voice_button.config(text="🛑 Stop Voice Mode")

    def handle_main_voice(self, text):
        if "blackjack" in text:
            self.launch_blackjack()
        elif "roulette" in text:
            self.launch_roulette()
        elif "slots" in text or "slot" in text:
            self.launch_slots()
        elif "quit" in text:
            self.quit()

    def launch_blackjack(self):
        self.clear_current_frame()
        self.current_screen = "blackjack"
        self.current_frame = BarbieBlackjackApp(self, self.state, go_back=self.show_main_menu)

    def launch_roulette(self):
        self.clear_current_frame()
        self.current_screen = "roulette"
        self.current_frame = BarbieRouletteApp(self, self.state, go_back=self.show_main_menu)

    def launch_slots(self):
        self.clear_current_frame()
        self.current_screen = "slots"
        self.current_frame = BarbieSlotsApp(self, self.state, go_back=self.show_main_menu)

    def clear_current_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()
    
    def update_voice_button_text(self):
        if self.voice_listener.running:
            self.voice_button.config(text="🛑 Stop Voice Mode")
        else:
            self.voice_button.config(text="🎙️ Start Voice Mode")

if __name__ == "__main__":
    app = BarbieCasinoApp()
    app.mainloop()

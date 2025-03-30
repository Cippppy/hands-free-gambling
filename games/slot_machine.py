# games/slot_machine.py
import tkinter as tk
import random
from voice_helper import transcribe_speech, parse_bet_command
from voice_listener import *
import re
import RPi.GPIO as GPIO    # Import Raspberry Pi GPIO library
from time import sleep     # Import the sleep function from the time module


class BarbieSlotsApp(tk.Frame):
    def __init__(self, master, state, go_back):
        super().__init__(master, bg="#FFB6C1")
        self.pack(fill="both", expand=True)
        self.state = state
        self.go_back = go_back

        self.symbols = ["💄", "👠", "💍", "🎀", "👜"]
        self.current_bet = 10

        self.init_ui()

    def init_ui(self):
        # Back to Casino button
        tk.Button(self, text="← Back to Casino", font=("Helvetica", 8),
                  bg="#FFD700", command=self.go_back).pack(pady=3)

        # Game title
        tk.Label(self, text="💗 Barbie Slots 💗", font=("Comic Sans MS", 28),
                 bg="#FFB6C1", fg="#DDA0DD").pack(pady=5)

        # Chip display
        self.chip_label = tk.Label(self, text=f"💎 Chips: {self.state.chips}",
                                   font=("Helvetica", 12), bg="#FFB6C1", fg="white")
        self.chip_label.pack()

        # Betting buttons
        bet_frame = tk.Frame(self, bg="#FFB6C1")
        bet_frame.pack()

        tk.Label(bet_frame, text="Bet:", font=("Helvetica", 12),
                 bg="#FFB6C1", fg="white").grid(row=0, column=0)
        self.bet_amount_label = tk.Label(bet_frame, text=f"{self.current_bet}",
                                         font=("Helvetica", 12), bg="#FFB6C1", fg="white")
        self.bet_amount_label.grid(row=0, column=1, padx=5)

        tk.Button(bet_frame, text="+5", command=lambda: self.adjust_bet(5),
                  font=("Helvetica", 8), bg="#DDA0DD").grid(row=0, column=2)
        tk.Button(bet_frame, text="-5", command=lambda: self.adjust_bet(-5),
                  font=("Helvetica", 8), bg="#FF69B4").grid(row=0, column=3)
        tk.Button(bet_frame, text="All In", command=lambda: self.set_bet(self.state.chips),
                  font=("Helvetica", 8), bg="#FF69B4").grid(row=0, column=4)
        tk.Button(bet_frame, text="Clear", command=lambda: self.set_bet(0),
                  font=("Helvetica", 8), bg="#FFD700").grid(row=0, column=5)
        
        self.voice_button = tk.Button(self, text="", font=("Helvetica", 9),
                              bg="#FFD700", fg="black", command=self.toggle_voice_mode)
        self.voice_button.pack(pady=5)
        self.update_voice_button_text()

        # Reel display
        self.reels_frame = tk.Frame(self, bg="#FFB6C1")
        self.reels_frame.pack(pady=12)

        self.reels = [tk.Label(self.reels_frame, text="❔", font=("Helvetica", 40), bg="#FFB6C1") for _ in range(3)]
        for r in self.reels:
            r.pack(side=tk.LEFT, padx=12)

        # Result text
        self.result_label = tk.Label(self, text="", font=("Helvetica", 12),
                                     bg="#FFB6C1", fg="white")
        self.result_label.pack(pady=12)

        # Spin button
        self.spin_button = tk.Button(self, text="🎰 Spin!", font=("Helvetica", 15),
                             bg="#FF69B4", fg="white", command=self.spin)
        self.spin_button.pack(pady=10)
        self.voice_toggle = tk.Button(self, text="", font=("Helvetica", 8),
                              bg="#DDA0DD", fg="black", command=self.toggle_voice_feedback)
        self.voice_toggle.pack(pady=5)
        self.update_voice_feedback_label()

    def adjust_bet(self, amount):
        new_bet = self.current_bet + amount
        if 0 <= new_bet <= self.state.chips:
            self.current_bet = new_bet
            self.update_bet_display()

    def set_bet(self, amount):
        if 0 <= amount <= self.state.chips:
            self.current_bet = amount
            self.update_bet_display()

    def update_bet_display(self):
        self.bet_amount_label.config(text=f"{self.current_bet}")

    def spin(self):
        if self.state.chips < self.current_bet or self.current_bet == 0:
            self.result_label.config(text="💔 Not enough chips to spin.")
            return

        self.state.chips -= self.current_bet
        self.update_chip_display()

        self.result_label.config(text="Spinning...")
        self.spin_button.config(state=tk.DISABLED)

        # Final outcome to reveal after animation
        self.final_symbols = [random.choice(self.symbols) for _ in range(3)]
        self.spin_cycles = 15
        self.current_cycle = 0

        self.animate_spin()

    def update_chip_display(self):
        self.chip_label.config(text=f"💎 Chips: {self.state.chips}")
    
    def animate_spin(self):
        for i in range(3):
            self.reels[i].config(text=random.choice(self.symbols))

        self.current_cycle += 1
        if self.current_cycle < self.spin_cycles:
            self.after(100, self.animate_spin)
        else:
            for i in range(3):
                self.reels[i].config(text=self.final_symbols[i])
            self.evaluate_spin()
            self.spin_button.config(state=tk.NORMAL)

    def evaluate_spin(self):
        outcome = self.final_symbols

        if outcome[0] == outcome[1] == outcome[2]:
            self.state.chips += self.current_bet + 100
            self.result_label.config(text="👑 JACKPOT! You win 100 chips!")
        elif outcome.count(outcome[0]) == 2 or outcome.count(outcome[1]) == 2:
            self.state.chips += self.current_bet + 30
            self.result_label.config(text="🎉 Two of a kind! You win 30 chips!")
        else:
            self.result_label.config(text="😿 No match. Better luck next time!")

        self.update_chip_display()
        symbols = " ".join(self.final_symbols)
        result_summary = f"The reels landed on {symbols}. "

        if "JACKPOT" in self.result_label.cget("text"):
            result_summary += "Jackpot! You won 100 chips!"
        elif "Two of a kind" in self.result_label.cget("text"):
            result_summary += "Two matching symbols! You won 30 chips!"
        else:
            result_summary += "No matches. Better luck next time."

        from voice_helper import generate_voice_feedback
        self.after(100, lambda: generate_voice_feedback(result_summary, state=self.state))
        if "won" in result_summary:
            lights()
        
    def handle_voice_bet(self):
        text = transcribe_speech()
        if not text:
            self.result_label.config(text="😶 Didn't catch that. Try again.")
            return

        parsed = parse_bet_command(text)
        if not parsed:
            self.result_label.config(text="🤷 Couldn't understand the bet.")
            return

        amount = parsed.get("amount")
        if not amount:
            self.result_label.config(text="🤷 Couldn't detect a bet amount.")
            return

        if amount > self.state.chips:
            self.result_label.config(text="💸 Not enough chips!")
            return

        self.current_bet = amount
        self.update_bet_display()
        self.result_label.config(text=f"🎙️ Voice set bet to {amount} chips.")
        
    def handle_voice_command(self, text):
        if "back" in text:
            self.go_back()
        elif "spin" in text:
            self.spin()
        elif "all in" in text:
            self.set_bet(self.state.chips)
            self.result_label.config(text=f"🎙️ All in! Bet {self.state.chips} chips.")
        elif "bet" in text:
            match = re.search(r'bet\s+(\d+)', text)
            if match:
                amount = int(match.group(1))
                if amount <= self.state.chips:
                    self.set_bet(amount)
                    self.result_label.config(text=f"🎙️ Bet set to {amount} chips.")
                else:
                    self.result_label.config(text="💸 Not enough chips for that bet.")
            else:
                self.result_label.config(text="🤷 Couldn't understand the amount.")
        else:
            self.result_label.config(text="❓ Command not recognized.")
            
    def toggle_voice_mode(self):
        if self.master.voice_listener.running:
            self.master.voice_listener.stop()
        else:
            self.master.voice_listener.start()
        self.update_voice_button_text()

    def update_voice_button_text(self):
        if self.master.voice_listener.running:
            self.voice_button.config(text="🛑 Stop Voice Mode")
        else:
            self.voice_button.config(text="🎙️ Start Voice Mode")

    def toggle_voice_feedback(self):
        self.state.voice_feedback_enabled = not self.state.voice_feedback_enabled
        self.update_voice_feedback_label()

    def update_voice_feedback_label(self):
        status = "🗣️ Voice Feedback: ON" if self.state.voice_feedback_enabled else "🔇 Voice Feedback: OFF"
        self.voice_toggle.config(text=status)
        
def lights():
    GPIO.setwarnings(False)    # Ignore warning for now
    GPIO.setmode(GPIO.BOARD)   # Use physical pin numbering
    GPIO.setup(8, GPIO.OUT, initial=GPIO.LOW)   # Set pin 8 to be an output pin and set initial value to low (off)

    GPIO.output(8, GPIO.HIGH) # Turn on
    sleep(1)                  # Sleep for 1 second
    GPIO.output(8, GPIO.LOW)  # Turn off
    sleep(1)                  # Sleep for 1 second

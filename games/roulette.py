import tkinter as tk
import random
from voice_helper import transcribe_speech, parse_bet_command
import re
from voice_listener import *
import RPi.GPIO as GPIO    # Import Raspberry Pi GPIO library
from time import sleep     # Import the sleep function from the time module


class BarbieRouletteApp(tk.Frame):
    def __init__(self, master, state, go_back):
        super().__init__(master, bg="#FFB6C1")
        self.pack(fill="both", expand=True)
        self.state = state
        self.go_back = go_back

        self.current_bet = 10
        self.choice = None

        self.init_ui()

    def init_ui(self):
        tk.Button(self, text="← Back to Casino", font=("Helvetica", 8),
                  bg="#FFD700", command=self.go_back).pack(pady=3)

        tk.Label(self, text="🎀 Barbie Roulette 🎀", font=("Comic Sans MS", 24),
                 bg="#FFB6C1", fg="#DDA0DD").pack(pady=3)

        self.chip_display = tk.Label(self, text=f"💎 Chips: {self.state.chips}",
                                     font=("Helvetica", 10), bg="#FFB6C1", fg="white")
        self.chip_display.pack()

        self.bet_amount_label = tk.Label(self, text=f"Bet: {self.current_bet} 💰",
                                         font=("Helvetica", 10), bg="#FFB6C1", fg="white")
        self.bet_amount_label.pack(pady=3)

        bet_buttons = tk.Frame(self, bg="#FFB6C1")
        bet_buttons.pack(pady=3)

        for label, val in [("+5", 5), ("-5", -5), ("10", 10), ("100", 100), ("All In", self.state.chips), ("Clear", 0)]:
            tk.Button(bet_buttons, text=label, font=("Helvetica", 8),
                      command=lambda v=val: self.adjust_bet(v), bg="#FF69B4", fg="white").pack(side=tk.LEFT, padx=5)

        self.bet_grid = tk.Frame(self, bg="#FFB6C1")
        self.bet_grid.pack(pady=3)

        tk.Button(self.bet_grid, text="0", width=4, bg="green", fg="white",
                  font=("Helvetica", 10), command=lambda: self.select_bet("0")).grid(row=0, column=0, columnspan=3)

        row = 1
        col = 0
        for number in range(1, 37):
            color = "red" if number % 2 else "black"
            fg = "white"
            btn = tk.Button(self.bet_grid, text=str(number), width=4,
                            bg=color, fg=fg, font=("Helvetica", 10),
                            command=lambda n=number: self.select_bet(str(n)))
            btn.grid(row=row, column=col)
            col += 1
            if col == 12:
                col = 0
                row += 1

        tk.Button(self.bet_grid, text="Red", width=6, bg="red", fg="white",
                  font=("Helvetica", 10), command=lambda: self.select_bet("red")).grid(row=row+1, column=0, columnspan=6)
        tk.Button(self.bet_grid, text="Black", width=6, bg="black", fg="white",
                  font=("Helvetica", 10), command=lambda: self.select_bet("black")).grid(row=row+1, column=6, columnspan=6)

        self.bet_display = tk.Label(self, text="🎯 Select a number or color to bet on", font=("Helvetica", 10),
                                    bg="#FFB6C1", fg="white")
        self.bet_display.pack(pady=3)

        self.spin_display = tk.Label(self, text="", font=("Helvetica", 20),
                                     bg="#FFB6C1", fg="white")
        self.spin_display.pack(pady=3)

        self.result_label = tk.Label(self, text="", font=("Helvetica", 10),
                                     bg="#FFB6C1", fg="white")
        self.result_label.pack(pady=3)

        self.spin_button = tk.Button(self, text="🎲 Spin!", font=("Helvetica", 10),
                                     bg="#FF69B4", fg="white", command=self.spin)
        self.spin_button.pack(pady=3)
        
        self.voice_button = tk.Button(self, text="", font=("Helvetica", 10),
                              bg="#FFD700", fg="black", command=self.toggle_voice_mode)
        self.voice_button.pack(pady=3)
        self.update_voice_button_text()
        self.voice_toggle = tk.Button(self, text="", font=("Helvetica", 10),
                              bg="#DDA0DD", fg="black", command=self.toggle_voice_feedback)
        self.voice_toggle.pack(pady=3)
        self.update_voice_feedback_label()

    def adjust_bet(self, amount):
        if amount == 0:
            self.current_bet = 0
        elif amount == self.state.chips:
            self.current_bet = self.state.chips
        else:
            new_bet = self.current_bet + amount
            if 0 <= new_bet <= self.state.chips:
                self.current_bet = new_bet
        self.bet_amount_label.config(text=f"Bet: {self.current_bet} 💰")

    def select_bet(self, bet_value):
        self.choice = bet_value
        self.bet_display.config(text=f"🎯 You selected: {bet_value.upper()}")

    def spin(self):
        if not self.choice:
            self.result_label.config(text="❌ Please select a number or color.")
            return

        if self.state.chips < self.current_bet or self.current_bet <= 0:
            self.result_label.config(text="💔 Not enough chips to spin.")
            return

        self.state.chips -= self.current_bet
        self.update_chip_display()

        self.result_label.config(text="Spinning...")
        self.spin_button.config(state=tk.DISABLED)

        self.final_number = random.randint(0, 36)
        self.spin_count = 0
        self.max_spin_count = 30

        self.animate_spin()

    def animate_spin(self):
        num = random.randint(0, 36)
        color = 'green' if num == 0 else ('red' if num % 2 else 'black')
        self.spin_display.config(text=f"{num}", fg=color)

        delay = int(30 + (self.spin_count ** 1.5))
        self.spin_count += 1

        if self.spin_count < self.max_spin_count:
            self.after(delay, self.animate_spin)
        else:
            self.show_final_spin()

    def show_final_spin(self):
        final = self.final_number
        color = 'green' if final == 0 else ('red' if final % 2 else 'black')
        self.spin_display.config(text=f"{final}", fg=color)

        win = False
        payout = 0

        if self.choice == str(final):
            win = True
            payout = self.current_bet * 36
        elif self.choice == color:
            win = True
            payout = self.current_bet * 2

        if win:
            self.state.chips += payout
            self.result_label.config(text=f"🎉 Ball landed on {final} {color.upper()}! You win {payout} chips!")
        else:
            self.result_label.config(text=f"😿 Ball landed on {final} {color.upper()}. You lose.")

        self.update_chip_display()
        self.spin_button.config(state=tk.NORMAL)
        result_summary = f"The ball landed on {final} {color.upper()}. "
        if win:
            result_summary += f"You won {payout} chips!"
        else:
            result_summary += "You lost this round."

        from voice_helper import generate_voice_feedback
        self.after(100, lambda: generate_voice_feedback(result_summary, state=self.state))
        if win:
            lights()

    def update_chip_display(self):
        self.chip_display.config(text=f"💎 Chips: {self.state.chips}")

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
        target = parsed.get("target")

        if not amount or not target:
            self.result_label.config(text="🤷 Missing amount or target.")
            return

        if amount > self.state.chips:
            self.result_label.config(text="💸 Not enough chips!")
            return

        self.current_bet = amount
        self.bet_amount_label.config(text=f"Bet: {self.current_bet} 💰")
        self.select_bet(str(target))
        
    def handle_voice_command(self, text):
        if "back" in text:
            self.go_back()
        elif "spin" in text:
            self.spin()
        elif "bet" in text:
            match = re.search(r'bet\s+(\d+)(?:\s+on\s+(\w+))?', text)
            if match:
                amount = int(match.group(1))
                target = match.group(2)
                if amount <= self.state.chips:
                    self.current_bet = amount
                    self.update_bet_display()
                    if target:
                        self.select_bet(target.lower())
                        self.result_label.config(text=f"🎙️ Bet {amount} on {target}")
                    else:
                        self.result_label.config(text=f"🎙️ Bet {amount} chips set. Now pick a number or color.")
                else:
                    self.result_label.config(text="💸 Not enough chips.")
            else:
                self.result_label.config(text="🤷 Couldn't understand your bet.")
        else:
            self.result_label.config(text="❓ Command not recognized.")

    def update_bet_display(self):
        self.bet_amount_label.config(text=f"Bet: {self.current_bet} 💰")
        
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
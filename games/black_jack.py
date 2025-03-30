# games/black_jack.py
import tkinter as tk
from PIL import Image, ImageTk
import random
import os
from voice_helper import transcribe_speech, parse_bet_command
import re
from voice_listener import *
import RPi.GPIO as GPIO    # Import Raspberry Pi GPIO library
from time import sleep     # Import the sleep function from the time module

CARD_WIDTH, CARD_HEIGHT = 100//2, 145//2
CARD_FOLDER = "assets/card_images"

class BlackjackGame:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.deck = [f"{rank}_of_{suit}" for rank in 
                     ['2','3','4','5','6','7','8','9','10','jack','queen','king','ace']
                     for suit in ['hearts','diamonds','clubs','spades']]
        random.shuffle(self.deck)
        self.player = [self.deck.pop(), self.deck.pop()]
        self.dealer = [self.deck.pop(), self.deck.pop()]
        self.game_over = False

    def hand_value(self, hand):
        value = 0
        aces = 0
        for card in hand:
            rank = card.split("_")[0]
            if rank in ['jack', 'queen', 'king']:
                value += 10
            elif rank == 'ace':
                aces += 1
                value += 11
            else:
                value += int(rank)
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    def hit(self):
        if not self.game_over:
            self.player.append(self.deck.pop())
            if self.hand_value(self.player) > 21:
                self.game_over = True

    def stand(self):
        while self.hand_value(self.dealer) < 17:
            self.dealer.append(self.deck.pop())
        self.game_over = True

    def result(self):
        player_score = self.hand_value(self.player)
        dealer_score = self.hand_value(self.dealer)
        if player_score > 21:
            return "💥 You busted! Dealer wins!"
        elif dealer_score > 21:
            return "🎉 Dealer busted! You win!"
        elif player_score > dealer_score:
            return "👑 You win, Barbie!"
        elif player_score < dealer_score:
            return "😿 Dealer wins!"
        else:
            return "🤝 Push! It's a tie!"

class BarbieBlackjackApp(tk.Frame):
    def __init__(self, master, state, go_back):
        super().__init__(master, bg="#FFB6C1")
        self.pack(fill="both", expand=True)
        self.state = state
        self.go_back = go_back
        self.init_ui()

    def init_ui(self):
        self.game = BlackjackGame()
        self.card_images = {}
        self.current_bet = 0
        self.can_double_down = True

        tk.Button(self, text="← Back to Casino", font=("Helvetica", 8),
                  bg="#FFD700", command=self.go_back).pack(pady=3)

        tk.Label(self, text="🎀 Barbie Blackjack 🎀", font=("Comic Sans MS", 24), bg="#FFB6C1", fg="#DDA0DD").pack(pady=5)

        self.chip_label = tk.Label(self, text=f"💎 Chips: {self.state.chips}", font=("Helvetica", 12), bg="#FFB6C1", fg="white")
        self.chip_label.pack()

        self.bet_frame = tk.Frame(self, bg="#FFB6C1")
        self.bet_frame.pack(pady=5)
        
        self.voice_button = tk.Button(self, text="", font=("Helvetica", 10),
                              bg="#FFD700", fg="black", command=self.toggle_voice_mode)
        self.voice_button.pack(pady=5)
        self.update_voice_button_text()

        tk.Label(self.bet_frame, text="Bet:", font=("Helvetica", 10), bg="#FFB6C1", fg="white").grid(row=0, column=0)
        self.bet_amount_label = tk.Label(self.bet_frame, text=f"{self.current_bet}", font=("Helvetica", 10),
                                         bg="#FFB6C1", fg="white")
        self.bet_amount_label.grid(row=0, column=1, padx=5)

        tk.Button(self.bet_frame, text="+5", command=lambda: self.adjust_bet(5),
                  font=("Helvetica", 8), bg="#DDA0DD").grid(row=0, column=2, padx=2)
        tk.Button(self.bet_frame, text="-5", command=lambda: self.adjust_bet(-5),
                  font=("Helvetica", 8), bg="#FF69B4").grid(row=0, column=3, padx=2)
        tk.Button(self.bet_frame, text="10", command=lambda: self.set_bet(10),
                  font=("Helvetica", 8), bg="#FF69B4").grid(row=0, column=4, padx=2)
        tk.Button(self.bet_frame, text="100", command=lambda: self.set_bet(100),
                  font=("Helvetica", 8), bg="#FF69B4").grid(row=0, column=5, padx=2)
        tk.Button(self.bet_frame, text="All In", command=lambda: self.set_bet(self.state.chips),
                  font=("Helvetica", 8), bg="#FF69B4").grid(row=0, column=6, padx=2)
        tk.Button(self.bet_frame, text="Clear", command=lambda: self.set_bet(0),
                  font=("Helvetica", 8), bg="#FFD700").grid(row=0, column=7, padx=2)

        self.place_bet_btn = tk.Button(self.bet_frame, text="Deal", font=("Helvetica", 8),
                                       command=self.place_bet)
        self.place_bet_btn.grid(row=0, column=8, padx=5)
        
        self.double_btn = tk.Button(self.bet_frame, text="Double Down", font=("Helvetica", 8),
                            command=self.double_down, state=tk.DISABLED)
        self.double_btn.grid(row=0, column=9, padx=5)

        self.dealer_frame = tk.Frame(self, bg="#FFB6C1")
        self.dealer_frame.pack(pady=5)
        self.dealer_cards = []

        self.player_frame = tk.Frame(self, bg="#FFB6C1")
        self.player_frame.pack(pady=5)
        self.player_cards_frame = tk.Frame(self.player_frame, bg="#FFB6C1")
        self.player_cards_frame.pack(side=tk.LEFT)

        self.player_cards = []
        self.player_count_label = tk.Label(self.player_frame, text="", font=("Helvetica", 12), bg="#FFB6C1", fg="white")
        self.player_count_label.pack(side=tk.RIGHT, padx=5)
        
        self.status_label = tk.Label(self, text="", font=("Helvetica", 10, "bold"), bg="#FFB6C1", fg="#FF69B4")
        self.status_label.pack(pady=5)

        self.button_frame = tk.Frame(self, bg="#FFB6C1")
        self.button_frame.pack(pady=5)

        self.hit_btn = tk.Button(self.button_frame, text="💅 Hit", font=("Helvetica", 10), bg="#FF69B4", fg="white", command=self.hit, state=tk.DISABLED)
        self.hit_btn.grid(row=0, column=0, padx=10)

        self.stand_btn = tk.Button(self.button_frame, text="👠 Stand", font=("Helvetica", 10), bg="#FF69B4", fg="white", command=self.stand, state=tk.DISABLED)
        self.stand_btn.grid(row=0, column=1, padx=10)

        self.reset_btn = tk.Button(self.button_frame, text="🌟 New Game", font=("Helvetica", 10), bg="#FFD700", fg="white", command=self.reset, state=tk.DISABLED)
        self.reset_btn.grid(row=0, column=2, padx=10)
        
        self.root = self.master  # reference to root window
        self.root.update_idletasks()
        self.root.minsize(900, 650)  # Ensure minimum size fits everything
        self.update_voice_button_text()
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

    def load_card_image(self, card_name):
        file_name = "back.png" if card_name == "back" else f"{card_name}.png"
        if file_name not in self.card_images:
            path = os.path.join(CARD_FOLDER, file_name)
            try:
                image = Image.open(path).resize((CARD_WIDTH, CARD_HEIGHT))
                self.card_images[file_name] = ImageTk.PhotoImage(image)
            except FileNotFoundError:
                return None
        return self.card_images[file_name]

    def clear_cards(self):
        for widget in self.player_cards + self.dealer_cards:
            widget.destroy()
        self.player_cards.clear()
        self.dealer_cards.clear()
        self.player_count_label.pack_forget()

    def display_hand(self, hand, frame, card_widgets, hide_last=False):
        for i, card in enumerate(hand):
            img = self.load_card_image("back" if hide_last and i == 1 else card)
            if img:
                if frame == self.player_frame:
                    label = tk.Label(self.player_cards_frame, image=img, bg="#FFB6C1")
                else:
                    label = tk.Label(frame, image=img, bg="#FFB6C1")
                label.pack(side=tk.LEFT, padx=5)
                card_widgets.append(label)
        if frame == self.player_frame:
            card_total = self.game.hand_value(hand)
            self.player_count_label.config(text=f"🧮 {card_total}")
            self.player_count_label.pack_forget()  # ensure it's not duplicated
            self.player_count_label.pack(side=tk.RIGHT, padx=10)

    def update_display(self):
        self.clear_cards()
        self.display_hand(self.game.dealer, self.dealer_frame, self.dealer_cards, hide_last=not self.game.game_over)
        self.display_hand(self.game.player, self.player_frame, self.player_cards)
        self.status_label.config(text=self.game.result() if self.game.game_over else "")

    def place_bet(self):
        bet = self.current_bet
        if bet <= 0 or bet > self.state.chips:
            self.status_label.config(text="❌ Invalid bet amount.")
            return

        self.state.chips -= bet
        self.can_double_down = True
        self.update_chip_display()

        self.place_bet_btn.config(state=tk.DISABLED)
        self.double_btn.config(state=tk.NORMAL)
        self.hit_btn.config(state=tk.NORMAL)
        self.stand_btn.config(state=tk.NORMAL)

        self.game.reset_game()
        self.update_display()

        player_val = self.game.hand_value(self.game.player)
        dealer_val = self.game.hand_value(self.game.dealer)
        if player_val == 21:
            self.game.game_over = True
            result = "🎉 Blackjack! You win 1.5x!"
            if dealer_val == 21:
                result = "🤝 Push! Both have Blackjack!"
                self.state.chips += bet
            else:
                self.state.chips += int(bet * 2.5)
            self.update_chip_display()
            self.update_display()
            self.status_label.config(text=result)
            self.reset_btn.config(state=tk.NORMAL)
            self.hit_btn.config(state=tk.DISABLED)
            self.stand_btn.config(state=tk.DISABLED)
            self.double_btn.config(state=tk.DISABLED)

    def hit(self):
        self.can_double_down = False
        self.double_btn.config(state=tk.DISABLED)
        self.game.hit()
        self.update_display()
        if self.game.game_over:
            self.finalize_round()

    def stand(self):
        self.can_double_down = False
        self.double_btn.config(state=tk.DISABLED)
        self.game.stand()
        self.finalize_round()

    def finalize_round(self):
        result = self.game.result()
        if "you win" in result.lower():
            self.state.chips += self.current_bet * 2
        elif "tie" in result.lower() or "push" in result.lower():
            self.state.chips += self.current_bet
        self.update_chip_display()
        player_score = self.game.hand_value(self.game.player)
        dealer_score = self.game.hand_value(self.game.dealer)
        result_text = f"Your final hand was {player_score}. Dealer had {dealer_score}. "

        if "busted" in result.lower():
            result_text += "You busted!" if player_score > 21 else "The dealer busted!"
        elif "win" in result.lower():
            result_text += "You won the hand!"
        elif "tie" in result.lower():
            result_text += "It's a push."
        else:
            result_text += "Dealer wins this round."

        self.update_display()
        self.status_label.config(text=result)
        self.reset_btn.config(state=tk.NORMAL)
        self.hit_btn.config(state=tk.DISABLED)
        self.stand_btn.config(state=tk.DISABLED)
        self.double_btn.config(state=tk.DISABLED)
        from voice_helper import generate_voice_feedback
        self.after(100, lambda: generate_voice_feedback(result_text, state=self.state))
        if "you win" in result.lower():
            lights()

    def update_chip_display(self):
        self.chip_label.config(text=f"💎 Chips: {self.state.chips}")

    def reset(self):
        self.current_bet = 0
        self.status_label.config(text="")
        self.place_bet_btn.config(state=tk.NORMAL)
        self.double_btn.config(state=tk.DISABLED)
        self.reset_btn.config(state=tk.DISABLED)
        self.clear_cards()
        self.update_chip_display()
        self.update_bet_display()
        
    def double_down(self):
        if not self.can_double_down or self.state.chips < self.current_bet:
            self.status_label.config(text="❌ Cannot double down.")
            return

        self.state.chips -= self.current_bet
        self.current_bet *= 2
        self.can_double_down = False
        self.update_chip_display()

        self.game.hit()
        self.game.stand()
        self.finalize_round()
        
    def handle_voice_bet(self):
        text = transcribe_speech()
        if not text:
            self.status_label.config(text="😶 Didn't catch that. Try again.")
            return

        parsed = parse_bet_command(text)
        if not parsed:
            self.status_label.config(text="🤷 Couldn't understand the bet.")
            return

        amount = parsed.get("amount")
        if not amount:
            self.status_label.config(text="🤷 Couldn't detect a bet amount.")
            return

        if amount > self.state.chips:
            self.status_label.config(text="💸 Not enough chips!")
            return

        self.current_bet = amount
        self.update_bet_display()
        self.status_label.config(text=f"🎙️ Voice set bet to {amount} chips.")
        
    def handle_voice_command(self, text):
        if "hit" in text:
            self.hit()
        if "another" in text:
            self.hit()
        elif "stand" in text:
            self.stand()
        elif "double" in text:
            self.double_down()
        elif "new" in text:
            self.reset()
        elif "new game" in text:
            self.reset()
        elif "deal" in text:
            self.place_bet()
        elif "play" in text:
            self.place_bet()
        elif "back" in text:
            self.go_back()
        elif "bet" in text:
            match = re.search(r'bet\s+(\d+)', text)
            if match:
                amount = int(match.group(1))
                if amount <= self.state.chips:
                    self.set_bet(amount)
                    self.status_label.config(text=f"🎙️ Bet set to {amount} chips.")
                else:
                    self.status_label.config(text="💸 Not enough chips for that bet.")
            else:
                self.status_label.config(text="🤷 Couldn't understand the amount.")
        else:
            self.status_label.config(text="❓ Command not recognized.")
            
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

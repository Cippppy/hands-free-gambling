import speech_recognition as sr
import google.generativeai as genai
import os
import re
import json
import pyttsx3
import tkinter as tk
import time

# You can also set this via environment variable
GEMINI_API_KEY = ""
genai.configure(api_key=GEMINI_API_KEY)

def transcribe_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening for command...")
        audio = r.listen(source, phrase_time_limit=5)

    try:
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"API error: {e}")
        return None

def parse_bet_command(prompt_text):
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(f"""
You are interpreting voice commands for a roulette game.

From the following user input:
"{prompt_text}"

Extract two values:
1. "amount": an integer bet amount (e.g. 25)
2. "target": either a number 0-36 or the string "red" or "black"

Respond with *only* a JSON object like:
{{"amount": 25, "target": "red"}}
""")

    raw_text = response.text.strip()
    print("🤖 Gemini response:\n", raw_text)

    try:
        # Try direct JSON parse first
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from any extra text
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

    return None

engine = pyttsx3.init()

# Make sure your Gemini model is set correctly
model = genai.GenerativeModel('gemini-2.0-flash')

def speak(text):
    try:
        print(f"🗣️ {text}")
        # Dummy phrase to trigger audio driver start
        engine.say("...")              # short dummy speech
        engine.runAndWait()            # flush it
        time.sleep(0.05)               # allow buffer to clear

        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("⚠️ pyttsx3 error:", e)

def generate_voice_feedback(prompt, state=None):
    if state and not state.voice_feedback_enabled:
        return

    concise_prompt = f"""
Respond with a short and clear summary of the outcome. Avoid storytelling or explanation. Only say the result.
Use one sentence if possible.

Context: {prompt}
"""
    try:
        response = model.generate_content(concise_prompt)
        time.sleep(0.2)  # <-- wait for screen updates to finish
        text = response.text.strip()
        speak(text)
    except Exception as e:
        print("⚠️ Error generating voice feedback:", e)

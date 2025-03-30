import threading
import time
from voice_helper import transcribe_speech

class VoiceCommandListener:
    def __init__(self, get_context, context_handlers):
        '''
        get_context: function that returns the current screen/context (e.g., "main", "blackjack", etc.)
        context_handlers: dict mapping context name to a handler function that takes voice command text
        '''
        self.get_context = get_context
        self.context_handlers = context_handlers
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
            self.thread = None

    def _run(self):
        print("🎙️ Voice Mode: Listening for commands...")
        while self.running:
            text = transcribe_speech()
            if text:
                print(f"🗣️ Heard: {text}")
                context = self.get_context()
                handler = self.context_handlers.get(context)
                if handler:
                    handler(text.lower())
            time.sleep(1)

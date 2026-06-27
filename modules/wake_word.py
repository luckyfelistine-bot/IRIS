"""IRIS v9 Wake Word Detection — Server + Browser Hybrid
Server-side: Porcupine/Vosk for local deployments
Browser-side: Web Speech API for Vercel/cloud deployments
"""
import os
import threading
import queue
import json
import logging
from typing import Callable, Optional
from config import config

logger = logging.getLogger(__name__)

class WakeWordDetector:
    """
    Hybrid wake word detection:
    - Server: Porcupine (fast) → Vosk (open-source) → Energy fallback
    - Browser: Web Speech API continuous listening (for Vercel)
    """

    def __init__(self):
        self.wake_word = config.WAKE_WORD.lower()
        self.sensitivity = config.WAKE_WORD_SENSITIVITY
        self.is_listening = False
        self.callback: Optional[Callable] = None
        self.detector = None
        self._init_detector()

    def _init_detector(self):
        """Initialize the best available wake word engine."""
        # Try Porcupine first
        try:
            import pvporcupine
            import pyaudio
            self.detector = "porcupine"
            self.porcupine = pvporcupine.create(
                access_key=os.getenv("PORCUPINE_ACCESS_KEY", ""),
                keyword_paths=[],
                keywords=["hey iris"],
                sensitivities=[self.sensitivity]
            )
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            logger.info("✅ Porcupine wake word engine initialized")
            return
        except Exception as e:
            logger.info(f"Porcupine not available: {e}")

        # Try Vosk
        try:
            from vosk import Model, KaldiRecognizer
            import pyaudio
            self.detector = "vosk"
            model_path = os.path.join(config.DATA_DIR, "vosk-model-small-en-us-0.15")
            if not os.path.exists(model_path):
                logger.warning("Vosk model not found. Download from https://alphacephei.com/vosk/models")
                raise FileNotFoundError("Vosk model missing")
            self.vosk_model = Model(model_path)
            self.vosk_recognizer = KaldiRecognizer(self.vosk_model, 16000)
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=16000, channels=1, format=pyaudio.paInt16,
                input=True, frames_per_buffer=4096
            )
            logger.info("✅ Vosk wake word engine initialized")
            return
        except Exception as e:
            logger.info(f"Vosk not available: {e}")

        # Browser fallback for Vercel
        self.detector = "browser"
        logger.info("🌐 Using browser-based wake word (Web Speech API)")

    def set_callback(self, callback: Callable):
        """Set callback function when wake word is detected."""
        self.callback = callback

    def start_listening(self):
        """Start listening for wake word in background thread."""
        if self.is_listening:
            return
        self.is_listening = True

        if self.detector in ["porcupine", "vosk"]:
            self.thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.thread.start()
            logger.info(f"🔊 Server wake word listener started. Say '{config.WAKE_WORD}' to activate IRIS.")
        else:
            logger.info("🌐 Browser wake word mode — listening handled client-side at /voice")

    def stop_listening(self):
        """Stop listening."""
        self.is_listening = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1)
        if self.detector == "porcupine":
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.porcupine.delete()
                self.pa.terminate()
            except: pass
        elif self.detector == "vosk":
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.pa.terminate()
            except: pass

    def _listen_loop(self):
        """Main server-side listening loop."""
        import numpy as np
        while self.is_listening:
            try:
                if self.detector == "porcupine":
                    pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                    pcm = np.frombuffer(pcm, dtype=np.int16)
                    keyword_index = self.porcupine.process(pcm)
                    if keyword_index >= 0:
                        self._on_wake_word_detected()

                elif self.detector == "vosk":
                    data = self.audio_stream.read(4096, exception_on_overflow=False)
                    if self.vosk_recognizer.AcceptWaveform(data):
                        result = json.loads(self.vosk_recognizer.Result())
                        text = result.get("text", "").lower()
                        if self.wake_word in text or "iris" in text:
                            self._on_wake_word_detected()

            except Exception as e:
                logger.error(f"Wake word error: {e}")
                import time
                time.sleep(0.1)

    def _on_wake_word_detected(self):
        """Handle wake word detection."""
        logger.info("🎯 Wake word detected!")
        if self.callback:
            self.callback()

    def is_available(self) -> bool:
        """Check if wake word detection is available."""
        return self.detector in ["porcupine", "vosk", "browser"]

    def get_status(self) -> dict:
        """Get current wake word detector status."""
        return {
            "detector": self.detector,
            "is_listening": self.is_listening,
            "wake_word": self.wake_word,
            "available": self.is_available()
        }


# Singleton
wake_word_detector = WakeWordDetector()

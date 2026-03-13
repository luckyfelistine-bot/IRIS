"""
IRIS Voice System v7.1 - FIXED Windows MP3 Playback
Multiple fallback methods for maximum compatibility
"""

import os
import threading
import queue
import time
import subprocess
import platform
import re
import tempfile
import shutil

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


class IRISVoiceSystem:
    VOICES = {
        "jarvis": {"name": "Jarvis", "voice": "en-GB-RyanNeural", "tone": "professional", "speed": "+0%", "pitch": "+0Hz", "energy": 0.8},
        "friday": {"name": "Friday", "voice": "en-US-JennyNeural", "tone": "warm", "speed": "+0%", "pitch": "+0Hz", "energy": 0.9},
        "tony": {"name": "Tony", "voice": "en-US-GuyNeural", "tone": "confident", "speed": "+5%", "pitch": "+10Hz", "energy": 1.0},
        "sarah": {"name": "Sarah", "voice": "en-US-SaraNeural", "tone": "calm", "speed": "-5%", "pitch": "-10Hz", "energy": 0.6},
        "anna": {"name": "Anna", "voice": "en-US-AriaNeural", "tone": "friendly", "speed": "+0%", "pitch": "+5Hz", "energy": 0.85},
        "david": {"name": "David", "voice": "en-US-DavisNeural", "tone": "analytical", "speed": "+0%", "pitch": "+0Hz", "energy": 0.7},
        "oliver": {"name": "Oliver", "voice": "en-GB-OliverNeural", "tone": "sophisticated", "speed": "-3%", "pitch": "-5Hz", "energy": 0.75},
        "libby": {"name": "Libby", "voice": "en-GB-LibbyNeural", "tone": "gentle", "speed": "-5%", "pitch": "-10Hz", "energy": 0.65},
        "neerja": {"name": "Neerja", "voice": "en-IN-NeerjaNeural", "tone": "professional", "speed": "+0%", "pitch": "+0Hz", "energy": 0.8},
        "prabhat": {"name": "Prabhat", "voice": "en-IN-PrabhatNeural", "tone": "enthusiastic", "speed": "+3%", "pitch": "+15Hz", "energy": 0.9},
    }

    def __init__(self):
        print("🎙️ Initializing IRIS Voice System v7.1...")
        self.speech_queue = queue.Queue()
        self.speaking = False
        self.profile = "jarvis"
        self.enabled = True
        self.stt_available = False
        self.tts_available = False
        self.tts_engine = None          # 'edge' or 'pyttsx3' or None
        self.tts_engine_obj = None      # only for pyttsx3
        self.recognizer = None
        self.microphone = None
        self.current_process = None

        if SPEECH_RECOGNITION_AVAILABLE:
            self._init_stt()

        self._init_tts()
        self._start_worker()

        status = []
        if self.stt_available:
            status.append("STT ✓")
        if self.tts_available:
            status.append("TTS ✓")

        if status:
            print(f"✅ Voice Ready ({', '.join(status)})")
        else:
            print("⚠️ Voice Limited")

    def _init_stt(self):
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            with self.microphone as source:
                print("🎤 Calibrating microphone...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.stt_available = True
            print("✅ Microphone ready")
        except Exception as e:
            print(f"⚠️ STT init failed: {e}")

    def _init_tts(self):
        if EDGE_TTS_AVAILABLE:
            if self._check_audio_player():
                self.tts_available = True
                self.tts_engine = 'edge'
                print("✅ TTS: edge-tts")
                return

        if PYTTSX3_AVAILABLE:
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)
                self.tts_engine_obj = engine
                self.tts_engine = 'pyttsx3'
                self.tts_available = True
                print("✅ TTS: pyttsx3 (offline)")
                return
            except Exception as e:
                print(f"⚠️ pyttsx3 init failed: {e}")

        print("⚠️ No TTS engine available")

    def _check_audio_player(self):
        system = platform.system()
        if system == "Windows":
            players = ["wmplayer", "vlc", "ffplay"]
            for player in players:
                if shutil.which(player):
                    return True
            return True   # Windows always has wmplayer as fallback
        elif system == "Darwin":
            return shutil.which("afplay") is not None
        else:
            return any(shutil.which(p) for p in ["mpg123", "ffplay", "cvlc", "aplay"])
        return False

    def _start_worker(self):
        def worker():
            while True:
                try:
                    item = self.speech_queue.get()
                    if item is None:
                        break
                    text, profile, mood = item
                    self.speaking = True
                    self._speak_internal(text, profile, mood)
                    self.speaking = False
                    time.sleep(0.2)
                except Exception as e:
                    print(f"Voice worker error: {e}")
                    self.speaking = False

        threading.Thread(target=worker, daemon=True).start()

    def is_mic_available(self):
        return self.stt_available

    def listen(self, timeout=5, phrase_time_limit=10):
        if not self.stt_available:
            return None

        try:
            print("🎤 Listening...")
            with self.microphone as source:
                # Adjust for ambient noise each time (optional)
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            print("🧠 Processing...")
            # Try Google first, then fallback to a local recognizer if available
            try:
                text = self.recognizer.recognize_google(audio)
            except sr.RequestError:
                # Google unavailable, try Sphinx (offline) if installed
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                except:
                    text = None
            except sr.UnknownValueError:
                text = None

            if text:
                print(f"📝 Heard: '{text}'")
                return text
            else:
                print("❓ Could not understand")
                return None
        except sr.WaitTimeoutError:
            print("⏱️ No speech detected")
            return None
        except Exception as e:
            print(f"🎤 Error: {e}")
            return None

    def _speak_internal(self, text: str, profile: str = None, mood: str = "neutral"):
        if not text:
            return

        clean_text = self._clean_text(text)
        if not clean_text:
            return

        print(f"🔊 Speaking: {clean_text[:80]}...")

        if self.tts_engine == 'edge' and EDGE_TTS_AVAILABLE:
            self._speak_edge(clean_text, profile or self.profile, mood)
        elif self.tts_engine == 'pyttsx3' and PYTTSX3_AVAILABLE and self.tts_engine_obj is not None:
            self._speak_pyttsx3(clean_text)
        else:
            print(f"🔇 [TTS unavailable] {clean_text[:100]}")

    def _speak_edge(self, text: str, profile: str, mood: str):
        import asyncio
        import subprocess
        import tempfile
        import os
        import time

        voice_config = self.VOICES.get(profile, self.VOICES["jarvis"])
        voice = voice_config["voice"]
        rate = voice_config["speed"]
        if mood == "stressed":
            rate = "-15%"
        elif mood == "excited":
            rate = "+10%"
        elif mood == "confused":
            rate = "-10%"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir="temp") as tmp:
            tmp_path = tmp.name

        try:
            # Run edge-tts asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            loop.run_until_complete(communicate.save(tmp_path))
            loop.close()

            # Play audio with Popen so we can kill it if needed
            if platform.system() == "Windows":
                # Use ffplay (you have it)
                self.current_process = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", tmp_path])
            else:
                self.current_process = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", tmp_path])
            try:
                self.current_process.wait(timeout=60)  # Wait up to 60 seconds
            except subprocess.TimeoutExpired:
                self.current_process.kill()
            finally:
                self.current_process = None

        except Exception as e:
            print(f"EdgeTTS error: {e}")
            # Fallback to pyttsx3 if available
            if self.tts_engine_obj is not None:
                self._speak_pyttsx3(text)
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    def _play_audio_fixed(self, filepath: str):
        system = platform.system()

        try:
            if system == "Windows":
                self._play_windows_fixed(filepath)
            elif system == "Darwin":
                subprocess.run(["afplay", filepath], check=True, timeout=60)
            else:
                self._play_linux(filepath)
        except Exception as e:
            print(f"Audio playback error: {e}")

    def _play_windows_fixed(self, filepath: str):
        # Method 1: ffplay (best)
        try:
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filepath],
                timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
            )
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Method 2: wmplayer (fallback)
        try:
            subprocess.run(["wmplayer", filepath], timeout=10, check=True)
        except:
            pass

    def _play_linux(self, filepath: str):
        # Try multiple players
        players = [
            ["mpg123", "-q", filepath],
            ["ffplay", "-nodisp", "-autoexit", filepath],
            ["cvlc", "--play-and-exit", filepath],
            ["aplay", filepath]
        ]
        for cmd in players:
            try:
                subprocess.run(cmd, timeout=60, check=True)
                return
            except:
                continue
        print("No suitable audio player found on Linux")

    def _speak_pyttsx3(self, text: str):
        if self.tts_engine_obj is None:
            print("pyttsx3 engine not initialized")
            return
        try:
            self.tts_engine_obj.say(text)
            self.tts_engine_obj.runAndWait()
        except Exception as e:
            print(f"pyttsx3 error: {e}")

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove markdown and special characters
        cleaned = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        cleaned = re.sub(r'\[.*?\]\(.*?\)', '', cleaned)
        cleaned = re.sub(r'[#*_~`>]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        if len(cleaned) > 500:
            cleaned = cleaned[:500] + "..."
        return cleaned

    def speak(self, text: str, profile: str = None, mood: str = "neutral"):
        if not self.enabled:
            return
        if not text:
            return
        self.speech_queue.put((text, profile, mood))

    def stop_speaking(self):
        """Immediately stop any ongoing speech and clear the queue."""
        if self.current_process:
            self.current_process.kill()      # force kill
            self.current_process = None
        self.speaking = False
        # Clear the speech queue
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
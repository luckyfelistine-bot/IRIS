"""IRIS v8 Voice System — TTS + Speech Recognition + 3D Face"""
import os
import asyncio
import edge_tts
import speech_recognition as sr
from typing import Optional, Dict
from config import config

class VoiceSystem:
    """
    IRIS voice capabilities:
    - Text-to-Speech (Edge TTS)
    - Speech Recognition (Google/Sphinx/Vosk)
    - 3D Face animation (HTML/CSS/JS)
    - Emotion-based voice modulation
    """

    def __init__(self):
        self.voice = config.EDGE_TTS_VOICE
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_speaking = False
        self.is_listening = False

    async def speak(self, text: str, emotion: str = "neutral", speed: float = 1.0) -> Dict:
        """Convert text to speech and save audio file."""
        try:
            output_path = os.path.join(config.DATA_DIR, "audio", f"iris_speech_{int(time.time())}.mp3")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Adjust voice based on emotion
            voice = self.voice
            rate = "+0%"
            if emotion == "excited":
                rate = "+20%"
            elif emotion == "sad":
                rate = "-10%"
            elif emotion == "determined":
                rate = "+10%"

            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(output_path)

            return {"success": True, "audio_path": output_path, "text": text, "emotion": emotion}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> Dict:
        """Listen for speech and convert to text."""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

            # Try Google first
            try:
                text = self.recognizer.recognize_google(audio)
                return {"success": True, "text": text, "engine": "google"}
            except sr.UnknownValueError:
                pass

            # Fallback to Sphinx (offline)
            try:
                text = self.recognizer.recognize_sphinx(audio)
                return {"success": True, "text": text, "engine": "sphinx"}
            except:
                pass

            return {"success": False, "error": "Could not understand audio"}
        except sr.WaitTimeoutError:
            return {"success": False, "error": "Listening timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_face_html(self) -> str:
        """Return HTML for 3D animated face."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { margin: 0; background: #0a0a0a; display: flex; justify-content: center; align-items: center; height: 100vh; }
                .iris-face {
                    width: 300px; height: 300px; border-radius: 50%;
                    background: radial-gradient(circle at 30% 30%, #4a90d9, #1a5276);
                    position: relative; box-shadow: 0 0 60px rgba(74, 144, 217, 0.5);
                    animation: pulse 3s ease-in-out infinite;
                }
                .eye {
                    width: 60px; height: 60px; border-radius: 50%;
                    background: radial-gradient(circle at 40% 40%, #fff, #a8d8ea);
                    position: absolute; top: 80px;
                    box-shadow: 0 0 20px rgba(255,255,255,0.3);
                    animation: blink 4s infinite;
                }
                .eye.left { left: 60px; }
                .eye.right { right: 60px; }
                .pupil {
                    width: 25px; height: 25px; border-radius: 50%;
                    background: #0a0a0a; position: absolute;
                    top: 50%; left: 50%; transform: translate(-50%, -50%);
                }
                .mouth {
                    width: 100px; height: 20px; border-radius: 0 0 50px 50px;
                    background: #2c3e50; position: absolute;
                    bottom: 60px; left: 50%; transform: translateX(-50%);
                    transition: all 0.3s ease;
                }
                .mouth.speaking { height: 40px; animation: speak 0.3s ease-in-out infinite alternate; }
                .mouth.happy { border-radius: 0 0 50px 50px; height: 30px; background: #e74c3c; }
                .mouth.sad { border-radius: 50px 50px 0 0; height: 15px; }
                @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.02); } }
                @keyframes blink { 0%, 96%, 100% { transform: scaleY(1); } 98% { transform: scaleY(0.1); } }
                @keyframes speak { from { height: 20px; } to { height: 40px; } }
                .status { position: absolute; bottom: 20px; color: #4a90d9; font-family: monospace; }
            </style>
        </head>
        <body>
            <div class="iris-face" id="face">
                <div class="eye left"><div class="pupil"></div></div>
                <div class="eye right"><div class="pupil"></div></div>
                <div class="mouth" id="mouth"></div>
            </div>
            <div class="status" id="status">IRIS is listening...</div>
            <script>
                const face = document.getElementById('face');
                const mouth = document.getElementById('mouth');
                const status = document.getElementById('status');
                const ws = new WebSocket('ws://' + window.location.host + '/ws/voice');
                ws.onmessage = (e) => {
                    const data = JSON.parse(e.data);
                    if (data.speaking) mouth.classList.add('speaking');
                    else mouth.classList.remove('speaking');
                    if (data.emotion) {
                        mouth.className = 'mouth ' + data.emotion;
                        face.style.background = data.emotion === 'happy' ? 'radial-gradient(circle at 30% 30%, #f39c12, #d35400)' :
                                               data.emotion === 'sad' ? 'radial-gradient(circle at 30% 30%, #5d6d7e, #2c3e50)' :
                                               'radial-gradient(circle at 30% 30%, #4a90d9, #1a5276)';
                    }
                    status.textContent = data.text || 'IRIS is listening...';
                };
            </script>
        </body>
        </html>
        """

# Singleton
voice_system = VoiceSystem()

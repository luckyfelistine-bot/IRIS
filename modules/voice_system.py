"""IRIS v9 Voice System — TTS + 3D Face Integration
Serves the standalone face page and handles text-to-speech.
"""
from flask import render_template

class VoiceSystem:
    """Voice system that integrates with the 3D face."""

    def get_face_html(self):
        """Return the standalone 3D face HTML page."""
        return render_template('iris_face.html')


# Singleton
voice_system = VoiceSystem()

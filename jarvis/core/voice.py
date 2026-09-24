"""
J.A.R.V.I.S. Voice Interface - Voice-first interaction
Natural, concise when simple, detailed when technical
"""
from enum import Enum
from typing import Dict, Optional
from datetime import datetime

class VoiceMode(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    HYBRID = "hybrid"

class VoiceResponse:
    def __init__(self, mode: VoiceMode = VoiceMode.TEXT):
        self.mode = mode
        self.voice_enabled = False

    def set_voice_mode(self, enabled: bool):
        self.voice_enabled = enabled

    def respond(self, text: str, level: str = "info", context: str = "") -> Dict:
        """
        Voice responses should feel natural per spec:
        Routine: "Done. The service is running normally."
        Monitoring: "Your Ubuntu server is online. CPU usage is 18 percent and Wazuh is reporting normally."
        Failure: "I couldn't complete that. The SSH connection timed out."
        Confirmation: "That will disable the firewall. Do you want me to proceed?"
        Calls: "The call to Brian has been initiated."
        """
        # In production, this would trigger TTS and audio output
        response = {
            "timestamp": datetime.now().isoformat(),
            "mode": self.mode.value,
            "level": level,
            "text": text,
            "context": context,
            "voice_enabled": self.voice_enabled
        }
        
        # Console output for now - in production would be spoken
        if level == "success":
            print(f"✓ {text}")
        elif level == "failure":
            print(f"✗ {text}")
        elif level == "confirmation":
            print(f"? {text}")
        else:
            print(f"JARVIS: {text}")
        
        return response

    def success(self, message: str) -> Dict:
        return self.respond(message, level="success")

    def failure(self, message: str, reason: str = "") -> Dict:
        full = f"{message}. {reason}" if reason else message
        return self.respond(full, level="failure")

    def confirmation(self, message: str) -> Dict:
        return self.respond(message, level="confirmation")

    def monitoring(self, message: str) -> Dict:
        return self.respond(message, level="monitoring")

    def call_status(self, contact: str, status: str) -> Dict:
        if status == "initiated":
            return self.respond(f"The call to {contact} has been initiated.", level="info", context="telephony")
        elif status == "incoming":
            return self.respond(f"Raphael, incoming call from {contact}.", level="info", context="telephony")
        elif status == "screen":
            return self.respond(f"Raphael, incoming call from an unknown number. Would you like me to screen it?", level="confirmation", context="telephony")
        return self.respond(f"Call status with {contact}: {status}")

voice = VoiceResponse()

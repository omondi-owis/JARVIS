"""
Voice Interface - Production
Wake phrase detection, speaker identification, natural language understanding
"""
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..core.audit import audit

class VoiceInterface:
    def __init__(self):
        self.wake_phrases = ["jarvis", "hey jarvis", "ok jarvis"]
        self.owner_name = "Raphael"
        self.enabled = False
        self.voice_recognition_enabled = False

    def detect_wake_phrase(self, text: str) -> bool:
        lower = text.lower()
        return any(phrase in lower for phrase in self.wake_phrases)

    def identify_speaker(self, voice_sample: Any = None) -> Dict[str, Any]:
        # In production, use speaker recognition model
        # This is additional identity signal, never sole authenticator
        return {
            "likely_speaker": "Raphael",
            "confidence": 0.85,
            "note": "Voice recognition identifies likely speaker but does not independently authenticate high-risk operations"
        }

    def parse_intent(self, text: str) -> Dict[str, Any]:
        """
        Natural language understanding for:
        - "JARVIS, check my server."
        - "JARVIS, what's happening with Wazuh?"
        - "JARVIS, call Brian."
        - "JARVIS, answer the call."
        - "JARVIS, turn off the bedroom lights."
        - "JARVIS, check the cameras."
        - "JARVIS, deploy the latest MlinziOps version."
        - "JARVIS, what's wrong with the server?"
        """
        lower = text.lower()
        
        # Remove wake phrase
        for phrase in self.wake_phrases:
            lower = lower.replace(phrase, "").strip()
        
        intent = {
            "raw": text,
            "cleaned": lower,
            "timestamp": datetime.now().isoformat()
        }
        
        # Server checks
        if any(kw in lower for kw in ["check server", "server status", "server health", "how is server", "what's wrong with server"]):
            intent["intent"] = "check_server"
            intent["target"] = "ubuntu_server"
            intent["action"] = "health_check"
        
        elif "wazuh" in lower:
            intent["intent"] = "check_wazuh"
            intent["target"] = "wazuh"
            if "alert" in lower or "event" in lower:
                intent["action"] = "get_alerts"
        
        elif "mlinziops" in lower:
            intent["intent"] = "check_mlinziops"
            intent["target"] = "mlinziops"
            if "deploy" in lower:
                intent["action"] = "deploy"
                intent["risk"] = "MEDIUM"
        
        elif any(kw in lower for kw in ["call ", "phone ", "dial "]):
            intent["intent"] = "outgoing_call"
            intent["target"] = "telephony"
            # Extract contact name
            match = re.search(r'call\s+([a-zA-Z\s]+)', lower)
            if match:
                intent["contact"] = match.group(1).strip()
            intent["risk"] = "MEDIUM"
        
        elif "answer" in lower and "call" in lower:
            intent["intent"] = "answer_call"
            intent["target"] = "telephony"
        
        elif any(kw in lower for kw in ["light", "lights"]):
            intent["intent"] = "iot_lights"
            intent["target"] = "iot"
            if "off" in lower:
                intent["action"] = "turn_off"
            elif "on" in lower:
                intent["action"] = "turn_on"
            # Extract room
            room_match = re.search(r'(bedroom|living room|kitchen|bathroom|office|all)\s+lights?', lower)
            if room_match:
                intent["room"] = room_match.group(1)
        
        elif "camera" in lower or "surveillance" in lower:
            intent["intent"] = "check_cameras"
            intent["target"] = "surveillance"
        
        elif "deploy" in lower:
            intent["intent"] = "deploy"
            intent["target"] = "deployment"
            intent["risk"] = "MEDIUM"
        
        elif "routine" in lower:
            intent["intent"] = "routine"
            if "morning" in lower:
                intent["routine"] = "morning"
            elif "night" in lower:
                intent["routine"] = "night"
        
        else:
            intent["intent"] = "unknown"
            intent["action"] = "clarify"
        
        audit.log(
            identity="Raphael",
            device="voice_interface",
            action=f"VOICE_INTENT:{intent.get('intent', 'unknown')}",
            target=intent.get("target", "unknown"),
            risk=intent.get("risk", "LOW"),
            auth_decision="ALLOWED",
            tool="voice_interface",
            result="PARSED",
            verification=f"Intent: {intent.get('intent')}, Raw: {text[:100]}"
        )
        
        return intent

    def generate_response(self, intent: Dict[str, Any], result: Dict[str, Any]) -> str:
        # Natural responses per spec
        if intent["intent"] == "check_server":
            if result.get("status") == "online":
                return f"Your Ubuntu server is online. CPU usage is {result.get('cpu_percent', 0)} percent and memory is {result.get('memory_percent', 0)} percent. {result.get('uptime', '')}"
            else:
                return f"I couldn't complete that. The server check returned {result.get('status', 'unknown')}."
        
        elif intent["intent"] == "outgoing_call":
            contact = intent.get("contact", "the number")
            if result.get("status") == "initiated":
                return f"The call to {contact} has been initiated."
            elif result.get("status") == "requires_confirmation":
                return f"This will call {contact}. Do you want me to proceed?"
        
        elif intent["intent"] == "iot_lights":
            if result.get("status") == "success":
                return result.get("message", "Done. The lights have been adjusted.")
        
        return result.get("message", "Done.")

voice_interface = VoiceInterface()

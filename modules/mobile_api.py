"""IRIS v8 Mobile API — Backend endpoints for mobile app"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from config import config

class MobileAPI:
    """
    API endpoints for IRIS mobile companion app:
    - Authentication
    - Voice commands
    - Push notifications
    - Device sync
    - Location tracking
    - Battery status
    """

    def __init__(self):
        self.devices = {}  # device_id -> device_info

    def register_device(self, device_id: str, device_type: str = "android", push_token: str = None) -> Dict:
        """Register a mobile device."""
        self.devices[device_id] = {
            "device_id": device_id,
            "device_type": device_type,
            "push_token": push_token,
            "registered_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "status": "active"
        }
        return {"success": True, "device_id": device_id, "message": "Device registered"}

    def update_device_status(self, device_id: str, battery_level: int = None, location: Dict = None) -> Dict:
        """Update device status from mobile app."""
        if device_id not in self.devices:
            return {"success": False, "error": "Device not registered"}

        self.devices[device_id]["last_seen"] = datetime.now().isoformat()
        if battery_level is not None:
            self.devices[device_id]["battery_level"] = battery_level
        if location:
            self.devices[device_id]["location"] = location

        return {"success": True, "device_id": device_id}

    def get_device_info(self, device_id: str) -> Dict:
        """Get device information."""
        if device_id not in self.devices:
            return {"success": False, "error": "Device not found"}
        return {"success": True, "device": self.devices[device_id]}

    def send_push_notification(self, device_id: str, title: str, body: str, data: Dict = None) -> Dict:
        """Send push notification to device."""
        if device_id not in self.devices:
            return {"success": False, "error": "Device not registered"}

        device = self.devices[device_id]
        if not device.get("push_token"):
            return {"success": False, "error": "No push token available"}

        # In production: integrate with Firebase Cloud Messaging or OneSignal
        return {
            "success": True,
            "device_id": device_id,
            "title": title,
            "body": body,
            "sent_at": datetime.now().isoformat()
        }

    def get_all_devices(self) -> List[Dict]:
        """Get all registered devices."""
        return list(self.devices.values())

    def sync_data(self, device_id: str, data_type: str, data: Dict) -> Dict:
        """Sync data between IRIS and mobile device."""
        if device_id not in self.devices:
            return {"success": False, "error": "Device not registered"}

        # Store sync data
        sync_file = os.path.join(config.DATA_DIR, "mobile_sync", f"{device_id}_{data_type}.json")
        os.makedirs(os.path.dirname(sync_file), exist_ok=True)
        with open(sync_file, "w") as f:
            json.dump({"data": data, "synced_at": datetime.now().isoformat()}, f)

        return {"success": True, "device_id": device_id, "data_type": data_type}

# Singleton
mobile_api = MobileAPI()

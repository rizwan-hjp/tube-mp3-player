# appwrite_handler.py
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import json
import uuid
import hashlib
import platform
import getpass

# Load the .env file
load_dotenv()

class AppwriteHandler:
    CONFIG_FILE = "config.json"

    def __init__(self):
        self.endpoint = os.getenv("APPWRITE_ENDPOINT")
        self.project_id = os.getenv("APPWRITE_PROJECT_ID")
        self.api_key = os.getenv("APPWRITE_API_KEY")
        self.database_id = os.getenv("APPWRITE_DATABASE_ID")
        self.collection_id = os.getenv("APPWRITE_COLLECTION_ID")
        self.headers = {
            "X-Appwrite-Project": self.project_id,
            "X-Appwrite-Key": self.api_key,
            "Content-Type": "application/json",
        }
        self.user_id = self.get_or_create_user_id()

    def generate_unique_id(self):
        """Generates a unique ID based on system information and UUID"""
        system_info = {
            'platform': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'node': platform.node(),
            'username': getpass.getuser(),
        }
        system_string = json.dumps(system_info, sort_keys=True)
        unique_string = f"{system_string}-{uuid.uuid4()}"
        hashed = hashlib.sha256(unique_string.encode()).hexdigest()
        return hashed[:32]

    def get_or_create_user_id(self):
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as file:
                    config = json.load(file)
                    if 'user_id' in config:
                        return config['user_id']
            user_id = self.generate_unique_id()
            self.save_config({'user_id': user_id})
            return user_id
        except Exception as e:
            print(f"Error handling user ID: {e}")
            return self.generate_unique_id()

    def save_config(self, data):
        try:
            existing_data = {}
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as file:
                    existing_data = json.load(file)
            existing_data.update(data)
            with open(self.CONFIG_FILE, 'w') as file:
                json.dump(existing_data, file)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_current_timestamp(self):
        """Returns the current timestamp in ISO 8601 format."""
        return datetime.utcnow().isoformat() + "Z"

    def send_event(self, event_name, additional_data=None):
        """Sends an event to the Appwrite server."""
        document_data = {
            "eventName": event_name,
            "timestamp": self.get_current_timestamp(),
            "userId": self.user_id,
        }
        
        if additional_data:
            document_data.update(additional_data)

        payload = {
            "documentId": "unique()",  # Let Appwrite generate the document ID
            "data": document_data
        }

        url = f"{self.endpoint}/databases/{self.database_id}/collections/{self.collection_id}/documents"
        
        try:
            # Print debug information
            print("Sending request to Appwrite:")
            print(f"URL: {url}")
            print("Headers:", {k: v for k, v in self.headers.items() if k != 'X-Appwrite-Key'})
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            # Print response information
            print(f"Response status code: {response.status_code}")
            print(f"Response body: {response.text}")
            
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending event to Appwrite: {e}")
            return False

    def is_first_time(self):
        if not os.path.exists(self.CONFIG_FILE):
            return True
        try:
            with open(self.CONFIG_FILE, "r") as file:
                config = json.load(file)
            return not config.get("first_launch_done", False)
        except (json.JSONDecodeError, FileNotFoundError):
            return True

    def mark_first_launch_done(self):
        self.save_config({"first_launch_done": True})

    def handle_first_launch(self):
        if self.is_first_time():
            print("First time opening the app. Sending event...")
            if self.send_event("app_download"):
                print("Event sent successfully!")
                self.mark_first_launch_done()
            else:
                print("Failed to send event.")
        else:
            print("Not the first time opening the app. Skipping event.")
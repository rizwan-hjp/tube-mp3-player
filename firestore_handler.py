import os
import json
import uuid
import hashlib
import platform
import getpass
from datetime import datetime
from firebase_admin import credentials, firestore, initialize_app

class FirestoreHandler:
    ASSETS_DIR = "assets"
    CONFIG_FILE = os.path.join(ASSETS_DIR, "config.json")
    
    def __init__(self):
        self._ensure_assets_directory()
        
        # Hard-code the Firebase credentials JSON path

        config= { }
            
            
        try:
                
            # Initialize Firebase with the credentials
            cred = credentials.Certificate(config)
           
            try:
                initialize_app(cred)
            except ValueError:
                # App already initialized
                pass
                
            self.db = firestore.client()
            self.events_collection = self.db.collection('events')
            self.user_id = self.get_or_create_user_id()
            
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in credentials file: {cred_path}")
        except Exception as e:
            raise Exception(f"Error initializing Firebase: {str(e)}")

    def _ensure_assets_directory(self):
        """Ensures the assets directory exists"""
        if not os.path.exists(self.ASSETS_DIR):
            try:
                os.makedirs(self.ASSETS_DIR)
                print(f"Created assets directory at: {os.path.abspath(self.ASSETS_DIR)}")
            except Exception as e:
                print(f"Error creating assets directory: {e}")

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
        """Saves configuration to the config file in assets directory"""
        try:
            existing_data = {}
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as file:
                    existing_data = json.load(file)
            existing_data.update(data)
            
            # Ensure the assets directory exists before saving
            self._ensure_assets_directory()
            
            with open(self.CONFIG_FILE, 'w') as file:
                json.dump(existing_data, file, indent=2)
            print(f"Config saved successfully to: {os.path.abspath(self.CONFIG_FILE)}")
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_current_timestamp(self):
        """Returns the current timestamp."""
        return datetime.utcnow()

    def send_event(self, event_name, additional_data=None):
        """Sends an event to Firestore."""
        document_data = {
            "eventName": event_name,
            "timestamp": self.get_current_timestamp(),
            "userId": self.user_id,
        }
        
        if additional_data:
            document_data.update(additional_data)

        try:
            # Print debug information
            print("Sending event to Firestore:")
            print(f"Event data: {json.dumps(document_data, default=str, indent=2)}")
            
            # Add a new document with a generated ID
            doc_ref = self.events_collection.document()
            doc_ref.set(document_data)
            
            print(f"Event sent successfully! Document ID: {doc_ref.id}")
            return True
        except Exception as e:
            print(f"Error sending event to Firestore: {e}")
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

# Usage example:
firestore_handler = FirestoreHandler()
firestore_handler.handle_first_launch()

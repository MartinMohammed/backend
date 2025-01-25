from app.models.session import Message, Conversation
from app.core.logging import LoggerMixin
from pathlib import Path
import json
from typing import Optional, Dict
import random
import os

class ChatService(LoggerMixin):
    def __init__(self):
        self.logger.info("Initializing ChatService")
        self.character_details: Dict = self._load_character_details()
        if not self.character_details:
            self.logger.error("Failed to initialize character details - dictionary is empty")
        else:
            self.logger.info(f"Loaded character details for wagons: {list(self.character_details.keys())}")
            
        self.mock_responses = {
            "greeting": [
                "Hello! How can I help you today?",
                "Hi there! What's on your mind?",
                "Greetings! What would you like to discuss?"
            ],
            "general": [
                "That's an interesting perspective. Tell me more.",
                "I understand what you mean. Let's explore that further.",
                "I see where you're coming from. What else is on your mind?"
            ],
            "farewell": [
                "It was nice talking to you!",
                "Take care! Let me know if you need anything else.",
                "Goodbye! Feel free to chat again anytime."
            ]
        }
        self.logger.info("ChatService initialized with mock responses")
        
    @classmethod
    def _load_character_details(cls) -> Dict:
        """Load character details from JSON files"""
        try:
            # Get the absolute path to the data directory
            current_dir = Path(__file__).resolve().parent
            app_dir = current_dir.parent
            backend_dir = app_dir.parent
            player_details_path = backend_dir / "data" / "player_details.json"
            
            cls.get_logger().info(f"Attempting to load character details from {player_details_path}")
            
            if not player_details_path.exists():
                cls.get_logger().error(f"File not found: {player_details_path}")
                return {}
                
            with open(player_details_path, "r") as f:
                data = json.load(f)
                if "player_details" not in data:
                    cls.get_logger().error("Missing 'player_details' key in JSON data")
                    return {}
                    
                details = data["player_details"]
                cls.get_logger().info(f"Successfully loaded character details. Available wagons: {list(details.keys())}")
                return details
        except json.JSONDecodeError as e:
            cls.get_logger().error(f"JSON parsing error: {str(e)}")
            return {}
        except Exception as e:
            cls.get_logger().error(f"Failed to load character details: {str(e)}")
            return {}

    def _get_character_context(self, uid: str) -> Optional[Dict]:
        """Get the character's context for the conversation"""
        try:
            self.logger.debug(f"Getting character context for uid: {uid}")
            # "wagon-<i>-player-<k>"
            uid_splitted = uid.split('-')
            wagon_id, player_id = uid_splitted[1], uid_splitted[3]
            wagon_key = f"wagon-{wagon_id}"
            player_key = f"player-{player_id}"
            
            if wagon_key not in self.character_details:
                self.logger.error(f"Wagon {wagon_key} not found in character details. Available wagons: {list(self.character_details.keys())}")
                return None
                
            if player_key not in self.character_details[wagon_key]:
                self.logger.error(f"Player {player_key} not found in wagon {wagon_key}. Available players: {list(self.character_details[wagon_key].keys())}")
                return None
                
            character = self.character_details[wagon_key][player_key]
            self.logger.debug("Retrieved character context", extra={
                "uid": uid,
                "wagon": wagon_key,
                "player": player_key,
                "occupation": character["profile"]["occupation"]
            })
            return character
        except (KeyError, IndexError) as e:
            self.logger.error(f"Failed to get character context: {str(e)}", extra={
                "uid": uid,
                "error": str(e),
                "character_details_keys": list(self.character_details.keys()) if self.character_details else None
            })
            return None

    def _get_mock_response(self, character: Dict, message: str) -> str:
        """Generate a mock response based on character profile and message"""
        message_lower = message.lower()
        
        # Determine response type
        if any(word in message_lower for word in ["hi", "hello", "hey"]):
            response_type = "greeting"
        elif any(word in message_lower for word in ["bye", "goodbye", "see you"]):
            response_type = "farewell"
        else:
            response_type = "general"

        # Get random response
        base_response = random.choice(self.mock_responses[response_type])
        occupation = character["profile"]["occupation"]
        trait = random.choice(character["traits"]["personality"])
        
        response = f"{base_response} As a {occupation}, I tend to be quite {trait}."
        
        self.logger.debug("Generated mock response", extra={
            "response_type": response_type,
            "occupation": occupation,
            "trait": trait,
            "response_length": len(response)
        })
        
        return response

    def generate_response(self, uid: str, conversation: Conversation) -> Optional[str]:
        """Generate a mock response based on character profile"""
        self.logger.info(f"Generating response for uid: {uid}")
        character = self._get_character_context(uid)
        if not character:
            self.logger.error(f"Cannot generate response - character not found for uid: {uid}")
            return None

        # Get the last user message
        last_message = next((msg.content for msg in reversed(conversation.messages) 
                           if msg.role == "user"), "")
        
        self.logger.info("Generating response", extra={
            "uid": uid,
            "message_length": len(last_message),
            "conversation_length": len(conversation.messages)
        })

        return self._get_mock_response(character, last_message) 
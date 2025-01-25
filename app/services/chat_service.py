from app.models.session import Conversation, Message
from app.core.logging import LoggerMixin
from pathlib import Path
import json
from typing import Optional, Dict, List
import os
from mistralai import Mistral
from fastapi import HTTPException

# Get the Mistral API key from environment (injected by ECS)
mistral_api_key = os.getenv("MISTRAL_API_KEY")


# Get the Mistral API key from environment (injected by ECS)
mistral_api_key = os.getenv("MISTRAL_API_KEY")


class ChatService(LoggerMixin):
    def __init__(self):
        self.logger.info("Initializing ChatService")
        self.character_details: Dict = self._load_character_details()

        if not self.character_details:
            self.logger.error(
                "Failed to initialize character details - dictionary is empty"
            )
        else:
<<<<<<< HEAD
            self.logger.info(f"Loaded character details for wagons: {list(self.character_details.keys())}")

=======
            self.logger.info(
                f"Loaded character details for wagons: {list(self.character_details.keys())}"
            )

        # Get the Mistral API key from environment (injected by ECS)
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
>>>>>>> 83ed757c1e333edd6dbaa922dc6fe7e43c254687
        if not mistral_api_key:
            self.logger.error("MISTRAL_API_KEY not found in environment variables")
            raise ValueError("MISTRAL_API_KEY is required")

        self.client = Mistral(api_key=mistral_api_key)
        self.model = "mistral-large-latest"

        self.logger.info("Initialized Mistral AI client")

    @classmethod
    def _load_character_details(cls) -> Dict:
        """Load character details from JSON files"""
        try:
            # Get the absolute path to the data directory
<<<<<<< HEAD
            current_dir = Path(__file__).resolve().parent  # Points to the directory of chat_service.py
            app_dir = current_dir.parent  # Points to the app directory
            data_dir = app_dir / "data"  # Points to the data directory inside the app folder
            player_details_path = data_dir / "player_details.json"

            cls.get_logger().info(f"Attempting to load character details from {player_details_path}")

            # Check if the file exists
=======
            current_dir = Path(__file__).resolve().parent
            app_dir = current_dir.parent
            backend_dir = app_dir.parent
            player_details_path = backend_dir / "data" / "player_details.json"

            # use cls because it's a class method
            cls.get_logger().info(
                f"Attempting to load character details from {player_details_path}"
            )

            # check if the file exists
>>>>>>> 83ed757c1e333edd6dbaa922dc6fe7e43c254687
            if not player_details_path.exists():
                cls.get_logger().error(f"File not found: {player_details_path}")
                return {}

<<<<<<< HEAD
            # Read the contents of the file
=======
            # read the contents of the file.
>>>>>>> 83ed757c1e333edd6dbaa922dc6fe7e43c254687
            with open(player_details_path, "r") as f:
                data = json.load(f)
                if "player_details" not in data:
                    cls.get_logger().error("Missing 'player_details' key in JSON data")
                    return {}
                details = data["player_details"]
                cls.get_logger().info(
                    f"Successfully loaded character details. Available wagons: {list(details.keys())}"
                )
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
            uid_splitted = uid.split("-")
            wagon_key, player_key = (
                f"wagon-{uid_splitted[1]}",
                f"player-{uid_splitted[3]}",
            )

<<<<<<< HEAD
            # Check if the wagon key exists
=======
            # check if the wagon key exists
>>>>>>> 83ed757c1e333edd6dbaa922dc6fe7e43c254687
            if wagon_key not in self.character_details:
                self.logger.error(
                    f"Wagon {wagon_key} not found in character details. Available wagons: {list(self.character_details.keys())}"
                )
                return None

<<<<<<< HEAD
            # Check if the player key exists
=======
            # check if the player key exists
>>>>>>> 83ed757c1e333edd6dbaa922dc6fe7e43c254687
            if player_key not in self.character_details[wagon_key]:
                self.logger.error(
                    f"Player {player_key} not found in wagon {wagon_key}. Available players: {list(self.character_details[wagon_key].keys())}"
                )
                return None

<<<<<<< HEAD
            # Get the details of the player that belongs to the wagon
=======
            # get the details of the player that belongs to the wagon
>>>>>>> 83ed757c1e333edd6dbaa922dc6fe7e43c254687
            character = self.character_details[wagon_key][player_key]
            self.logger.debug(
                "Retrieved character context",
                extra={
                    "uid": uid,
                    "wagon": wagon_key,
                    "player": player_key,
                    "occupation": character["profile"]["occupation"],
                },
            )
            return character
        except (KeyError, IndexError) as e:
<<<<<<< HEAD
            self.logger.error(f"Failed to get character context: {str(e)}", extra={"uid": uid, "error": str(e)})
=======
            self.logger.error(
                f"Failed to get character context: {str(e)}",
                extra={
                    "uid": uid,
                    "error": str(e),
                    "character_details_keys": list(self.character_details.keys())
                    if self.character_details
                    else None,
                },
            )
>>>>>>> 83ed757c1e333edd6dbaa922dc6fe7e43c254687
            return None

    def _create_character_prompt(self, character: Dict) -> str:
        """Create a prompt that describes the character's personality and context"""
        occupation = character["profile"]["occupation"]
        traits = ", ".join(character["traits"]["personality"])
        background = character["profile"].get("background", "")

        prompt = f"""You are a character in a wagon train journey. You are a {occupation} with the following traits: {traits}. 
{background}
Please respond to messages in character, maintaining these personality traits and incorporating your occupation into your responses when relevant.
Keep responses concise and natural, as if in a real conversation."""
<<<<<<< HEAD
        return prompt

    def generate_response(self, uid: str, conversation: List[Message], prompt: str) -> str:
        """
        Generate a response using the Mistral AI model based on the provided prompt and conversation history.
        """
        try:
            # Combine the prompt and conversation history
            full_prompt = prompt + "\n\nConversation History:\n"
            for message in conversation:
                full_prompt += f"{message.role}: {message.content}\n"

            self.logger.info(f"Generating response for UID: {uid}")

            # Call the Mistral AI API
            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": full_prompt}],
            )

            # Extract the generated response
            ai_response = response.choices[0].message.content
            self.logger.info(f"Generated response: {ai_response}")

            return ai_response

        except Exception as e:
            self.logger.error(f"Failed to generate response: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")
=======

        return prompt

    def generate_response(self, uid: str, conversation: Conversation) -> Optional[str]:
        """Generate a response using Mistral AI based on character profile"""
        self.logger.info(f"Generating response for uid: {uid}")
        character = self._get_character_context(uid)

        if not character:
            self.logger.error(
                f"Cannot generate response - character not found for uid: {uid}"
            )
            return None

        try:
            # Create the system prompt with character context
            system_prompt = self._create_character_prompt(character)

            # Convert conversation history to Mistral AI format
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history (limit to last 10 messages to stay within context window)
            for msg in conversation.messages[-10:]:
                # Convert 'agent' role to 'assistant' for Mistral compatibility
                role = "assistant" if msg.role == "agent" else msg.role
                messages.append({"role": role, "content": msg.content})

            # Get response from Mistral AI
            chat_response = self.client.chat.complete(
                model=self.model, messages=messages, temperature=0.7, max_tokens=500
            )

            response = chat_response.choices[0].message.content

            self.logger.info(
                "Generated Mistral AI response",
                extra={
                    "uid": uid,
                    "response_length": len(response),
                    "conversation_length": len(conversation.messages),
                },
            )

            return response

        except Exception as e:
            self.logger.error(
                f"Failed to generate Mistral AI response: {str(e)}",
                extra={"uid": uid, "error": str(e)},
            )
            return "I apologize, but I'm having trouble responding right now. Please try again later."
>>>>>>> 83ed757c1e333edd6dbaa922dc6fe7e43c254687

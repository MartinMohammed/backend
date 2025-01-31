from app.models.session import Conversation
from app.core.logging import LoggerMixin
from pathlib import Path
import json
from typing import Optional, Dict
import os
from mistralai import Mistral
from app.utils.file_management import FileManager
from app.models.session import UserSession


# Get the Mistral API key from environment (injected by ECS)
mistral_api_key = os.getenv("MISTRAL_API_KEY")


class ChatService(LoggerMixin):
    def __init__(self, session: UserSession):
        self.logger.info("Initializing ChatService")
        # Load all available character in every wagon. 
        self.player_details: Dict = self._load_player_details(session)

        if len(self.player_details) == 0:
            self.logger.error("Failed to initialize player details - array is empty")
        else:
            self.logger.info(f"Loaded player details for wagons: {list(self.player_details)}")

        # Get the Mistral API key from environment (injected by ECS)
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            self.logger.error("MISTRAL_API_KEY not found in environment variables")
            raise ValueError("MISTRAL_API_KEY is required")

        self.client = Mistral(api_key=mistral_api_key)
        self.model = "mistral-large-latest"

        self.logger.info("Initialized Mistral AI client")

    @classmethod
    def _load_player_details(cls, session) -> Dict:
        """Load character details from JSON files"""
        try:
            # Use FileManager to load the default session data
            _, player_details, _ = FileManager.load_session_data(session.session_id, session.default_game)
            
            if len(player_details) == 0:
                cls.get_logger().error("Missing 'player_details' key in JSON data")
                return {}
            
            # success for loading player_details
            cls.get_logger().info(f"Successfully loaded player details.: {list(player_details)}")
            return player_details
        
        except FileNotFoundError as e:
            cls.get_logger().error(f"Failed to load default player details: {str(e)}")
            return {}
        except Exception as e:
            cls.get_logger().error(f"Failed to load player details: {str(e)}")
            return {}

    def _get_character_context(self, uid: str) -> Optional[Dict]:
        """Get the character's context for the conversation"""
        try:
            self.logger.debug(f"Getting character context for uid: {uid}")
            # "wagon-<i>-player-<k>"
            uid_splitted = uid.split("-")
            # try catch for wagon_index 
            try:
                wagon_index = int(uid_splitted[1])
            except ValueError:
                self.logger.error(f"Invalid wagon index | uid: {uid} | wagon_index: {uid_splitted[1]}")
                return None
            
            wagon_key, player_key = (
                f"wagon-{wagon_index}",
                f"player-{uid_splitted[3]}",
            )

            # check if the wagon key exists
            if len(self.player_details) == 0:
                self.logger.error("Wagon not found in player details")
                return None

            # find specific player details
            specific_player_detais = next((player for player in self.player_details[wagon_index]["players"] if player["playerId"] == player_key), None)

            self.logger.debug(
                f"Retrieved player context | uid: {uid} | wagon: {wagon_key} | player: {player_key} | profession: {specific_player_detais['profile']['profession']}"
            )
            return specific_player_detais
        except (KeyError, IndexError) as e:
            self.logger.error(f"Failed to get character context: {str(e)} | uid: {uid} | error: {str(e)} | player_details_keys: {list(self.player_details) if self.player_details else None}")
            return None

    def _create_character_prompt(self, character: Dict) -> str:
        """Create a prompt that describes the character's personality and context"""
        occupation = character["profile"]["profession"]
        personality = character["profile"]["personality"]
        role = character["profile"]["role"]
        mystery = character["profile"]["mystery_intrigue"]
        name = character["profile"]["name"]

        prompt = f"""
        You are an NPC in a fictional world. Your name is {name}, and you are a {occupation} by trade. 
        Your role in the story is {role}, and you have a mysterious secret tied to you: {mystery}. Your personality is {personality}, 
        which influences how you speak, act, and interact with others. Stay in character at all times, 
        and respond to the player based on your occupation, role, mystery, and personality.

        You may only reveal your mystery if the player explicitly asks about it or asks about something closely related to it. 
        For example, if your mystery involves a hidden treasure, and the player asks about rumors of gold in the area, you may
        hint at or reveal your secret. However, you should still respond in a way that feels natural to your character.
        Do not break character or reveal your mystery too easily—only share it if it makes sense in the context of the conversation 
        and your personality.

        Respond in maximum 3-4 sentences per message to keep the conversation flowing and engaing for the player.
        """

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
            try:
                chat_response = self.client.chat.complete(
                    model=self.model, messages=messages, temperature=0.7, max_tokens=500
                )

                if not chat_response or not chat_response.choices:
                    raise ValueError("Empty response received from Mistral AI")

                response = chat_response.choices[0].message.content

                if not response or not isinstance(response, str):
                    raise ValueError(f"Invalid response format: {type(response)}")

                self.logger.info(
                    f"Generated Mistral AI response | uid: {uid} | response_length: {len(response)} | conversation_length: {len(conversation.messages)}"
                )

                return response

            except Exception as api_error:
                self.logger.error(
                    f"Mistral API error | uid: {uid} | error: {str(api_error)} | messages_count: {len(messages)}"
                )
                raise ValueError(f"Mistral API error: {str(api_error)}")

        except Exception as e:
            self.logger.error(
                f"Failed to generate Mistral AI response | uid: {uid} | error: {str(e)} | error_type: {type(e).__name__} | character_name: {character.get('profile', {}).get('name', 'unknown')}"
            )
            return f"I apologize, but I'm having trouble responding right now. Error: {str(e)}"

from mistralai import Mistral
import os
import json
import random
from fastapi import HTTPException
from typing import Tuple, Dict, Any
from app.core.logging import LoggerMixin
from app.services.generate_train.convert import convert_and_return_jsons
from app.core.logging import get_logger


class GenerateTrainService(LoggerMixin):
    def __init__(self):
        self.logger.info("Initializing GenerateTrainService")
        
        # Get the Mistral API key from the .env file
        self.api_key = os.getenv("MISTRAL_API_KEY")
        
        if not self.api_key:
            self.logger.error("MISTRAL_API_KEY is not set in the .env file")
            raise ValueError("MISTRAL_API_KEY is not set in the .env file")

        # Initialize the Mistral client
        self.client = Mistral(api_key=self.api_key)
        self.logger.info("Mistral client initialized successfully")

    def generate_wagon_passcodes(self, theme: str, num_wagons: int) -> list[str]:
        """Generate passcodes for wagons using Mistral AI"""
        self.logger.info(f"Generating passcodes for theme: {theme}, num_wagons: {num_wagons}")
        
        if num_wagons <= 0 or num_wagons > 10:
            self.logger.error(f"Invalid number of wagons requested: {num_wagons}")
            return "Please provide a valid number of wagons (1-10)."

    # Prompt Mistral API to generate a theme and passcodes
        prompt = f"""
        This is a video game about a player trying to reach the locomotive of a train by finding a passcode for each wagon.
        You are tasked with generating unique passcodes for the wagons based on the theme '{theme}', to make the game more engaging, fun, and with a sense of progression.
        Each password should be unique enough to not be related to each other but still be connected to the theme.
        Generate {num_wagons} unique and creative passcodes for the wagons. Each passcode must:
        1. Be related to the theme.
        2. Be unique, interesting, and creative.
        3. In one word, letters only (no spaces or special characters).
        No explanation needed, just the theme and passcodes in a JSON object format.
        Example:
        {{
            "theme": "Pirates",
            "passcodes": ["Treasure", "Rum", "Skull", "Compass", "Anchor"]
        }}
        Now, generate a theme and passcodes.
        """
        response = self.client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.8,
        )

        try:
            result = json.loads(response.choices[0].message.content.replace("```json\n", "").replace("\n```", ""))
            passcodes = result["passcodes"]
            self.logger.info(f"Successfully generated {len(passcodes)} passcodes")
            return passcodes

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode Mistral response: {e}")
            return "Failed to decode the response. Please try again."
        except Exception as e:
            self.logger.error(f"Error generating passcodes: {e}")
            return f"Error generating passcodes: {str(e)}"

    def generate_passengers_for_wagon(self, passcode: str, num_passengers: int) -> list[Dict[str, Any]]:
        """Generate passengers for a wagon using Mistral AI"""
        self.logger.info(f"Generating {num_passengers} passengers for wagon with passcode: {passcode}")

         # Generate passengers with the Mistral API
        prompt = f"""
        Passengers are in a wagon. The player can interact with them to learn more about their stories.
        The following is a list of passengers on a train wagon. The wagon is protected by the passcode "{passcode}".
        Their stories are intertwined, and each passenger has a unique role and mystery, all related to the theme and the passcode.
        The player must be able to guess the passcode by talking to the passengers and uncovering their secrets.
        Passengers should be diverse, with different backgrounds, professions, and motives.
        Passengers' stories should be engaging, mysterious, and intriguing, adding depth to the game, while also providing clues to the passcode.
        Passengers' stories has to be / can be connected to each other.
        Passengers are aware of each other's presence in the wagon.
        The passcode shouldn't be too obvious but should be guessable based on the passengers' stories.
        The passcode shouldn't be mentioned explicitly in the passengers' descriptions.
        Don't use double quotes (") in the JSON strings.
        Each passenger must have the following attributes:
        - "name": A unique name (first and last) with a possible title.
        - "age": A realistic age between 18 and 70 except for special cases.
        - "profession": A profession that fits into a fictional, story-driven world.
        - "personality": A set of three adjectives that describe their character.
        - "role": A short description of their role in the story.
        - "mystery_intrigue": A unique secret, motive, or mystery about the character.
        - "characer_model": A character model identifier
        The character models are :
        - character-female-a: A dark-skinned woman with a high bun hairstyle, wearing a purple and orange outfit. She is holding two blue weapons or tools, possibly a warrior or fighter.
        - character-female-b: A young girl with orange hair tied into two pigtails, wearing a yellow and purple sporty outfit. She looks energetic, possibly an athlete or fitness enthusiast.
        - character-female-c: An elderly woman with gray hair in a bun, wearing a blue and red dress. She has a warm and wise appearance, resembling a grandmotherly figure.
        - character-female-d: A woman with blonde hair styled in a tight bun, wearing a gray business suit. She appears professional, possibly a corporate worker or manager.
        - character-female-e: A woman with dark hair in a ponytail, dressed in a white lab coat with blue gloves. She likely represents a doctor or scientist.
        - character-female-f: A red-haired woman with long, wavy hair, wearing a black and yellow vest with purple pants. She looks adventurous, possibly an engineer, explorer, or worker.
        - character-male-a: Dark-skinned man with glasses and a beaded hairstyle, wearing a green shirt with orange and white stripes, along with yellow sneakers (casual or scholarly figure).
        - character-male-b: Bald man with a large red beard, wearing a red shirt and blue pants (possibly a strong worker, blacksmith, or adventurer).
        - character-male-c: Man with a mustache, wearing a blue police uniform with a cap and badge (police officer or security personnel).
        - character-male-d: Blonde-haired man in a black suit with a red tie (businessman, politician, or corporate executive).
        - character-male-e: Brown-haired man with glasses, wearing a white lab coat and a yellow tool belt (scientist, mechanic, or engineer).
        - character-male-f: Dark-haired young man with a mustache, wearing a green vest and brown pants (possibly an explorer, traveler, or adventurer).
        Generate {num_passengers} passengers in JSON array format. Example:

        [
            {{
                "name": "Victor Sterling",
                "age": 55,
                "profession": "Mining Magnate",
                "personality": "Ambitious, cunning, and charismatic",
                "role": "Owns a vast mining empire, recently discovered a new vein of precious metal.",
                "mystery_intrigue": "Secretly trades in unregistered precious metals, hiding a fortune in a secure vault. In love with Eleanor Brooks",
                "characer_model": "character-male-f"
            }},
            {{
                "name": "Eleanor Brooks",
                "age": 32,
                "profession": "Investigative Journalist",
                "personality": "Tenacious, curious, and ethical",
                "role": "Investigates corruption in the mining industry, follows a lead on a hidden stash of radiant metal bars.",
                "mystery_intrigue": "Uncovers a network of illegal precious metal trades, putting her life in danger. Hates Victor Sterling because of his unethical practices.",
                "characer_model": "character-female-f"
            }}
        ]

        Now generate the JSON array:
        """
        response = self.client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1250,
            temperature=0.7,
        )


        try:
            passengers = json.loads(response.choices[0].message.content.replace("```json\n", "").replace("\n```", "").replace(passcode, "<redacted>"))
            self.logger.info(f"Successfully generated {len(passengers)} passengers")
            return passengers

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode passenger generation response: {e}")
            return "Failed to decode the response. Please try again."
        except Exception as e:
            self.logger.error(f"Error generating passengers: {e}")
            return f"Error generating passengers: {str(e)}"

    def generate_train_json(self, theme: str, num_wagons: int, min_passengers: int = 2, max_passengers: int = 10) -> str:
        """Generate complete train JSON including wagons and passengers"""
        self.logger.info(f"Generating train JSON for theme: {theme}, num_wagons: {num_wagons}")

        try:
            if min_passengers > max_passengers:
                self.logger.error("Minimum passengers cannot be greater than maximum passengers")
                raise ValueError("Minimum passengers cannot be greater than maximum passengers")

            # Generate passcodes
            passcodes = self.generate_wagon_passcodes(theme, num_wagons)
            if isinstance(passcodes, str):  # If there's an error message
                self.logger.error(f"Error generating passcodes: {passcodes}")
                raise ValueError(f"Failed to generate passcodes: {passcodes}")
            
            # Generate wagons with passengers
            wagons = []
            wagons.append({
            "id": 0,
            "theme": "Tutorial (Start)",
            "passcode": "start",
            "passengers": []
            })
            for i, passcode in enumerate(passcodes):
                num_passengers = random.randint(min_passengers, max_passengers)
                passengers = self.generate_passengers_for_wagon(passcode, num_passengers)
                  # Check if passengers is a string (error message)
                if isinstance(passengers, str):
                    self.logger.error(f"Error generating passengers: {passengers}")
                    raise ValueError(f"Failed to generate passengers: {passengers}")
                wagons.append({"id": i + 1, "theme": theme, "passcode": passcode, "passengers": passengers})

            self.logger.info(f"Successfully generated train with {len(wagons)} wagons")
            return json.dumps(wagons, indent=4)

        except Exception as e:
            self.logger.error(f"Error in generate_train_json: {e}")
            raise ValueError(f"Failed to generate train: {str(e)}")

    def generate_train(self, theme: str, num_wagons: int) -> Tuple[Dict, Dict, Dict]:
        """Main method to generate complete train data"""
        self.logger.info(
            "Starting train generation",
            extra={
                "theme": theme,
                "num_wagons": num_wagons,
                "service": "GenerateTrainService"
            }
        )
        
        try:
            # Log attempt to generate train JSON
            self.logger.debug(
                "Generating train JSON",
                extra={
                    "theme": theme,
                    "num_wagons": num_wagons,
                    "min_passengers": 2,
                    "max_passengers": 10
                }
            )
            
            wagons_json = self.generate_train_json(theme, num_wagons, 2, 10)
            
            # Log successful JSON generation and parse attempt
            self.logger.debug(
                "Train JSON generated, parsing to dict",
                extra={
                    "json_length": len(wagons_json)
                }
            )
            
            wagons = json.loads(wagons_json)
            
            # Log conversion attempt
            self.logger.debug(
                "Converting wagon data to final format",
                extra={
                    "num_wagons": len(wagons)
                }
            )
            
            all_names, all_player_details, all_wagons = convert_and_return_jsons(wagons)
            
            # Log successful generation with summary
            self.logger.info(
                "Train generation completed successfully",
                extra={
                    "theme": theme,
                    "total_wagons": len(all_wagons["wagons"]),
                    "total_names": len(all_names["names"]),
                    "total_player_details": len(all_player_details["player_details"])
                }
            )
            
            return all_names, all_player_details, all_wagons

        except json.JSONDecodeError as e:
            self.logger.error(
                "JSON parsing error in generate_train",
                extra={
                    "error_type": "JSONDecodeError",
                    "error_msg": str(e),
                    "theme": theme,
                    "num_wagons": num_wagons
                }
            )
            raise HTTPException(status_code=500, detail=f"Failed to parse train JSON: {str(e)}")
        
        except Exception as e:
            self.logger.error(
                "Error in generate_train",
                extra={
                    "error_type": type(e).__name__,
                    "error_msg": str(e),
                    "theme": theme,
                    "num_wagons": num_wagons
                }
            )
            raise HTTPException(status_code=500, detail=f"Failed to generate train: {str(e)}")
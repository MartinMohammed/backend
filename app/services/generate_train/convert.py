from typing import Dict, List, Tuple
import random
from app.core.logging import get_logger

logger = get_logger("convert")

def parse_name(full_name):
    """
    Splits the full name into firstName and lastName.
    This is a simple heuristic:
       - lastName is the last token
       - firstName is everything before
    For example:
       "Dr. Amelia Hartford" -> firstName: "Dr. Amelia", lastName: "Hartford"
       "Thomas Maxwell" -> firstName: "Thomas", lastName: "Maxwell"
    Adjust this to your own naming conventions if needed.
    """
    tokens = full_name.strip().split()
    if len(tokens) == 1:
        return full_name, ""  # No clear lastName
    else:
        return " ".join(tokens[:-1]), tokens[-1]

def infer_sex_from_model(model_type):
    """
    A simple inference: if the string 'female' is in model_type, mark sex as 'female';
    if 'male' is in model_type, mark as 'male';
    otherwise, mark as 'unknown' (or handle however you prefer).
    """
    model_type_lower = model_type.lower()
    if 'female' in model_type_lower:
        return 'female'
    elif 'male' in model_type_lower:
        return 'male'
    else:
        return 'unknown'

# triggered for one single wagon 
def convert_wagon_to_three_jsons(wagon_data: Dict) -> Tuple[Dict, Dict, Dict]:
    """
    Given a single wagon JSON structure like:
    {
      "id": 1,
      "theme": "Alien by Ridley Scott",
      "passcode": "Nostromo",
      "passengers": [
        {
          "name": "Dr. Amelia Hartford",
          "age": 47,
          "profession": "Medical Researcher",
          "personality": "Analytical, compassionate, and meticulous",
          "role": "...",
          "mystery_intrigue": "...",
          "characer_model": "character-female-e"
        },
        ...
      ]
    }
    produce:
      1) names_json
      2) player_details_json
      3) wagons_json
    """
    wagon_id = wagon_data.get("id", 0)
    theme = wagon_data.get("theme", "Unknown Theme")
    passcode = wagon_data.get("passcode", "no-passcode")
    passengers = wagon_data.get("passengers", [])

    logger.debug(f"Processing wagon conversion | wagon_id={wagon_id} | theme={theme} | num_passengers={len(passengers)}")

    try:
        # 1) Build the "names" object for this wagon
        names_entry = {
            "wagonId": f"wagon-{wagon_id}",
            "players": []
        }

        # 2) Build the "player_details" object for this wagon
        player_details_entry = {
            "wagonId": f"wagon-{wagon_id}",
            "players": []
        }

        # 3) Build the "wagon" object
        wagon_entry = {
            "id": wagon_id,
            "theme": theme,
            "passcode": passcode,
            "people": []
        }

        # Process each passenger
        for i, passenger in enumerate(passengers, 1):
            logger.debug(f"Converting passenger data | wagon_id={wagon_id} | passenger_index={i} | passenger_name={passenger.get('name', 'Unknown')}")
            
            player_key = f"player-{i}"
            name = passenger.get("name", "")
            
            # Split name into components
            name_parts = name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            # Determine sex based on character model
            model_type = passenger.get("characer_model", "character-male-a")
            sex = "female" if "female" in model_type else "male"

            # Add to names structure
            names_entry["players"].append({
                "playerId": player_key,
                "firstName": first_name,
                "lastName": last_name,
                "sex": sex,
                "fullName": name
            })

            # Add to player_details structure
            profile = {
                "name": name,
                "age": passenger.get("age", 0),
                "profession": passenger.get("profession", ""),
                "personality": passenger.get("personality", ""),
                "role": passenger.get("role", ""),
                "mystery_intrigue": passenger.get("mystery_intrigue", "")
            }
            player_details_entry["players"].append({"playerId": player_key, "profile": profile})

            # Add to wagon people structure
            person_dict = {
                "uid": f"wagon-{wagon_id}-player-{i}",
                "position": [round(random.random(), 2), round(random.random(), 2)],
                "rotation": round(random.random(), 2),
                "model_type": model_type,
                "items": []
            }
            wagon_entry["people"].append(person_dict)

        logger.debug(f"Completed wagon conversion | wagon_id={wagon_id} | players_processed={len(passengers)}")
        return names_entry, player_details_entry, wagon_entry

    except Exception as e:
        logger.error(f"Error converting wagon | wagon_id={wagon_id} | error_type={type(e).__name__} | error_msg={str(e)}")
        raise

def convert_and_return_jsons(wagons_data: List[Dict]) -> Tuple[Dict, Dict, Dict]:
    """Convert raw wagon data into the three required JSON structures"""
    logger.info(f"Starting conversion of wagon data | total_wagons={len(wagons_data)}")
    
    all_names = []
    all_player_details = []
    all_wagons = []

    try:
        for wagon in wagons_data:
            logger.debug(f"Converting wagon | wagon_id={wagon['id']} | theme={wagon['theme']} | num_passengers={len(wagon.get('passengers', []))}")
            
            names, player_details, wagon_entry = convert_wagon_to_three_jsons(wagon)
            
            all_names.append(names)
            all_player_details.append(player_details)
            all_wagons.append(wagon_entry)

        logger.info(f"Successfully converted all wagons | total_names={len(all_names)} | total_player_details={len(all_player_details)} | total_wagons={len(all_wagons)}")
        return all_names, all_player_details, all_wagons

    except Exception as e:
        logger.error(f"Error converting wagon data | error_type={type(e).__name__} | error_msg={str(e)}")
        raise
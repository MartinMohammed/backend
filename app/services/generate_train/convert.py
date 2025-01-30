import random

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

def convert_wagon_to_three_jsons(wagon_data):
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

    # 1) Build the "names" object for this wagon
    #    The final structure should be: {"wagon-N": {"player-1": {...}, "player-2": {...}, ...}}
    names_output = {}
    wagon_key = f"wagon-{wagon_id}"
    names_output[wagon_key] = {}

    # 2) Build the "player_details" object for this wagon
    #    The final structure: {"wagon-N": {"player-1": { "profile": {...}}, "player-2": {"profile": {...}}}}
    player_details_output = {}
    player_details_output[wagon_key] = {}

    # 3) Build the "wagons" array entry for this wagon
    #    Each wagon in the final output is something like:
    #    {
    #      "id": wagon_id,
    #      "theme": "...",
    #      "passcode": "...",
    #      "people": [
    #         {
    #           "uid": "wagon-N-player-i",
    #           "position": [rand, rand],
    #           "rotation": rand,
    #           "model_type": "character-female-e",
    #           "items": []
    #         }, ...
    #       ]
    #    }
    wagon_entry = {
        "id": wagon_id,
        "theme": theme,
        "passcode": passcode,
        "people": []
    }

    # Loop over passengers to fill each part
    for i, passenger in enumerate(passengers, start=1):
        player_key = f"player-{i}"
        full_name = passenger.get("name", "Unknown")
        first_name, last_name = parse_name(full_name)

        model_type = passenger.get("characer_model", "character-unknown")
        sex = infer_sex_from_model(model_type)

        # 1) Fill names
        names_output[wagon_key][player_key] = {
            "firstName": first_name,
            "lastName": last_name,
            "sex": sex,
            "fullName": full_name
        }

        # 2) Fill player_details
        profile_dict = {
            "name": full_name,
            "age": passenger.get("age", 0),
            "profession": passenger.get("profession", ""),
            "personality": passenger.get("personality", ""),
            "role": passenger.get("role", ""),
            "mystery_intrigue": passenger.get("mystery_intrigue", "")
        }
        player_details_output[wagon_key][player_key] = {
            "profile": profile_dict
        }

        # 3) Fill wagons "people"
        #    Random position within [0..1], random rotation in [0..1], items always []
        person_dict = {
            "uid": f"wagon-{wagon_id}-player-{i}",
            "position": [round(random.random(), 2), round(random.random(), 2)],
            "rotation": round(random.random(), 2),
            "model_type": model_type,
            "items": []
        }
        wagon_entry["people"].append(person_dict)

    return names_output, player_details_output, wagon_entry

def convert_and_return_jsons(wagon_data):
    names_result, player_details_result, wagons_entry = {}, {}, []
    for wagon in wagon_data:
        names_output, player_details_output, wagon_entry = convert_wagon_to_three_jsons(wagon)
        names_result.update(names_output)
        player_details_result.update(player_details_output)
        wagons_entry.append(wagon_entry)

    # 1) The 'names' JSON typically might aggregate multiple wagons, so we embed our single wagon's result:
    #    For demonstration, just put it as "names": { ...single wagon data... }
    all_names = {"names": names_result}

    # 2) The 'player_details' JSON also might aggregate multiple wagons
    all_player_details = {"player_details": player_details_result}

    # 3) The 'wagons' JSON is typically an array of wagons. Here, we only have one:
    all_wagons = {
        "wagons": wagons_entry
    }

    return all_names, all_player_details, all_wagons
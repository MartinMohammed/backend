from mistralai import Mistral
import os
import orjson
import time

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")


class ScoringService:
    def __init__(self: "ScoringService"):
        self.client = Mistral(api_key=MISTRAL_API_KEY)
        self.model = "mistral-small-2409"
        self.max_retries = 3

    def is_similar(
        self: "ScoringService", password: str, guess: str, theme: str
    ) -> bool:
        messages = [
            {
                "role": "system",
                "content": """
                Return a similarity score between the two given words, relatively to a theme. Return the score in the range [0, 1] in a JSON format with the key 'score'
                """,
            },
            {
                "role": "user",
                "content": f"Answer: {password}\nGuess: {guess}\nTheme: {theme}",
            },
        ]

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.complete(
                    model=self.model,
                    messages=messages,
                    temperature=0.0,
                    response_format={
                        "type": "json_object",
                    },
                )

                # Parse the response with orjson
                parsed_response = orjson.loads(response.choices[0].message.content)
                return parsed_response["score"]
            except orjson.JSONDecodeError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                else:
                    raise e

        return 0.5

import os
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from app.models.session import Message
from app.prompts import GUESSING_PROMPT

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")


class GuessResponse(BaseModel):
    guess: str = Field(description="A one-word guess for the password related theme")
    thoughts: list[str] = Field(
        title="Thoughts spoken out loud leading to the password guess"
    )


class GuessingService:
    def __init__(self: "GuessingService") -> None:
        prompt = PromptTemplate.from_template(GUESSING_PROMPT)

        llm = (
            ChatMistralAI(
                model_name="ministral-8b-latest",
                temperature=1,
            )
            .with_structured_output(schema=GuessResponse)
            .with_retry(stop_after_attempt=3)
        )

        self.chain = prompt | llm

    def generate(
        self: "GuessingService",
        previous_guesses: list[str],
        theme: str,
        previous_indications: list[Message],
        current_indication: str,
    ) -> GuessResponse:
        previous_indications = [message.content for message in previous_indications]

        return self.chain.invoke(
            {
                "previous_guesses": previous_guesses[:3],
                "theme": theme,
                "previous_indications": previous_indications[:5],
                "current_indication": current_indication,
            }
        )

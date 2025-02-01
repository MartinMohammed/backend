import os
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from app.models.session import Message
from app.core.logging import LoggerMixin
from app.prompts import GUESSING_PROMPT

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")


class GuessResponse(BaseModel):
    guess: str = Field(description="A one-word guess for the password related theme")
    thoughts: str = Field(
        description="Thoughts spoken out loud leading to the password guess"
    )


class GuessingService(LoggerMixin):
    def __init__(self: "GuessingService") -> None:
        self.logger.info("Initializing GuessingService")
        prompt = PromptTemplate.from_template(GUESSING_PROMPT)

        llm = (
            ChatMistralAI(
                model_name="mistral-large-latest",
                temperature=1,
            )
            .with_structured_output(schema=GuessResponse)
            .with_retry(stop_after_attempt=3)
        )

        self.chain = prompt | llm
        self.logger.info("GuessingService initialized with Mistral LLM")

    def filter_password(self: "GuessingService", indication: str, password: str) -> str:
        filtered = indication.replace(password, "*******")
        self.logger.debug(f"Filtered password from indication | original_length={len(indication)} | filtered_length={len(filtered)}")
        return filtered

    def generate(
        self: "GuessingService",
        previous_guesses: list[str],
        theme: str,
        previous_indications: list[Message],
        current_indication: str,
        password: str,
    ) -> GuessResponse:
        self.logger.info(f"Generating guess | theme={theme} | num_previous_guesses={len(previous_guesses)} | num_previous_indications={len(previous_indications)}")
        
        previous_indications = [message.content for message in previous_indications]
        self.logger.debug(f"Processing previous indications | count={len(previous_indications)}")

        current_indication = self.filter_password(current_indication, password)
        
        try:
            response = self.chain.invoke(
                {
                    "previous_guesses": previous_guesses[:3],
                    "theme": theme,
                    "previous_indications": previous_indications[:5],
                    "current_indication": current_indication,
                }
            )
            self.logger.info(f"Generated guess successfully | guess={response.guess} | thoughts_length={len(response.thoughts)}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to generate guess | error={str(e)} | theme={theme}")
            raise

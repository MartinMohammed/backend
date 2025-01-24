from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

from neuraljam.model import State

history_session: dict[str, list[any]] = {}

knowledge_session: dict[str, list[str]] = {}

llm = ChatMistralAI(
    model="mistral-large-latest",
)


def generate_response(state: State) -> dict[str, any]:
    if state.user_id not in knowledge_session.keys():
        knowledge_session[state.user_id] = []

    if state.conversation_id not in history_session.keys():
        history_session[state.conversation_id] = []

    prompt_template = ChatPromptTemplate(
        [
            ("system", ""),
            ("user", ""),
        ]
    )

    # TODO: CREATE A PROMPT TEMPLATE FOR THE SYSTEM
    prompt = prompt_template.invoke()
    response = llm.generate(prompt)

    history_session[state.conversation_id].extend(
        [HumanMessage(content=state.question), AIMessage(content=response.content)]
    )

    return {"response": response}


def update_knowledge(state: State) -> dict[str, any]:
    pass


def provide_hint(state: State) -> dict[str, any]:
    if state.status == "OPEN":
        pass

    return state

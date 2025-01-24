from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from typing import Literal

load_dotenv()

# { 
#     "knownledge": []
#     "history": { id : list[] }
# }


Message = HumanMessage | SystemMessage | AIMessage

history_session : dict[str, list[Message]]= {}

knowledge_session : dict[str, list[str]]= {} 

llm = ChatMistralAI(
    model="mistral-large-latest",
) 

class State(TypeDict):
    question: str
    user_id: str
    conversation_id: str
    response: str
    hint: str
    status: Literal["OPEN", "CLOSED"]

graph_builder = StateGraph(State)


SYSTEM_PROMPT_GENERATE = """
Instructions:

History:
{history}

Knowledge:
{knowledge}
"""

USER_PROMPT_GENERATE = """
{question}
"""

SYSTEM_PROMPT_KNOWLEDGE = """
Instructions:
""" 

USER_PROMPT_KNOWLEDGE = """
{history}
"""

SYSTEM_PROMPT_HINT = """
Instructions:
{history}


"""

USER_PROMPT_HINT = """
"""


def generate(state: State): 
    prompt_template = ChatPromptTemplate([
        ("system", SYSTEM_PROMPT_GENERATE),

        ("user", USER_PROMPT_GENERATE)
    ])

    message = llm.generate(prompt_template, {"history": state.history, "knowledge": state.
    knowledge, "question": state.question})

    if not state.user_id in knowledge_session.keys():
        knowledge_session[state.user_id] = []

    if not state.conversation_id in history_session.keys():
        history_session[state.conversation_id] = []


    return state

def knowledge(state: State):
    prompt_template = ChatPromptTemplate([
        ("system", SYSTEM_PROMPT_GENERATE),
        ("user", USER_PROMPT_GENERATE)
    ])

    return state

def hint(state: State):
    if state.status == "OPEN":
        prompt_template = ChatPromptTemplate([
            ("system", SYSTEM_PROMPT_HINT),
            ("user", USER_PROMPT_HINT)
        ])


    return state

graph_builder.add_node(START)
graph_builder.add_node("generate", generate)
graph_builder.add_node("knowledge", knowledge)
graph_builder.add_node("hint", hint)
graph_builder.add_node(END)

graph_builder.add_edge(START, "generate")
graph_builder.add_edge("generate", "knowledge")
graph_builder.add_edge("knowledge", "hint")
graph_builder.add_edge("hint", END)

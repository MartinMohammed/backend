from langgraph.graph import StateGraph, START, END

from dotenv import load_dotenv
from neuraljam.model import State
from neuraljam.service import generate_response, update_knowledge, provide_hint
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles

if __name__ == "__main__":
    load_dotenv()

    graph_builder = StateGraph(State)

    graph_builder.add_node("generate_response", generate_response)
    graph_builder.add_node("update_knowledge", update_knowledge)
    graph_builder.add_node("provide_hint", provide_hint)

    graph_builder.add_edge(START, "generate_response")
    graph_builder.add_edge("generate_response", "update_knowledge")
    graph_builder.add_edge("update_knowledge", "provide_hint")
    graph_builder.add_edge("provide_hint", END)

    app = graph_builder.compile()

    print(
        app.get_graph().draw_mermaid()
    )

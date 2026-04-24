"""LangGraph agent graph definition."""
from langgraph.graph import END, StateGraph

from core.agent.nodes import llm_node
from core.agent.state import AgentState


def build_agent_graph():
    """Build and return the compiled LangGraph agent graph."""
    graph = StateGraph(AgentState)

    graph.add_node("llm", llm_node)
    graph.set_entry_point("llm")
    graph.add_edge("llm", END)

    return graph.compile()


# Module-level compiled graph — built once on import.
agent_graph = build_agent_graph()

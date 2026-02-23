from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.state import AgentState
from src.nodes import (
    scope_decomposition_node, dependency_mapping_node, 
    smart_scheduler_node, resource_allocation_node, 
    risk_audit_node, optimization_insight_node
)

def routing_logic(state: AgentState):
    # Stop if max iterations reached or risk score is low (< 15)
    last_score = state['project_risk_score_iterations'][-1]
    if state["iteration_number"] >= state["max_iteration"] or last_score < 15:
        return END
    return "optimizer"

def build_graph():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("scoper", scope_decomposition_node)
    workflow.add_node("mapper", dependency_mapping_node)
    workflow.add_node("scheduler", smart_scheduler_node)
    workflow.add_node("allocator", resource_allocation_node)
    workflow.add_node("auditor", risk_audit_node)
    workflow.add_node("optimizer", optimization_insight_node)

    # Add Edges
    workflow.set_entry_point("scoper")
    workflow.add_edge("scoper", "mapper")
    workflow.add_edge("mapper", "scheduler")
    workflow.add_edge("scheduler", "allocator")
    workflow.add_edge("allocator", "auditor")
    workflow.add_conditional_edges("auditor", routing_logic)
    workflow.add_edge("optimizer", "scheduler")

    return workflow.compile(checkpointer=MemorySaver())

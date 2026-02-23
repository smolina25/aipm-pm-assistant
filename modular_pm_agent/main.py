from src.models import Team, TeamMember
from src.graph import build_graph
from src.visualization import visualize_results

def main():
    # 1. Define Team
    my_team = Team(team_members=[
        TeamMember(name="Alice", role="Lead Dev", skills=["Python", "LangGraph", "Architecture"], seniority="Senior"),
        TeamMember(name="Bob", role="Frontend", skills=["React", "UI/UX"], seniority="Mid"),
        TeamMember(name="Charlie", role="QA", skills=["Testing", "Python"], seniority="Junior")
    ])

    # 2. Define Initial State
    init_state = {
        "project_description": "Create a secure, multi-user AI dashboard using LangGraph and React.",
        "team": my_team,
        "iteration_number": 0,
        "max_iteration": 2,
        "insights": [],
        "project_risk_score_iterations": []
    }

    # 3. Build & Run
    print("Initializing Workflow...")
    graph = build_graph()
    
    print("Running Agent...")
    final_state = graph.invoke(init_state, {"configurable": {"thread_id": "prod_v1"}})
    
    print("Workflow Finished!")
    
    # 4. Report
    visualize_results(final_state)

if __name__ == "__main__":
    main()

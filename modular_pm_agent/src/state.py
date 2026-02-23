from typing import TypedDict, List
from src.models import Team, TaskList, Schedule, TaskAllocationList, RiskList

class AgentState(TypedDict):
    project_description: str
    team: Team
    tasks: TaskList
    dependencies: List[dict]
    schedule: Schedule
    task_allocations: TaskAllocationList
    risks: RiskList
    iteration_number: int
    max_iteration: int
    insights: List[str]
    project_risk_score_iterations: List[int]

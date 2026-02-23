from typing import List, Optional, Any, Annotated
from pydantic import BaseModel, Field, AliasChoices, BeforeValidator, model_validator


# --- Helpers ---
def force_string(v):
    return str(v) if v is not None else None


def list_to_string(v):
    """
    Robustly handles skills whether they come as a string "Python"
    or a list ["Python", "LangGraph"].
    """
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    return str(v) if v is not None else "General"


StringId = Annotated[Optional[str], BeforeValidator(force_string)]
FlexibleString = Annotated[str, BeforeValidator(list_to_string)]


# --- Base Entities ---
class Task(BaseModel):
    id: StringId = None
    # Handles snake_case, camelCase, PascalCase, and variations
    task_name: str = Field(
        ...,
        validation_alias=AliasChoices(
            "title", "name", "task_name", "task", "taskName", "TaskName", "Name"
        ),
    )
    task_description: str = Field(
        default="",
        validation_alias=AliasChoices(
            "description", "task_description", "desc", "taskDescription", "Description"
        ),
    )
    estimated_day: int = Field(
        ...,
        validation_alias=AliasChoices(
            "duration_days",
            "estimated_days",
            "estimated_day",
            "duration",
            "time",
            "estimatedDay",
            "EstimatedDay",
        ),
    )

    # FIX: FlexibleString handles the List[str] error from Scoper
    required_skill: FlexibleString = Field(
        default="General",
        validation_alias=AliasChoices(
            "required_skill",
            "skill",
            "skills",
            "required_skills",
            "requiredSkills",
            "requiredSkill",
            "RequiredSkill",
        ),
    )


class TeamMember(BaseModel):
    name: str
    role: str
    skills: List[str]
    seniority: str


class Team(BaseModel):
    team_members: List[TeamMember]


# --- Workflow Containers ---


class TaskList(BaseModel):
    task: List[Task] = Field(..., validation_alias=AliasChoices("tasks", "task"))

    @model_validator(mode="before")
    @classmethod
    def wrap(cls, data: Any) -> Any:
        target = data
        if isinstance(data, dict):
            # Check for common wrapper keys including class name
            for key in ["tasks", "task", "items", "TaskList", "task_list"]:
                if key in data:
                    target = data[key]
                    break

        if isinstance(target, list):
            return {"task": target}
        return data


class Dependency(BaseModel):
    # FIX: Added 'ID' (PascalCase) alias
    task_id: str = Field(
        ...,
        validation_alias=AliasChoices(
            "task_id", "id", "task", "taskId", "ID", "TaskID"
        ),
    )
    # FIX: Added 'Dependencies' (PascalCase) alias
    dependent_on: List[str] = Field(
        ...,
        validation_alias=AliasChoices(
            "dependent_on",
            "dependencies",
            "deps",
            "depends_on",
            "dependsOn",
            "Dependencies",
            "DependsOn",
        ),
    )


class DependencyList(BaseModel):
    dependencies: List[Dependency] = Field(
        ..., validation_alias=AliasChoices("dependencies", "deps", "DependencyList")
    )

    @model_validator(mode="before")
    @classmethod
    def wrap(cls, data: Any) -> Any:
        target = data
        if isinstance(data, dict):
            # Check for common wrapper keys including class name "DependencyList"
            for key in [
                "dependencies",
                "deps",
                "items",
                "DependencyList",
                "dependency_list",
            ]:
                if key in data:
                    target = data[key]
                    break

        # Handle Map format {"A": ["B"]} -> [{"task_id": "A", "dependent_on": ["B"]}]
        if isinstance(target, dict):
            return {
                "dependencies": [
                    {"task_id": k, "dependent_on": v} for k, v in target.items()
                ]
            }

        if isinstance(target, list):
            return {"dependencies": target}

        return data


class TaskSchedule(BaseModel):
    task: Task
    start_day: int
    end_day: int


class Schedule(BaseModel):
    schedule: List[TaskSchedule]


class TaskAllocation(BaseModel):
    task: Task
    team_member: TeamMember


class TaskAllocationList(BaseModel):
    task_allocations: List[TaskAllocation]

    @model_validator(mode="before")
    @classmethod
    def wrap(cls, data: Any) -> Any:
        target = data
        if isinstance(data, dict):
            for key in [
                "task_allocations",
                "allocs",
                "allocations",
                "TaskAllocationList",
            ]:
                if key in data:
                    target = data[key]
                    break

        # Handle Map format {"Task1": "Alice"}
        if isinstance(target, dict):
            return {
                "task_allocations": [
                    {"task_id": k, "member_name": v} for k, v in target.items()
                ]
            }

        if isinstance(target, list):
            return {"task_allocations": target}
        return data


class Risk(BaseModel):
    task_name: str = Field(
        ...,
        validation_alias=AliasChoices(
            "task_name", "task", "name", "taskName", "risk_id", "id", "TaskName", "ID"
        ),
    )
    score: int = Field(
        ..., validation_alias=AliasChoices("score", "risk_score", "riskScore", "Score")
    )
    reason: str = Field(
        ...,
        validation_alias=AliasChoices(
            "reason", "description", "riskReason", "Reason", "Description"
        ),
    )


class RiskList(BaseModel):
    risks: List[Risk]

    @model_validator(mode="before")
    @classmethod
    def wrap(cls, data: Any) -> Any:
        target = data
        if isinstance(data, dict):
            for key in ["risks", "RiskList", "Risks"]:
                if key in data:
                    target = data[key]
                    break

        if isinstance(target, list):
            return {"risks": target}
        return data

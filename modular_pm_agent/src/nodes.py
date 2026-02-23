import uuid
from typing import List, Any, Optional, Annotated
from pydantic import BaseModel, Field, AliasChoices, model_validator, BeforeValidator
from src.config import llm
from src.models import (
    TaskList,
    DependencyList,
    Schedule,
    TaskSchedule,
    TaskAllocation,
    TaskAllocationList,
    Risk,
    RiskList,
)
from src.state import AgentState


# --- Helper: Universal Data Wrapper ---
def standardize_to_list(data: Any, key_alias="id") -> List[dict]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        converted = []
        for k, v in data.items():
            if isinstance(v, dict):
                new_item = {key_alias: k}
                new_item.update(v)
                converted.append(new_item)
        return converted
    return []


# --- Helper: Int Validator ---
def force_int(v):
    if v is None:
        return -1
    try:
        return int(v)
    except (ValueError, TypeError):
        return -1


SafeInt = Annotated[int, BeforeValidator(force_int)]


# --- 1. Scoper ---
def scope_decomposition_node(state: AgentState):
    print("--- Node: Scoper ---")
    prompt = f"""
    Project: {state['project_description']}
    Team Skills: {[m.skills for m in state['team'].team_members]}
    
    DECOMPOSITION RULES:
    1. Break the project into **AT LEAST 10-15 granular tasks**.
    2. No task should exceed 3 days. If a task is longer, break it down further.
    3. Include specific tasks for: Setup, Database, API, Frontend Components, Testing, Security, and Deployment.
    4. REQUIRED JSON FIELDS: 'task_name', 'task_description', 'estimated_day', 'required_skill'.
    
    Return a comprehensive JSON list.
    """
    struct_llm = llm.with_structured_output(TaskList, method="json_mode")
    response = struct_llm.invoke(prompt)

    for t in response.task:
        if not t.id:
            t.id = str(uuid.uuid4())[:4]

    print(f"Generated {len(response.task)} tasks.")
    return {"tasks": response}


# --- 2. Mapper ---
def dependency_mapping_node(state: AgentState):
    print("--- Node: Mapper ---")
    tasks_fmt = "\n".join(
        [f"ID: {t.id} | Name: {t.task_name}" for t in state["tasks"].task]
    )
    prompt = f"Map dependencies for:\n{tasks_fmt}\nReturn JSON matching DependencyList. Use IDs."
    struct_llm = llm.with_structured_output(DependencyList, method="json_mode")
    response = struct_llm.invoke(prompt)
    return {"dependencies": response.dependencies}


# --- 3. Scheduler ---
def smart_scheduler_node(state: AgentState):
    print("--- Node: Scheduler ---")

    class SimpleSchedItem(BaseModel):
        task_id: str = Field(
            ..., validation_alias=AliasChoices("task_id", "id", "task_name")
        )
        start: SafeInt = Field(..., validation_alias=AliasChoices("start", "start_day"))
        end: SafeInt = Field(..., validation_alias=AliasChoices("end", "end_day"))

    class SimpleSched(BaseModel):
        items: List[SimpleSchedItem]

        @model_validator(mode="before")
        @classmethod
        def wrap(cls, data):
            target = data
            if isinstance(data, dict):
                for key in ["tasks", "schedule", "items", "timeline", "task_schedules"]:
                    if key in data:
                        target = data[key]
                        break
            if isinstance(target, dict):
                return {"items": standardize_to_list(target, key_alias="task_id")}
            if isinstance(target, list):
                return {"items": target}
            return data

    prompt = f"""
    Schedule tasks: {state['tasks']}
    Dependencies: {state.get('dependencies')}
    
    CRITICAL INSTRUCTIONS: 
    1. Return JSON with start/end days (integers).
    2. If circular dependency detected, BREAK THE LOOP and assign best guess integer.
    3. DO NOT return null. Start day must be an integer (0, 1, 2...).
    """
    struct_llm = llm.with_structured_output(SimpleSched, method="json_mode")
    resp = struct_llm.invoke(prompt)

    task_map = {t.id: t for t in state["tasks"].task}
    task_map.update({t.task_name: t for t in state["tasks"].task})

    final_sched = []
    for item in resp.items:
        task = task_map.get(str(item.task_id))
        if task:
            s = item.start if item.start >= 0 else 0
            e = item.end if item.end >= 0 else s + 1
            final_sched.append(TaskSchedule(task=task, start_day=s, end_day=e))

    return {"schedule": Schedule(schedule=final_sched)}


# --- 4. Allocator ---
def resource_allocation_node(state: AgentState):
    print("--- Node: Allocator ---")

    class SimpleAllocItem(BaseModel):
        task_id: str = Field(..., validation_alias=AliasChoices("task_id", "task_name"))
        member_name: str = Field(
            ...,
            validation_alias=AliasChoices(
                "member_name",
                "assignee",
                "allocated_to",
                "team_member",
                "assigned_to",
                "team_member_name",
            ),
        )

    class SimpleAlloc(BaseModel):
        allocs: List[SimpleAllocItem]

        @model_validator(mode="before")
        @classmethod
        def wrap(cls, data):
            target = data
            # 1. Unwrap known keys
            if isinstance(data, dict):
                for key in [
                    "allocations",
                    "allocs",
                    "assignments",
                    "task_allocation",
                    "task_allocations",
                    "team",
                ]:
                    if key in data:
                        target = data[key]
                        break

            # 2. Handle Dict/Map formats
            if isinstance(target, dict):
                # FIX: Check for "Person-Centric" grouping: {"Alice": [{"task_id": "1"}, ...]}
                # Detect if values are Lists
                first_val = next(iter(target.values()), None)
                if isinstance(first_val, list):
                    flattened = []
                    for member, tasks in target.items():
                        if isinstance(tasks, list):
                            for t in tasks:
                                # Extract task_id from the nested dict
                                t_id = t.get("task_id") or t.get("id") or t.get("task")
                                if t_id:
                                    flattened.append(
                                        {"task_id": t_id, "member_name": member}
                                    )
                    if flattened:
                        return {"allocs": flattened}

                # Case: Simple Map { "Task1": "Alice" }
                if all(isinstance(v, str) for v in target.values()):
                    return {
                        "allocs": [
                            {"task_id": k, "member_name": v} for k, v in target.items()
                        ]
                    }

                # Case: Nested Object Map { "Task1": {"assignee": "Alice"} }
                return {"allocs": standardize_to_list(target, key_alias="task_id")}

            if isinstance(target, list):
                return {"allocs": target}
            return data

    prompt = f"Allocate tasks: {state['tasks']} to Team: {state['team']}. IMPORTANT: Return JSON."
    struct_llm = llm.with_structured_output(SimpleAlloc, method="json_mode")
    resp = struct_llm.invoke(prompt)

    task_map = {t.id: t for t in state["tasks"].task}
    task_map.update({t.task_name: t for t in state["tasks"].task})
    member_map = {m.name: m for m in state["team"].team_members}

    final_allocs = []
    for a in resp.allocs:
        task = task_map.get(str(a.task_id))
        member = member_map.get(a.member_name)
        if task and member:
            final_allocs.append(TaskAllocation(task=task, team_member=member))

    return {"task_allocations": TaskAllocationList(task_allocations=final_allocs)}


# --- 5. Auditor ---
def risk_audit_node(state: AgentState):
    print("--- Node: Auditor ---")

    def repair_risk_item(item: Any) -> Any:
        if isinstance(item, dict):
            if "task_name" not in item:
                if "id" in item:
                    item["task_name"] = str(item["id"])
                elif "risk_id" in item:
                    item["task_name"] = str(item["risk_id"])
            if "score" not in item and "impact" in item:
                impact_map = {"High": 8, "Medium": 5, "Low": 2}
                item["score"] = impact_map.get(item["impact"], 5)
            if "score" not in item:
                item["score"] = 5
            if "reason" not in item:
                item["reason"] = item.get("description", "No reason")
        return item

    class SimpleRisk(BaseModel):
        task_name: str = Field(
            ...,
            validation_alias=AliasChoices("task_name", "task", "name", "risk_id", "id"),
        )
        score: SafeInt = Field(
            ..., validation_alias=AliasChoices("score", "risk_score")
        )
        reason: str = Field(..., validation_alias=AliasChoices("reason", "description"))

        @model_validator(mode="before")
        @classmethod
        def fix(cls, data):
            return repair_risk_item(data)

    class SimpleRiskList(BaseModel):
        risks: List[SimpleRisk]

        @model_validator(mode="before")
        @classmethod
        def wrap(cls, data):
            target = data
            if isinstance(data, dict):
                for key in ["risks", "issues", "threats", "audit"]:
                    if key in data:
                        target = data[key]
                        break
            if isinstance(target, dict):
                return {"risks": standardize_to_list(target, key_alias="task_name")}
            if isinstance(target, list):
                return {"risks": target}
            return data

    prompt = f"Audit Plan. Schedule: {state.get('schedule')}, Allocations: {state.get('task_allocations')}. Return JSON risk list."
    struct_llm = llm.with_structured_output(SimpleRiskList, method="json_mode")
    resp = struct_llm.invoke(prompt)

    final_risks = [
        Risk(task_name=r.task_name, score=r.score, reason=r.reason) for r in resp.risks
    ]
    score = sum(r.score for r in final_risks)

    return {
        "risks": RiskList(risks=final_risks),
        "project_risk_score_iterations": state.get("project_risk_score_iterations", [])
        + [score],
        "iteration_number": state.get("iteration_number", 0) + 1,
    }


# --- 6. Optimizer ---
def optimization_insight_node(state: AgentState):
    print("--- Node: Optimizer ---")
    prompt = f"Risks: {state['risks']}. Suggest 1 concrete change to lower risk."
    insight = llm.invoke(prompt).content
    return {"insights": state.get("insights", []) + [insight]}

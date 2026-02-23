## AI Project Manager Agent

This repository contains an autonomous AI Agent designed to plan, schedule, and allocate resources for software projects. It uses **LangGraph** for orchestration and **Groq (Llama 3)** as the LLM engine.

### **Repository Structure**

- **`modular_pm_agent/`**: Contains the main application logic.
  - `main.py`: Entry point to run the agent.
  - `src/`: Source code for nodes, models, state, and visualization.
- **`1_PM_assistant_v2_Llama.ipynb`**: Interactive notebook for testing and development.
- **`requirements.txt`**: List of dependencies.

### **Prerequisites**

You need a **Groq API Key** to run the agent.
1. Get a free key from [Groq](https://console.groq.com/keys).
2. Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=""
   ```

### **Installation**

**`macOS` / `Linux`**
```bash
# Set up Python environment
pyenv local 3.11.3
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**`Windows` (PowerShell)**
```powershell
# Set up Python environment
pyenv local 3.11.3
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### **Usage**

To run the full autonomous agent:

```bash
python modular_pm_agent/main.py
```

The agent will:
1. **Scope:** Break down the project into granular tasks (Scoper Node).
2. **Map:** Identify dependencies between tasks (Mapper Node).
3. **Schedule:** Create a timeline and handle circular dependencies (Scheduler Node).
4. **Allocate:** Assign tasks to team members based on skills (Allocator Node).
5. **Audit:** Assess project risks (Auditor Node).
6. **Visualize:** Generate an interactive **Gantt Chart**.

**Output:**
After a successful run, open the generated HTML file to see the schedule:
```bash
open project_schedule.html  # macOS
# OR double-click the file in Explorer/Finder
```

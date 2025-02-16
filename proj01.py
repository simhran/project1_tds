import os
import re
import json
import subprocess
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import FileResponse

# Constants
DATA_DIR = "/data"
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://aiproxy.sanand.workers.dev/openai/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI()

class TaskRequest(BaseModel):
    task: str

def generate_prompt(task: str) -> str:
    """Create a structured prompt for the LLM."""
    return f"""
    You are an automation agent. Your goal is to generate and execute Python code to complete the given task. 
    Task: {task}
    Ensure the output is saved in a relevant file inside the /data directory.
    Provide only executable Python code in your response.
    """

def get_code_from_llm(task: str) -> str:
    """Query the GPT-4o-mini model to generate executable Python code."""
    prompt = generate_prompt(task)
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
    
    response = requests.post(f"{OPENAI_API_BASE}/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return None

def execute_code(code: str) -> str:
    """Execute dynamically generated Python code."""
    exec_globals = {}
    try:
        exec(code, exec_globals)
    except Exception as e:
        return str(e)
    return "Execution completed."

def download_and_run_script(url: str, args: list) -> str:
    """Download and execute an external script."""
    script_path = os.path.join(DATA_DIR, "script.py")
    response = requests.get(url)
    if response.status_code == 200:
        with open(script_path, "w") as file:
            file.write(response.text)
        try:
            subprocess.run(["python", script_path] + args, check=True)
            return "Script executed successfully."
        except subprocess.CalledProcessError as e:
            return str(e)
    return "Failed to download script."

@app.post("/run")
async def run_task(request: TaskRequest):
    task = request.task
    if not task:
        raise HTTPException(status_code=400, detail="No task provided.")
    
    if task.startswith("http"):
        match = re.search(r"(https?://\\S+) with \\$(\\w+)", task)
        if match:
            url, arg = match.groups()
            return {"message": download_and_run_script(url, [arg])}
        raise HTTPException(status_code=400, detail="Invalid script task format.")
    
    code = get_code_from_llm(task)
    if code:
        result = execute_code(code)
        return {"message": result}
    raise HTTPException(status_code=500, detail="Failed to generate code.")

@app.get("/read")
async def read_file(path: str):
    if not path or not path.startswith(DATA_DIR):
        raise HTTPException(status_code=400, detail="Invalid file path.")
    
    try:
        return FileResponse(path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

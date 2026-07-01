#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

# Configuration
LITELLM_URL = os.environ.get("LITELLM_URL", "http://localhost:4000/v1/chat/completions")
LITELLM_MASTER_KEY = os.environ.get("LITELLM_MASTER_KEY", "")
LITELLM_MODEL = os.environ.get("LITELLM_MODEL", "gemini-flash")

def do_chat(messages):
    payload = {
        "model": LITELLM_MODEL,
        "messages": messages,
        "temperature": 0.2
    }
    json_data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(LITELLM_URL, method="POST", data=json_data)
    req.add_header("Content-Type", "application/json")
    if LITELLM_MASTER_KEY:
        req.add_header("Authorization", f"Bearer {LITELLM_MASTER_KEY}")

    try:
        with urllib.request.urlopen(req) as response:
            response_body = response.read().decode("utf-8")
            resp_json = json.loads(response_body)

            if "choices" in resp_json and len(resp_json["choices"]) > 0:
                return resp_json["choices"][0]["message"]["content"], None
            else:
                return None, Exception("No response from LLM.")

    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')
        return None, Exception(f"API Error (status {e.code}): {err_body}")
    except Exception as e:
        return None, Exception(f"Unexpected Error: {e}")

def run_command(command: str) -> str:
    """Executes a shell command locally on the device safely."""
    console.print(f"[bold yellow]Executing command:[/bold yellow] {command}")
    try:
        # Prevent executing dangerous commands
        blacklist = ["rm -rf /", "mkfs", "dd ", "shutdown", "reboot"]
        if any(item in command for item in blacklist):
            return "Error: Command contains blacklisted patterns for safety."
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout
        if result.stderr:
            output += f"\nStderr:\n{result.stderr}"
        return output if output else "[No output returned]"
    except subprocess.TimeoutExpired:
        return "Error: Command execution timed out after 30 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"

def read_file(filepath: str) -> str:
    """Reads content from a local file."""
    console.print(f"[bold yellow]Reading file:[/bold yellow] {filepath}")
    try:
        if not os.path.exists(filepath):
            return f"Error: File '{filepath}' does not exist."
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(filepath: str, content: str) -> str:
    """Writes content to a local file."""
    console.print(f"[bold yellow]Writing file:[/bold yellow] {filepath}")
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        return f"Success: File successfully written to {filepath}."
    except Exception as e:
        return f"Error writing file: {str(e)}"

# Register available tools
TOOLS = {
    "run_command": run_command,
    "read_file": read_file,
    "write_file": write_file
}

SYSTEM_PROMPT = """You are an autonomous AI edge worker running locally on a secure iPhone 8 node.
Your objective is to complete the user's task using the tools provided to inspect the system, manage files, and execute shell commands.

You have access to the following tools:
1. run_command: Run a local shell command safely.
2. read_file: Read the content of a local file.
3. write_file: Write or overwrite content to a local file.

To call a tool, output a JSON block matching this structure:
```json
{
  "tool": "run_command",
  "arguments": {
    "command": "uname -a"
  }
}
```

Wait for the result after calling a tool. Do not call multiple tools in a single response.
Once the task is fully accomplished, write your final summary prefixed with "FINAL ANSWER:".
Always explain what you are doing in your reasoning step before executing tools.
"""

def run_agent(task: str):
    console.print(Panel(
        Text(f"Target Objective:\n{task}", style="bold cyan"),
        title="[bold green]Secure Edge Agent Started[/bold green]",
        border_style="cyan"
    ))

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Task: {task}"}
    ]

    max_steps = 10
    for step in range(max_steps):
        console.print(f"\n[bold magenta]=== Step {step + 1} of {max_steps} ===[/bold magenta]")
        
        try:
            # Query the model
            ai_response, err = do_chat(messages)
            if err:
                raise err
            console.print(f"[bold green]Agent Thoughts/Output:[/bold green]\n{ai_response}")
            messages.append({"role": "assistant", "content": ai_response})

            # Check if finalized
            if "FINAL ANSWER:" in ai_response:
                console.print("\n[bold green]Task complete![/bold green]")
                break

            # Try to parse tool call from JSON blocks
            tool_call_found = False
            if "```json" in ai_response:
                try:
                    # Extract JSON content
                    parts = ai_response.split("```json")
                    json_str = parts[1].split("```")[0].strip()
                    tool_data = json.loads(json_str)
                    
                    tool_name = tool_data.get("tool")
                    args = tool_data.get("arguments", {})
                    
                    if tool_name in TOOLS:
                        tool_call_found = True
                        # Run tool
                        if tool_name == "run_command":
                            tool_result = TOOLS[tool_name](args.get("command"))
                        elif tool_name == "read_file":
                            tool_result = TOOLS[tool_name](args.get("filepath"))
                        elif tool_name == "write_file":
                            tool_result = TOOLS[tool_name](args.get("filepath"), args.get("content"))
                        
                        console.print(f"[bold blue]Tool Output:[/bold blue]\n{tool_result}")
                        messages.append({"role": "user", "content": f"Tool Result:\n{tool_result}"})
                    else:
                        error_msg = f"Error: Tool '{tool_name}' is not recognized."
                        console.print(f"[bold red]{error_msg}[/bold red]")
                        messages.append({"role": "user", "content": error_msg})
                        tool_call_found = True
                except Exception as e:
                    error_msg = f"Error parsing tool call JSON: {e}"
                    console.print(f"[bold red]{error_msg}[/bold red]")
                    messages.append({"role": "user", "content": error_msg})
                    tool_call_found = True

            if not tool_call_found:
                # If no tool call and no FINAL ANSWER, ask for clarification or next steps
                messages.append({"role": "user", "content": "Please proceed to execute the task or output FINAL ANSWER if done."})

        except Exception as e:
            console.print(f"[bold red]Error in agent loop:[/bold red] {e}")
            break
    else:
        console.print("[bold red]Maximum step limit reached before achieving final answer.[/bold red]")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[bold yellow]Usage:[/bold yellow] python3 edge_agent.py \"<task description>\"")
        sys.exit(1)
    
    target_task = sys.argv[1]
    run_agent(target_task)

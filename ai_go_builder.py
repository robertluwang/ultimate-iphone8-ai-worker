#!/usr/bin/env python3
import os
import sys
import subprocess
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.status import Status

console = Console()

# Configuration
API_BASE = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE") or "http://127.0.0.1:4000/v1"
API_KEY = os.getenv("OPENAI_API_KEY") or "fake-key-for-gateway"
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME") or os.getenv("OPENAI_MODEL") or "gemini-flash"

try:
    client = OpenAI(base_url=API_BASE, api_key=API_KEY)
except Exception as e:
    console.print(f"[bold red]Error initializing client:[/bold red] {e}")
    sys.exit(1)

def generate_go_code(prompt: str) -> str:
    console.print(f"[bold yellow]-> Asking Gemini to code:[/bold yellow] {prompt}...")
    sys_prompt = "You are an expert Go developer. Write a single main.go file to run on darwin/arm64. Output ONLY the ```go code block."
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        console.print(f"[bold red]AI Generation failed:[/bold red] {e}")
        sys.exit(1)

def build_go(llm_output: str, name: str):
    os.makedirs(name, exist_ok=True)
    
    try:
        # Extract Go code block
        if "```go" in llm_output:
            code = llm_output.split("```go")[1].split("```")[0].strip()
        elif "```" in llm_output:
            code = llm_output.split("```")[1].split("```")[0].strip()
        else:
            code = llm_output.strip()
            
        file_path = f"{name}/main.go"
        with open(file_path, "w") as f:
            f.write(code)
        console.print(f"[green]✔[/green] Wrote source file: [bold]{file_path}[/bold]")
    except Exception as e:
        console.print(f"[bold red]Failed to write Go code to file:[/bold red] {e}")
        sys.exit(1)
    
    console.print("[bold yellow]-> Compiling native Go binary...[/bold yellow]")
    with Status("Running go build...", spinner="dots") as status:
        try:
            # Go mod init
            subprocess.run(["go", "mod", "init", name], cwd=name, capture_output=True, text=True)
            # Go mod tidy
            subprocess.run(["go", "mod", "tidy"], cwd=name, capture_output=True, text=True)
            # Compile with stripped debug symbols for performance
            res = subprocess.run(["go", "build", "-ldflags=-s -w", "-o", name, "main.go"], cwd=name, capture_output=True, text=True)
            
            if res.returncode == 0:
                console.print(Panel.fit(
                    f"[bold green]✅ Success![/bold green] Native arm64 Go binary compiled.\n"
                    f"To run, execute:\n"
                    f"[bold cyan]./{name}/{name}[/bold cyan]",
                    title="On-Device Go Factory",
                    border_style="green"
                ))
            else:
                console.print(f"[bold red]❌ Go compilation failed![/bold red]")
                console.print(f"[bold red]Stdout:[/bold red]\n{res.stdout}")
                console.print(f"[bold red]Stderr:[/bold red]\n{res.stderr}")
        except Exception as e:
            console.print(f"[bold red]Error launching Go compiler:[/bold red] {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        console.print("[bold yellow]Usage:[/bold yellow] python3 ai_go_builder.py \"<App Name>\" \"<Description of Go program>\"")
        console.print("Example: python3 ai_go_builder.py \"PortScanner\" \"A fast, concurrent TCP port scanner targeting localhost\"")
        sys.exit(1)
        
    app_name = sys.argv[1]
    app_desc = sys.argv[2]
    
    go_code = generate_go_code(app_desc)
    build_go(go_code, app_name)

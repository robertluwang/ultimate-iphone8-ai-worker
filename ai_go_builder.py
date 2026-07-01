#!/usr/bin/env python3
import os
import sys
import argparse
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
    sys_prompt = (
        "You are an expert Go developer. Write a single main.go file designed to run on iOS (darwin/arm64). "
        "Keep dependencies to standard library if possible. Output ONLY the ```go code block."
    )
    
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

def build_go(llm_output: str, name: str, device_ip: str = None, ssh_user: str = "root", ssh_port: int = 22, host_compile: bool = False):
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
    
    console.print("[bold yellow]-> Compiling Go binary...[/bold yellow]")
    with Status("Running go build...", spinner="dots") as status:
        try:
            # Go mod init
            subprocess.run(["go", "mod", "init", name], cwd=name, capture_output=True, text=True)
            # Go mod tidy
            subprocess.run(["go", "mod", "tidy"], cwd=name, capture_output=True, text=True)
            
            # Setup environment for cross-compiling
            env = os.environ.copy()
            if not host_compile:
                env["GOOS"] = "ios"
                env["GOARCH"] = "arm64"
                console.print("[bold cyan]Targeting iOS (GOOS=ios GOARCH=arm64)[/bold cyan]")
            else:
                console.print("[bold cyan]Targeting Host System (Native build)[/bold cyan]")
                
            # Compile with stripped debug symbols for performance
            res = subprocess.run(["go", "build", "-ldflags=-s -w", "-o", name, "main.go"], cwd=name, capture_output=True, text=True, env=env)
            
            if res.returncode == 0:
                console.print(Panel.fit(
                    f"[bold green]✅ Success![/bold green] Go binary compiled.\n"
                    f"Output path: [bold]{name}/{name}[/bold]",
                    title="Go Factory Builder",
                    border_style="green"
                ))
            else:
                console.print(f"[bold red]❌ Go compilation failed![/bold red]")
                console.print(f"[bold red]Stdout:[/bold red]\n{res.stdout}")
                console.print(f"[bold red]Stderr:[/bold red]\n{res.stderr}")
                return
        except Exception as e:
            console.print(f"[bold red]Error launching Go compiler:[/bold red] {e}")
            return

    # Deployment phase
    if device_ip and not host_compile:
        console.print(f"[bold yellow]-> Deploying binary to iPhone at {device_ip}...[/bold yellow]")
        # Standard rootless Procursus bin directory
        remote_path = f"/var/jb/usr/bin/{name}"
        scp_cmd = ["scp", "-P", str(ssh_port), f"{name}/{name}", f"{ssh_user}@{device_ip}:{remote_path}"]
        
        with Status("Copying via SCP...", spinner="aesthetic") as status:
            try:
                deploy_res = subprocess.run(scp_cmd, capture_output=True, text=True)
                if deploy_res.returncode == 0:
                    console.print(Panel.fit(
                        f"[bold green]🚀 Deployment Successful![/bold green]\n"
                        f"The binary was copied to your iPhone.\n\n"
                        f"To execute, SSH into your iPhone and run:\n"
                        f"[bold cyan]{name}[/bold cyan]  (or {remote_path})",
                        title="Deployment Complete",
                        border_style="green"
                    ))
                else:
                    console.print(f"[bold red]❌ Deployment via SCP failed![/bold red]")
                    console.print(f"Command run: {' '.join(scp_cmd)}")
                    console.print(f"[bold red]Stderr:[/bold red]\n{deploy_res.stderr}")
                    console.print("[bold yellow]Please copy the binary manually using:[/bold yellow]")
                    console.print(f"scp -P {ssh_port} {name}/{name} {ssh_user}@{device_ip}:{remote_path}")
            except Exception as e:
                console.print(f"[bold red]Error deploying via SCP:[/bold red] {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Cross-compile Go scripts with Gemini for iOS deployment."
    )
    parser.add_argument("name", type=str, help="Application Name (e.g. PortScanner)")
    parser.add_argument("prompt", type=str, help="What should the program do?")
    parser.add_argument("--ip", type=str, help="iPhone IP address for SCP deployment")
    parser.add_argument("--user", type=str, default="root", help="SSH/SCP user on iPhone (default: root)")
    parser.add_argument("--port", type=int, default=22, help="SSH/SCP port on iPhone (default: 22)")
    parser.add_argument("--host", action="store_true", help="Build natively for current host architecture instead of iOS")
    
    args = parser.parse_args()
    
    go_code = generate_go_code(args.prompt)
    build_go(
        go_code, 
        args.name, 
        device_ip=args.ip, 
        ssh_user=args.user, 
        ssh_port=args.port, 
        host_compile=args.host
    )

if __name__ == "__main__":
    main()

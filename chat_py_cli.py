#!/usr/bin/env python3
import os
import sys
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel

# Initialize Rich Console
console = Console()

# Load Configuration from environment variables
api_base = os.getenv("OPENAI_API_BASE", "http://localhost:4000/v1")
api_key = os.getenv("OPENAI_API_KEY", "fake-key-for-gateway")
model_name = os.getenv("OPENAI_MODEL", "gemini-1.5-flash")

def main():
    console.print(Panel.fit(
        "[bold green]iPhone 8 Secure Edge AI Terminal Chat[/bold green]\n"
        f"[dim]Base URL: {api_base}[/dim]\n"
        f"[dim]Model: {model_name}[/dim]\n"
        "Type [bold red]exit[/bold red] or [bold red]quit[/bold red] to end the session.\n"
        "Type [bold yellow]clear[/bold yellow] to clear the conversation history.",
        title="Secure Edge AI CLI",
        border_style="blue"
    ))

    # Initialize OpenAI Client
    try:
        client = OpenAI(base_url=api_base, api_key=api_key)
    except Exception as e:
        console.print(f"[bold red]Error initializing OpenAI client:[/bold red] {e}")
        sys.exit(1)

    messages = [
        {"role": "system", "content": "You are a helpful assistant running on a jailbroken iPhone 8 secure edge node. Keep your responses precise, technically accurate, and optimized for display in a terminal interface."}
    ]

    while True:
        try:
            user_input = console.input("\n[bold cyan]You[/bold cyan] > ").strip()
            
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                console.print("[bold green]Goodbye![/bold green]")
                break

            if user_input.lower() == "clear":
                messages = [messages[0]]  # Keep system prompt
                console.print("[yellow]Conversation history cleared.[/yellow]")
                continue

            messages.append({"role": "user", "content": user_input})

            console.print("\n[bold green]AI Assistant[/bold green] > ", end="")
            
            response_content = ""
            with Live(Markdown(""), refresh_per_second=10, console=console) as live:
                try:
                    # Request streaming response from LiteLLM proxy
                    stream = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        stream=True,
                    )
                    
                    for chunk in stream:
                        delta = chunk.choices[0].delta.content if chunk.choices else None
                        if delta:
                            response_content += delta
                            live.update(Markdown(response_content))
                except Exception as e:
                    console.print(f"\n[bold red]API Error:[/bold red] {e}")
                    # Remove last user message since it failed
                    messages.pop()
                    continue

            # Append assistant response to history
            messages.append({"role": "assistant", "content": response_content})

        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted. Type 'exit' to quit.[/yellow]")
        except EOFError:
            console.print("\n[bold green]Goodbye![/bold green]")
            break

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import sys
import argparse
import re
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.status import Status

console = Console()

# Configuration
API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:4000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "fake-key-for-gateway")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gemini-flash")

try:
    client = OpenAI(base_url=API_BASE, api_key=API_KEY)
except Exception as e:
    console.print(f"[bold red]Error initializing client:[/bold red] {e}")
    sys.exit(1)

SYSTEM_PROMPT = """You are an iOS developer assistant specialized in building modern SwiftUI applications.
Your job is to generate all necessary Swift source files and layout configurations for a given application idea.

You must output exactly four files in your response:
1. control (Debian control format for metadata)
2. Makefile (Theos build system configuration)
3. AppNameApp.swift (App entrypoint)
4. ContentView.swift (Main application UI view)

For each file, use a markdown code block labeled with the filename in the header comment, like this:
```objc
// FILENAME: control
Package: com.robertluwang.appname
Name: AppName
Depends: mobilesubstrate
Version: 0.0.1
Architecture: iphoneos-arm64
Description: AI Generated SwiftUI Application
Maintainer: robertluwang <robert.lu.wang@gmail.com>
Author: robertluwang <robert.lu.wang@gmail.com>
Section: Utilities
```

```makefile
// FILENAME: Makefile
TARGET := iphone:clang:latest:15.0
INSTALL_TARGET_PROCESSES = AppName

include $(THEOS)/makefiles/common.mk

APPLICATION_NAME = AppName

AppName_FILES = AppNameApp.swift ContentView.swift
AppName_FRAMEWORKS = SwiftUI Combine

include $(THEOS_MAKE_PATH)/application.mk
```

```swift
// FILENAME: AppNameApp.swift
import SwiftUI

@main
struct AppNameApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
```

And then write a modern, beautiful SwiftUI implementation for ContentView.swift inside:
```swift
// FILENAME: ContentView.swift
import SwiftUI

struct ContentView: View {
    var body: some View {
        // Implement gorgeous modern UI here...
    }
}
```

Make sure the app UI is extremely beautiful, modern, has a dark mode themed background, high-quality SwiftUI controls, custom styling, animations, state management, and is fully functional.
Ensure the code is perfectly valid, clean Swift, compatible with iOS 15/16 SwiftUI features, and error-free.
"""

def extract_files(text: str) -> dict:
    """Parses files matching FILENAME: <name> inside code blocks."""
    files = {}
    blocks = re.findall(r"```[a-zA-Z0-9_-]*\s*([\s\S]*?)```", text)
    for block in blocks:
        match = re.search(r"(?://|#)\s*FILENAME:\s*([a-zA-Z0-9_\-\.]+)", block)
        if match:
            filename = match.group(1).strip()
            content = re.sub(r"^(?://|#)\s*FILENAME:\s*([a-zA-Z0-9_\-\.]+)\s*\n", "", block, flags=re.MULTILINE)
            files[filename] = content.strip()
    return files

def build_app(app_name: str, app_description: str, force_theos: bool = False):
    # Print Definitive Research Warning
    console.print(Panel(
        "[bold yellow]⚠️ WARNING: ON-DEVICE SWIFTUI COMPILATION IS NOT RECOMMENDED[/bold yellow]\n\n"
        "[white]Based on our latest Edge Worker research, on-device Swift/Theos compilation on "
        "iOS 16 rootless is highly restricted, prone to compiler crashes, and lacks proper "
        "visual preview/layout support.\n\n"
        "✔ [bold green]Recommended Workflow:[/bold green] Generate code with this script, then copy the folder "
        "to your Mac to compile/sign inside Xcode.\n"
        "✔ [bold green]Rapid GUI Alternative:[/bold green] Use the [bold cyan]Node.js Local Web App[/bold cyan] "
        "workflow which requires no compiling/codesigning and runs beautifully in full screen.[/white]",
        title="[bold red]Architecture Boundary Notice[/bold red]",
        border_style="yellow"
    ))

    safe_name = re.sub(r"\s+", "", app_name)
    output_dir = os.path.join(os.getcwd(), safe_name.lower())
    
    console.print(Panel(
        f"[bold cyan]AppName:[/bold cyan] {app_name} ({safe_name})\n"
        f"[bold cyan]Idea:[/bold cyan] {app_description}\n"
        f"[bold cyan]Directory:[/bold cyan] {output_dir}",
        title="[bold green]Generating SwiftUI Code Blocks[/bold green]"
    ))

    user_prompt = f"Please build a native iOS SwiftUI application named '{safe_name}' with the following functionality: {app_description}"

    with Status("Generating application code via Gemini...", spinner="dots") as status:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            ai_text = response.choices[0].message.content
        except Exception as e:
            console.print(f"[bold red]AI Generation failed:[/bold red] {e}")
            return

    files = extract_files(ai_text)
    if not files:
        console.print("[bold red]Error: No source files could be extracted from the AI response![/bold red]")
        console.print(f"Response snippet:\n{ai_text[:500]}...")
        return

    # Write files
    os.makedirs(output_dir, exist_ok=True)
    for name, content in files.items():
        cleaned_content = content.replace("AppName", safe_name)
        file_path = os.path.join(output_dir, name)
        with open(file_path, 'w') as f:
            f.write(cleaned_content)
        console.print(f"[green]✔[/green] Created file: [bold]{name}[/bold]")

    console.print(f"\n[bold green]🎉 SwiftUI Code Generated in folder: [bold cyan]{safe_name.lower()}/[/bold cyan][/bold green]")
    console.print(f"Transfer this folder to your Mac and import into Xcode or a swift package to compile!")

    if force_theos:
        THEOS_PATH = os.getenv("THEOS", "/var/jb/opt/theos")
        console.print("\n[bold yellow]Attempting forced local compilation via Theos...[/bold yellow]")
        if not os.path.exists(THEOS_PATH):
            console.print(f"[bold red]Error:[/bold red] Theos not found at '{THEOS_PATH}'. Can't build on-device.")
            return

        with Status("Compiling iOS App binary via Theos...", spinner="aesthetic") as status:
            try:
                env = os.environ.copy()
                env["THEOS"] = THEOS_PATH
                import subprocess
                res = subprocess.run("make clean package", shell=True, cwd=output_dir, capture_output=True, text=True, env=env)
                if res.returncode == 0:
                    console.print("[bold green]🎉 Success! Compilation completed.[/bold green]")
                    console.print(res.stdout)
                else:
                    console.print("[bold red]❌ Compilation failed![/bold red]")
                    console.print(f"[bold red]Stdout:[/bold red]\n{res.stdout}")
                    console.print(f"[bold red]Stderr:[/bold red]\n{res.stderr}")
            except Exception as e:
                console.print(f"[bold red]Error launching compile task:[/bold red] {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate beautiful SwiftUI code and config files using Gemini.")
    parser.add_argument("name", type=str, help="Application Name (e.g. RetroTicTacToe)")
    parser.add_argument("prompt", type=str, help="What should the app do?")
    parser.add_argument("--force-theos", action="store_true", help="Force attempt on-device Theos compilation")
    
    args = parser.parse_args()
    build_app(args.name, args.prompt, force_theos=args.force_theos)

if __name__ == "__main__":
    main()

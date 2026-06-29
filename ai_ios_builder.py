#!/usr/bin/env python3
import os
import sys
import json
import re
import subprocess
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.status import Status

console = Console()

# Configuration
API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:4000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "fake-key-for-gateway")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gemini-1.5-flash")
THEOS_PATH = os.getenv("THEOS", "/theos")

try:
    client = OpenAI(base_url=API_BASE, api_key=API_KEY)
except Exception as e:
    console.print(f"[bold red]Error initializing client:[/bold red] {e}")
    sys.exit(1)

SYSTEM_PROMPT = """You are an iOS developer assistant specialized in building native UIKit applications for jailbroken iOS devices using the Theos build system.
Your job is to generate all necessary source files and compilation instructions for a given application idea.

You must output exactly five files in your response:
1. control
2. Makefile
3. main.m
4. AppDelegate.h
5. AppDelegate.m
6. RootViewController.h
7. RootViewController.m

For each file, use a markdown code block labeled with the filename in the header comment, like this:
```objc
// FILENAME: control
Package: com.robertluwang.appname
Name: AppName
Depends: mobilesubstrate
Version: 0.0.1
Architecture: iphoneos-arm64
Description: AI Generated Application
Maintainer: robertluwang <robert.lu.wang@gmail.com>
Author: robertluwang <robert.lu.wang@gmail.com>
Section: Utilities
```

```makefile
// FILENAME: Makefile
TARGET := iphone:clang:latest:14.0
INSTALL_TARGET_PROCESSES = AppName

include $(THEOS)/makefiles/common.mk

APPLICATION_NAME = AppName

AppName_FILES = main.m AppDelegate.m RootViewController.m
AppName_FRAMEWORKS = UIKit CoreGraphics

include $(THEOS_MAKE_PATH)/application.mk
```

```objc
// FILENAME: main.m
#import <UIKit/UIKit.h>
#import "AppDelegate.h"

int main(int argc, char *argv[]) {
    @autoreleasepool {
        return UIApplicationMain(argc, argv, nil, NSStringFromClass([AppDelegate class]));
    }
}
```

```objc
// FILENAME: AppDelegate.h
#import <UIKit/UIKit.h>

@interface AppDelegate : UIResponder <UIApplicationDelegate>
@property (strong, nonatomic) UIWindow *window;
@end
```

```objc
// FILENAME: AppDelegate.m
#import "AppDelegate.h"
#import "RootViewController.h"

@implementation AppDelegate

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    self.window = [[UIWindow alloc] initWithFrame:[[UIScreen mainScreen] bounds]];
    RootViewController *rootVC = [[RootViewController alloc] init];
    self.window.rootViewController = rootVC;
    [self.window makeKeyAndVisible];
    return YES;
}

@end
```

```objc
// FILENAME: RootViewController.h
#import <UIKit/UIKit.h>

@interface RootViewController : UIViewController
@end
```

And then write a modern, beautiful UIKit/Objective-C implementation for RootViewController.m inside:
```objc
// FILENAME: RootViewController.m
...
```

Make sure the app UI is extremely beautiful, modern, has a dark mode themed background, high-quality controls, buttons with callbacks, labels, text fields, and responds nicely. Include rich interactive features like calculations, games, state management, or custom animations in Objective-C.
Ensure code is perfectly valid, clean, and doesn't use deprecated iOS 6 methods.
"""

def extract_files(text: str) -> dict:
    """Parses files matching FILENAME: <name> inside code blocks."""
    files = {}
    # Match markdown blocks
    blocks = re.findall(r"```[a-zA-Z0-9_-]*\s*([\s\S]*?)```", text)
    for block in blocks:
        # Find comments like // FILENAME: control or # FILENAME: control
        match = re.search(r"(?://|#)\s*FILENAME:\s*([a-zA-Z0-9_\-\.]+)", block)
        if match:
            filename = match.group(1).strip()
            # Strip the filename indicator line
            content = re.sub(r"^(?://|#)\s*FILENAME:\s*([a-zA-Z0-9_\-\.]+)\s*\n", "", block, flags=re.MULTILINE)
            files[filename] = content.strip()
    return files

def build_app(app_name: str, app_description: str):
    safe_name = re.sub(r"\s+", "", app_name)
    output_dir = os.path.join(os.getcwd(), safe_name.lower())
    
    console.print(Panel(
        f"[bold cyan]AppName:[/bold cyan] {app_name} ({safe_name})\n"
        f"[bold cyan]Idea:[/bold cyan] {app_description}\n"
        f"[bold cyan]Directory:[/bold cyan] {output_dir}",
        title="[bold green]Preparing On-Device Compilation[/bold green]"
    ))

    # Construct the user prompt
    user_prompt = f"Please build a native iOS application named '{safe_name}' with the following functionality: {app_description}"

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
        # Clean some templates if app name is customized
        cleaned_content = content.replace("AppName", safe_name)
        file_path = os.path.join(output_dir, name)
        with open(file_path, 'w') as f:
            f.write(cleaned_content)
        console.print(f"[green]✔[/green] Created file: [bold]{name}[/bold]")

    # Check for compile capability
    console.print("\n[bold yellow]Attempting local compilation via Theos...[/bold yellow]")
    if not os.path.exists(THEOS_PATH):
        console.print(f"[bold yellow]Warning:[/bold yellow] Theos not found at '{THEOS_PATH}'. Skipping build step. You can copy the generated folder '{safe_name.lower()}' to your iOS device manually.")
        return

    # Check if we can run make
    with Status("Compiling iOS App binary...", spinner="aesthetic") as status:
        try:
            env = os.environ.copy()
            env["THEOS"] = THEOS_PATH
            # Run theos build
            res = subprocess.run("make clean package", shell=True, cwd=output_dir, capture_output=True, text=True, env=env)
            if res.returncode == 0:
                console.print("[bold green]🎉 Success! Compilation completed and package generated.[/bold green]")
                console.print(res.stdout)
            else:
                console.print("[bold red]❌ Compilation failed![/bold red]")
                console.print(f"[bold red]Stdout:[/bold red]\n{res.stdout}")
                console.print(f"[bold red]Stderr:[/bold red]\n{res.stderr}")
        except Exception as e:
            console.print(f"[bold red]Error launching compile task:[/bold red] {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        console.print("[bold yellow]Usage:[/bold yellow] python3 ai_ios_builder.py \"<App Name>\" \"<App Description>\"")
        console.print("Example: python3 ai_ios_builder.py \"CalcMaster\" \"A full featured scientific calculator with animations\"")
        sys.exit(1)
        
    build_app(sys.argv[1], sys.argv[2])

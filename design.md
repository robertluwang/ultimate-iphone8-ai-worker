# The Ultimate Guide: iPhone 8 Secure Edge AI Worker & App Factory

This master guide transforms an aging iPhone 8 into a secure, low-power AI edge worker and native compilation factory.

By offloading heavy LLM computation to Vertex AI Gemini and proxying requests through a LiteLLM Gateway VM, the iPhone acts as the pure execution node. Because the iPhone 8 has 2GB of RAM, the A11 Bionic chip, and modern Procursus bootstrap (iOS 15+), it has the overhead to run native Golang and Swift compilers directly on-device—something older 1GB iPads cannot do without crashing.

---

## Architecture Overview

*   **The Brain (Vertex AI):** Handles the massive LLM inference.
*   **The Gateway (LiteLLM VM):** Securely holds Cloud credentials and translates OpenAI-formatted requests to Vertex.
*   **The Secure Tunnel (autossh):** An encrypted tunnel binding the iPhone's local port `4000` to the VM's port `4000`.
*   **The Execution Node (iPhone 8):** Runs natively compiled Go binaries (`chat-go-cli`) for instant chat, and uses AI to write and compile backend Go tools and frontend SwiftUI apps natively.

---

## Phase 1: Device Preparation & Base Packages

To unlock the ability to compile native iOS apps and Go binaries, the device must be jailbroken. The iPhone 8 maxes out at iOS 16.7.x, making it the perfect candidate for the palera1n hardware jailbreak.

> ⚠️ **Important Note on Sideloadly:**  
> Do not attempt to use `.ipa` files (like unc0ver) via Sideloadly. Apple patched app-based jailbreaks in iOS 15/16. You must use a Mac or Linux PC to execute the unpatchable checkm8 hardware exploit via USB using the palera1n CLI.

### Step-by-Step Jailbreak:
1.  **Disable Passcode:** Go to Settings > Touch ID & Passcode and **Turn Passcode Off**. *(Crucial for A11 devices on iOS 16)*.
2.  **Connect Device:** Plug the iPhone 8 into your computer (USB-A to Lightning recommended).
3.  **Run palera1n (on PC):** Open your PC terminal and run:
    ```bash
    sudo /bin/sh -c "$(curl -fsSL https://static.palera.in/scripts/install.sh)"
    sudo palera1n
    ```
4.  **Enter DFU Mode:** Follow the on-screen terminal instructions exactly.
5.  **Install Sileo:** Once booted, open the palera1n app on the iOS home screen and install Sileo.
6.  **Install the Ultimate Dev Stack:** Open Sileo (or SSH into the phone) and install all core dependencies at once:
    ```bash
    apt update
    apt install bash curl git make clang llvm ldid swift golang python3 python3-pip openssh-client autossh tmux
    ```

---

## Phase 2: Secure Networking (Passwordless SSH)

Allow the iPhone to auto-connect to your VM without human intervention:

1.  **Generate an SSH key on the iPhone:**
    ```bash
    ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
    ```
2.  **Copy the key to your LiteLLM VM:** (Replace `<VM_USER>` and `<VM_IP>`)
    ```bash
    ssh-copy-id <VM_USER>@<VM_IP>
    ```

---

## Phase 3: Shell Automation (`.bashrc`)

Configure the iPhone's shell to automatically establish the SSH tunnel and set API variables.

1.  **Edit your shell profile:** `nano ~/.bashrc`
2.  **Paste the following configuration:**
    ```bash
    # ==========================================
    # LITELLM SECURE TUNNEL & API CONFIG
    # ==========================================
    export OPENAI_API_KEY="<your_litellm_master_key>"
    export OPENAI_BASE_URL="http://127.0.0.1:4000/v1"
    export OPENAI_MODEL_NAME="gemini-flash"
    export MODEL="gemini-flash" # Fallback for some Go CLIs

    # SSH Tunnel Details
    VM_USER="ubuntu"    
    VM_IP="192.168.1.50"
    PRIVATE_KEY="~/.ssh/id_ed25519"

    if ! pgrep -f "L 4000:127.0.0.1:4000" > /dev/null; then
       echo "Starting LiteLLM secure tunnel in background..."
       autossh -M 0 -f -N -q -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" -i $PRIVATE_KEY -L 4000:127.0.0.1:4000 $VM_USER@$VM_IP
    fi
    ```
3.  **Apply changes:**
    ```bash
    source ~/.bashrc
    ```

---

## Phase 4: Lightning-Fast Native Chat (`chat-go-cli`)

Instead of running interpreted Python scripts, we compile a Go-based CLI natively on the A11 processor for instant startup times and near-zero memory footprint.

### Clone and compile natively on the iPhone:
```bash
cd ~
git clone https://github.com/robertluwang/chat-go-cli.git
cd chat-go-cli
go mod tidy

# Compile and strip debug info for max performance
go build -ldflags="-s -w" -o chat-go .
```

### Install system-wide:
```bash
# Move to the rootless bin path
mv chat-go /var/jb/usr/local/bin/chat
```

**To use:** From anywhere in your terminal, simply type `chat`. The compiled Go binary will load instantly, sending your prompts through the local SSH tunnel to your VM Gateway!

---

## Phase 5: AI On-Device Golang Factory (Backend Tools)

For headless background workers or network scanners, Go is the ultimate weapon. We use Python to orchestrate the LLM request, but the iPhone compiles the result into a blazing-fast Go binary.

### Create the script: `nano ~/ai_go_builder.py`
```python
#!/usr/bin/env python3
import os
import sys
import subprocess
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"), 
    base_url=os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:4000/v1")
)
MODEL = os.environ.get("OPENAI_MODEL_NAME", "gemini-flash")

def generate_go_code(prompt):
    print(f"-> Asking Gemini to code: {prompt}...")
    sys_prompt = "You are a Go dev. Write a single main.go file to run on darwin/arm64. Output ONLY the ```go file block."
    response = client.chat.completions.create(
        model=MODEL, 
        messages=[
            {"role": "system", "content": sys_prompt}, 
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def build_go(llm_output, name):
    os.makedirs(name, exist_ok=True)
    code = llm_output.split("```go")[1].split("```")[0].strip()
    with open(f"{name}/main.go", "w") as f: 
        f.write(code)
    
    print("-> Compiling native Go binary...")
    subprocess.run(["go", "mod", "init", name], cwd=name, capture_output=True)
    subprocess.run(["go", "build", "-ldflags=-s -w", "-o", name, "main.go"], cwd=name)
    print(f"✅ Success! Run with: ./{name}/{name}")

if __name__ == "__main__":
    name = input("App Name: ")
    build_go(generate_go_code(input("What should it do? ")), name)
```

**Usage:** `python3 ~/ai_go_builder.py` -> Instantly generates and compiles custom, concurrent backend binaries on-device!

---

## Phase 6: AI On-Device SwiftUI Factory (Frontend Apps)

For native GUI apps, we use Theos and the on-device Swift compiler.

### 1. Setup Theos
```bash
export THEOS=/var/jb/opt/theos
git clone --recursive https://github.com/theos/theos.git $THEOS
curl -LO https://github.com/theos/sdks/archive/master.zip
TMP=$(mktemp -d); unzip master.zip -d $TMP
mv $TMP/sdks-master/*.sdk $THEOS/sdks; rm -r master.zip $TMP
```

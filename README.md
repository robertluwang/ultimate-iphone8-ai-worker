# iPhone 8 Secure Edge AI Worker & App Factory 📱🤖

Welcome to the **iPhone 8 Secure Edge AI Worker** repository. This project contains a complete suite of tools to transform an aging, jailbroken iPhone 8 (or similar iOS device) into an autonomous, secure Edge AI execution node and terminal chatbot. 

---

## 🏗️ Architecture Blueprint

```
 ┌─────────────────┐           ┌─────────────────┐            ┌───────────────────┐
 │   iPhone 8      │  autossh  │   LiteLLM VM    │   HTTPS    │     Vertex AI     │
 │  (Edge Node)    ├──────────►│   (Gateway)     ├───────────►│ (Gemini LLM Brain)│
 │                 │  Tunnel   │                 │            │                   │
 └──────┬──────────┘           └─────────────────┘            └───────────────────┘
        │
        ├─► [Python Stack] ────► edge_agent.py   (Autonomous local system agent)
        │                  ────► chat_py_cli.py  (Interactive python chat console)
        │
        ├─► [Node.js Stack] ───► node-chatbot-ui (Stunning local web UI, add to Home Screen)
        │
        ├─► [Go Stack] ────────► chat-go-cli     (Blazing fast client, cross-compiled from Mac)
```

By establishing an encrypted SSH tunnel (`autossh`) to a remote Gateway VM running LiteLLM, we offload heavy AI computation to Google Cloud's Vertex AI Gemini, while keeping local execution on the iPhone itself. 

For full details on hardware constraints, setup instructions, and the core development philosophy, see [design.md](design.md).

---

## 📂 Repository Contents

This repository implements all the software components required for the edge worker:

| File / Folder | Type | Description |
| :--- | :--- | :--- |
| **`node-chatbot-ui/`** | Node.js Project | A beautiful, responsive Express & tailwind-based Web App. Runs locally on the phone. Using Safari's "Add to Home Screen", it acts exactly like a native app. |
| **`chat-go-cli/`** | Go Project | Standard Go module. Designed to be cross-compiled on a Mac for instant-startup, low-memory execution on-device with built-in Vertex Google Search. |
| **`ai_go_builder.py`** | Python Utility | Cross-compilation orchestrator. Generates specialized Go code via Gemini on your Mac, builds it targeting the iPhone, and deploys it automatically over SCP. |
| **`ai_ios_builder.py`** | Python Utility | SwiftUI App Generator. Generates complete SwiftUI code blocks suitable for copying into Xcode projects. |
| **`chat_py_cli.py`** | Python Utility | A beautiful, color-coded, streaming interactive terminal interface to chat with the Gemini brain in real-time natively on the device. |
| **`edge_agent.py`** | Python Utility | An autonomous agent capable of reasoning, running shell commands locally, reading/writing files, and solving tasks automatically. |
| **`requirements.txt`** | Dependency File| Lists the Python package dependencies (`openai`, `rich`, `requests`) required for the scripts. |
| **`design.md`** | Markdown Document | The full step-by-step design specification, jailbreak guide, networking instructions, and bootstrap details. |

---

## 🚀 Quick Start

### 1. Installation
Install the python dependencies on your developer machine and/or iPhone 8 (requires Python 3.x and Pip):
```bash
pip3 install -r requirements.txt
```

### 2. Connect the Secure Tunnel (iPhone)
Follow [design.md](design.md) to set up passwordless SSH, then configure your Gateway VM details and launch the background tunnel:
```bash
# Add this check/start into your ~/.bashrc or run directly:
autossh -M 0 -f -N -q -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" -i ~/.ssh/id_ed25519 -L 4000:127.0.0.1:4000 ubuntu@<YOUR_VM_IP>
```

This binds the remote Gateway's LLM endpoint locally to port `4000`.

### 3. Launch the Node.js Local Web App (iPhone)
The most practical way to have a gorgeous, home-screen-accessible chatbot in seconds:
```bash
cd node-chatbot-ui
npm install
npm start
```
*   **The iOS Standalone Hack:** Open Safari on your iPhone, navigate to `http://localhost:3000`, tap **Share**, and choose **"Add to Home Screen"**. It will launch full-screen with no browser address bar!

### 4. Deploy the Cross-Compiled Go Chat Client (`chat-go-cli`)
Compile on your Mac targeting the iPhone's architecture for ultra-fast, native CLI execution:
```bash
# Run this on your Mac
cd chat-go-cli
GOOS=ios GOARCH=arm64 go build -ldflags="-s -w" -o chat-go .
scp chat-go root@<IPHONE_IP>:/var/jb/usr/bin/chat

# Run this on your iPhone terminal
chat
```

### 5. Generate and Deploy Custom Go Tools via `ai_go_builder.py`
Run this script on your Mac to design, write, compile, and push custom Go tools directly to the phone:
```bash
# On your Mac:
python3 ai_go_builder.py "PortScanner" "A concurrent TCP port scanner targeting localhost" --ip <IPHONE_IP>
```

---

## ⚙️ Environment Variables

Ensure these are set in your execution environments:
- `OPENAI_API_BASE` / `OPENAI_BASE_URL`: Defaults to `http://localhost:4000/v1`
- `OPENAI_API_KEY`: Defaults to `fake-key-for-gateway`
- `OPENAI_MODEL_NAME` / `OPENAI_MODEL`: Defaults to `gemini-flash`

---

## 👤 Author
- **Name:** robertluwang
- **Email:** robert.lu.wang@gmail.com
- **Repository:** [https://github.com/robertluwang/ultimate-iphone8-ai-worker](https://github.com/robertluwang/ultimate-iphone8-ai-worker)

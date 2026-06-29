# iPhone 8 Secure Edge AI Worker & App Factory 📱🤖

Welcome to the **iPhone 8 Secure Edge AI Worker** repository. This project contains the complete suite of tools to transform an aging, jailbroken iPhone 8 (or similar iOS device) into an autonomous, secure Edge AI node, terminal chatbot, and on-device native app compilation factory.

---

## 🏗️ Architecture Blueprint

```
 ┌─────────────────┐           ┌─────────────────┐            ┌───────────────────┐
 │   iPhone 8      │  autossh  │   LiteLLM VM    │   HTTPS    │     Vertex AI     │
 │  (Edge Node)    ├──────────►│   (Gateway)     ├───────────►│ (Gemini LLM Brain)│
 └──────┬──────────┘  Tunnel   └─────────────────┘            └───────────────────┘
        │
        ├─► chat_py_cli.py (Interactive Chat Console)
        ├─► edge_agent.py  (Autonomous Edge System Agent)
        └─► ai_ios_builder.py ──► [ Theos Build System ] ──► Native iOS App (.deb)
```

By establishing an encrypted SSH tunnel (`autossh`) to a remote Gateway VM running LiteLLM, we offload heavy AI computation to Google Cloud's Vertex AI Gemini, while keeping all local execution, terminal feedback, and compilation on the iPhone itself. 

For full details on the concept, hardware constraints, and setup, see [design.md](design.md).

---

## 📂 Repository Contents

This repository implements all the software components required for the edge worker:

| File | Type | Description |
| :--- | :--- | :--- |
| **`autossh_tunnel.sh`** | Bash Script | Automates starting and managing the background reverse SSH tunnel connecting your device to the Gateway VM. |
| **`chat_py_cli.py`** | Python Utility | A beautiful, color-coded, streaming interactive terminal interface to chat with the Gemini brain in real-time. |
| **`edge_agent.py`** | Python Utility | An autonomous agent capable of reasoning, running shell commands locally, reading/writing files, and solving tasks automatically. |
| **`ai_ios_builder.py`** | Python Utility | The App Factory script. Ask the model for an app idea; it generates perfect Objective-C code and runs the local Theos compiler to build a native `.deb` app package. |
| **`requirements.txt`** | Dependency File| Lists the Python package dependencies (`openai`, `rich`, `requests`) required for the scripts. |
| **`design.md`** | Markdown Document | The full step-by-step design specification, jailbreak guide, networking instructions, and bootstrap details. |

---

## 🚀 Quick Start

### 1. Installation
Install the python requirements on your iPhone 8 (requires Python 3.x and Pip, installed via Sileo/APT):
```bash
pip3 install -r requirements.txt
```

### 2. Connect the Secure Tunnel
Configure your Gateway VM details inside `autossh_tunnel.sh` and make it executable:
```bash
chmod +x autossh_tunnel.sh
./autossh_tunnel.sh
```

This sets up the proxy, exposing the Gateway's LLM endpoint locally on port `4000`.

### 3. Run the Terminal Chat Client
Launch the interactive streaming chatbot:
```bash
python3 chat_py_cli.py
```

### 4. Run the Autonomous Edge Agent
Instruct the local edge agent to perform a system or file task:
```bash
python3 edge_agent.py "Analyze the disk space and write a summary to disk_report.txt"
```

### 5. Compile Native Apps Natively (The App Factory)
Ask the compiler script to design and build a native iOS application:
```bash
python3 ai_ios_builder.py "RetroTicTacToe" "A classic Tic-Tac-Toe game with neon styling, scoreboard, and smooth feedback"
```
The script will prompt the AI model, create the file structure, and run `make` using your local Theos toolchain!

---

## ⚙️ Requirements & Environment

- **Device:** iPhone 8 (or any Procursus-based iOS 15-16 jailbroken device)
- **Jailbreak:** palera1n (rootful or rootless)
- **Packages:** `python3`, `python3-pip`, `autossh`, `theos` (for Phase 6 compilation)
- **Environment Variables:**
  - `OPENAI_API_BASE`: Defaults to `http://localhost:4000/v1`
  - `OPENAI_API_KEY`: Defaults to `fake-key-for-gateway`
  - `OPENAI_MODEL`: Defaults to `gemini-1.5-flash`

---

## 👤 Author
- **Name:** robertluwang
- **Email:** robert.lu.wang@gmail.com
- **Repository:** [https://github.com/robertluwang/ultimate-iphone8-ai-worker](https://github.com/robertluwang/ultimate-iphone8-ai-worker)

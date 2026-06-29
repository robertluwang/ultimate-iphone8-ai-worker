#!/bin/bash

# Configuration Variables
VM_USER="ubuntu"
VM_IP="YOUR_GATEWAY_VM_IP" # Replace with your LiteLLM VM IP
LOCAL_PORT=4000
REMOTE_PORT=4000

echo "=== iPhone 8 Secure Edge AI Worker Tunnel ==="

# Check if autossh is installed
if ! command -v autossh &> /dev/null; then
    echo "[-] autossh could not be found. Please install it using 'apt install autossh' or Sileo."
    exit 1
fi

echo "[+] Starting autossh tunnel..."
echo "    Local Port: $LOCAL_PORT"
echo "    Remote VM: $VM_USER@$VM_IP:$REMOTE_PORT"

# Execute autossh
# -M 0: disables the internal echo port monitoring (uses SSH's ServerAliveInterval instead)
# -N: Do not execute a remote command (just port forward)
# -f: Run in background
# -R: Reverse port forward
autossh -M 0 -N -f \
    -o "PubkeyAuthentication=yes" \
    -o "StrictHostKeyChecking=no" \
    -o "ServerAliveInterval=30" \
    -o "ServerAliveCountMax=3" \
    -R ${REMOTE_PORT}:localhost:${LOCAL_PORT} \
    ${VM_USER}@${VM_IP}

if [ $? -eq 0 ]; then
    echo "[+] Tunnel successfully backgrounded!"
    echo "[+] Exporting environment variables for current session:"
    echo "    export OPENAI_API_BASE=\"http://localhost:${LOCAL_PORT}/v1\""
    echo "    export OPENAI_API_KEY=\"fake-key-for-gateway\""
    echo "    export OPENAI_MODEL=\"gemini-1.5-flash\""
    
    # Optional bashrc setup warning
    echo ""
    echo "To automate this every time you login, add the following to your ~/.bashrc or ~/.zshrc:"
    echo "--------------------------------------------------------"
    echo "export OPENAI_API_BASE=\"http://localhost:${LOCAL_PORT}/v1\""
    echo "export OPENAI_API_KEY=\"fake-key-for-gateway\""
    echo "export OPENAI_MODEL=\"gemini-1.5-flash\""
    echo "--------------------------------------------------------"
else
    echo "[-] Failed to establish tunnel. Please check ssh keys and VM connection."
fi

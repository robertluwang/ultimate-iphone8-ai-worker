#!/usr/bin/env python3

import os
import sys
import json
import urllib.request
import urllib.error
import argparse

def do_chat(messages, gateway_url, api_key, model, tools):
    payload = {
        "model": model,
        "messages": messages,
        "tools": tools
    }
    json_data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(gateway_url, method="POST", data=json_data)
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(req) as response:
            response_body = response.read().decode("utf-8")
            resp_json = json.loads(response_body)

            if "choices" in resp_json and len(resp_json["choices"]) > 0:
                reply_msg = resp_json["choices"][0]["message"]
                return reply_msg, None
            else:
                return None, Exception("No response from LLM.")

    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')
        return None, Exception(f"API Error (status {e.code}): {err_body}")
    except urllib.error.URLError as e:
        return None, Exception(f"Error communicating with gateway: {e.reason}")
    except Exception as e:
        return None, Exception(f"Unexpected Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Python CLI Chat with Built-in Vertex Google Search")
    parser.add_argument("--model", type=str, help="Model to use (overrides LITELLM_MODEL)")
    parser.add_argument("prompt", nargs="*", help="Optional single prompt for one-shot execution")
    args = parser.parse_args()

    # Read environment variables with fallbacks
    gateway_url = os.environ.get("LITELLM_URL", "http://localhost:4000/v1/chat/completions")
    api_key = os.environ.get("LITELLM_MASTER_KEY", "")
    
    # Priority: CLI flag > Env Var > Default
    model = args.model if args.model else os.environ.get("LITELLM_MODEL", "gemini-flash")

    # Native Google Search tool payload for Vertex AI through LiteLLM
    tools = [{"googleSearch": {}}]
    messages = []

    # One-shot mode
    if args.prompt:
        prompt_text = " ".join(args.prompt)
        messages.append({"role": "user", "content": prompt_text})
        
        reply_msg, err = do_chat(messages, gateway_url, api_key, model, tools)
        if err:
            print(f"❌ {err}")
            sys.exit(1)
        
        print(reply_msg.get("content", ""))
        sys.exit(0)

    # Interactive mode
    print("🚀 Starting Python CLI Chat with Built-in Vertex Google Search (Type 'exit' to stop)")
    print(f"🌐 Gateway URL: {gateway_url}")
    print(f"🤖 Model:       {model}")
    print("-" * 55)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        
        reply_msg, err = do_chat(messages, gateway_url, api_key, model, tools)
        
        if err:
            print(f"❌ {err}")
            messages.pop() # remove last user message on failure
        else:
            content = reply_msg.get("content", "")
            print(f"🤖 LLM:\n{content}")
            messages.append({"role": "assistant", "content": content})

if __name__ == "__main__":
    main()

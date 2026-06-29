package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

// Message represents a chat message.
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// ChatRequest represents the payload sent to LiteLLM/OpenAI compatible gateway.
type ChatRequest struct {
	Model    string    `json:"model"`
	Messages []Message `json:"messages"`
	Tools    []any     `json:"tools,omitempty"`
}

// ChatResponse represents the response from the gateway.
type ChatResponse struct {
	Choices []struct {
		Message Message `json:"message"`
	} `json:"choices"`
	Error *struct {
		Message string `json:"message"`
	} `json:"error,omitempty"`
}

func doChat(messages []Message, gatewayURL, apiKey, model string, tools []any) (*Message, error) {
	reqBody := ChatRequest{
		Model:    model,
		Messages: messages,
		Tools:    tools,
	}

	jsonBody, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("error marshaling request: %w", err)
	}

	req, err := http.NewRequest("POST", gatewayURL, bytes.NewBuffer(jsonBody))
	if err != nil {
		return nil, fmt.Errorf("error creating request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if apiKey != "" {
		req.Header.Set("Authorization", "Bearer "+apiKey)
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("error communicating with gateway: %w", err)
	}
	defer resp.Body.Close()

	bodyText, _ := io.ReadAll(resp.Body)

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API Error (status %d): %s", resp.StatusCode, string(bodyText))
	}

	var chatResp ChatResponse
	if err := json.Unmarshal(bodyText, &chatResp); err != nil {
		return nil, fmt.Errorf("error parsing response JSON: %w", err)
	}

	if chatResp.Error != nil {
		return nil, fmt.Errorf("gateway Error: %s", chatResp.Error.Message)
	}

	if len(chatResp.Choices) == 0 {
		return nil, fmt.Errorf("no response from LLM")
	}

	return &chatResp.Choices[0].Message, nil
}

func printUsage() {
	fmt.Println("Usage: chat-go [options] [prompt]")
	fmt.Println("\nA lightweight CLI for interacting with LLMs via a LiteLLM/OpenAI compatible gateway.")
	fmt.Println("\nOptions:")
	fmt.Println("  --model <model_name>   Model to use (overrides LITELLM_MODEL env var)")
	fmt.Println("  -h, --help             Show this help message")
	fmt.Println("\nModes:")
	fmt.Println("  Interactive Mode:      Run without arguments to start a chat session.")
	fmt.Println("  Non-Interactive Mode:  Provide a prompt as arguments for a single-shot response.")
	fmt.Println("\nEnvironment Variables:")
	fmt.Println("  LITELLM_URL        API gateway URL (default: http://localhost:4000/v1/chat/completions)")
	fmt.Println("  LITELLM_MASTER_KEY API key for authorization")
	fmt.Println("  LITELLM_MODEL      Model identifier (default: gemini-flash)")
	fmt.Println("\nExamples:")
	fmt.Println("  ./chat-go")
	fmt.Println("  ./chat-go --model gemini-pro \"What is the weather like today?\"")
	fmt.Println("  ./chat-go Explain quantum computing in one sentence")
}

func main() {
	gatewayURL := os.Getenv("LITELLM_URL")
	if gatewayURL == "" {
		gatewayURL = "http://localhost:4000/v1/chat/completions"
	}

	apiKey := os.Getenv("LITELLM_MASTER_KEY")
	
	defaultModel := os.Getenv("LITELLM_MODEL")
	if defaultModel == "" {
		defaultModel = "gemini-flash"
	}

	modelPtr := flag.String("model", "", "Model to use (overrides LITELLM_MODEL)")
	
	// Override the default Usage function
	flag.Usage = printUsage
	flag.Parse()

	model := *modelPtr
	if model == "" {
		model = defaultModel
	}

	// Native Google Search tool payload for Vertex AI through LiteLLM
	tools := []any{
		map[string]any{
			"googleSearch": map[string]any{},
		},
	}

	args := flag.Args()

	// If arguments are provided, run non-interactively and exit
	if len(args) > 0 {
		prompt := strings.Join(args, " ")
		messages := []Message{{Role: "user", Content: prompt}}

		replyMsg, err := doChat(messages, gatewayURL, apiKey, model, tools)
		if err != nil {
			fmt.Fprintf(os.Stderr, "❌ %v\n", err)
			os.Exit(1)
		}

		fmt.Println(replyMsg.Content)
		return
	}

	fmt.Println("🚀 Starting Go CLI Chat with Built-in Vertex Google Search (Type 'exit' to stop)")
	fmt.Printf("🌐 Gateway URL: %s\n", gatewayURL)
	fmt.Printf("🤖 Model:       %s\n", model)
	fmt.Println("-------------------------------------------------------")

	scanner := bufio.NewScanner(os.Stdin)
	var messages []Message

	for {
		fmt.Print("\nYou: ")
		if !scanner.Scan() {
			break
		}

		input := strings.TrimSpace(scanner.Text())
		if input == "exit" || input == "quit" {
			fmt.Println("Goodbye!")
			break
		}
		if input == "" {
			continue
		}

		messages = append(messages, Message{Role: "user", Content: input})

		replyMsg, err := doChat(messages, gatewayURL, apiKey, model, tools)
		if err != nil {
			fmt.Println("❌", err)
			messages = messages[:len(messages)-1] // remove last user message
			continue
		}

		// Because Vertex AI handles the tool on the server side, it will
		// directly return the final text response in Content!
		fmt.Println("🤖 LLM:", replyMsg.Content)
		messages = append(messages, Message{Role: "assistant", Content: replyMsg.Content})
	}
}

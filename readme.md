# Claude Connect - Anthropic API Proxy

Follow me for more AI & dev content!
[![TikTok](https://img.shields.io/badge/TikTok-@vibinwiththechef-ff0050?logo=tiktok&logoColor=white)](https://www.tiktok.com/@vibinwiththechef)

A universal proxy server that translates Anthropic API requests to OpenAI-compatible format, allowing Claude Code to work with any OpenAI-compatible API endpoint.

## TLDR

Use Claude Code CLI with any LLM provider - OpenAI, local models, or any OpenAI-compatible API

## What This Does

This proxy lets you use Claude Code with different AI providers by translating Anthropic's message format to OpenAI's format. You can switch between providers just by changing environment variables.

**Supported Providers:**

- OpenAI (GPT-4, GPT-3.5, etc.)
- Azure OpenAI
- LM Studio (local models)
- Ollama
- vLLM
- Together AI
- Any OpenAI-compatible API

## Setup

### Requirements

- Python 3.7+
- FastAPI and dependencies (install with `pip install fastapi uvicorn httpx pydantic`)

### Configuration

The proxy is configured using environment variables:

- `OPENAI_BASE_URL` - Where to forward requests
- `OPENAI_API_KEY` - Authentication key (if needed)
- `OPENAI_MODEL` - Which model to use
- `PROXY_PORT` - Port for the proxy server (default: 8080)

## Provider Configuration Examples

### For OpenAI

```bash
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_API_KEY="sk-proj-YOUR-KEY"
export OPENAI_MODEL="gpt-4o"
```

### For LM Studio (Local)

```bash
export OPENAI_BASE_URL="http://localhost:1234/v1"
export OPENAI_API_KEY=""
export OPENAI_MODEL="local-model"
```

### For Together AI

```bash
export OPENAI_BASE_URL="https://api.together.xyz/v1"
export OPENAI_API_KEY="together-key-..."
export OPENAI_MODEL="meta-llama/Llama-3-70b-chat-hf"
```

## Running the System

You'll need **2 terminals** to run this setup:

### Terminal 1: Start the Proxy Server

```bash
# Set your environment variables first
export OPENAI_BASE_URL="http://localhost:1234/v1"  # or your chosen provider
export OPENAI_MODEL="your-model-name"
# Add OPENAI_API_KEY if needed

# Run the proxy
python claude_connect.py
```

The proxy will start on `http://localhost:8080` and display configuration information.

### Terminal 2: Configure and Run Claude Code

```bash
# Configure Claude Code to use the proxy
export ANTHROPIC_BASE_URL="http://localhost:8080"
export ANTHROPIC_API_KEY="dummy-key"  # Can be any value since we're using the proxy

# Run Claude Code
claude-code
```

## How It Works

1. **Claude Code** sends requests in Anthropic's format to the proxy
2. **Proxy Server** translates the request to OpenAI format
3. **Backend Provider** (OpenAI, LM Studio, etc.) processes the request
4. **Proxy Server** translates the response back to Anthropic format
5. **Claude Code** receives the response as if it came from Anthropic

The core difference between providers is just configuration - all the translation work is handled automatically by the proxy.

## Provider-Specific Setup

### LM Studio

1. Download and install LM Studio
2. Load your preferred model
3. Start the local server (usually on port 1234)
4. Use the LM Studio configuration above

### Ollama

```bash
export OPENAI_BASE_URL="http://localhost:11434/v1"
export OPENAI_API_KEY=""
export OPENAI_MODEL="llama2"  # or your installed model
```

### Azure OpenAI

```bash
export OPENAI_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
export OPENAI_API_KEY="your-azure-key"
export OPENAI_MODEL="gpt-4"
```

## API Endpoints

### `/v1/messages` (POST)

Main endpoint that accepts Anthropic Messages API requests.

### `/v1/models` (GET)

Returns available models for API compatibility.

### `/` (GET)

Root endpoint with usage instructions and status.

## Troubleshooting

- **Connection errors**: Make sure your backend provider is running and accessible
- **Authentication errors**: Verify your API key is correct for the chosen provider
- **Model errors**: Ensure the model name matches what's available on your provider
- **Port conflicts**: Change `PROXY_PORT` if port 8080 is in use

## Features

- ✅ Request/response translation between Anthropic and OpenAI formats
- ✅ Streaming support
- ✅ System message handling
- ✅ Token limit management
- ✅ Error handling and logging
- ✅ Health check endpoints
- ✅ Multi-provider support
- ✅ Role mapping (human → user)
- ✅ Multimodal content extraction

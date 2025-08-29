# Anthropic API to LM Studio Proxy

A lightweight proxy server that translates Anthropic Claude API requests to LM Studio's OpenAI-compatible format, enabling Claude Code and other Anthropic API clients to work seamlessly with local LLMs.

## Features

- **API Translation**: Converts Anthropic Messages API format to OpenAI/LM Studio format
- **Streaming Support**: Full support for streaming responses
- **Role Mapping**: Automatically maps Anthropic roles (`human`) to OpenAI roles (`user`)
- **System Messages**: Preserves system prompts across API formats
- **Health Monitoring**: Built-in health check endpoint to verify LM Studio connectivity
- **Comprehensive Logging**: Detailed request/response logging for debugging

## Requirements

- Python 3.7+
- LM Studio running locally with a loaded model
- Required Python packages:
  - `fastapi`
  - `httpx`
  - `uvicorn`
  - `pydantic`

## Installation

1. Clone this repository:

```bash
git clone <repository-url>
cd anthropic_api
```

2. Install dependencies:

```bash
pip install fastapi httpx uvicorn pydantic
```

## Configuration

### Environment Variables

Set the following environment variables for Claude Code integration:

```bash
export ANTHROPIC_BASE_URL=http://localhost:8080
export ANTHROPIC_AUTH_TOKEN=sk-7a9c3f8e2b4d6a1e9f5c8b3d7e2a4c6f
export API_TIMEOUT_MS=600000
export ANTHROPIC_MODEL={NAME_OF_MODEL_FROM_LM_STUDIO}
export ANTHROPIC_SMALL_FAST_MODEL={NAME_OF_MODEL_FROM_LM_STUDIO}
```

Note: The auth token can be any value as LM Studio doesn't require authentication.

### Proxy Settings

The proxy runs on port 8080 by default and expects LM Studio on port 1234. You can modify these in `main.py`:

```python
LM_STUDIO_BASE_URL = "http://localhost:1234"  # LM Studio port
PROXY_PORT = 8080  # Proxy server port
```

## Usage

1. **Start LM Studio** and load your preferred model

2. **Run the proxy server**:

```bash
python main.py
```

You'll see:

```
╔══════════════════════════════════════════════════════════╗
║       Anthropic to LM Studio Proxy Server               ║
╠══════════════════════════════════════════════════════════╣
║  Proxy running on: http://localhost:8080                 ║
║  LM Studio URL:    http://localhost:1234                 ║
║                                                          ║
║  Configure Claude Code to use:                          ║
║  API URL: http://localhost:8080/v1/messages              ║
║                                                          ║
║  Make sure LM Studio is running with a model loaded!    ║
╚══════════════════════════════════════════════════════════╝
```

3. **Configure Claude Code** or any Anthropic API client to use `http://localhost:8080` as the API endpoint

## API Endpoints

### `/v1/messages` (POST)

Main endpoint that accepts Anthropic Messages API requests and proxies them to LM Studio.

**Request Format** (Anthropic):

```json
{
  "model": "claude-3-opus",
  "messages": [{ "role": "human", "content": "Hello!" }],
  "max_tokens": 4096,
  "temperature": 1.0,
  "stream": false
}
```

### `/health` (GET)

Health check endpoint that verifies both proxy and LM Studio status.

**Response**:

```json
{
  "status": "healthy",
  "lm_studio_status": "healthy",
  "lm_studio_url": "http://localhost:1234"
}
```

### `/` (GET)

Root endpoint with usage instructions.

## How It Works

1. **Request Reception**: The proxy receives Anthropic API requests on `/v1/messages`
2. **Format Translation**: Converts the request to OpenAI/LM Studio compatible format:
   - Maps `human` role to `user`
   - Extracts system messages
   - Handles multimodal content (extracts text)
3. **LM Studio Communication**: Forwards the converted request to LM Studio
4. **Response Translation**: Converts LM Studio's OpenAI-format response back to Anthropic format
5. **Streaming Support**: For streaming requests, translates chunks in real-time

## Troubleshooting

### LM Studio Connection Issues

- Ensure LM Studio is running and has a model loaded
- Check the health endpoint: `http://localhost:8080/health`
- Verify LM Studio is accessible at `http://localhost:1234`

### API Format Errors

- Enable debug logging to see request/response translations
- Check that your Anthropic API client is sending properly formatted requests
- Verify the model name in your requests

### Performance Issues

- For large contexts, increase the `API_TIMEOUT_MS` environment variable
- Ensure your LM Studio model has sufficient context length
- Monitor memory usage if running large models

## Limitations

- Multimodal content (images) is not supported - only text is extracted
- Some Anthropic-specific features may not have direct LM Studio equivalents
- Response quality depends on the underlying LM Studio model

## License

[Your License Here]

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

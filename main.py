#!/usr/bin/env python3
"""
Anthropic API to LM Studio Proxy Server

This proxy translates Anthropic API requests to LM Studio format,
allowing Claude Code to work with local LLMs.
"""

import json
import logging
from typing import Dict, Any, Optional, AsyncIterator
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import uvicorn
from pydantic import BaseModel
from typing import List, Union
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configuration
LM_STUDIO_BASE_URL = "http://localhost:1234"  # Default LM Studio port
PROXY_PORT = 8080

class AnthropicMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]

class AnthropicRequest(BaseModel):
    model: str
    messages: List[AnthropicMessage]
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    stream: Optional[bool] = False
    system: Optional[str] = None
    stop_sequences: Optional[List[str]] = None

def convert_anthropic_to_openai(anthropic_req: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Anthropic API format to OpenAI/LM Studio format."""
    
    openai_messages = []
    
    # Add system message if present
    if anthropic_req.get("system"):
        openai_messages.append({
            "role": "system",
            "content": anthropic_req["system"]
        })
    
    # Convert messages
    for msg in anthropic_req.get("messages", []):
        role = msg["role"]
        content = msg["content"]
        
        # Handle role mapping (Anthropic uses 'human', OpenAI uses 'user')
        if role == "human":
            role = "user"
        
        # Handle content that might be a list (for multimodal, though LM Studio may not support)
        if isinstance(content, list):
            # For now, just extract text content
            text_content = ""
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_content += item.get("text", "")
                elif isinstance(item, str):
                    text_content += item
            content = text_content
        
        openai_messages.append({
            "role": role,
            "content": content
        })
    
    # Build OpenAI request
    openai_req = {
        "messages": openai_messages,
        "temperature": anthropic_req.get("temperature", 1.0),
        "max_tokens": anthropic_req.get("max_tokens", 4096),
        "top_p": anthropic_req.get("top_p", 1.0),
        "stream": anthropic_req.get("stream", False)
    }
    
    # Add stop sequences if present
    if anthropic_req.get("stop_sequences"):
        openai_req["stop"] = anthropic_req["stop_sequences"]
    
    return openai_req

def convert_openai_to_anthropic_response(openai_resp: Dict[str, Any]) -> Dict[str, Any]:
    """Convert OpenAI/LM Studio response to Anthropic format."""
    
    # Extract the assistant's response
    if "choices" in openai_resp and len(openai_resp["choices"]) > 0:
        message = openai_resp["choices"][0]["message"]
        content = message.get("content", "")
        
        # Build Anthropic response
        anthropic_resp = {
            "id": openai_resp.get("id", "msg_" + str(hash(content))[:8]),
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ],
            "model": openai_resp.get("model", "unknown"),
            "stop_reason": "end_turn" if openai_resp["choices"][0].get("finish_reason") == "stop" else "max_tokens",
            "stop_sequence": None,
            "usage": {
                "input_tokens": openai_resp.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": openai_resp.get("usage", {}).get("completion_tokens", 0)
            }
        }
        
        return anthropic_resp
    else:
        raise ValueError("Invalid OpenAI response format")

async def convert_stream_chunk(chunk: str) -> Optional[str]:
    """Convert a streaming chunk from OpenAI to Anthropic format."""
    
    if not chunk.strip() or chunk.strip() == "data: [DONE]":
        return None
    
    if chunk.startswith("data: "):
        chunk = chunk[6:]
    
    try:
        openai_chunk = json.loads(chunk)
        
        if "choices" in openai_chunk and len(openai_chunk["choices"]) > 0:
            delta = openai_chunk["choices"][0].get("delta", {})
            content = delta.get("content", "")
            
            if content:
                # Create Anthropic streaming chunk
                anthropic_chunk = {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {
                        "type": "text_delta",
                        "text": content
                    }
                }
                return f"data: {json.dumps(anthropic_chunk)}\n\n"
            
            # Check if this is the final chunk
            if openai_chunk["choices"][0].get("finish_reason") == "stop":
                # Send the stop event
                stop_event = {
                    "type": "message_stop"
                }
                return f"data: {json.dumps(stop_event)}\n\n"
    except json.JSONDecodeError:
        logger.error(f"Failed to parse chunk: {chunk}")
    
    return None

@app.post("/v1/messages")
@app.post("/messages")
async def create_message(request: Request):
    """Handle Anthropic Messages API requests."""
    
    try:
        # Parse the incoming Anthropic request
        anthropic_req = await request.json()
        logger.info(f"Received Anthropic request: {json.dumps(anthropic_req, indent=2)}")
        
        # Convert to OpenAI format
        openai_req = convert_anthropic_to_openai(anthropic_req)
        logger.info(f"Converted to OpenAI format: {json.dumps(openai_req, indent=2)}")
        
        # Forward to LM Studio
        async with httpx.AsyncClient() as client:
            if anthropic_req.get("stream", False):
                # Handle streaming
                async def stream_generator():
                    async with client.stream(
                        "POST",
                        f"{LM_STUDIO_BASE_URL}/v1/chat/completions",
                        json=openai_req,
                        timeout=None
                    ) as response:
                        # Send initial message start event
                        start_event = {
                            "type": "message_start",
                            "message": {
                                "id": "msg_" + str(hash(str(anthropic_req)))[:8],
                                "type": "message",
                                "role": "assistant",
                                "content": [],
                                "model": anthropic_req.get("model", "unknown"),
                                "usage": {
                                    "input_tokens": 0,
                                    "output_tokens": 0
                                }
                            }
                        }
                        yield f"data: {json.dumps(start_event)}\n\n"
                        
                        # Send content block start
                        content_start = {
                            "type": "content_block_start",
                            "index": 0,
                            "content_block": {
                                "type": "text",
                                "text": ""
                            }
                        }
                        yield f"data: {json.dumps(content_start)}\n\n"
                        
                        async for line in response.aiter_lines():
                            if line:
                                converted = await convert_stream_chunk(line)
                                if converted:
                                    yield converted
                
                return StreamingResponse(
                    stream_generator(),
                    media_type="text/event-stream"
                )
            else:
                # Handle non-streaming
                response = await client.post(
                    f"{LM_STUDIO_BASE_URL}/v1/chat/completions",
                    json=openai_req,
                    timeout=None
                )
                response.raise_for_status()
                
                openai_resp = response.json()
                logger.info(f"Received OpenAI response: {json.dumps(openai_resp, indent=2)}")
                
                # Convert back to Anthropic format
                anthropic_resp = convert_openai_to_anthropic_response(openai_resp)
                logger.info(f"Converted to Anthropic format: {json.dumps(anthropic_resp, indent=2)}")
                
                return JSONResponse(content=anthropic_resp)
                
    except httpx.RequestError as e:
        logger.error(f"Error connecting to LM Studio: {e}")
        raise HTTPException(status_code=502, detail=f"Error connecting to LM Studio: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Try to check if LM Studio is responsive
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LM_STUDIO_BASE_URL}/v1/models", timeout=5.0)
            lm_studio_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        lm_studio_status = "unreachable"
    
    return {
        "status": "healthy",
        "lm_studio_status": lm_studio_status,
        "lm_studio_url": LM_STUDIO_BASE_URL
    }

@app.get("/")
async def root():
    """Root endpoint with usage instructions."""
    return {
        "message": "Anthropic to LM Studio Proxy",
        "usage": "Configure Claude Code to use http://localhost:8080 as the API endpoint",
        "health_check": "/health",
        "lm_studio_backend": LM_STUDIO_BASE_URL
    }

if __name__ == "__main__":
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║       Anthropic to LM Studio Proxy Server               ║
    ╠══════════════════════════════════════════════════════════╣
    ║  Proxy running on: http://localhost:{PROXY_PORT:<5}                 ║
    ║  LM Studio URL:    {LM_STUDIO_BASE_URL:<38}║
    ║                                                          ║
    ║  Configure Claude Code to use:                          ║
    ║  API URL: http://localhost:{PROXY_PORT}          ║
    ║                                                          ║
    ║  Make sure LM Studio is running with a model loaded!    ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=PROXY_PORT)
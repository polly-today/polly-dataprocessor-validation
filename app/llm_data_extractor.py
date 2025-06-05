import time
from fastapi import status, HTTPException
from typing import Any
from pydantic import BaseModel
from openai import AsyncOpenAI
from enum import Enum
import os
from dotenv import load_dotenv


async def get_chat_gpt_response(
        system_prompt: str, 
        response_format, 
        model: str,
        text_to_analize: str | None = None,
        encoded_image:str | None = None,
        encoded_pdf:str | None = None,
        ) -> Any:
    
    # Get API key
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if OPENAI_API_KEY is None:
        raise RuntimeError("OPENAI_API_KEY not found—did you create a .env with that variable?")

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    """Send a prompt and text to GPT and return its response."""
    content = []
    if text_to_analize:
        content.append({"type": "text", "text": text_to_analize})

    elif encoded_image:
        content.append({
            "type": "image_url", 
            "image_url": {
                "url": f"data:image/jpeg;base64,{encoded_image}",
                "detail": "high"
                }
            })
    
    elif encoded_pdf:
        content.append({
            "type": "file",
            "file": {
                "file_data": f"data:application/pdf;base64,{encoded_pdf}",
                "filename": f"file_{int(time.time())}.pdf'"
                }
            })
    
    
    chat_response = await client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        temperature=0,
        response_format=response_format
    )

    response_content = None
    if isinstance(response_format, dict):
        response_content = chat_response.choices[0].message.content
    elif issubclass(response_format, BaseModel):
        response_content = chat_response.choices[0].message.parsed

    if response_content is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Received None content from chat response"
        )
    return response_content
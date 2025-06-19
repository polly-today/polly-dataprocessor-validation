import time
from typing import Any
from pydantic import BaseModel
import json
import base64
from io import BytesIO
from PyPDF2 import PdfReader
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

        # Decode base64 PDF and detect page count dynamically
        pdf_bytes = base64.b64decode(encoded_pdf)
        reader = PdfReader(BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        print(f"Total pages in PDF: {total_pages}")
        
        all_offers = []
        for page in range(1, total_pages + 1):
            print(f"Processing page {page} of {total_pages}...")
            prompt = f"Please extract the text from page {page} of {total_pages} and return only valid JSON matching the schema."
            
            try:
                chat_response = await client.beta.chat.completions.parse(
                    model=model,
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": content},
                        {"role": "user",   "content": prompt}
                    ],
                    temperature=0,
                    response_format=response_format
                )
            except Exception as e:
                print(f"Error processing page {page}: {e}")
                continue

            # Parse page response
            if isinstance(response_format, dict):
                page_data = json.loads(chat_response.choices[0].message.content)
            else:
                page_data = response_format.parse_obj(json.loads(chat_response.choices[0].message.content)).dict()
            offers = page_data.get("product_offers", [])
            all_offers.extend(offers)

        # Return unified JSON
        return {"product_offers": all_offers}

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

    return response_content
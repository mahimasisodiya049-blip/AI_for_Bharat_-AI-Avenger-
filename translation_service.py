"""
Translation service with Bhashini API integration and timeout handling.
"""

import requests
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from config import config

logger = logging.getLogger(__name__)

# Bhashini API timeout in seconds
BHASHINI_TIMEOUT = 10


class TranslationRequest(BaseModel):
    text: str
    source_language: str
    target_language: str


class TranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str


async def translate_text(
    text: str,
    source_lang: str,
    target_lang: str
) -> str:
    """
    Translate text using Bhashini API with timeout handling.
    
    Args:
        text: Text to translate
        source_lang: Source language code (e.g., 'en', 'hi', 'ta')
        target_lang: Target language code
        
    Returns:
        Translated text
        
    Raises:
        HTTPException: If translation fails or times out
    """
    # If source and target are the same, return original text
    if source_lang == target_lang:
        return text
    
    # Check if Bhashini API is configured
    if not config.BHASHINI_API_KEY or not config.BHASHINI_API_URL:
        logger.warning("Bhashini API not configured, returning original text")
        return text  # Fallback to original text
    
    try:
        # Prepare request payload
        payload = {
            "text": text,
            "source_language": source_lang,
            "target_language": target_lang
        }
        
        headers = {
            "Authorization": f"Bearer {config.BHASHINI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Make request with timeout
        response = requests.post(
            f"{config.BHASHINI_API_URL}/translate",
            json=payload,
            headers=headers,
            timeout=BHASHINI_TIMEOUT
        )
        
        # Check response status
        if response.status_code == 200:
            result = response.json()
            translated_text = result.get('translated_text', text)
            logger.info(f"Successfully translated text from {source_lang} to {target_lang}")
            return translated_text
        elif response.status_code == 401:
            raise HTTPException(
                status_code=503,
                detail="Bhashini API authentication failed. Please check your API key."
            )
        elif response.status_code == 429:
            raise HTTPException(
                status_code=503,
                detail="Bhashini API rate limit exceeded. Please try again later."
            )
        else:
            logger.error(f"Bhashini API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=503,
                detail=f"Translation service error: {response.status_code}"
            )
            
    except requests.Timeout:
        logger.error(f"Bhashini API timeout after {BHASHINI_TIMEOUT} seconds")
        raise HTTPException(
            status_code=503,
            detail=f"Translation service timeout. The service did not respond within {BHASHINI_TIMEOUT} seconds."
        )
    except requests.ConnectionError:
        logger.error("Bhashini API connection error")
        raise HTTPException(
            status_code=503,
            detail="Translation service unavailable. Please check your internet connection."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected translation error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Translation service error: {str(e)}"
        )


# Supported language codes
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'ta': 'Tamil',
    'te': 'Telugu',
    'bn': 'Bengali',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'pa': 'Punjabi'
}


def get_supported_languages() -> dict:
    """Get list of supported languages."""
    return SUPPORTED_LANGUAGES

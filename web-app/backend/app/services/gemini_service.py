"""
Gemini API service abstraction layer.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini API."""
    
    def __init__(self):
        """Initialize Gemini client."""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
        self.timeout = settings.GEMINI_TIMEOUT_SECONDS
    
    def generate_content(
        self,
        prompt: str,
        safety_settings: Optional[Dict[str, Any]] = None,
        generation_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate content using Gemini API.
        
        Args:
            prompt: Input prompt text
            safety_settings: Safety settings override
            generation_config: Generation config override
        
        Returns:
            Generated text response
        """
        try:
            # Default safety settings - allow all for now
            if safety_settings is None:
                safety_settings = [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE"
                    }
                ]
            
            # Default generation config
            if generation_config is None:
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                }
            
            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings,
                generation_config=generation_config
            )
            
            return response.text
        
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def generate_json_content(
        self,
        prompt: str,
        safety_settings: Optional[Dict[str, Any]] = None,
        generation_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate content and parse as JSON.
        
        Args:
            prompt: Input prompt text
            safety_settings: Safety settings override
            generation_config: Generation config override
        
        Returns:
            Parsed JSON response
        """
        try:
            text = self.generate_content(prompt, safety_settings, generation_config)
            
            # Try to extract JSON from markdown code blocks if present
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                text = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                text = text[start:end].strip()
            
            return json.loads(text)
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {text}")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")
        except Exception as e:
            logger.error(f"Error generating JSON content: {e}")
            raise


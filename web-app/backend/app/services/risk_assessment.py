"""
Risk assessment pipeline service.
"""
import logging
from typing import List, Dict, Any, Optional
from app.services.gemini_service import GeminiService
from pathlib import Path

logger = logging.getLogger(__name__)


class RiskAssessmentService:
    """Service for risk assessment using Gemini API."""
    
    def __init__(self, gemini_service: GeminiService):
        """Initialize risk assessment service."""
        self.gemini = gemini_service
        self._prompt_template = None
        self._risk_assessment_template = None
    
    def _load_template(self, filename: str) -> str:
        """Load prompt template from file."""
        template_path = Path(__file__).parent.parent.parent / "assets" / filename
        if not template_path.exists():
            # Fallback to current directory
            template_path = Path(__file__).parent.parent / "assets" / filename
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {filename}")
        
        return template_path.read_text()
    
    def _get_prompt_template(self) -> str:
        """Get prompt template (cached)."""
        if self._prompt_template is None:
            self._prompt_template = self._load_template("prompt.md")
        return self._prompt_template
    
    def _get_risk_assessment_template(self) -> str:
        """Get risk assessment template (cached)."""
        if self._risk_assessment_template is None:
            self._risk_assessment_template = self._load_template("risk_assessment.md")
        return self._risk_assessment_template
    
    def _format_conversation_history_as_xml(self, messages: List[str]) -> str:
        """Format conversation history as XML (placeholder for now)."""
        # TODO: Replace with actual XML formatting when XML extractor is integrated
        return "\n".join(f"<message>{msg}</message>" for msg in messages[-5:])
    
    def assess_risk(
        self,
        draft_text: str,
        conversation_history: List[str],
        masked_draft: Optional[str] = None,
        masked_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Assess risk of a draft message.
        
        Args:
            draft_text: Original draft text
            conversation_history: List of previous messages
            masked_draft: Masked draft (if already processed)
            masked_history: Masked history (if already processed)
        
        Returns:
            Risk assessment result with risk_level, explanation, safer_rewrite, etc.
        """
        try:
            # Use masked versions if provided, otherwise use originals
            draft = masked_draft if masked_draft else draft_text
            history = masked_history if masked_history else conversation_history
            
            # Format history as XML
            history_xml = self._format_conversation_history_as_xml(history)
            
            # Step 1: Load and fill first prompt template
            prompt_template = self._get_prompt_template()
            first_prompt = prompt_template.replace("{history}", history_xml)
            first_prompt = first_prompt.replace("{input}", draft)
            first_prompt = first_prompt.replace(
                "{rag_examples",
                """[
                    {
                        "summary": "Stranger requests OTP after casual greeting",
                        "ground_truth": "Malicious",
                        "key_pattern": "Credential request after rapport-building"
                    },
                    {
                        "summary": "Recruiter requests ID after interview",
                        "ground_truth": "Benign",
                        "key_pattern": "Contextually justified document request"
                    }
                ]"""
            )
            
            # Step 2: Call Gemini API for first stage
            logger.info("Calling Gemini API for first stage analysis")
            first_stage_result = self.gemini.generate_json_content(first_prompt)
            
            # Step 3: Load and fill risk assessment template
            risk_template = self._get_risk_assessment_template()
            second_prompt = risk_template.replace(
                "{prompt_output}",
                json.dumps(first_stage_result, indent=2)
            )
            
            # Step 4: Call Gemini API for second stage
            logger.info("Calling Gemini API for risk assessment")
            risk_result = self.gemini.generate_json_content(second_prompt)
            
            # Parse result
            risk_level = risk_result.get("Risk_Level", "LOW").upper()
            explanation = risk_result.get("Explanation", "")
            show_warning = risk_result.get("Show_Warning", False)
            
            # Generate safer rewrite (simplified for now)
            safer_rewrite = self._generate_safer_rewrite(draft_text, risk_result)
            
            return {
                "risk_level": risk_level,
                "explanation": explanation,
                "safer_rewrite": safer_rewrite,
                "show_warning": show_warning,
                "primary_risk_factors": risk_result.get("Primary_Risk_Factors", []),
                "first_stage_analysis": first_stage_result
            }
        
        except Exception as e:
            logger.error(f"Risk assessment error: {e}", exc_info=True)
            # Return safe default
            return {
                "risk_level": "LOW",
                "explanation": f"Error during assessment: {str(e)}",
                "safer_rewrite": draft_text,
                "show_warning": False,
                "primary_risk_factors": [],
                "error": str(e)
            }
    
    def _generate_safer_rewrite(
        self,
        original_text: str,
        risk_result: Dict[str, Any]
    ) -> str:
        """
        Generate a safer rewrite suggestion.
        This is a placeholder - could be enhanced with LLM generation.
        """
        # For now, return original text
        # TODO: Implement actual rewrite generation
        return original_text


import json


"""
GLiNER service implementation for PII detection and masking.
Based on the gliner_chunking.ipynb notebook logic.
"""

import logging
import os
from typing import List, Optional
from dataclasses import dataclass
from gliner import GLiNER
from transformers import AutoTokenizer
from nltk.tokenize import sent_tokenize
import nltk

logger = logging.getLogger(__name__)


@dataclass
class PiiSpan:
    """Represents a detected PII span."""
    start: int
    end: int
    label: str
    text: str


@dataclass
class MaskingResult:
    """Result of masking and chunking operation."""
    masked_text: str
    chunks: List[str]
    pii_spans: List[PiiSpan]


class GliNERService:
    """Service for GLiNER-based PII detection and masking."""
    
    # PII labels from the notebook
    PERSONAL_LABELS = [
        "name",
        "first name",
        "last name",
        "name medical professional",
        "dob",
        "age",
        "gender",
        "marital status"
    ]
    
    CONTACT_LABELS = [
        "email address",
        "phone number",
        "ip address",
        "url",
        "location address",
        "location street",
        "location city",
        "location state",
        "location country",
        "location zip"
    ]
    
    FINANCIAL_LABELS = [
        "account number",
        "bank account",
        "routing number",
        "credit card",
        "credit card expiration",
        "cvv",
        "ssn",
        "money"
    ]
    
    HEALTHCARE_LABELS = [
        "condition",
        "medical process",
        "drug",
        "dose",
        "blood type",
        "injury",
        "organization medical facility",
        "healthcare number",
        "medical code"
    ]
    
    ID_LABELS = [
        "passport number",
        "driver license",
        "username",
        "password",
        "vehicle id"
    ]
    
    def __init__(self, model_name: str | None = None):
        """Initialize GLiNER model and tokenizer."""
        self.model_name = model_name or os.getenv("GLINER_MODEL_NAME", "knowledgator/gliner-pii-base-v1.0")
        self.model: Optional[GLiNER] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.labels = (
            self.PERSONAL_LABELS +
            self.CONTACT_LABELS +
            self.FINANCIAL_LABELS +
            self.HEALTHCARE_LABELS +
            self.ID_LABELS
        )
        self._initialized = False
        
    def _ensure_nltk_data(self):
        """Ensure NLTK punkt tokenizer data is available."""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            logger.info("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt', quiet=True)
    
    def initialize(self):
        """Lazy initialization of model and tokenizer."""
        if self._initialized:
            return
        
        try:
            logger.info(f"Loading GLiNER model: {self.model_name}")
            try:
                self.model = GLiNER.from_pretrained(self.model_name, strict=False)
            except TypeError:
                self.model = GLiNER.from_pretrained(self.model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._ensure_nltk_data()
            self._initialized = True
            logger.info("GLiNER model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load GLiNER model: {e}")
            raise
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._initialized and self.model is not None
    
    def mask_and_chunk(
        self,
        text: str,
        max_tokens: int = 512
    ) -> MaskingResult:
        """
        Mask PII entities and chunk text.
        
        Args:
            text: Input text to process
            max_tokens: Maximum tokens per chunk
            
        Returns:
            MaskingResult with masked text, chunks, and PII spans
        """
        if not self.is_loaded():
            self.initialize()
        logger.info("GLiNER masking start (len=%s)", len(text))
        
        # Step 1: Detect PII entities
        entities = self.model.predict_entities(text, self.labels)
        
        # Step 2: Mask PII entities (replace from end to start to preserve positions)
        masked_text = text
        pii_spans = []
        
        for ent in sorted(entities, key=lambda x: x['start'], reverse=True):
            label = ent['label'].upper().replace(" ", "_")
            tag = f"[{label}]"
            
            # Store PII span info
            pii_spans.append(PiiSpan(
                start=ent['start'],
                end=ent['end'],
                label=ent['label'],
                text=text[ent['start']:ent['end']]
            ))
            
            # Replace entity with tag
            masked_text = masked_text[:ent['start']] + tag + masked_text[ent['end']:]
        
        # Step 3: Chunk the masked text
        chunks = self._chunk_sentences(masked_text, max_tokens)
        
        # Sort PII spans by start position for return
        pii_spans.sort(key=lambda x: x.start)
        
        return MaskingResult(
            masked_text=masked_text,
            chunks=chunks,
            pii_spans=pii_spans
        )
    
    def _chunk_sentences(self, text: str, max_tokens: int) -> List[str]:
        """
        Chunk text by sentences respecting token limit.
        Based on the notebook's chunk_sentences function.
        """
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            # Encode sentence to get token count
            sentence_tokens = self.tokenizer.encode(
                sentence,
                add_special_tokens=False
            )
            sentence_token_len = len(sentence_tokens)
            
            if current_tokens + sentence_token_len <= max_tokens:
                current_chunk.append(sentence)
                current_tokens += sentence_token_len
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_token_len
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        # If no chunks created (empty text), return empty list
        return chunks if chunks else [text] if text else []
    
    def cleanup(self):
        """Cleanup resources."""
        self.model = None
        self.tokenizer = None
        self._initialized = False
        logger.info("GLiNER service cleaned up")

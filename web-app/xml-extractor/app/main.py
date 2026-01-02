"""
Stub XML extractor service.
This is a placeholder for the XML extractor that will be integrated later.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="XML Extractor Service",
    description="Stub service for XML extraction (to be implemented)",
    version="1.0.0-stub"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExtractRequest(BaseModel):
    """XML extraction request."""
    text: str
    metadata: Optional[dict] = None


class ExtractResponse(BaseModel):
    """XML extraction response."""
    xml_content: str
    status: str = "stub"


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "xml-extractor",
        "version": "stub"
    }


@app.post("/extract")
async def extract_xml(request: ExtractRequest):
    """
    Stub endpoint for XML extraction.
    Returns placeholder XML structure.
    """
    logger.info(f"XML extraction requested (stub mode): {len(request.text)} chars")
    
    # Stub response - return simple XML wrapper
    xml_content = f"""<conversation>
    <message>{request.text}</message>
</conversation>"""
    
    return ExtractResponse(
        xml_content=xml_content,
        status="stub"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)


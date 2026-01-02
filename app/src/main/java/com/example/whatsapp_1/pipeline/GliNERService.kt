package com.example.whatsapp_1.pipeline

/**
 * Service for GLiNER-based PII masking and chunking.
 * 
 * Implementations:
 * 1. BackendGliNERService - Calls FastAPI backend (Cloud Run + Cloudflare)
 * 2. StubGliNERService - Local stub for testing/fallback
 */
interface GliNERService {
    suspend fun maskAndChunk(
        text: String,
        maxTokens: Int = 512
    ): MaskingResult
}

data class MaskingResult(
    val maskedText: String,
    val chunks: List<String>,
    val piiSpans: List<PiiSpan>
)

/**
 * Stub implementation that performs basic placeholder masking.
 * Replace this with actual GLiNER integration (backend service or local model).
 */
class StubGliNERService : GliNERService {
    override suspend fun maskAndChunk(
        text: String,
        maxTokens: Int
    ): MaskingResult {
        // For now, return text as-is with empty PII spans
        // This will be replaced with actual GLiNER logic
        val chunks = chunkBySentences(text, maxTokens)
        return MaskingResult(
            maskedText = text, // Will be masked by actual GLiNER
            chunks = chunks,
            piiSpans = emptyList()
        )
    }
    
    private fun chunkBySentences(text: String, maxTokens: Int): List<String> {
        // Simple sentence splitting (can be enhanced with proper tokenization)
        val sentences = text.split(Regex("[.!?]+\\s+"))
        val chunks = mutableListOf<String>()
        var currentChunk = StringBuilder()
        
        for (sentence in sentences) {
            val sentenceWithPunctuation = sentence.trim()
            if (sentenceWithPunctuation.isEmpty()) continue
            
            // Simple token estimation (rough: 1 token ≈ 4 characters)
            val estimatedTokens = sentenceWithPunctuation.length / 4
            
            if (currentChunk.isNotEmpty() && 
                (currentChunk.length + sentenceWithPunctuation.length) / 4 > maxTokens) {
                chunks.add(currentChunk.toString().trim())
                currentChunk.clear()
            }
            
            if (currentChunk.isNotEmpty()) {
                currentChunk.append(" ")
            }
            currentChunk.append(sentenceWithPunctuation)
        }
        
        if (currentChunk.isNotEmpty()) {
            chunks.add(currentChunk.toString().trim())
        }
        
        return if (chunks.isEmpty()) listOf(text) else chunks
    }
}

/**
 * Backend implementation that calls the FastAPI GLiNER service.
 * Uses BackendApiClient to communicate with Cloud Run + Cloudflare backend.
 */
class BackendGliNERService(
    private val backendClient: com.example.whatsapp_1.api.backend.BackendApiClient
) : GliNERService {
    override suspend fun maskAndChunk(
        text: String,
        maxTokens: Int
    ): MaskingResult {
        val result = backendClient.maskAndChunk(text, maxTokens)
        
        return result.getOrElse { throwable ->
            // If backend fails, throw exception (caller can handle fallback)
            throw Exception("Backend GLiNER service failed: ${throwable.message}", throwable)
        }.let { response ->
            MaskingResult(
                maskedText = response.maskedText,
                chunks = response.chunks,
                piiSpans = response.piiSpans.map { span ->
                    PiiSpan(
                        start = span.start,
                        end = span.end,
                        label = span.label
                    )
                }
            )
        }
    }
}


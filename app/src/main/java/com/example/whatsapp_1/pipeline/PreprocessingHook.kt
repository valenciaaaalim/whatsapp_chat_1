package com.example.whatsapp_1.pipeline

/**
 * Hook for preprocessing text with GLiNER chunking and PII masking.
 * Uses GliNERService to perform actual masking and chunking.
 */
data class PreprocessingResult(
    val maskedDraft: String,
    val maskedContextChunks: List<String>,
    val piiSpans: List<PiiSpan> = emptyList()
)

data class PiiSpan(
    val start: Int,
    val end: Int,
    val label: String
)

interface PreprocessingHook {
    suspend fun preprocessWithGilnerChunking(
        draftText: String,
        conversationHistory: List<String>
    ): PreprocessingResult
}

class GliNERPreprocessingHook(
    private val gliNERService: GliNERService
) : PreprocessingHook {
    override suspend fun preprocessWithGilnerChunking(
        draftText: String,
        conversationHistory: List<String>
    ): PreprocessingResult {
        // Mask and chunk the draft text
        val draftResult = gliNERService.maskAndChunk(draftText)
        
        // Mask and chunk conversation history
        val maskedHistoryChunks = conversationHistory.flatMap { historyMsg ->
            gliNERService.maskAndChunk(historyMsg).chunks
        }
        
        return PreprocessingResult(
            maskedDraft = draftResult.maskedText,
            maskedContextChunks = maskedHistoryChunks + draftResult.chunks,
            piiSpans = draftResult.piiSpans
        )
    }
}

class StubPreprocessingHook : PreprocessingHook {
    override suspend fun preprocessWithGilnerChunking(
        draftText: String,
        conversationHistory: List<String>
    ): PreprocessingResult {
        // Stub implementation - returns text as-is
        return PreprocessingResult(
            maskedDraft = draftText,
            maskedContextChunks = listOf(draftText),
            piiSpans = emptyList()
        )
    }
}


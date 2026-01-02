package com.example.whatsapp_1.pipeline

import com.example.whatsapp_1.data.RiskLevel
import com.example.whatsapp_1.data.WarningState
import java.util.UUID

/**
 * Hook for LLM-based risk assessment.
 * Uses RiskAssessmentPipeline to perform two-stage Gemini API calls.
 */
interface RiskAssessmentHook {
    suspend fun assessRiskLLM(
        maskedDraft: String,
        maskedContextChunks: List<String>,
        conversationHistory: List<String>
    ): WarningState?
    
    fun cancelCurrentAssessment()
}

class GeminiRiskAssessmentHook(
    private val pipeline: RiskAssessmentPipeline
) : RiskAssessmentHook {
    private var currentRequestId: String? = null
    
    override suspend fun assessRiskLLM(
        maskedDraft: String,
        maskedContextChunks: List<String>,
        conversationHistory: List<String>
    ): WarningState? {
        val requestId = UUID.randomUUID().toString()
        currentRequestId = requestId
        
        val result = pipeline.assessRisk(
            draftText = maskedDraft,
            conversationHistory = conversationHistory,
            requestId = requestId
        )
        
        return when (result) {
            is RiskAssessmentResult.Success -> {
                if (result.showWarning) {
                    result.warningState
                } else {
                    null
                }
            }
            is RiskAssessmentResult.Error -> {
                // Log error but don't show warning
                null
            }
            is RiskAssessmentResult.Cancelled -> {
                null
            }
        }
    }
    
    override fun cancelCurrentAssessment() {
        currentRequestId?.let { pipeline.cancelRequest(it) }
        currentRequestId = null
    }
}

class StubRiskAssessmentHook : RiskAssessmentHook {
    override suspend fun assessRiskLLM(
        maskedDraft: String,
        maskedContextChunks: List<String>,
        conversationHistory: List<String>
    ): WarningState? {
        // Stub implementation - returns null (no risk) for now
        // Can be modified to return mock WarningState for testing
        return null
    }
    
    override fun cancelCurrentAssessment() {
        // No-op for stub
    }
}


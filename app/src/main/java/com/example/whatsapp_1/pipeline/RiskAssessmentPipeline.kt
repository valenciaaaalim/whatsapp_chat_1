package com.example.whatsapp_1.pipeline

import android.content.Context
import com.example.whatsapp_1.api.gemini.GeminiApiClient
import com.google.gson.Gson
import com.google.gson.JsonObject
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

/**
 * Two-stage risk assessment pipeline:
 * 1. First prompt: Analyze conversation (prompt.md template)
 * 2. Second prompt: Assess risk (risk_assessment.md template)
 * 
 * Includes concurrency control to prevent multiple simultaneous API calls.
 */
class RiskAssessmentPipeline(
    private val context: Context,
    private val geminiApiClient: GeminiApiClient?,
    private val gliNERService: GliNERService
) {
    private val gson = Gson()
    private val pipelineMutex = Mutex()
    private var currentRequestId: String? = null
    
    /**
     * Formats conversation history as XML (placeholder for now).
     * This will be replaced with actual XML formatting when that code is integrated.
     */
    private fun formatConversationHistoryAsXml(messages: List<String>): String {
        // Placeholder: Return simple text format for now
        // TODO: Replace with actual XML formatting
        return messages.joinToString("\n") { "<message>$it</message>" }
    }
    
    suspend fun assessRisk(
        draftText: String,
        conversationHistory: List<String>,
        requestId: String
    ): RiskAssessmentResult {
        // Check if there's an ongoing request
        pipelineMutex.withLock {
            // If a different request is in progress, cancel this one
            if (currentRequestId != null && currentRequestId != requestId) {
                return RiskAssessmentResult.Cancelled
            }
            
            currentRequestId = requestId
        }
        
        return try {
            // Step 1: Mask and chunk using GLiNER
            val maskingResult = gliNERService.maskAndChunk(draftText)
            val maskedDraft = maskingResult.maskedText
            val maskedHistory = conversationHistory.map { historyMsg ->
                gliNERService.maskAndChunk(historyMsg).maskedText
            }
            
            // Step 2: Format conversation history (XML placeholder)
            val historyXml = formatConversationHistoryAsXml(maskedHistory.takeLast(5))
            
            // Step 3: Load and fill first prompt template
            val promptTemplate = loadTemplate("prompt.md")
            val firstPrompt = PromptTemplate.fillPromptTemplate(
                template = promptTemplate,
                history = historyXml,
                input = maskedDraft
            )
            
            // Step 4: Call Gemini API for first stage
            val firstStageResult = geminiApiClient?.generateContent(firstPrompt)
                ?: return RiskAssessmentResult.Error("Gemini API client not initialized")
            
            val analysisJson = firstStageResult.getOrElse {
                return RiskAssessmentResult.Error("First stage failed: ${it.message}")
            }
            
            // Step 5: Load and fill risk assessment template
            val riskAssessmentTemplate = loadTemplate("risk_assessment.md")
            val secondPrompt = PromptTemplate.fillRiskAssessmentTemplate(
                template = riskAssessmentTemplate,
                promptOutput = analysisJson
            )
            
            // Step 6: Call Gemini API for second stage
            val secondStageResult = geminiApiClient.generateContent(secondPrompt)
                ?: return RiskAssessmentResult.Error("Gemini API client not initialized")
            
            val riskJson = secondStageResult.getOrElse {
                return RiskAssessmentResult.Error("Second stage failed: ${it.message}")
            }
            
            // Step 7: Parse risk assessment result
            val riskAssessment = parseRiskAssessment(riskJson)
            
            // Clear current request
            pipelineMutex.withLock {
                if (currentRequestId == requestId) {
                    currentRequestId = null
                }
            }
            
            riskAssessment
        } catch (e: Exception) {
            pipelineMutex.withLock {
                if (currentRequestId == requestId) {
                    currentRequestId = null
                }
            }
            RiskAssessmentResult.Error("Pipeline error: ${e.message}")
        }
    }
    
    fun cancelRequest(requestId: String) {
        // This allows cancelling if needed
        // The mutex will handle preventing new requests
    }
    
    private fun loadTemplate(filename: String): String {
        return try {
            context.assets.open(filename).bufferedReader().use { it.readText() }
        } catch (e: Exception) {
            // Fallback to empty template if file not found
            ""
        }
    }
    
    private fun parseRiskAssessment(jsonString: String): RiskAssessmentResult {
        return try {
            val json = gson.fromJson(jsonString, JsonObject::class.java)
            val riskLevelStr = json.get("Risk_Level")?.asString ?: "Low"
            val explanation = json.get("Explanation")?.asString ?: "No explanation provided"
            val showWarning = json.get("Show_Warning")?.asBoolean ?: false
            
            // Extract primary risk factors
            val riskFactors = json.get("Primary_Risk_Factors")?.asJsonArray?.map { it.asString }
                ?: emptyList()
            
            val riskLevel = when (riskLevelStr.lowercase()) {
                "high" -> com.example.whatsapp_1.data.RiskLevel.HIGH
                "medium" -> com.example.whatsapp_1.data.RiskLevel.MEDIUM
                else -> com.example.whatsapp_1.data.RiskLevel.LOW
            }
            
            // Generate safer rewrite (placeholder - can be enhanced)
            val saferRewrite = generateSaferRewrite(explanation, riskFactors)
            
            RiskAssessmentResult.Success(
                warningState = com.example.whatsapp_1.data.WarningState(
                    riskLevel = riskLevel,
                    explanation = explanation,
                    saferRewrite = saferRewrite
                ),
                showWarning = showWarning
            )
        } catch (e: Exception) {
            RiskAssessmentResult.Error("Failed to parse risk assessment: ${e.message}")
        }
    }
    
    private fun generateSaferRewrite(explanation: String, riskFactors: List<String>): String {
        // Placeholder: Return a generic safer rewrite suggestion
        // This can be enhanced to use the explanation and risk factors
        return "Consider revising this message to reduce privacy risk."
    }
}

sealed class RiskAssessmentResult {
    data class Success(
        val warningState: com.example.whatsapp_1.data.WarningState,
        val showWarning: Boolean
    ) : RiskAssessmentResult()
    
    data class Error(val message: String) : RiskAssessmentResult()
    object Cancelled : RiskAssessmentResult()
}


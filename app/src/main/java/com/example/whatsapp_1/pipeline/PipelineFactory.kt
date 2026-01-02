package com.example.whatsapp_1.pipeline

import android.content.Context
import com.example.whatsapp_1.api.backend.BackendApiClient
import com.example.whatsapp_1.api.gemini.GeminiApiClient
import com.example.whatsapp_1.config.SecretsManager

/**
 * Factory for creating pipeline components.
 * Handles initialization of GLiNER service, Gemini API client, and risk assessment pipeline.
 */
object PipelineFactory {
    fun createPreprocessingHook(context: Context): PreprocessingHook {
        // Initialize secrets manager
        SecretsManager.initialize(context)
        
        // Try to create backend GLiNER service
        val gliNERService: GliNERService = createGliNERService(context)
        
        return GliNERPreprocessingHook(gliNERService)
    }
    
    fun createRiskAssessmentHook(context: Context): RiskAssessmentHook {
        // Initialize secrets manager
        SecretsManager.initialize(context)
        
        // Get Gemini API key
        val apiKey = SecretsManager.getGeminiApiKey()
        
        // Create Gemini API client if key is available
        val geminiClient = apiKey?.let { GeminiApiClient(it) }
        
        // Create GLiNER service (backend or stub)
        val gliNERService: GliNERService = createGliNERService(context)
        
        // Create risk assessment pipeline
        val pipeline = RiskAssessmentPipeline(
            context = context,
            geminiApiClient = geminiClient,
            gliNERService = gliNERService
        )
        
        // Return appropriate hook based on whether API key is available
        return if (geminiClient != null) {
            GeminiRiskAssessmentHook(pipeline)
        } else {
            // Fall back to stub if no API key
            StubRiskAssessmentHook()
        }
    }
    
    private fun createGliNERService(context: Context): GliNERService {
        // Initialize secrets manager if not already done
        SecretsManager.initialize(context)
        
        // Try to get backend URL
        val backendUrl = SecretsManager.getBackendUrl()
        val backendApiKey = SecretsManager.getBackendApiKey()
        
        return if (!backendUrl.isNullOrBlank()) {
            // Create backend client
            val backendClient = BackendApiClient(
                baseUrl = backendUrl.trimEnd('/'),
                apiKey = backendApiKey
            )
            
            // Use backend service
            BackendGliNERService(backendClient)
        } else {
            // Fall back to stub if no backend URL configured
            StubGliNERService()
        }
    }
}


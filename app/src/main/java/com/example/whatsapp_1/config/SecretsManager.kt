package com.example.whatsapp_1.config

import android.content.Context
import java.io.File
import java.util.Properties

object SecretsManager {
    private var properties: Properties? = null
    
    fun initialize(context: Context) {
        try {
            // Try to load from app/secrets.properties file
            // This file should be placed in app/secrets.properties (same level as build.gradle.kts)
            // and should be gitignored
            val appDir = File(context.filesDir.parentFile?.parentFile, "app")
            val secretsFile = File(appDir, "secrets.properties")
            
            if (secretsFile.exists()) {
                secretsFile.inputStream().use { inputStream ->
                    properties = Properties().apply {
                        load(inputStream)
                    }
                }
            } else {
                // Fallback: try assets folder (for development/testing)
                try {
                    val inputStream = context.assets.open("secrets.properties")
                    properties = Properties().apply {
                        load(inputStream)
                    }
                    inputStream.close()
                } catch (e: Exception) {
                    // If neither exists, properties will remain null
                    // This allows the app to run with stubbed implementations
                }
            }
        } catch (e: Exception) {
            // If secrets.properties doesn't exist, properties will remain null
            // This allows the app to run with stubbed implementations
        }
    }
    
    fun getGeminiApiKey(): String? {
        return properties?.getProperty("GEMINI_API_KEY")
    }
    
    fun getBackendUrl(): String? {
        return properties?.getProperty("BACKEND_URL")
    }
    
    fun getBackendApiKey(): String? {
        return properties?.getProperty("BACKEND_API_KEY")
    }
}


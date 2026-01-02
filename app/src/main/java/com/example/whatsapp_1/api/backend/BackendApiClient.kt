package com.example.whatsapp_1.api.backend

import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import java.io.IOException
import java.util.concurrent.TimeUnit

data class MaskRequest(
    val text: String,
    @SerializedName("max_tokens")
    val maxTokens: Int = 512
)

data class MaskResponse(
    @SerializedName("masked_text")
    val maskedText: String,
    val chunks: List<String>,
    @SerializedName("pii_spans")
    val piiSpans: List<PiiSpanResponse>,
    @SerializedName("processing_time_ms")
    val processingTimeMs: Double
)

data class PiiSpanResponse(
    val start: Int,
    val end: Int,
    val label: String,
    val text: String
)

data class HealthResponse(
    val status: String,
    @SerializedName("model_loaded")
    val modelLoaded: Boolean,
    val version: String
)

class BackendApiClient(
    private val baseUrl: String,
    private val apiKey: String? = null
) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .build()
    
    private val gson = Gson()
    private val jsonMediaType = "application/json".toMediaType()
    
    suspend fun checkHealth(): Result<HealthResponse> = withContext(Dispatchers.IO) {
        try {
            val url = "$baseUrl/health"
            val request = buildRequest(url)
            
            val response: Response = client.newCall(request).execute()
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(
                    IOException("Health check failed: ${response.code} ${response.message}")
                )
            }
            
            val responseBody = response.body?.string() ?: ""
            val healthResponse = gson.fromJson(responseBody, HealthResponse::class.java)
            
            Result.success(healthResponse)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun maskAndChunk(
        text: String,
        maxTokens: Int = 512
    ): Result<MaskResponse> = withContext(Dispatchers.IO) {
        try {
            val requestBody = MaskRequest(text = text, maxTokens = maxTokens)
            val jsonBody = gson.toJson(requestBody)
            val body = jsonBody.toRequestBody(jsonMediaType)
            
            val url = "$baseUrl/mask"
            val request = buildRequest(url)
                .post(body)
                .build()
            
            val response: Response = client.newCall(request).execute()
            
            if (!response.isSuccessful) {
                val errorBody = response.body?.string() ?: ""
                return@withContext Result.failure(
                    IOException("API call failed: ${response.code} ${response.message}. $errorBody")
                )
            }
            
            val responseBody = response.body?.string() ?: ""
            val maskResponse = gson.fromJson(responseBody, MaskResponse::class.java)
            
            Result.success(maskResponse)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    private fun buildRequest(url: String): Request.Builder {
        val builder = Request.Builder().url(url)
        
        // Add API key header if provided
        apiKey?.let {
            builder.addHeader("X-API-Key", it)
        }
        
        return builder
    }
}


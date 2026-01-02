package com.example.whatsapp_1.api.gemini

import com.google.gson.Gson
import com.google.gson.JsonObject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import java.io.IOException

data class GeminiRequest(
    val contents: List<Content>
)

data class Content(
    val parts: List<Part>
)

data class Part(
    val text: String
)

data class GeminiResponse(
    val candidates: List<Candidate>?
)

data class Candidate(
    val content: Content?
)

class GeminiApiClient(private val apiKey: String) {
    private val client = OkHttpClient()
    private val gson = Gson()
    private val baseUrl = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    
    suspend fun generateContent(prompt: String): Result<String> = withContext(Dispatchers.IO) {
        try {
            val requestBody = GeminiRequest(
                contents = listOf(
                    Content(
                        parts = listOf(
                            Part(text = prompt)
                        )
                    )
                )
            )
            
            val jsonBody = gson.toJson(requestBody)
            val mediaType = "application/json".toMediaType()
            val body = jsonBody.toRequestBody(mediaType)
            
            val url = "$baseUrl?key=$apiKey"
            val request = Request.Builder()
                .url(url)
                .post(body)
                .build()
            
            val response: Response = client.newCall(request).execute()
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(
                    IOException("API call failed: ${response.code} ${response.message}")
                )
            }
            
            val responseBody = response.body?.string() ?: ""
            val geminiResponse = gson.fromJson(responseBody, GeminiResponse::class.java)
            
            val text = geminiResponse.candidates?.firstOrNull()?.content?.parts?.firstOrNull()?.text
                ?: return@withContext Result.failure(IOException("No text in response"))
            
            Result.success(text)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}


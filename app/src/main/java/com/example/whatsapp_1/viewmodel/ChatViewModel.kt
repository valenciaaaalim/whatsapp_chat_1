package com.example.whatsapp_1.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.whatsapp_1.data.ChatUiState
import com.example.whatsapp_1.data.Message
import com.example.whatsapp_1.data.MessageDirection
import com.example.whatsapp_1.data.RiskLevel
import com.example.whatsapp_1.data.WarningState
import com.example.whatsapp_1.pipeline.PreprocessingHook
import com.example.whatsapp_1.pipeline.RiskAssessmentHook
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.Date
import java.util.UUID

class ChatViewModel(
    private val preprocessingHook: PreprocessingHook,
    private val riskAssessmentHook: RiskAssessmentHook
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()
    
    private var typingPauseJob: Job? = null
    private val debounceMs = 1500L
    
    fun updateDraftText(text: String) {
        _uiState.update { it.copy(draftText = text) }
        
        // Cancel previous debounce job and any ongoing risk assessment
        typingPauseJob?.cancel()
        riskAssessmentHook.cancelCurrentAssessment()
        
        // Start new debounce job
        if (text.isNotBlank()) {
            typingPauseJob = viewModelScope.launch {
                delay(debounceMs)
                onTypingPaused(text)
            }
        }
    }
    
    private suspend fun onTypingPaused(draftText: String) {
        // Step 1: Preprocess with GLiNER chunking
        val conversationHistory = _uiState.value.messages.map { it.text }
        val preprocessingResult = preprocessingHook.preprocessWithGilnerChunking(
            draftText = draftText,
            conversationHistory = conversationHistory
        )
        
        // Step 2: Assess risk with LLM (using masked content only)
        val warningState = riskAssessmentHook.assessRiskLLM(
            maskedDraft = preprocessingResult.maskedDraft,
            maskedContextChunks = preprocessingResult.maskedContextChunks,
            conversationHistory = conversationHistory
        )
        
        // Step 3: Show warning if risk >= Medium
        if (warningState != null && warningState.riskLevel != RiskLevel.LOW) {
            _uiState.update { it.copy(warningState = warningState) }
        }
    }
    
    fun onSendPressed() {
        val draftText = _uiState.value.draftText.trim()
        if (draftText.isEmpty()) return
        
        // Cancel any pending typing pause job
        typingPauseJob?.cancel()
        
        // Create new message
        val newMessage = Message(
            id = UUID.randomUUID().toString(),
            text = draftText,
            direction = MessageDirection.SENT,
            timestamp = Date()
        )
        
        // Add message to list
        _uiState.update { state ->
            state.copy(
                messages = state.messages + newMessage,
                draftText = "",
                warningState = null
            )
        }
    }
    
    fun acceptSaferRewrite() {
        val warningState = _uiState.value.warningState ?: return
        _uiState.update { state ->
            state.copy(
                draftText = warningState.saferRewrite,
                warningState = null
            )
        }
    }
    
    fun continueAnyway() {
        _uiState.update { it.copy(warningState = null) }
    }
}


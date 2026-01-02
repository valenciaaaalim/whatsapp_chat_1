package com.example.whatsapp_1.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.example.whatsapp_1.pipeline.PreprocessingHook
import com.example.whatsapp_1.pipeline.RiskAssessmentHook

class ChatViewModelFactory(
    private val preprocessingHook: PreprocessingHook,
    private val riskAssessmentHook: RiskAssessmentHook
) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(ChatViewModel::class.java)) {
            return ChatViewModel(preprocessingHook, riskAssessmentHook) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}


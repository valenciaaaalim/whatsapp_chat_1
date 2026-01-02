package com.example.whatsapp_1.data

data class ChatUiState(
    val messages: List<Message> = emptyList(),
    val draftText: String = "",
    val warningState: WarningState? = null
)


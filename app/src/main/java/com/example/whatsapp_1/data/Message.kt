package com.example.whatsapp_1.data

import java.util.Date

data class Message(
    val id: String,
    val text: String,
    val direction: MessageDirection,
    val timestamp: Date
)

enum class MessageDirection {
    SENT,
    RECEIVED
}


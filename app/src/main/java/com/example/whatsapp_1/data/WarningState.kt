package com.example.whatsapp_1.data

enum class RiskLevel {
    LOW,
    MEDIUM,
    HIGH
}

data class WarningState(
    val riskLevel: RiskLevel,
    val explanation: String,
    val saferRewrite: String
)


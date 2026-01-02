package com.example.whatsapp_1.ui.chat

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import com.example.whatsapp_1.data.RiskLevel
import com.example.whatsapp_1.data.WarningState

@Composable
fun WarningModal(
    warningState: WarningState,
    onAcceptRewrite: () -> Unit,
    onContinueAnyway: () -> Unit,
    modifier: Modifier = Modifier
) {
    Dialog(onDismissRequest = onContinueAnyway) {
        Card(
            modifier = modifier
                .fillMaxWidth()
                .padding(16.dp),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surface
            )
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Risk Level Badge
                RiskLevelBadge(riskLevel = warningState.riskLevel)
                
                Spacer(modifier = Modifier.height(16.dp))
                
                // Explanation
                Text(
                    text = warningState.explanation,
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.fillMaxWidth()
                )
                
                Spacer(modifier = Modifier.height(24.dp))
                
                // Buttons
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // Continue anyway (secondary)
                    OutlinedButton(
                        onClick = onContinueAnyway,
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("Continue anyway")
                    }
                    
                    // Accept safer rewrite (primary)
                    Button(
                        onClick = onAcceptRewrite,
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = MaterialTheme.colorScheme.primary
                        )
                    ) {
                        Text("Accept safer rewrite")
                    }
                }
            }
        }
    }
}

@Composable
fun RiskLevelBadge(
    riskLevel: RiskLevel,
    modifier: Modifier = Modifier
) {
    val (text, color) = when (riskLevel) {
        RiskLevel.LOW -> "Low Risk" to Color(0xFF4CAF50)
        RiskLevel.MEDIUM -> "Medium Risk" to Color(0xFFFF9800)
        RiskLevel.HIGH -> "High Risk" to Color(0xFFF44336)
    }
    
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        color = color.copy(alpha = 0.2f)
    ) {
        Text(
            text = text,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.Bold,
            color = color
        )
    }
}


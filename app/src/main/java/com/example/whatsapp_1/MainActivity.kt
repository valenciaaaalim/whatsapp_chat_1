package com.example.whatsapp_1

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.whatsapp_1.pipeline.PipelineFactory
import com.example.whatsapp_1.ui.chat.ChatScreen
import com.example.whatsapp_1.ui.theme.Whatsapp_1Theme
import com.example.whatsapp_1.viewmodel.ChatViewModel
import com.example.whatsapp_1.viewmodel.ChatViewModelFactory

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            Whatsapp_1Theme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val viewModel: ChatViewModel = viewModel(
                        factory = ChatViewModelFactory(
                            preprocessingHook = PipelineFactory.createPreprocessingHook(this),
                            riskAssessmentHook = PipelineFactory.createRiskAssessmentHook(this)
                        )
                    )
                    ChatScreen(
                        viewModel = viewModel,
                        contactName = "John Doe"
                    )
                }
            }
        }
    }
}
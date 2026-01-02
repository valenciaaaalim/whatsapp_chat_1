package com.example.whatsapp_1.pipeline

import java.io.InputStream

object PromptTemplate {
    fun loadTemplate(stream: InputStream): String {
        return stream.bufferedReader().use { it.readText() }
    }
    
    fun fillPromptTemplate(
        template: String,
        history: String,
        input: String,
        ragExamples: String = getDefaultRagExamples()
    ): String {
        var result = template
            .replace("{history}", history)
            .replace("{input}", input)
        
        // Handle {rag_examples...} block replacement
        val ragPattern = Regex("\\{rag_examples[^}]*\\}")
        result = ragPattern.replace(result, ragExamples)
        
        return result
    }
    
    fun fillRiskAssessmentTemplate(
        template: String,
        promptOutput: String
    ): String {
        return template.replace("{prompt_output}", promptOutput)
    }
    
    private fun getDefaultRagExamples(): String {
        return """
		[
		  {
		    "summary": "Stranger requests OTP after casual greeting",
		    "ground_truth": "Malicious",
		    "key_pattern": "Credential request after rapport-building"
		  },
		  {
		    "summary": "Recruiter requests ID after interview",
		    "ground_truth": "Benign",
		    "key_pattern": "Contextually justified document request"
		  }
		]
		"""
    }
}


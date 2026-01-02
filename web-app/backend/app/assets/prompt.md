You are an expert in social engineering and privacy risk analysis.

Analyze the following private messaging conversation.

### INPUT
Conversation History (last 5 turns):
{history}

Current User Message (draft):
{input}

Retrieved Similar Conversations (for reference only):
{rag_examples

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

}

### TASK
Analyze the situation across the following dimensions.
Do NOT assign a risk level yet.

1. PII Sensitivity
- Identify whether the user message contains or reveals personal information.
- Classify the sensitivity based on NIST SP 800-122 (None / Low / Moderate / High).
- Explain briefly why.

2. Contextual Necessity (Validity Gap)
- Is revealing this information logically necessary to achieve the stated purpose of the conversation?
- Consider relationship, role, and platform norms.
- Classify as: Valid / Questionable / Invalid.

3. Intent Trajectory
- Does the conversation progress naturally toward this request, or is there an abrupt pivot?
- You may reference the retrieved similar conversations to identify shared *interaction patterns*.
- Similarity alone does NOT imply malicious intent.
- Classify as: Natural / Mild Divergence / Strong Divergence.

4. Psychological Pressure
- Identify any coercive tactics (urgency, authority, fear, secrecy, guilt).
- Rate intensity: None / Mild / Strong.

5. Identity & Trust Signals
- Is the sender's identity consistent with the contact context?
- Are there signs of impersonation, ambiguity, or unverifiable claims?

### OUTPUT
Return a JSON object with one field per dimension and a short explanation for each.
Do NOT summarize or assign a final risk.


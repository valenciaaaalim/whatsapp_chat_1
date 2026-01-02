You are acting as a risk assessor evaluating whether to warn a user about potential privacy harm.

### INPUT
Analysis Summary:
{prompt_output}

### RISK RUBRIC
- LOW RISK:
  Disclosure is low-impact or justified by context. No manipulation or intent divergence.

- MEDIUM RISK:
  Either the data is sensitive but context is ambiguous, OR mild manipulation is present.
  A cautious user should pause and reconsider.

- HIGH RISK:
  Disclosure involves high-impact personal data AND lacks valid justification,
  OR strong indicators of social engineering or coercion are present.

### TASK
1. Determine the overall risk level (Low / Medium / High).
2. Explain which dimensions most strongly influenced this judgment.
3. Suggest whether a warning should be shown.

### OUTPUT
Return JSON:
{
  "Risk_Level": "...",
  "Primary_Risk_Factors": ["..."],
  "Explanation": "...",
  "Show_Warning": true/false
}

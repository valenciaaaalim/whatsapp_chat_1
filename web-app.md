+You are working on this repository to transform the current native application into a secure, test-ready web application. Apply the following requirements comprehensively.
+
+## Core Delivery
+1. **Web App Server (Google Cloud hosting)**
+   - Build a full web application that replicates all core native flows.
+   - Containerize the web app and deploy it on Google Cloud (Cloud Run or GKE).
+   - Provide IaC or deployment scripts, and document the exact deployment steps.
+
+2. **Cloudflare Security**
+   - Front the Google Cloud deployment with Cloudflare for DNS, TLS, DDoS/WAF protection, and rate limiting.
+   - Document DNS and SSL/TLS configuration, origin settings, and any required headers for authenticated edge traffic.
+
+3. **Gemini API Integration**
+   - Provision Gemini API keys and wire them into the backend service.
+   - Abstract model calls behind a service layer with configuration for model names, safety settings, and timeouts.
+
+4. **XML Repo Backend (Docker)**
+   - Integrate the XML extractor repo as a secondary Docker service the web app can call.
+   - Provide a docker-compose (or equivalent) that brings up the web app plus the XML backend, with network wiring and health checks.
+   - Stub the extractor call for now but preserve the integration contract; the full extractor will be added later.
+
+5. **Task Flow & Screens**
+   - Recreate the three testing scenarios by loading the annotated conversations from `annotated_test.json` (each conversation is independent).
+   - Build UI screens for the conversations, survey questions, intermittent checks, and action buttons.
+   - Add a final screen that routes the user back to Prolific via the correct completion URL/token.
+
+## Data & Experimentation
+1. **Conversation Data**
+   - Seed a small database with three sample conversations (use the annotated conversations) that the UI can load.
+
+2. **User Input Capture**
+   - Before a user clicks **Rewrite** or **Ignore**, capture and store the text they typed.
+   - Also store the final submitted text for each of the three scenarios.
+
+3. **Surveys & Intermittent Testing**
+   - Define survey questions and mid-session comprehension checks; persist all answers.
+   - Present survey prompts at logical checkpoints between scenarios.
+
+4. **Storage**
+   - Create a database schema/tables to hold conversation content, survey responses, per-action inputs (pre-click and post-submit), and metadata.
+
+5. **A/B Assignment**
+   - Implement a random assignment algorithm to place each participant into variant A or B, using existing database state to balance groups.
+   - Persist the assignment and expose it to the UI.
+
+6. **Analytics & Audit**
+   - Add server-side logging for all stored inputs and survey answers (no voice/screen/video capture).
+
+## Additional Requirements
+- **No audio/video/screen recording**: ensure the web experience does not request or depend on microphone/camera/screen permissions.
+- Provide developer run instructions for local/dev/prod, including how to run the two-service Docker setup and how to seed the sample data.
+- Keep security best practices: env-based secrets, HTTPS-only cookies, CSRF protection, and input validation.
+
+## Deliverables
+- Updated codebase implementing the web app, services, and storage layers described above.
+- Deployment and Cloudflare configuration documentation.
+- A working seed of three conversations and survey question sets.
+- Prolific return link wired into the final screen.

# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Overview

This project is an Android WhatsApp-style chat client with an AI-powered privacy risk advisor, plus a FastAPI backend for GLiNER-based PII masking and chunking. The Android app can run fully locally with stubbed services, or integrate with the deployed backend and Gemini.

## Core Commands

### Android app (module `app`)

From the project root:

- **Assemble debug APK** (CI-safe build):
  - `./gradlew :app:assembleDebug`
- **Run unit tests (JVM):**
  - `./gradlew :app:testDebugUnitTest`
- **Run instrumentation tests (if devices/emulator available):**
  - `./gradlew :app:connectedAndroidTest`
- **Lint (Android default lint task):**
  - `./gradlew :app:lintDebug`

You will usually launch the app from Android Studio, but these commands are what automated agents and scripts should use.

### Backend (GLiNER PII service in `backend/`)

From the project root unless otherwise noted:

- **Install dependencies (first-time setup):**
  - `cd backend && pip install -r requirements.txt`
- **Run backend locally with auto-reload:**
  - `cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8080`
- **Quick health check while running locally:**
  - `curl http://localhost:8080/health`
- **Smoke-test masking endpoint:**
  - `curl -X POST http://localhost:8080/mask \`
    `  -H "Content-Type: application/json" \`
    `  -d '{"text": "My name is John Doe and my email is john@example.com", "max_tokens": 512}'`
- **Build and run Docker image locally:**
  - `cd backend && docker build -t gliner-pii-service .`
  - `docker run -p 8080:8080 gliner-pii-service`
- **Deploy to Cloud Run using the provided script (see `BACKEND_SETUP.md`/`backend/README.md` for details):**
  - `cd backend && export GOOGLE_CLOUD_PROJECT=your-project-id REGION=us-central1`
  - `./deploy.sh`

## Configuration & Secrets

### Android app secrets (`app/secrets.properties`)

The app reads secrets via `SecretsManager` from a `secrets.properties` file that is **not** checked into git:

- Location (expected): `app/secrets.properties` (same level as `app/build.gradle.kts`).
- This file is gitignored; create it manually based on the documented format in `SETUP.md` and `BACKEND_SETUP.md`.
- Recognized keys:
  - `GEMINI_API_KEY` – used by `GeminiApiClient` for LLM calls.
  - `BACKEND_URL` – base URL for the GLiNER backend (often a Cloudflare-protected Cloud Run URL).
  - `BACKEND_API_KEY` – optional API key sent as `X-API-Key` header to the backend.

If `GEMINI_API_KEY` is missing, the app falls back to `StubRiskAssessmentHook` (no real risk analysis). If `BACKEND_URL` is missing, the app uses `StubGliNERService` (no true PII masking, only basic local chunking).

### Backend configuration

Backend configuration is primarily via environment variables read in `backend/app/config.py`:

- `GLINER_MODEL_NAME` – GLiNER model identifier (default `knowledgator/gliner-pii-base-v1.0`).
- `GOOGLE_CLOUD_PROJECT`, `REGION`, `SERVICE_NAME` – used for Cloud Run deployment.
- `RATE_LIMIT_PER_MINUTE` – for rate-limiting configuration (used together with Cloudflare rules).

The backend also expects CORS origins to be configured via `ALLOWED_ORIGINS` in `backend/app/config.py` (typically your Cloudflare-protected domain and localhost for testing).

## High-Level Architecture

### Android app

Single-module app (`:app`) built with Jetpack Compose and a simple MVVM-ish structure:

- **Entry point:** `MainActivity` wires the Compose UI and constructs `ChatViewModel` using `ChatViewModelFactory` and `PipelineFactory`.
- **UI layer:**
  - `ui/chat/ChatScreen.kt` – main chat screen: header, message list, composer, and wiring to warning modal.
  - `ui/chat/WarningModal.kt` – dialog that surfaces risk information and an optional safer rewrite of the current draft.
  - `ui/theme/*` – standard Compose theme setup.
- **ViewModel & state:**
  - `ChatViewModel` owns `ChatUiState` (messages, current draft, optional `WarningState`).
  - Handles typing debounce (1.5s) via a coroutine `Job`, and orchestrates preprocessing + risk assessment when the user pauses typing.
  - `onSendPressed()` finalizes the current draft into a `Message` and clears any warning.
- **Data models:**
  - `data/Message.kt` – chat message model + `MessageDirection` (SENT/RECEIVED).
  - `data/ChatUiState.kt` – overall UI state for the chat screen.
  - `data/WarningState.kt` – risk level (LOW/MEDIUM/HIGH), explanation, and safer rewrite text returned from the pipeline.

### Pipeline and external services

The key logic for privacy analysis lives under `app/src/main/java/com/example/whatsapp_1/pipeline` and `api` packages:

- **Secrets & configuration:**
  - `config/SecretsManager.kt` – lazily loads `secrets.properties` from `app/` (or assets as a fallback) and exposes getters for the Gemini API key and backend URL/API key.
- **GliNER/PII handling:**
  - `pipeline/GliNERService.kt` – defines the `GliNERService` interface and two implementations:
    - `BackendGliNERService` – calls the remote FastAPI backend via `BackendApiClient`.
    - `StubGliNERService` – local stub; performs simple sentence chunking and does **not** perform real PII masking.
  - `pipeline/PreprocessingHook.kt` – `GliNERPreprocessingHook` uses `GliNERService` to:
    - Mask and chunk the current draft.
    - Mask/chunk conversation history and assemble `maskedContextChunks`.
    - Return a `PreprocessingResult` containing the masked draft, context chunks, and PII spans.
- **Risk assessment:**
  - `api/gemini/GeminiApiClient.kt` – thin OkHttp-based client for Gemini `generateContent` API.
  - `pipeline/RiskAssessmentPipeline.kt` – orchestrates the two-stage LLM pipeline:
    1. Fill the analysis prompt from `app/src/main/assets/prompt.md`, using XML-wrapped masked history and current masked draft.
    2. Call Gemini and get a JSON analysis summary.
    3. Fill the risk assessment prompt from `app/src/main/assets/risk_assessment.md` with that summary.
    4. Call Gemini again to get a final JSON risk verdict (risk level, risk factors, explanation, and `Show_Warning`).
    5. Parse into a strongly-typed `RiskAssessmentResult` and construct a `WarningState` including a basic placeholder safer rewrite.
    6. Enforce a simple concurrency model with a `Mutex` and a `currentRequestId` to avoid overlapping assessments.
  - `pipeline/RiskAssessmentHook.kt` – adapter between the pipeline and the UI:
    - `GeminiRiskAssessmentHook` invokes `RiskAssessmentPipeline`, returning `WarningState?` only when `showWarning` is true.
    - `StubRiskAssessmentHook` is used when no Gemini API key is configured and always returns `null` (no warning).
  - `pipeline/PromptTemplate.kt` – utilities for loading/filling prompt templates, including injection of default RAG examples.
- **Pipeline wiring:**
  - `pipeline/PipelineFactory.kt` – central factory that:
    - Initializes `SecretsManager`.
    - Chooses between `BackendGliNERService` and `StubGliNERService` based on `BACKEND_URL`.
    - Creates a `GeminiApiClient` if `GEMINI_API_KEY` is present.
    - Constructs the `RiskAssessmentPipeline` and selects `GeminiRiskAssessmentHook` vs `StubRiskAssessmentHook`.

### Backend service

The backend under `backend/` is a standalone FastAPI service designed to run on Cloud Run behind Cloudflare:

- **Entrypoint:** `backend/app/main.py`
  - Exposes `GET /health` and `POST /mask`.
  - Applies CORS via `CORSMiddleware` with `settings.ALLOWED_ORIGINS`.
  - Lazily initializes a `GliNERService` instance at startup and cleans up on shutdown.
  - `/mask` logs useful metrics (text length, PII count, chunk count, processing time) and wraps errors into HTTP 500 with PII-safe messages.
- **GLiNER integration:** `backend/app/services/gliner_service.py`
  - Wraps the GLiNER model and tokenizer, handling:
    - NLTK sentence tokenization setup.
    - Predicting entities for a fixed label set (personal, contact, financial, healthcare, ID categories).
    - Masking PII inline in the text with `[{LABEL}]` tags.
    - Sentence-level chunking with an approximate token budget per chunk.
  - Returns a `MaskingResult` (masked text, chunks, PII spans) that matches what the Android client expects.
- **Configuration:** `backend/app/config.py`
  - Centralized settings object for allowed origins, model name, Cloud Run identifiers, and request/rate limits.
- **Packaging and deployment:**
  - `backend/requirements.txt` – Python deps including FastAPI, GLiNER, Transformers, Torch, and NLTK.
  - `backend/Dockerfile` – production-ready container with healthcheck and pre-downloaded NLTK data.
  - `backend/deploy.sh` – convenience script for building, pushing, and deploying to Cloud Run with recommended resource settings.
  - `backend/cloudflare-config.md` – step-by-step Cloudflare DNS/WAF/rate-limiting guidance that should be followed when exposing `/mask` and `/health` publicly.

## Editing Prompts

Prompt templates that drive Gemini behavior live in both the repo root and in `app/src/main/assets/`, but **the Android app reads from the assets versions** at runtime:

- `app/src/main/assets/prompt.md`
- `app/src/main/assets/risk_assessment.md`

When changing model behavior (analysis dimensions, risk rubric, output JSON schema), update the asset files. Keep them in sync with any copies at the repo root so that documentation stays accurate.

## How to Safely Extend the System

- When adding new analysis dimensions or risk levels, update:
  - The prompt templates in `app/src/main/assets/`.
  - The JSON parsing logic in `RiskAssessmentPipeline.parseRiskAssessment`.
  - The `RiskLevel` enum and any UI that branches on it (e.g., `RiskLevelBadge`).
- When changing how GLiNER masking or chunking works, ensure:
  - The backend response shape remains compatible with `BackendApiClient` and `BackendGliNERService`.
  - The Android-side `MaskingResult` continues to expose `maskedText`, `chunks`, and `piiSpans` in the expected format.
- For any new network integration, follow the existing pattern:
  - Thin OkHttp client in `api/*`.
  - Small interface in `pipeline/*` that the ViewModel depends on, to keep the UI testable and easily stubbed.

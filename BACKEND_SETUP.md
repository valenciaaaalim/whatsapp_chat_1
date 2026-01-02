# Backend Setup Summary

## What Was Created

### FastAPI Backend (`backend/`)

A complete FastAPI backend service that implements GLiNER-based PII masking and chunking:

- **`app/main.py`**: FastAPI application with health check and mask endpoints
- **`app/services/gliner_service.py`**: GLiNER service implementation (based on notebook)
- **`app/config.py`**: Configuration settings
- **`requirements.txt`**: Python dependencies
- **`Dockerfile`**: Container configuration for Cloud Run
- **`deploy.sh`**: Deployment script for Cloud Run
- **`cloudflare-config.md`**: Detailed Cloudflare setup guide
- **`README.md`**: Backend documentation

### Android Integration

Updated Android app to use the backend:

- **`BackendApiClient.kt`**: HTTP client for backend API
- **`BackendGliNERService.kt`**: Service wrapper that calls backend
- **`PipelineFactory.kt`**: Automatically uses backend if URL is configured
- **`SecretsManager.kt`**: Added `BACKEND_URL` and `BACKEND_API_KEY` support

## Quick Start

### 1. Deploy Backend to Cloud Run

```bash
cd backend
export GOOGLE_CLOUD_PROJECT=your-project-id
export REGION=us-central1
./deploy.sh
```

### 2. Set Up Cloudflare

1. Add domain to Cloudflare
2. Create CNAME: `api.yourdomain.com` → `your-service.run.app`
3. Enable proxy (orange cloud)
4. Configure WAF rules (see `backend/cloudflare-config.md`)

### 3. Configure Android App

Edit `app/secrets.properties`:
```
GEMINI_API_KEY=your_gemini_key
BACKEND_URL=https://api.yourdomain.com
BACKEND_API_KEY=optional_if_configured
```

## Architecture

```
Android App
    ↓
Cloudflare (WAF, Rate Limiting, DDoS Protection)
    ↓
Cloud Run (FastAPI + GLiNER Model)
    ↓
Response (Masked Text + Chunks + PII Spans)
```

## Features

✅ **PII Detection**: Uses GLiNER model to detect 50+ PII types
✅ **PII Masking**: Replaces PII with `[LABEL]` tags
✅ **Text Chunking**: Splits text by sentences respecting token limits
✅ **Health Checks**: `/health` endpoint for monitoring
✅ **Error Handling**: Comprehensive error handling and logging
✅ **Security**: Cloudflare WAF, rate limiting, DDoS protection
✅ **Scalability**: Cloud Run auto-scaling (0 to N instances)

## API Endpoints

### `GET /health`
Health check endpoint.

### `POST /mask`
Mask PII and chunk text.

**Request:**
```json
{
  "text": "My name is John Doe",
  "max_tokens": 512
}
```

**Response:**
```json
{
  "masked_text": "My name is [NAME]",
  "chunks": ["My name is [NAME]"],
  "pii_spans": [
    {
      "start": 11,
      "end": 19,
      "label": "name",
      "text": "John Doe"
    }
  ],
  "processing_time_ms": 123.45
}
```

## Cost Estimation

- **Cloud Run**: Pay per request (free tier: 2M requests/month)
- **Memory**: 2Gi allocated (for GLiNER model)
- **CPU**: 2 CPUs (for faster inference)
- **Min instances**: 0 (scale to zero when idle)
- **Estimated cost**: ~$10-50/month for moderate usage

## Next Steps

1. Deploy backend to Cloud Run
2. Set up Cloudflare
3. Update Android app `secrets.properties`
4. Test the integration
5. Monitor usage and costs

## Troubleshooting

### Backend not responding
- Check Cloud Run service is running
- Verify CNAME is correct
- Check Cloud Run logs: `gcloud logging read`

### High latency
- Increase Cloud Run CPU allocation
- Use min instances > 0 to avoid cold starts
- Check Cloudflare caching settings

### Model loading errors
- Verify memory allocation (needs 2Gi+)
- Check Cloud Run logs for model download issues
- Ensure model name is correct


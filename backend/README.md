# GLiNER PII Masking Backend

FastAPI backend service for PII detection and masking using GLiNER model. Deployed to Google Cloud Run with Cloudflare in front for security hardening.

## Features

- ✅ GLiNER-based PII detection and masking
- ✅ Sentence-based chunking with token limits
- ✅ FastAPI with async support
- ✅ Docker containerization
- ✅ Cloud Run deployment ready
- ✅ Health check endpoint
- ✅ Comprehensive error handling

## Local Development

### Prerequisites

- Python 3.11+
- Docker (for containerized deployment)

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Download NLTK data:**
   ```bash
   python -c "import nltk; nltk.download('punkt')"
   ```

3. **Run locally:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

4. **Test the API:**
   ```bash
   # Health check
   curl http://localhost:8080/health
   
   # Mask endpoint
   curl -X POST http://localhost:8080/mask \
     -H "Content-Type: application/json" \
     -d '{"text": "My name is John Doe and my email is john@example.com", "max_tokens": 512}'
   ```

## Docker Build

```bash
docker build -t gliner-pii-service .
docker run -p 8080:8080 gliner-pii-service
```

## Cloud Run Deployment

### Prerequisites

- Google Cloud SDK installed
- GCP project with billing enabled
- Docker installed

### Deploy

1. **Set environment variables:**
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   export REGION=us-central1
   export SERVICE_NAME=gliner-pii-service
   ```

2. **Run deployment script:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

   Or manually:
   ```bash
   # Build and push
   gcloud builds submit --tag gcr.io/PROJECT_ID/SERVICE_NAME
   
   # Deploy
   gcloud run deploy SERVICE_NAME \
     --image gcr.io/PROJECT_ID/SERVICE_NAME \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 2
   ```

### Configuration

- **Memory**: 2Gi (GLiNER model requires significant memory)
- **CPU**: 2 (for faster inference)
- **Timeout**: 300s (for large text processing)
- **Min instances**: 0 (cost optimization)
- **Max instances**: 10 (scale as needed)

## Cloudflare Setup

See [cloudflare-config.md](./cloudflare-config.md) for detailed Cloudflare configuration.

Quick setup:
1. Add domain to Cloudflare
2. Create CNAME pointing to Cloud Run service
3. Enable proxy (orange cloud)
4. Configure WAF rules
5. Set up rate limiting

## API Endpoints

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0"
}
```

### `POST /mask`

Mask PII and chunk text.

**Request:**
```json
{
  "text": "My name is John Doe and my email is john@example.com",
  "max_tokens": 512
}
```

**Response:**
```json
{
  "masked_text": "My name is [NAME] and my email is [EMAIL_ADDRESS]",
  "chunks": [
    "My name is [NAME] and my email is [EMAIL_ADDRESS]"
  ],
  "pii_spans": [
    {
      "start": 11,
      "end": 19,
      "label": "name",
      "text": "John Doe"
    },
    {
      "start": 38,
      "end": 54,
      "label": "email address",
      "text": "john@example.com"
    }
  ],
  "processing_time_ms": 123.45
}
```

## Environment Variables

- `GLINER_MODEL_NAME`: GLiNER model name (default: `knowledgator/gliner-pii-base-v1.0`)
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `REGION`: Cloud Run region
- `SERVICE_NAME`: Cloud Run service name
- `RATE_LIMIT_PER_MINUTE`: Rate limit (default: 60)

## Cost Optimization

- Use **min instances: 0** to scale to zero when not in use
- Use **CPU allocation: 2** for faster cold starts
- Consider **Cloud Run Jobs** for batch processing
- Monitor usage with Cloud Monitoring

## Monitoring

- Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision"`
- Cloud Run metrics: Available in GCP Console
- Cloudflare Analytics: Available in Cloudflare dashboard

## Security Considerations

- ✅ CORS configured
- ✅ Request size limits
- ✅ Error handling (no PII in error messages)
- ✅ Cloudflare WAF protection
- ✅ Rate limiting
- ✅ HTTPS only (via Cloudflare)

## Troubleshooting

### Model Loading Issues

If model fails to load:
- Check memory allocation (needs at least 2Gi)
- Verify model name is correct
- Check Cloud Run logs for errors

### Timeout Issues

- Increase Cloud Run timeout (max 300s)
- Reduce `max_tokens` in requests
- Optimize chunking logic

### High Latency

- Increase CPU allocation
- Use Cloud Run with min instances > 0
- Consider model optimization/quantization


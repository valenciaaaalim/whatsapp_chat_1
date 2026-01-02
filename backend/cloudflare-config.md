# Cloudflare Configuration Guide

This guide explains how to set up Cloudflare in front of your Cloud Run service for security hardening.

## 1. Cloudflare DNS Setup

1. Add your domain to Cloudflare
2. Create a CNAME record pointing to your Cloud Run service:
   ```
   Type: CNAME
   Name: api (or your subdomain)
   Target: your-service-url.run.app
   Proxy: Proxied (orange cloud)
   ```

## 2. Cloudflare Page Rules / Transform Rules

### Rate Limiting
Create a rate limiting rule:
- **Rule Name**: API Rate Limit
- **If**: URI Path starts with `/mask` or `/health`
- **Then**: Rate limit to 60 requests per minute per IP

### Security Headers
Add security headers via Transform Rules or Workers:

```javascript
// Cloudflare Worker script (optional)
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const response = await fetch(request)
  
  // Clone response to modify headers
  const newResponse = new Response(response.body, response)
  
  // Add security headers
  newResponse.headers.set('X-Content-Type-Options', 'nosniff')
  newResponse.headers.set('X-Frame-Options', 'DENY')
  newResponse.headers.set('X-XSS-Protection', '1; mode=block')
  newResponse.headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
  newResponse.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  
  return newResponse
}
```

## 3. WAF (Web Application Firewall) Rules

### Block Common Attacks
- SQL Injection
- XSS (Cross-Site Scripting)
- Path Traversal
- Command Injection

### Custom Rules
Create a custom rule to validate request size:
```
(http.request.body.truncated) or (len(http.request.body) > 50000)
```
Action: Block

## 4. DDoS Protection

Enable Cloudflare's DDoS protection:
- **Auto**: Automatic DDoS mitigation
- **I'm Under Attack Mode**: For severe attacks (may impact legitimate traffic)

## 5. SSL/TLS Settings

1. **SSL/TLS encryption mode**: Full (strict)
2. **Minimum TLS Version**: 1.2
3. **Always Use HTTPS**: Enabled

## 6. Caching (Optional)

For `/health` endpoint, you can cache:
- **Cache Level**: Standard
- **Edge Cache TTL**: 1 minute
- **Browser Cache TTL**: 1 minute

**Do NOT cache** `/mask` endpoint (always dynamic).

## 7. Access Control (Optional)

### IP Access Rules
Restrict access to specific IPs if needed:
- **Action**: Allow
- **IP Address**: Your allowed IPs

### API Token Authentication
If you want to add API key authentication via Cloudflare Workers:

```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const apiKey = request.headers.get('X-API-Key')
  const validKey = 'your-secret-api-key'
  
  if (apiKey !== validKey) {
    return new Response('Unauthorized', { status: 401 })
  }
  
  return fetch(request)
}
```

## 8. Monitoring & Analytics

Enable Cloudflare Analytics to monitor:
- Request volume
- Error rates
- Response times
- Geographic distribution
- Attack patterns

## 9. Recommended Settings Summary

- **Security Level**: Medium
- **Bot Fight Mode**: On
- **Challenge Passage**: 30 minutes
- **Browser Integrity Check**: On
- **Privacy Pass Support**: Enabled

## 10. Testing

After setup, test your configuration:

```bash
# Test health endpoint
curl https://your-domain.com/health

# Test mask endpoint
curl -X POST https://your-domain.com/mask \
  -H "Content-Type: application/json" \
  -d '{"text": "My name is John Doe", "max_tokens": 512}'
```

## Troubleshooting

### 502 Bad Gateway
- Check Cloud Run service is running
- Verify CNAME target is correct
- Check Cloud Run service URL is accessible

### CORS Issues
- Update `ALLOWED_ORIGINS` in `app/config.py` with your Cloudflare domain
- Ensure Cloudflare is forwarding origin headers

### Timeout Issues
- Increase Cloud Run timeout (max 300s)
- Check Cloudflare timeout settings (default 100s)


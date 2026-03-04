# Troubleshooting Guide

This document contains solutions to common issues encountered when deploying and running VisiSense - CatalogIQ.

## Table of Contents

- [Docker Compose Issues](#docker-compose-issues)
- [Configuration Issues](#configuration-issues)
- [LLM Provider Issues](#llm-provider-issues)
- [API Issues](#api-issues)
- [Frontend Issues](#frontend-issues)
- [Image Upload Issues](#image-upload-issues)
- [Chat Issues](#chat-issues)
- [Performance Issues](#performance-issues)

---

## Docker Compose Issues

### Containers fail to start

**Problem**: Docker containers won't start or crash immediately

**Solution**:

1. Check logs for specific errors:
   ```bash
   docker compose logs backend
   docker compose logs frontend
   ```

2. Ensure required ports are available:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   netstat -ano | findstr :5173

   # Unix/Mac/Linux
   lsof -i :8000
   lsof -i :5173
   ```

3. Clean up and rebuild:
   ```bash
   docker compose down -v
   docker compose up --build
   ```

4. Restart Docker Desktop/Engine if issues persist

### Port conflicts

**Problem**: `Error: Port already in use`

**Solution**:

1. Check what's using the port:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F

   # Unix/Mac/Linux
   lsof -i :8000
   kill -9 <PID>
   ```

2. Or change ports in `docker-compose.yml`:
   ```yaml
   backend:
     ports:
       - "8001:8000"  # Use 8001 instead
   ```

### Build failures

**Problem**: Docker build fails with errors

**Solution**:

1. Clean Docker cache:
   ```bash
   docker compose down
   docker system prune -a
   ```

2. Rebuild from scratch:
   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

3. View detailed build output:
   ```bash
   docker compose up --build
   ```

---

## Configuration Issues

### Missing .env file error

**Problem**: `Error: LLM_API_KEY not configured`

**Solution**:

1. Create `backend/.env` from template:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Add your API key:
   ```bash
   nano backend/.env
   # Add: LLM_API_KEY=your_actual_key_here
   ```

3. Restart backend:
   ```bash
   docker compose restart backend
   ```

### Frontend can't connect to backend (Local Development)

**Problem**: `Analysis failed: Not Found` when running locally

**Solution**:

For **local development** (not Docker), you must configure frontend to connect to backend:

1. Create `frontend/.env`:
   ```bash
   cp frontend/.env.example frontend/.env
   ```

2. Set backend URL:
   ```bash
   echo "VITE_API_URL=http://localhost:8000" > frontend/.env
   ```

3. Restart frontend:
   ```bash
   cd frontend
   npm run dev
   ```

**Note**: For Docker deployment, leave `VITE_API_URL` empty (Nginx proxy handles routing).

---

## LLM Provider Issues

### OpenAI API errors

**Problem**: `401 Unauthorized` or `403 Forbidden`

**Solution**:

1. Verify API key is correct:
   ```bash
   docker compose exec backend python -c "
   from config import settings
   print(f'API Key: {settings.LLM_API_KEY[:20]}...')
   "
   ```

2. Check API key in OpenAI dashboard:
   - Visit https://platform.openai.com/api-keys
   - Verify key is active and has permissions
   - Check billing status

3. Update `backend/.env` with correct key:
   ```bash
   LLM_API_KEY=sk-...
   ```

4. Restart backend:
   ```bash
   docker compose restart backend
   ```

### Rate limit errors (429)

**Problem**: `429 Too Many Requests`

**Solution**:

1. For **OpenAI**: Upgrade tier or reduce request frequency
2. For **Groq**: Free tier has limits (30 req/min, 6000 tokens/min)
3. Add retry logic (already implemented with `MAX_RETRIES=3`)
4. Switch to a different provider:
   ```bash
   # Try Groq for fast free tier
   LLM_PROVIDER=groq
   LLM_API_KEY=gsk_...
   LLM_BASE_URL=https://api.groq.com/openai/v1
   LLM_MODEL=llama-3.2-90b-vision-preview
   ```

### Ollama connection errors

**Problem**: `Connection refused` when using Ollama

**Solution**:

1. Check if Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Verify model is installed:
   ```bash
   ollama list
   ```

3. Pull required model if missing:
   ```bash
   ollama pull qwen2.5-vl:7b
   ```

4. Test model directly:
   ```bash
   ollama run qwen2.5-vl:7b "Describe this" < image.jpg
   ```

5. For Docker, use `host.docker.internal` instead of `localhost`:
   ```bash
   # backend/.env
   LLM_BASE_URL=http://host.docker.internal:11434/v1
   ```

### Model not found errors

**Problem**: `404 Model not found`

**Solution**:

1. Check available models for your provider:
   ```bash
   # OpenAI
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $LLM_API_KEY"

   # Groq
   curl https://api.groq.com/openai/v1/models \
     -H "Authorization: Bearer $LLM_API_KEY"
   ```

2. Update `LLM_MODEL` in `backend/.env` to match available models

3. Verify model supports vision (not all models do):
   - OpenAI: `gpt-4o`, `gpt-4-turbo`, `gpt-4o-mini`
   - Groq: `llama-3.2-90b-vision-preview`, `llama-3.2-11b-vision-preview`
   - Ollama: `qwen2.5-vl:7b`, `llama3.2-vision:11b`, `bakllava`

---

## API Issues

### API not responding

**Problem**: Backend health check fails

**Solution**:

1. Check service health:
   ```bash
   curl http://localhost:8000/health
   ```

2. View backend logs:
   ```bash
   docker compose logs backend --tail 50
   ```

3. Verify container is running:
   ```bash
   docker compose ps
   ```

4. Restart backend:
   ```bash
   docker compose restart backend
   ```

### CORS errors

**Problem**: `CORS policy blocked` in browser console

**Solution**:

1. Check CORS settings in `backend/.env`:
   ```bash
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000
   # Or allow all:
   CORS_ORIGINS=*
   ```

2. Restart backend:
   ```bash
   docker compose restart backend
   ```

### Timeout errors

**Problem**: `Request timeout after 120 seconds`

**Solution**:

1. Increase timeout in `backend/.env`:
   ```bash
   REQUEST_TIMEOUT=300  # 5 minutes
   ```

2. Check if LLM provider is slow:
   - Ollama with large models may be slower
   - Try a smaller/faster model

3. Verify system resources:
   ```bash
   docker stats
   ```

---

## Frontend Issues

### Build errors

**Problem**: Frontend fails to build with dependency errors

**Solution**:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Vite errors

**Problem**: `Error: Could not resolve...`

**Solution**:

1. Clear Vite cache:
   ```bash
   cd frontend
   rm -rf node_modules/.vite
   npm run dev
   ```

2. Reinstall dependencies:
   ```bash
   npm ci
   ```

### Styling issues

**Problem**: Styles not applying correctly

**Solution**:

1. Rebuild Tailwind CSS:
   ```bash
   cd frontend
   npm run dev
   ```

2. Clear browser cache (Ctrl+Shift+R / Cmd+Shift+R)

---

## Image Upload Issues

### Upload fails with size error

**Problem**: `File too large` error

**Solution**:

1. Check file size limits in `backend/.env`:
   ```bash
   MAX_IMAGE_SIZE_MB=10
   ```

2. Compress images before upload

3. Verify image format is supported:
   - Supported: JPG, PNG, WEBP
   - Not supported: GIF, BMP, TIFF

### Upload fails with validation error

**Problem**: `Invalid file type` error

**Solution**:

1. Ensure file has correct MIME type:
   - `image/jpeg`, `image/png`, `image/webp`

2. Rename file with correct extension:
   - `.jpg`, `.jpeg`, `.png`, `.webp`

3. Check allowed types in `backend/.env`:
   ```bash
   ALLOWED_IMAGE_TYPES=image/jpeg,image/png,image/webp
   ```

### Multiple images not working

**Problem**: Can only upload one image

**Solution**:

1. Check max images limit in `backend/.env`:
   ```bash
   MAX_IMAGES_PER_REQUEST=5
   ```

2. Upload images together (not one at a time)

3. Ensure all images meet size requirements

---

## Chat Issues

### Chat session expired

**Problem**: `Session not found` error

**Solution**:

Sessions expire after 30 minutes of inactivity by default.

1. To extend session lifetime in `backend/.env`:
   ```bash
   CHAT_SESSION_TTL_MINUTES=60  # 60 minutes
   ```

2. Or disable expiration (not recommended):
   ```bash
   CHAT_SESSION_TTL_MINUTES=0  # Never expire
   ```

3. Restart backend:
   ```bash
   docker compose restart backend
   ```

### Chat not responding

**Problem**: Chat messages receive no response

**Solution**:

1. Verify product analysis was completed first (chat requires analysis data)

2. Check backend logs:
   ```bash
   docker compose logs backend --tail 50 --follow
   ```

3. Verify session exists:
   - Analysis creates session
   - Check if session expired

4. Try analyzing product again

### Chat responses are slow

**Problem**: Chat takes too long to respond

**Solution**:

1. Check LLM provider performance:
   - OpenAI: Usually fast
   - Groq: Very fast
   - Ollama: Depends on local hardware

2. Use faster model:
   ```bash
   # For Groq
   LLM_MODEL=llama-3.2-11b-vision-preview  # Faster than 90b

   # For OpenAI
   LLM_MODEL=gpt-4o-mini  # Faster than gpt-4o
   ```

3. Reduce max tokens:
   ```bash
   MAX_TOKENS=1024  # Default is 2048
   ```

---

## Performance Issues

### Slow analysis

**Problem**: Product analysis takes too long

**Solution**:

1. Use faster LLM provider:
   - Groq (fastest)
   - OpenAI GPT-4o-mini (fast + quality)
   - Ollama (depends on hardware)

2. Reduce image sizes before upload

3. Use fewer images (1-3 instead of 5)

4. Check system resources:
   ```bash
   docker stats
   ```

### High memory usage

**Problem**: Docker containers using too much memory

**Solution**:

1. Limit Docker memory in Docker Desktop settings

2. Clear session store periodically:
   ```bash
   docker compose restart backend
   ```

3. Reduce session TTL:
   ```bash
   CHAT_SESSION_TTL_MINUTES=15  # Default is 30
   ```

### Slow Docker builds

**Problem**: Docker build takes too long

**Solution**:

1. Use cached builds:
   ```bash
   docker compose build  # Without --no-cache
   ```

2. Increase Docker resources in Docker Desktop

3. Use pre-built images if available

---

## Debug Mode

Enable detailed logging for comprehensive diagnostics:

```bash
# Update backend/.env
LOG_LEVEL=DEBUG

# Restart backend
docker compose restart backend

# View detailed logs
docker compose logs -f backend
```

---

## Getting Help

If issues persist after trying these solutions:

1. Check backend logs: `docker compose logs backend`
2. Check frontend logs: `docker compose logs frontend`
3. Verify environment variables: `cat backend/.env`
4. Test LLM provider API directly with curl
5. Review Docker container status: `docker compose ps`
6. Check system resources: `docker stats`

---

## Additional Resources

- [README.md](./README.md) - Main documentation
- [LLM Provider Configuration](#) - Provider-specific setup
- [Environment Variables](#) - Configuration reference
- [Docker Documentation](https://docs.docker.com/)

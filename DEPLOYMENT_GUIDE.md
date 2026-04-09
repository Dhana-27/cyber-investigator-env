# 🚀 HuggingFace Spaces Deployment Guide

## Quick Start (5 minutes)

### Step 1: Create HF Space

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in:
   - **Owner**: Your username
   - **Space name**: `cyber-investigator-env`
   - **License**: MIT
   - **Runtime**: Docker (NOT Python)
4. Click **"Create Space"**

### Step 2: Connect Your Repository

```bash
# Clone the space
git clone https://huggingface.co/spaces/YOUR_USERNAME/cyber-investigator-env
cd cyber-investigator-env

# Copy your project files
# Copy: app/, *.py, openenv.yaml, requirements.txt, Dockerfile, README.md

# Push to HF
git add .
git commit -m "Initial OpenEnv submission"
git push
```

### Step 3: Set Up Secrets

Go to **Space Settings** → **Repository secrets**

Add these secrets:
```
OPENAI_API_KEY = sk-proj-...
API_BASE_URL = https://api.openai.com/v1
MODEL_NAME = gpt-4o-mini
HF_TOKEN = your_hf_token_here
```

### Step 4: Deployment

Once you push, HF automatically:
1. ✅ Builds Docker image
2. ✅ Deploys container
3. ✅ Runs `docker run`
4. ✅ Executes `inference.py`
5. ✅ Captures output in logs

**Your Space is live!**

---

## Verification Checklist

### Local Testing
- [ ] `python inference.py` runs successfully
- [ ] Output shows: `[START]`, `[STEP]`, `[END]`
- [ ] Final score is between 0.0 and 1.0
- [ ] No errors in logs
- [ ] Completes in < 20 minutes

### Docker Testing
```bash
# Build locally
docker build -t cyber-investigator-env .

# Run with env vars
docker run \
  -e OPENAI_API_KEY="sk-..." \
  -e API_BASE_URL="https://api.openai.com/v1" \
  -e MODEL_NAME="gpt-4o-mini" \
  cyber-investigator-env
```

### HF Space Deployment
- [ ] Space created with Docker runtime
- [ ] Repository secrets configured
- [ ] Code pushed to HF
- [ ] Space builds successfully
- [ ] Space logs show `[END] Final Score: X.XX`
- [ ] No API key exposed in logs

---

## Troubleshooting

### Problem: "ModuleNotFoundError"
**Solution**: Ensure all packages in requirements.txt are installed
```bash
pip install -r requirements.txt
```

### Problem: "OPENAI_API_KEY not set"
**Solution**: Set environment variable before running
```bash
# Bash
export OPENAI_API_KEY="sk-..."

# Windows PowerShell
$env:OPENAI_API_KEY="sk-..."
```

### Problem: "Rate limit error"
**Solution**: Check QuotaError message - might need to:
1. Add billing to OpenAI account
2. Use different API key
3. Switch to OpenRouter (free tier available)

### Problem: Space build fails
**Solution**: Check tha
```bash
# Local Docker build to debug
docker build -t test .
docker run test
```

---

## Performance Optimization

### Reduce Runtime
```python
# In inference.py - reduce max_steps
max_steps = 3  # Instead of 5
```

### Reduce Memory
- Use `gpt-4o-mini` (smallest model)
- Batch tasks processing
- Clean up temp files

### Reduce Cost
- Use free tier models (OpenRouter)
- Cache LLM responses
- Limit task iterations

---

## API Provider Options

### Option 1: OpenAI (DEFAULT)
```
API_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
Cost: ~$0.00015 per token
```

### Option 2: OpenRouter (FREE TIER) ⭐
```
API_BASE_URL=https://openrouter.ai/api/v1
MODEL_NAME=mistralai/mistral-7b-instruct
Cost: $0.00
Features: Free tier, no credit card needed
```

### Option 3: Local (Ollama)
```
API_BASE_URL=http://localhost:11434/v1
MODEL_NAME=llama3
Cost: $0.00
Requirements: Ollama installed locally
```

---

## Security Best Practices

✅ **DO**:
- Store API keys in HF Secrets
- Use environment variables
- Validate API responses
- Log anonymously

❌ **DON'T**:
- Commit API keys to GitHub
- Print secrets in logs
- Hardcode credentials
- Use debug tokens

---

## Advanced: Custom Domain

Already have HF Space? Upgrade to custom domain:

1. Go to **Space Settings**
2. Select **Persistent Datasets** (if needed)
3. Enable **Persistent Storage**
4. Add custom domain in settings

---

## Support

- **OpenEnv Spec**: https://github.com/meta-pytorch/OpenEnv
- **HF Documentation**: https://huggingface.co/docs/hub/spaces
- **OpenAI Docs**: https://platform.openai.com/docs
- **Troubleshooting**: Check Space logs → Runtime logs tab

---

Generated for OpenEnv Hackathon 2024

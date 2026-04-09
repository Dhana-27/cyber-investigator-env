---
title: AI Cyber Investigator Environment
emoji: 🔒
colorFrom: blue
colorTo: purple
sdk: docker
python_version: 3.10
app_file: inference.py
pinned: false
---

# � AI Cyber Investigator - OpenEnv-Compliant Environment

An **OpenEnv-compliant** cybersecurity threat detection environment for training and benchmarking AI agents. Agents learn to detect fraud, trace malicious networks, and analyze account linking patterns through deterministic task graders scoring 0.0–1.0.

---

## 📋 Quick Navigation

- [Overview](#overview)
- [Observation & Action Spaces](#observation--action-spaces)
- [3 Tasks with Graders](#3-tasks-with-graders)
- [Reward Function](#reward-function)
- [Setup Instructions](#setup-instructions)
- [Usage & API](#usage--api)
- [Baseline Performance](#baseline-performance)
- [OpenEnv Compliance](#openenv-compliance-checklist)
- [Docker Deployment](#docker-deployment)

---

## 🎯 Overview

### Motivation

Real-world cybersecurity operations require AI systems that can:
- Make high-stakes decisions with incomplete information
- Provide interpretable reasoning for security actions
- Trade speed vs. accuracy (quick decisive action vs. thorough investigation)
- Learn from immediate, continuous feedback (reward signals)

This environment operationalizes these requirements into a realistic, OpenEnv-compliant benchmark.

### Environment Features

✅ **Fully OpenEnv Compliant**
- Typed `InvestigatorAction`, `InvestigatorObservation`, `InvestigatorState` (Pydantic models)
- `reset()`, `step()`, `state` endpoints with correct signatures
- `openenv.yaml` specification metadata
- Validation script (`validate.py`) for compliance checking

✅ **3+ Deterministic Task Graders**
- Fraud Detection (40% weight) — Easy
- IP Trace (35% weight) — Medium
- Account Link Analysis (25% weight) — Hard

✅ **Meaningful Reward Function**
- Provides signal over full trajectory (not just binary end-of-episode)
- Rewards partial progress toward task completion
- Penalizes clearly undesirable behavior (missed fraud, false alarms, invalid actions)

✅ **Baseline Inference Script**
- `inference.py` in project root
- Uses OpenAI Client for all LLM calls
- Reads API credentials from environment variables (`API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`/`OPENAI_API_KEY`)
- Emits strictly formatted structured logs: `[START]`, `[STEP]`, `[END]`
- Produces reproducible baseline scores on all 3 tasks

---

## 🔄 Observation & Action Spaces

### Observation Space

Each observation is a **typed `InvestigatorObservation` Pydantic model**:

```python
{
    "task_type": "fraud" | "ip_trace" | "account_link"  # Task being evaluated
    "transaction_amount": int,                           # 100 → 100,000
    "ip_address": str,                                   # e.g., "185.220.101.45"
    "user_age_days": int,                                # Account age (1 → 1000 days)
    "previous_flags": int,                               # Prior violations (0 → 5)
    "location_match": bool,                              # Geographic consistency
    "risk_score": float,                                 # 0.0 → 1.0
    "step_count": int,                                   # Current step
    "done": bool,                                        # Episode terminal flag
    "reward": float,                                     # Immediate step reward
    "message": Optional[str]                             # Human-readable feedback
}
```

### Action Space

**Valid Actions** (string-based):
- `FLAG_TRANSACTION` — Mark transaction as fraudulent
- `IGNORE` — Allow transaction/activity
- `TRACE_IP` — Investigate IP origin
- `BLOCK_ACCOUNT` — Disable account
- Any other string → treated as invalid

---

## 🎮 3 Tasks with Graders

### Task 1: Fraud Detection (40% weight)

**Difficulty**: ⭐ Easy

**Grading Rubric** (Deterministic):

| Actual | Agent Action | Reward | Status |
|--------|--------------|--------|--------|
| Fraud | FLAG_TRANSACTION | 1.0 + risk_bonus | ✅ Perfect |
| Legitimate | IGNORE | 0.7 | ✅ Correct |
| Fraud | IGNORE | -0.5 - risk_penalty | ❌ Missed fraud |
| Legitimate | FLAG_TRANSACTION | -0.3 | ⚠️ False alarm |
| Any | Invalid | -0.2 | ❌ Invalid action |

**Scoring**: Normalized to [0.0, 1.0]

---

### Task 2: IP Trace Investigation (35% weight)

**Difficulty**: ⭐⭐ Medium

**Malicious IP Patterns**: 
- `185.220.x.x` (Tor exit nodes)
- `192.0.2.x` (test range)
- `198.51.100.x` (test range)

**Grading Rubric**:

| Actual | Agent Action | Reward | Status |
|--------|--------------|--------|--------|
| Malicious | TRACE_IP | 1.0 + speed_bonus | ✅ Perfect |
| Benign | IGNORE | 0.7 | ✅ Correct |
| Malicious | IGNORE | -0.4 - penalty | ❌ Missed threat |
| Benign | TRACE_IP | -0.2 | ⚠️ False positive |
| Any | Invalid | -0.3 | ❌ Invalid action |

**Scoring**: Normalized to [0.0, 1.0]

---

### Task 3: Account Link Analysis (25% weight)

**Difficulty**: ⭐⭐⭐ Hard

**Grading Rubric**:

| Actual | Agent Action | Reward | Status |
|--------|--------------|--------|--------|
| Fraud | BLOCK_ACCOUNT | 1.0 + speed_bonus | ✅ Perfect |
| Legitimate | IGNORE | 0.8 | ✅ Correct |
| Fraud | FLAG_TRANSACTION | 0.5 | ⚠️ Partial |
| Fraud | IGNORE | -0.3 | ❌ Missed fraud |
| Legitimate | BLOCK_ACCOUNT | -0.4 | ❌ False block |
| Any | Invalid | -0.2 | ❌ Invalid action |

**Scoring**: Normalized to [0.0, 1.0]

---

## 💰 Reward Function

### Design Properties

The reward function is **rich, continuous, and trajectory-aware**:

```python
reward = _calculate_reward(task_type, is_fraud, action, risk_score, step_count)
# Returns: float in [-1.0, 1.0]
```

**Key Features**:

1. **Trajectory Signal**: Agents receive immediate feedback for each step (not just end-of-episode binary)
2. **Partial Progress**: Correct but suboptimal actions receive partial credit
3. **Speed Bonus**: Solving tasks in ≤3 steps grants +0.1 bonus
4. **Risk-Aware Scaling**: Higher risk transactions grant bonuses for correct detection
5. **Penalty Structure**:
   - Missing fraud: -0.5 to -0.8 (serious penalty)
   - False alarms: -0.2 to -0.3 (minor penalty)
   - Invalid actions: -0.2 (discourage nonsense)

### Example Trajectory

```
Episode: "fraud" task, is_fraud=True, risk_score=0.8

Step 1: Action=IGNORE
  → Reward = -0.5 - (0.8 * 0.2) = -0.66 (missed fraud + risk penalty) ❌
  → Done=False (opportunity to correct)

Step 2: Action=FLAG_TRANSACTION
  → Reward = 1.0 + (0.8 * 0.1) = 1.08 → clamped to 1.0 ✅
  → Done=True (episode ends on correct decision)

Episode Summary:
  - Total reward: -0.66 + 1.0 = 0.34
  - Trajectory: [-0.66, 1.0]
  - Task grade: 0.833 (normalized)
```

---

## 📦 Setup Instructions

### Prerequisites

- Python 3.10+
- pip or conda
- Docker (for containerized deployment)

### Local Installation

```bash
# 1. Clone/enter directory
cd cyber-investigator-env

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials:
#   OPENAI_API_KEY=sk-...
#   API_BASE_URL=https://api.openai.com/v1
#   MODEL_NAME=gpt-4o-mini

# 5. Validate setup (optional)
python validate.py
```

### Environment Variables (Required)

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `https://api.openai.com/v1` | LLM API endpoint |
| `MODEL_NAME` | `gpt-4o-mini` | Model identifier for LLM calls |
| `OPENAI_API_KEY` or `HF_TOKEN` | None (required) | API credentials — NO hardcoded defaults |

---

## 🚀 Usage & API

### Running Inference Script

```bash
python inference.py
```

**Environment Variables Read**:
- `API_BASE_URL`: LLM endpoint
- `MODEL_NAME`: Model to use
- `OPENAI_API_KEY` or `HF_TOKEN`: API key
- `INVESTIGATOR_TASK` (optional): Task focus ("fraud", "ip_trace", or "account_link")

**Output** (Structured Logging):
```
[START] task=fraud env=investigator model=gpt-4o-mini
[STEP] step=1 action=FLAG_TRANSACTION reward=1.00 done=true error=null
[STEP] step=2 action=TRACE_IP reward=0.70 done=false error=null
[STEP] step=3 action=IGNORE reward=-0.30 done=true error=null
[END] success=true steps=3 score=0.467 rewards=1.00,0.70,-0.30
```

### OpenAPI Endpoints

Start server: `uvicorn server.app:app --port 7860`

#### `POST /reset`
Reset environment to initial state.

**Request**:
```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "fraud"}'
```

**Response**:
```json
{
  "observation": {
    "task_type": "fraud",
    "transaction_amount": 5000,
    "ip_address": "192.168.1.1",
    "risk_score": 0.75,
    "done": false,
    "reward": 0.0,
    "step_count": 0
  },
  "done": false,
  "reward": 0.0,
  "info": {"message": "Environment reset", "task": "fraud"}
}
```

#### `POST /step`
Execute action in environment.

**Request**:
```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"action": "FLAG_TRANSACTION"}'
```

**Response**:
```json
{
  "observation": {...},
  "reward": 1.0,
  "done": true,
  "info": {"message": "Action 'FLAG_TRANSACTION' successful"}
}
```

#### `GET /state`
Get current environment state.

**Request**:
```bash
curl http://localhost:7860/state
```

**Response**:
```json
{
  "step_count": 1,
  "task_type": "fraud",
  "done": true,
  "current_reward": 1.0,
  "is_fraud": true,
  "risk_score": 0.75
}
```

#### `GET /health`
Health check (for HF Space automated pings).

**Response** (must return 200):
```json
{
  "status": "healthy",
  "environment": "investigator",
  "version": "1.0.0",
  "spec": "openenv-v1"
}
```

---

## 📊 Baseline Performance

### Baseline Agent

- **Model**: OpenAI `gpt-4o-mini`
- **Strategy**: Zero-shot decision-making
- **System Prompt**:
  ```
  You are a cyber-security AI agent. 
  Analyse the environment state and respond with EXACTLY one action word — 
  no punctuation, no explanation.
  Valid actions: FLAG_TRANSACTION, IGNORE, TRACE_IP, BLOCK_ACCOUNT
  ```

### Expected Scores

| Task | Weight | Expected | Status |
|------|--------|----------|--------|
| Fraud Detection | 40% | 0.65–0.75 | ⚠️ Medium |
| IP Trace | 35% | 0.60–0.70 | ⚠️ Medium |
| Account Link | 25% | 0.50–0.65 | ⚠️ Fair |
| **Composite** | 100% | **0.59–0.70** | ⚠️ Fair–Good |

### Reproduce Baseline

```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export OPENAI_API_KEY="sk-..."

python inference.py
```

Expected output includes `[END] success=true ... score=0.6X`

---

## ✅ OpenEnv Compliance Checklist

Run `python validate.py` to check all requirements:

```bash
python validate.py

# Expected output:
# ✅ openenv.yaml valid (name=investigator, type=standard)
# ✅ InvestigatorAction is typed Pydantic model
# ✅ InvestigatorObservation is typed Pydantic model
# ✅ InvestigatorState is typed Pydantic model
# ✅ step(action) method exists with correct signature
# ✅ reset() method exists
# ✅ state property exists
# ✅ 3 task graders defined
# ...
# 🎉 Environment is compliant with OpenEnv specification!
```

### Compliance Requirements Met

- ✅ **Spec Version**: `openenv.yaml` with `spec_version: 1`
- ✅ **Typed Models**: `Action`, `Observation`, `State` (Pydantic BaseModel)
- ✅ **Core Methods**: `reset()` → Observation, `step(action)` → Observation, `state` property
- ✅ **3+ Tasks**: Fraud, IP Trace, Account Link (with graders)
- ✅ **Graders**: Deterministic 0.0–1.0 scoring with clear criteria
- ✅ **Reward Function**: Provides trajectory signal, partial progress, penalties
- ✅ **Baseline**: `inference.py` using OpenAI client + structured logging
- ✅ **Validation**: `validate.py` checks all compliance requirements

---

## 🐳 Docker Deployment

### Build & Test Locally

```bash
# Build Docker image
docker build -t cyber-investigator:latest .

# Run container with environment variables
docker run -p 7860:7860 \
  -e API_BASE_URL="https://api.openai.com/v1" \
  -e MODEL_NAME="gpt-4o-mini" \
  -e OPENAI_API_KEY="sk-..." \
  cyber-investigator:latest

# Test endpoints
curl http://localhost:7860/health
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task":"fraud"}'
```

### Deploy to Hugging Face Spaces

1. **Create Space**:
   - https://huggingface.co/new-space
   - Select "Docker" SDK
   - Python 3.10

2. **Push Code**:
   ```bash
   git clone https://huggingface.co/spaces/USERNAME/cyber-investigator-env
   cd cyber-investigator-env
   git add .
   git commit -m "Initial OpenEnv submission"
   git push
   ```

3. **Set Secrets** (in Space settings):
   - `OPENAI_API_KEY` = your API key
   - `API_BASE_URL` = https://api.openai.com/v1
   - `MODEL_NAME` = gpt-4o-mini
   - HF_TOKEN = (optional, for HF inference)

4. **Verify Deployment**:
   ```bash
   # Manual test
   curl https://USERNAME-cyber-investigator-env.hf.space/health
   # Expected: 200 with status=healthy
   
   # Automated pings every 15 minutes
   # Must return 200 and respond to /reset endpoint
   ```

---

## 📁 Project Structure

```
cyber-investigator-env/
├── app.py                       # FastAPI server with OpenEnv endpoints
├── environment.py               # Core InvestigatorEnvironment class
├── models.py                    # Pydantic models (Action, Observation, State)
├── tasks.py                     # Task graders (3 independent tasks)
├── inference.py                 # Baseline agent using OpenAI API
├── validate.py                  # OpenEnv compliance validator
├── server.py                    # Server entry point
├── Dockerfile                   # Docker configuration
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── openenv.yaml                 # OpenEnv specification
└── README.md                    # This file
```

---

## 🧪 Testing & Validation

```bash
# 1. Validate OpenEnv compliance
python validate.py

# 2. Run baseline inference (requires API key)
python inference.py

# 3. Start server for manual testing
python -m uvicorn server.app:app --port 7860
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'openenv'` | `pip install -r requirements.txt` |
| `OPENAI_API_KEY not set` | Set in `.env`: `OPENAI_API_KEY=sk-...` |
| Port 7860 already in use | Use `--port 8000` or kill existing process |
| `validate.py` shows failures | Check error messages and run specific tests |
| Docker build fails | Ensure `requirements.txt` is valid: `pip install --dry-run -r requirements.txt` |

---

## 📚 References

- [OpenEnv Specification](https://github.com/meta-pytorch/OpenEnv)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Hugging Face Spaces Documentation](https://huggingface.co/docs/hub/spaces)

---

## 📄 License

MIT License - Use freely

---

**Status**: ✅ OpenEnv Compliant v1.0 | **Built for OpenEnv Hackathon 2024**

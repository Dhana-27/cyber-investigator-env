"""
FastAPI Server for AI Cyber Investigator Environment
Implements full OpenEnv specification with typed endpoints.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from environment import InvestigatorEnvironment
from models import InvestigatorAction, InvestigatorObservation, InvestigatorState

# ── Initialize FastAPI app ──────────────────────────────────────────────────
app = FastAPI(
    title="AI Cyber Investigator",
    description="OpenEnv-compliant cybersecurity investigation environment",
    version="1.0.0"
)

# ── Global environment instance ──────────────────────────────────────────────
env = InvestigatorEnvironment()

# ── Request models ──────────────────────────────────────────────────────────
class ResetRequest(BaseModel):
    """Reset request - can specify task (optional)."""
    task: Optional[str] = None
    seed: Optional[int] = None


class StepRequest(BaseModel):
    """Step request - action to execute."""
    action: str


# ── OpenEnv endpoints ───────────────────────────────────────────────────────

@app.post("/reset")
async def reset(request: Optional[ResetRequest] = None):
    """
    Reset environment to initial state.
    
    OpenEnv Spec: Returns initial observation after reset.
    """
    try:
        observation = env.reset()
        return {
            "observation": observation.dict(),
            "done": False,
            "reward": 0.0,
            "info": {
                "message": "Environment reset",
                "task": env._task_type,
                "step": 0
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "type": "reset_error"}
        )


@app.post("/step")
async def step(request: StepRequest):
    """
    Execute action in environment.
    
    OpenEnv Spec: Takes action, returns (observation, reward, done, info).
    """
    try:
        # Create action object
        action = InvestigatorAction(action=request.action)
        
        # Step environment
        observation = env.step(action)
        
        return {
            "observation": observation.dict(),
            "reward": observation.reward,
            "done": observation.done,
            "info": {
                "message": observation.message,
                "step": observation.step_count,
                "task": env._task_type
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e), "type": "step_error"}
        )


@app.get("/state")
async def get_state():
    """
    Get current environment state.
    
    OpenEnv Spec: Returns full state including step_count, task_type, done, reward.
    """
    try:
        state = env.state
        return {
            "step_count": state.step_count,
            "task_type": state.task_type,
            "done": state.done,
            "current_reward": state.current_reward,
            "is_fraud": env._state_data.get("is_fraud", False),
            "transaction_amount": env._state_data.get("transaction_amount", 0),
            "ip_address": env._state_data.get("ip_address", ""),
            "risk_score": env._state_data.get("risk_score", 0.0),
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "type": "state_error"}
        )


@app.get("/health")
async def health():
    """
    Health check endpoint for monitoring.
    
    Must return 200 for Hugging Face Space automated pings.
    """
    return {
        "status": "healthy",
        "environment": "investigator",
        "version": "1.0.0",
        "spec": "openenv-v1"
    }


@app.get("/")
async def root():
    """Root endpoint with API documentation."""
    return {
        "name": "AI Cyber Investigator",
        "description": "OpenEnv-compliant cybersecurity investigation environment",
        "endpoints": {
            "reset": "POST /reset - Reset environment",
            "step": "POST /step - Execute action",
            "state": "GET /state - Get current state",
            "health": "GET /health - Health check",
        },
        "spec_version": "openenv-v1"
    }


def main():
    """Entry point for the FastAPI application."""
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", "7860"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()


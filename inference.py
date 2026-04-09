"""
Inference Script - AI Cyber Investigator Environment
Follows OpenEnv submission requirements strictly.
"""

import os
import sys
from typing import List, Optional
from openai import OpenAI

# ── Environment variables (NO hardcoded defaults for HF_TOKEN) ──────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY")

# ── Task / benchmark config ──────────────────────────────────────────────────
TASK_NAME  = os.getenv("INVESTIGATOR_TASK", "fraud")
BENCHMARK  = "investigator"
MAX_STEPS  = 50
TEMPERATURE = 0.0
MAX_TOKENS  = 20

VALID_ACTIONS = ["FLAG_TRANSACTION", "IGNORE", "TRACE_IP", "BLOCK_ACCOUNT"]

SYSTEM_PROMPT = (
    "You are a cyber-security AI agent. "
    "Analyse the environment state and respond with EXACTLY one action word — "
    "no punctuation, no explanation. "
    "Valid actions: FLAG_TRANSACTION, IGNORE, TRACE_IP, BLOCK_ACCOUNT"
)

# ── Stdout helpers (exact format required) ───────────────────────────────────
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float,
             done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val  = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float,
            rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )

# ── LLM call via OpenAI client ───────────────────────────────────────────────
def get_action(client: OpenAI, state: dict) -> str:
    user_prompt = (
        f"Task: {state.get('task_type', 'unknown')}\n"
        f"Transaction amount: {state.get('transaction_amount')}\n"
        f"IP address: {state.get('ip_address')}\n"
        f"User age (days): {state.get('user_age_days')}\n"
        f"Previous flags: {state.get('previous_flags')}\n"
        f"Location match: {state.get('location_match')}\n"
        f"Risk score: {state.get('risk_score')}\n"
        "What is your action?"
    )
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        raw = (completion.choices[0].message.content or "").strip().upper()
        # pick first matching valid action
        for a in VALID_ACTIONS:
            if a in raw:
                return a
        return "IGNORE"
    except Exception as exc:
        print(f"[DEBUG] LLM call failed: {exc}", flush=True)
        return "IGNORE"

# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    # All LLM calls use the OpenAI client configured via env variables
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # Import environment locally so the script is runnable standalone
    sys.path.insert(0, os.path.dirname(__file__))
    from environment import InvestigatorEnvironment  # noqa: E402
    from models import InvestigatorAction  # noqa: E402

    env = InvestigatorEnvironment()

    rewards:    List[float] = []
    steps_taken = 0
    score       = 0.0
    success     = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        state = env.reset()
        done  = False

        for step in range(1, MAX_STEPS + 1):
            if done:
                break

            action_str = get_action(client, state.__dict__)
            action = InvestigatorAction(action=action_str)

            observation = env.step(action)
            reward      = float(observation.reward)
            done        = observation.done
            error_msg   = observation.message if observation.message else None

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action_str, reward=reward,
                     done=done, error=error_msg)

            if done:
                break

        # score: normalise cumulative reward to [0, 1]
        # max possible = 1.0 per step * MAX_STEPS
        max_total = float(MAX_STEPS)
        raw_score = sum(r for r in rewards if r > 0)   # only positive rewards
        score     = min(max(raw_score / max_total, 0.0), 1.0)
        success   = score >= 0.1

    except Exception as exc:
        print(f"[DEBUG] Episode error: {exc}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken,
                score=score, rewards=rewards)


if __name__ == "__main__":
    main()

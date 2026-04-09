from openenv.core.env_server import Action, Observation, State
from typing import Optional

class InvestigatorAction(Action):
    action: str  # FLAG_TRANSACTION | IGNORE | TRACE_IP | BLOCK_ACCOUNT

class InvestigatorObservation(Observation):
    # done and reward are inherited from Observation
    task_type: str
    transaction_amount: int
    ip_address: str
    user_age_days: int
    previous_flags: int
    location_match: bool
    risk_score: float
    step_count: int
    message: Optional[str] = None

class InvestigatorState(State):
    # step_count inherited from State
    task_type: str
    done: bool
    current_reward: float

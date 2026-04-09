import random
from typing import Dict, Any
from openenv.core.env_server import Environment
from models import InvestigatorAction, InvestigatorObservation, InvestigatorState
from tasks import CompositeGrader


class InvestigatorEnvironment(Environment):
    """
    AI Cyber Investigator - real-world fraud/cyber triage environment.
    
    Implements full OpenEnv spec with:
    - Typed Observation, Action, State Pydantic models
    - step(action) → InvestigatorObservation with reward, done, info
    - reset() → InvestigatorObservation
    - state() → InvestigatorState
    - Meaningful reward function with partial progress signals
    - Clear task objectives (0.0-1.0 scoring)
    """

    def __init__(self):
        self._task_type = "fraud"
        self._state_data = {}
        self._done = False
        self._step_count = 0
        self._max_steps = 10
        self._is_fraud = False
        self._episode_rewards = []
        self._current_action = None

    def reset(self) -> InvestigatorObservation:
        """
        Reset environment to initial state.
        Returns initial observation.
        """
        self._task_type = random.choice(["fraud", "ip_trace", "account_link"])
        self._is_fraud = random.choice([True, False])
        self._done = False
        self._step_count = 0
        self._episode_rewards = []
        self._current_action = None

        self._state_data = {
            "task_type": self._task_type,
            "transaction_amount": random.choice([100, 500, 5000, 50000, 100000]),
            "ip_address": random.choice(
                ["192.168.1.1", "10.0.0.5", "185.220.101.45", "172.16.0.0"]
            ),
            "user_age_days": random.choice([1, 30, 365, 1000]),
            "previous_flags": random.choice([0, 1, 2, 5]),
            "location_match": random.choice([True, False]),
            "risk_score": round(random.uniform(0.0, 1.0), 2),
            "step_count": 0,
            "is_fraud": self._is_fraud,
        }

        return InvestigatorObservation(
            task_type=self._state_data["task_type"],
            transaction_amount=self._state_data["transaction_amount"],
            ip_address=self._state_data["ip_address"],
            user_age_days=self._state_data["user_age_days"],
            previous_flags=self._state_data["previous_flags"],
            location_match=self._state_data["location_match"],
            risk_score=self._state_data["risk_score"],
            step_count=0,
            done=False,
            reward=0.0,
            message=f"New {self._task_type} investigation started.",
        )

    def step(self, action: InvestigatorAction) -> InvestigatorObservation:
        """
        Execute action in environment.
        
        Args:
            action: InvestigatorAction with valid action string
            
        Returns:
            InvestigatorObservation with reward, done flag, and info
        """
        # Validate action
        valid_actions = ["FLAG_TRANSACTION", "IGNORE", "TRACE_IP", "BLOCK_ACCOUNT"]
        if action.action not in valid_actions:
            action.action = "IGNORE"  # Default to safe action
        
        self._step_count += 1
        self._state_data["step_count"] = self._step_count
        self._current_action = action.action
        
        # Calculate reward using task graders
        reward = self._calculate_reward(action.action)
        self._episode_rewards.append(reward)

        # Determine if episode ends
        # Episode ends when: decisive action taken OR max_steps reached
        if reward >= 0.5:  # Good action
            self._done = True
            message = f"Action '{action.action}' successful. Episode complete."
        elif reward <= -0.3:  # Bad action - penalize but allow retry
            self._done = self._step_count >= self._max_steps
            message = f"Action '{action.action}' performed poorly. "
        else:  # Neutral/moderate action
            self._done = self._step_count >= self._max_steps
            message = f"Action '{action.action}' executed. Continuing investigation..."

        return InvestigatorObservation(
            task_type=self._state_data["task_type"],
            transaction_amount=self._state_data["transaction_amount"],
            ip_address=self._state_data["ip_address"],
            user_age_days=self._state_data["user_age_days"],
            previous_flags=self._state_data["previous_flags"],
            location_match=self._state_data["location_match"],
            risk_score=self._state_data["risk_score"],
            step_count=self._step_count,
            done=self._done,
            reward=reward,
            message=message,
        )

    @property
    def state(self) -> InvestigatorState:
        """
        Get current environment state.
        Implements OpenEnv state() endpoint.
        """
        return InvestigatorState(
            step_count=self._step_count,
            task_type=self._task_type,
            done=self._done,
            current_reward=self._episode_rewards[-1] if self._episode_rewards else 0.0,
        )

    def _calculate_reward(self, action: str) -> float:
        """
        Calculate reward with meaningful signal over trajectory.
        
        Reward structure provides:
        - Positive reward for correct actions
        - Partial credit for partially correct actions
        - Penalties for wrong actions
        - Encourages decisive action (not infinite loops)
        """
        reward = 0.0
        task = self._task_type
        is_fraud = self._state_data.get("is_fraud", False)
        is_malicious_ip = "185.220" in self._state_data.get("ip_address", "")
        risk_score = self._state_data.get("risk_score", 0.5)
        
        # FRAUD DETECTION TASK
        if task == "fraud":
            if action == "FLAG_TRANSACTION" and is_fraud:
                # Correct decision
                reward = 1.0 + (risk_score * 0.1)  # Bonus for high-risk detection
            elif action == "IGNORE" and not is_fraud:
                # Correct allow-through
                reward = 0.7
            elif action == "FLAG_TRANSACTION" and not is_fraud:
                # False positive - penalize
                reward = -0.3
            elif action == "IGNORE" and is_fraud:
                # Missed fraud - significant penalty
                reward = -0.5 - (risk_score * 0.2)
            else:
                # Invalid action for this task
                reward = -0.2
        
        # IP TRACE TASK
        elif task == "ip_trace":
            if action == "TRACE_IP" and is_malicious_ip:
                reward = 1.0 + (0.1 if self._step_count <= 3 else 0)  # Bonus for quick detection
            elif action == "IGNORE" and not is_malicious_ip:
                reward = 0.7
            elif action == "TRACE_IP" and not is_malicious_ip:
                # False positive investigation - minor penalty
                reward = -0.2
            elif action == "IGNORE" and is_malicious_ip:
                # Missed malicious IP - significant penalty
                reward = -0.4 - (0.1 if risk_score > 0.7 else 0)
            else:
                reward = -0.3
        
        # ACCOUNT LINK TASK
        elif task == "account_link":
            if action == "BLOCK_ACCOUNT" and is_fraud:
                reward = 1.0 + (0.05 if self._step_count <= 2 else 0)  # Bonus for quick response
            elif action == "IGNORE" and not is_fraud:
                reward = 0.8
            elif action == "FLAG_TRANSACTION" and is_fraud:
                # Partial credit for identifying fraud but not blocking account
                reward = 0.5
            elif action == "BLOCK_ACCOUNT" and not is_fraud:
                # Falsely blocked account - significant penalty
                reward = -0.4
            elif action == "IGNORE" and is_fraud:
                # Missed fraud - major penalty
                reward = -0.3
            else:
                reward = -0.2
        
        # Clamp reward to [-1.0, 1.0]
        return max(-1.0, min(1.0, reward))


"""
Task definitions and graders for AI Cyber Investigator Environment.
Each task has deterministic success/failure criteria (0.0-1.0 scoring).
"""

from typing import Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class TaskGrade:
    """Result of task grading."""
    task_name: str
    score: float  # 0.0 to 1.0
    success: bool
    reason: str
    reward_trajectory: list  # List of step rewards


class FraudDetectionGrader:
    """
    Task 1: Fraud Detection (40% weight)
    Detect fraudulent financial transactions.
    
    Success criteria:
    - If is_fraud=True and action=FLAG_TRANSACTION → +1.0
    - If is_fraud=False and action=IGNORE → +0.7
    - If is_fraud=True and action=IGNORE → -0.5 (missed fraud)
    - If is_fraud=False and action=FLAG_TRANSACTION → -0.3 (false alarm)
    """
    
    name = "fraud_detection"
    difficulty = "easy"
    weight = 0.40
    
    @staticmethod
    def evaluate(state: Dict[str, Any], action: str, 
                 rewards_trajectory: list) -> TaskGrade:
        """Score fraud detection task performance."""
        is_fraud = state.get("is_fraud", False)
        
        # Determine correctness
        if is_fraud and action == "FLAG_TRANSACTION":
            final_reward = 1.0
            success = True
            reason = "Correctly flagged fraudulent transaction"
        elif not is_fraud and action == "IGNORE":
            final_reward = 0.7
            success = True
            reason = "Correctly allowed legitimate transaction"
        elif is_fraud and action == "IGNORE":
            final_reward = -0.5
            success = False
            reason = "Missed fraud - allowed fraudulent transaction"
        elif not is_fraud and action == "FLAG_TRANSACTION":
            final_reward = -0.3
            success = False
            reason = "False alarm - flagged legitimate transaction"
        else:
            final_reward = -0.2
            success = False
            reason = f"Invalid action '{action}' for fraud detection"
        
        # Normalize score to [0, 1] range
        normalized_score = max(0.0, min(1.0, (final_reward + 1.0) / 2.0))
        
        return TaskGrade(
            task_name=FraudDetectionGrader.name,
            score=normalized_score,
            success=success,
            reason=reason,
            reward_trajectory=rewards_trajectory
        )


class IPTraceGrader:
    """
    Task 2: IP Investigation (35% weight)
    Identify and trace malicious IP addresses.
    
    Success criteria:
    - Malicious IP (185.220.*) + TRACE_IP → +1.0
    - Benign IP + IGNORE → +0.7
    - Malicious IP + IGNORE → -0.4 (missed threat)
    - Benign IP + TRACE_IP → -0.2 (false positive investigation)
    """
    
    name = "ip_trace"
    difficulty = "medium"
    weight = 0.35
    
    MALICIOUS_IP_PATTERNS = ["185.220", "192.0.2", "198.51.100"]  # TOR, test ranges
    
    @staticmethod
    def is_malicious_ip(ip: str) -> bool:
        """Check if IP is malicious based on known patterns."""
        return any(ip.startswith(pattern) for pattern in IPTraceGrader.MALICIOUS_IP_PATTERNS)
    
    @staticmethod
    def evaluate(state: Dict[str, Any], action: str,
                 rewards_trajectory: list) -> TaskGrade:
        """Score IP trace task performance."""
        ip = state.get("ip_address", "")
        is_malicious = IPTraceGrader.is_malicious_ip(ip)
        
        if is_malicious and action == "TRACE_IP":
            final_reward = 1.0
            success = True
            reason = f"Correctly traced malicious IP {ip}"
        elif not is_malicious and action == "IGNORE":
            final_reward = 0.7
            success = True
            reason = f"Correctly ignored benign IP {ip}"
        elif is_malicious and action == "IGNORE":
            final_reward = -0.4
            success = False
            reason = f"Missed threat - ignored malicious IP {ip}"
        elif not is_malicious and action == "TRACE_IP":
            final_reward = -0.2
            success = False
            reason = f"False positive - investigated benign IP {ip}"
        else:
            final_reward = -0.3
            success = False
            reason = f"Invalid action '{action}' for IP trace task"
        
        normalized_score = max(0.0, min(1.0, (final_reward + 1.0) / 2.0))
        
        return TaskGrade(
            task_name=IPTraceGrader.name,
            score=normalized_score,
            success=success,
            reason=reason,
            reward_trajectory=rewards_trajectory
        )


class AccountLinkGrader:
    """
    Task 3: Account Link Analysis (25% weight)
    Detect and respond to linked account fraud patterns.
    
    Success criteria:
    - Fraud detected + BLOCK_ACCOUNT → +1.0
    - Legitimate + IGNORE → +0.8
    - Fraud detected + FLAG_TRANSACTION → +0.5 (partial credit)
    - Fraud detected + IGNORE → -0.3 (missed fraud)
    """
    
    name = "account_link"
    difficulty = "hard"
    weight = 0.25
    
    @staticmethod
    def evaluate(state: Dict[str, Any], action: str,
                 rewards_trajectory: list) -> TaskGrade:
        """Score account link analysis task performance."""
        is_fraud = state.get("is_fraud", False)
        
        if is_fraud and action == "BLOCK_ACCOUNT":
            final_reward = 1.0
            success = True
            reason = "Correctly blocked fraudulent linked account"
        elif not is_fraud and action == "IGNORE":
            final_reward = 0.8
            success = True
            reason = "Correctly allowed legitimate linked account"
        elif is_fraud and action == "FLAG_TRANSACTION":
            final_reward = 0.5
            success = True
            reason = "Partially identified fraud (flagged transaction instead of blocking account)"
        elif is_fraud and action == "IGNORE":
            final_reward = -0.3
            success = False
            reason = "Missed linked fraud account"
        elif not is_fraud and action == "BLOCK_ACCOUNT":
            final_reward = -0.4
            success = False
            reason = "Incorrectly blocked legitimate account"
        else:
            final_reward = -0.2
            success = False
            reason = f"Invalid action '{action}' for account link task"
        
        normalized_score = max(0.0, min(1.0, (final_reward + 1.0) / 2.0))
        
        return TaskGrade(
            task_name=AccountLinkGrader.name,
            score=normalized_score,
            success=success,
            reason=reason,
            reward_trajectory=rewards_trajectory
        )


class CompositeGrader:
    """
    Composite grader that evaluates all 3 tasks and computes weighted score.
    """
    
    GRADERS = [
        FraudDetectionGrader,
        IPTraceGrader,
        AccountLinkGrader,
    ]
    
    @staticmethod
    def grade_all(state: Dict[str, Any], action: str,
                  rewards_trajectory: list) -> Dict[str, TaskGrade]:
        """Grade all tasks for a given episode."""
        results = {}
        for grader_class in CompositeGrader.GRADERS:
            grade = grader_class.evaluate(state, action, rewards_trajectory)
            results[grade.task_name] = grade
        return results
    
    @staticmethod
    def compute_composite_score(grades: Dict[str, TaskGrade]) -> Tuple[float, Dict]:
        """
        Compute weighted composite score from all task grades.
        Returns (float score [0-1], dict with breakdown).
        """
        total_score = 0.0
        total_weight = 0.0
        breakdown = {}
        
        for grader_class in CompositeGrader.GRADERS:
            task_name = grader_class.name
            if task_name in grades:
                grade = grades[task_name]
                weighted = grade.score * grader_class.weight
                total_score += weighted
                total_weight += grader_class.weight
                breakdown[task_name] = {
                    "score": grade.score,
                    "weight": grader_class.weight,
                    "weighted_score": weighted,
                    "success": grade.success,
                    "reason": grade.reason,
                }
        
        # Normalize by total weight to handle missing tasks
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 0.0
        
        breakdown["composite"] = {
            "final_score": max(0.0, min(1.0, final_score)),
            "total_weight": total_weight,
        }
        
        return max(0.0, min(1.0, final_score)), breakdown

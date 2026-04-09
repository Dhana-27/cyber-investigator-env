#!/usr/bin/env python3
"""
Validation script for OpenEnv spec compliance.

Run: python validate.py
or:  openenv validate

Checks:
- openenv.yaml syntax and metadata
- Typed Pydantic models (Observation, Action, State)
- step(), reset(), state() method signatures
- Grader definitions and scoring (0.0-1.0)
- Reward function properties
- Task definitions (3+ tasks)
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))


def validate_openenv_yaml() -> Tuple[bool, List[str]]:
    """Validate openenv.yaml exists and has required fields."""
    errors = []
    try:
        import yaml
        
        yaml_path = Path(__file__).parent / "openenv.yaml"
        if not yaml_path.exists():
            errors.append("❌ openenv.yaml not found")
            return False, errors
        
        with open(yaml_path) as f:
            config = yaml.safe_load(f)
        
        required_fields = ["spec_version", "name", "type", "runtime"]
        for field in required_fields:
            if field not in config:
                errors.append(f"❌ Missing required field in openenv.yaml: {field}")
        
        if config.get("spec_version") != 1:
            errors.append(f"❌ spec_version should be 1, got: {config.get('spec_version')}")
        
        if config.get("type") not in ["standard", "benchmark"]:
            errors.append(f"❌ type should be 'standard' or 'benchmark', got: {config.get('type')}")
        
        if not errors:
            errors.append(f"✅ openenv.yaml valid (name={config.get('name')}, type={config.get('type')})")
        
        return len(errors) == 1, errors  # Success if only the ✅ message
    
    except Exception as e:
        errors.append(f"❌ Error validating openenv.yaml: {e}")
        return False, errors


def validate_pydantic_models() -> Tuple[bool, List[str]]:
    """Validate typed Pydantic models exist."""
    errors = []
    try:
        from models import InvestigatorAction, InvestigatorObservation, InvestigatorState
        from pydantic import BaseModel
        
        # Check each model is a Pydantic model
        for model_name, model_class in [
            ("InvestigatorAction", InvestigatorAction),
            ("InvestigatorObservation", InvestigatorObservation),
            ("InvestigatorState", InvestigatorState),
        ]:
            if not issubclass(model_class, BaseModel):
                errors.append(f"❌ {model_name} is not a Pydantic BaseModel")
            else:
                errors.append(f"✅ {model_name} is typed Pydantic model")
        
        # Check required fields
        obs_fields = InvestigatorObservation.model_fields.keys()
        required_obs_fields = {"task_type", "step_count", "done", "reward"}
        if not required_obs_fields.issubset(obs_fields):
            missing = required_obs_fields - set(obs_fields)
            errors.append(f"❌ InvestigatorObservation missing fields: {missing}")
        
        return len([e for e in errors if e.startswith("❌")]) == 0, errors
    
    except Exception as e:
        errors.append(f"❌ Error validating models: {e}")
        return False, errors


def validate_environment_methods() -> Tuple[bool, List[str]]:
    """Validate environment has step(), reset(), state() methods."""
    errors = []
    try:
        from environment import InvestigatorEnvironment
        from models import InvestigatorAction, InvestigatorObservation
        import inspect
        
        env = InvestigatorEnvironment()
        
        # Check step() method
        if not hasattr(env, "step"):
            errors.append("❌ Environment missing step() method")
        else:
            sig = inspect.signature(env.step)
            if "action" not in sig.parameters:
                errors.append("❌ step() missing 'action' parameter")
            else:
                errors.append("✅ step(action) method exists with correct signature")
        
        # Check reset() method
        if not hasattr(env, "reset"):
            errors.append("❌ Environment missing reset() method")
        else:
            errors.append("✅ reset() method exists")
        
        # Check state property/method
        if not hasattr(env, "state"):
            errors.append("❌ Environment missing state property/method")
        else:
            errors.append("✅ state property exists")
        
        # Test methods return correct types
        try:
            obs = env.reset()
            if not isinstance(obs, InvestigatorObservation):
                errors.append(f"❌ reset() returns {type(obs)}, expected InvestigatorObservation")
            else:
                errors.append(f"✅ reset() returns InvestigatorObservation")
            
            action = InvestigatorAction(action="IGNORE")
            obs = env.step(action)
            if not isinstance(obs, InvestigatorObservation):
                errors.append(f"❌ step() returns {type(obs)}, expected InvestigatorObservation")
            else:
                errors.append(f"✅ step() returns InvestigatorObservation with reward={obs.reward:.2f}")
        except Exception as e:
            errors.append(f"❌ Error testing environment methods: {e}")
        
        return len([e for e in errors if e.startswith("❌")]) == 0, errors
    
    except Exception as e:
        errors.append(f"❌ Error validating environment: {e}")
        return False, errors


def validate_reward_function() -> Tuple[bool, List[str]]:
    """Validate reward function properties."""
    errors = []
    try:
        from environment import InvestigatorEnvironment
        from models import InvestigatorAction
        
        env = InvestigatorEnvironment()
        env.reset()
        
        # Test that rewards are in [-1, 1] range
        rewards = []
        test_actions = ["FLAG_TRANSACTION", "IGNORE", "TRACE_IP", "BLOCK_ACCOUNT"]
        
        for action_str in test_actions:
            try:
                action = InvestigatorAction(action=action_str)
                obs = env.step(action)
                rewards.append(obs.reward)
                env.reset()  # Reset for next action
            except:
                pass
        
        if not rewards:
            errors.append("❌ Could not test any reward values")
            return False, errors
        
        all_in_range = all(-1.0 <= r <= 1.0 for r in rewards)
        if not all_in_range:
            out_of_range = [r for r in rewards if not (-1.0 <= r <= 1.0)]
            errors.append(f"❌ Rewards out of range [-1, 1]: {out_of_range}")
        else:
            errors.append(f"✅ All rewards in valid range [-1, 1]")
        
        # Check for trajectory rewards (not just binary end-of-episode)
        if len(set(rewards)) > 1:
            errors.append(f"✅ Reward function provides varied signals: {rewards}")
        else:
            errors.append(f"⚠️  Reward function may be too binary")
        
        return all_in_range, errors
    
    except Exception as e:
        errors.append(f"❌ Error validating reward function: {e}")
        return False, errors


def validate_task_graders() -> Tuple[bool, List[str]]:
    """Validate task grader definitions."""
    errors = []
    try:
        from tasks import CompositeGrader, FraudDetectionGrader, IPTraceGrader, AccountLinkGrader
        
        graders = [FraudDetectionGrader, IPTraceGrader, AccountLinkGrader]
        
        if len(graders) < 3:
            errors.append(f"❌ Need at least 3 tasks, got {len(graders)}")
        else:
            errors.append(f"✅ {len(graders)} task graders defined")
        
        # Check each grader
        for grader_class in graders:
            task_name = getattr(grader_class, "name", "unknown")
            difficulty = getattr(grader_class, "difficulty", "unknown")
            weight = getattr(grader_class, "weight", 0)
            
            if not hasattr(grader_class, "evaluate"):
                errors.append(f"❌ {task_name} grader missing evaluate() method")
            else:
                errors.append(f"✅ {task_name} task (difficulty={difficulty}, weight={weight:.2f})")
            
            # Test grader
            try:
                test_state = {"is_fraud": True, "ip_address": "185.220.101.45"}
                grade = grader_class.evaluate(test_state, "FLAG_TRANSACTION", [])
                if not (0.0 <= grade.score <= 1.0):
                    errors.append(f"❌ {task_name} grader score out of range: {grade.score}")
                else:
                    errors.append(f"✅ {task_name} grader score valid: {grade.score:.2f}")
            except Exception as e:
                errors.append(f"❌ Error testing {task_name} grader: {e}")
        
        return len([e for e in errors if e.startswith("❌")]) == 0, errors
    
    except Exception as e:
        errors.append(f"❌ Error validating task graders: {e}")
        return False, errors


def validate_inference_script() -> Tuple[bool, List[str]]:
    """Validate inference.py exists and has required structure."""
    errors = []
    try:
        inference_path = Path(__file__).parent / "inference.py"
        
        if not inference_path.exists():
            errors.append("❌ inference.py not found in root directory")
            return False, errors
        
        with open(inference_path) as f:
            content = f.read()
        
        # Check for required components
        checks = [
            ("API_BASE_URL", "API_BASE_URL environment variable"),
            ("MODEL_NAME", "MODEL_NAME environment variable"),
            ("HF_TOKEN", "HF_TOKEN/API_KEY environment variable"),
            ("OpenAI", "OpenAI client import"),
            ("log_start", "[START] logging function"),
            ("log_step", "[STEP] logging function"),
            ("log_end", "[END] logging function"),
        ]
        
        missing = []
        for var, desc in checks:
            if var not in content:
                missing.append(desc)
        
        if missing:
            errors.append(f"❌ inference.py missing: {', '.join(missing)}")
        else:
            errors.append("✅ inference.py has all required components")
        
        return len(missing) == 0, errors
    
    except Exception as e:
        errors.append(f"❌ Error validating inference.py: {e}")
        return False, errors


def main():
    """Run all validation checks."""
    print("\n" + "="*70)
    print("🔐 OpenEnv Specification Compliance Validation")
    print("="*70 + "\n")
    
    checks = [
        ("openenv.yaml", validate_openenv_yaml),
        ("Pydantic Models", validate_pydantic_models),
        ("Environment Methods", validate_environment_methods),
        ("Reward Function", validate_reward_function),
        ("Task Graders (3+ tasks)", validate_task_graders),
        ("Inference Script", validate_inference_script),
    ]
    
    results = {}
    for check_name, check_func in checks:
        print(f"\n📋 Checking {check_name}...")
        try:
            passed, messages = check_func()
            results[check_name] = (passed, messages)
            for msg in messages:
                print(f"  {msg}")
        except Exception as e:
            print(f"  ❌ Exception during check: {e}")
            results[check_name] = (False, [str(e)])
    
    # Summary
    print("\n" + "="*70)
    print("📊 Validation Summary")
    print("="*70)
    
    passed_count = sum(1 for passed, _ in results.values() if passed)
    total_count = len(results)
    
    for check_name, (passed, _) in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {check_name}")
    
    print(f"\n  Overall: {passed_count}/{total_count} checks passed")
    
    if passed_count == total_count:
        print("\n🎉 Environment is compliant with OpenEnv specification!")
        print("   Ready for submission to Hugging Face Spaces.\n")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} checks failed. Please fix the issues above.\n")
        return 1


if __name__ == "__main__":
    sys_exit_code = main()
    sys.exit(sys_exit_code)

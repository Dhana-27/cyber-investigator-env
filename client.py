from openenv.core import EnvClient, StepResult
from models import InvestigatorAction, InvestigatorObservation, InvestigatorState


class InvestigatorEnv(EnvClient[InvestigatorAction, InvestigatorObservation, InvestigatorState]):

    def _step_payload(self, action: InvestigatorAction) -> dict:
        return {"action": action.action}

    def _parse_result(self, payload: dict) -> StepResult[InvestigatorObservation]:
        obs = InvestigatorObservation(**payload["observation"])
        return StepResult(
            observation=obs,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> InvestigatorState:
        return InvestigatorState(**payload)

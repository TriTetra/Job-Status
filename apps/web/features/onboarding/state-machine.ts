import { STEP_ORDER } from "./constants";
import type { OnboardingState } from "./types";

export function nextState(
  current: OnboardingState
): OnboardingState {
  if (current === "NOT_STARTED") return "IDENTITY";
  const idx = STEP_ORDER.indexOf(current as typeof STEP_ORDER[number]);
  if (idx === -1 || idx === STEP_ORDER.length - 1) return "READY";
  return STEP_ORDER[idx + 1];
}

export function stepIndex(state: OnboardingState): number {
  return STEP_ORDER.indexOf(state as typeof STEP_ORDER[number]);
}

export function isComplete(state: OnboardingState): boolean {
  return state === "READY";
}

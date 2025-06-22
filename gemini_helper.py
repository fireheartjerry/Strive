import os
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# -------------------- Exceptions --------------------
class GeminiError(Exception):
    pass

class GeminiAuthError(GeminiError):
    pass

class GeminiRateLimitError(GeminiError):
    pass

class GeminiTimeoutError(GeminiError):
    pass

class GeminiAPIError(GeminiError):
    pass

# -------------------- Configuration --------------------
@dataclass
class GeminiConfig:
    api_key: str = field(default_factory=lambda: os.getenv("GENAI_API_KEY", ""))
    model: str = "gemini-2.5-flash-lite-preview-06-17"
    temperature: float = 1.0
    max_output_tokens: int = 1024
    max_retries: int = 5
    initial_backoff: float = 1.0
    max_backoff: float = 16.0
    timeout: float = 30.0  # seconds

# -------------------- Client Initialization --------------------
def create_client(config: GeminiConfig) -> genai.Client:
    if not config.api_key:
        raise GeminiAuthError("No API key provided. Set GENAI_API_KEY or pass api_key.")
    return genai.Client(api_key=config.api_key, timeout=config.timeout)

# -------------------- Prompt Builder --------------------
class GeminiHelper:
    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config or GeminiConfig()
        self.client = create_client(self.config)

    def build_workout_prompt(
        self,
        workout_type: str,
        history: List[int],
        average: float,
        fitness_level: str,
        target_outcome: str,
        equipment: List[str],
        time_available: int,
        injury_flags: List[str],
        previous_responses: Optional[List[str]] = None,
    ) -> List[types.Content]:
        # Summarize context
        history_str = ", ".join(str(x) for x in history)
        eq_str = ", ".join(equipment) if equipment else "none"
        inj_str = ", ".join(injury_flags) if injury_flags else "none"
        prev_block = ("\n".join(previous_responses[-3:]) if previous_responses else "none")

        # Map muscles
        muscle_map = {
            'plank': ['core'],
            'vsit': ['core'],
            'pushup': ['chest', 'shoulders', 'triceps'],
        }
        muscles = muscle_map.get(workout_type, ['full-body'])

        # Difficulty scaling
        level_scale = {'beginner': 0.6, 'intermediate': 0.8, 'advanced': 1.0}
        scale = level_scale.get(fitness_level.lower(), 0.75)
        prog_pct = int((scale - 0.5) * 100)

        # Outcome parameters
        outcome_params = {
            'hypertrophy': {'reps': '8-12', 'rest': '60-90s'},
            'endurance': {'reps': '15-20', 'rest': '30-45s'},
            'recovery': {'reps': '10-15 light', 'rest': '90-120s mobility'},
        }
        params = outcome_params.get(target_outcome.lower(), {'reps': '10-15', 'rest': '60s'})

        # Assemble prompt
        lines = [
            "You are an elite fitness coach specializing in dynamic, data-driven plans.",
            f"Workout Type: {workout_type}",
            f"History: [{history_str}] (avg {average:.1f} sec/reps)",
            f"Fitness Level: {fitness_level}",
            f"Target Outcome: {target_outcome}",
            "",  # section break
            "Constraints:",
            f"- Equipment: {eq_str}",
            f"- Time Available: {time_available} minutes",
            f"- Injury Flags: {inj_str}",
            "",  # section break
            "Parameters:",
            f"- Muscle Groups: {', '.join(muscles)}",
            f"- Difficulty: {int(scale*100)}% effort",
            f"- Reps/Range: {params['reps']}",
            f"- Rest Interval: {params['rest']}",
            f"- Weekly Progression: +{prog_pct}% load",
            "",  # section break
            "Structure Outline:",
            "1) Warm-up: 5-10min dynamic mobilization",
            "2) Main Sets: list exercises by muscle, sets x reps at % effort, rest intervals",
            "3) Cool-down: mobility/stretch, 5min",
            "",  # section break
            "Incorporate balance across exercise categories, adjust for time, and ensure safety.",
            f"Continue reasoning across turns; reference prior: {prev_block}",
            "",  # final instruction
            "Respond as a coach in conversational tone, detailing each section, and end with a motivational message."
        ]
        prompt_text = "\n".join(lines)

        system_part = types.Part.from_text(
            text=(
                "You generate expert workout plans with clear rationale. "
                "Provide detailed guidance and a motivational closing sentence."
            )
        )
        user_part = types.Part.from_text(text=prompt_text)

        return [
            types.Content(role="system", parts=[system_part]),
            types.Content(role="user", parts=[user_part])
        ]

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, max=16),
        retry=retry_if_exception_type((GeminiRateLimitError, GeminiTimeoutError, GeminiAPIError)),
    )
    def generate_workout_plan(
        self,
        workout_type: str,
        history: List[int],
        average: float,
        fitness_level: str,
        target_outcome: str,
        equipment: List[str],
        time_available: int,
        injury_flags: List[str],
        previous_responses: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        contents = self.build_workout_prompt(
            workout_type, history, average,
            fitness_level, target_outcome, equipment,
            time_available, injury_flags, previous_responses
        )
        start = time.time()
        try:
            chunks = list(self.client.models.generate_content_stream(
                model=self.config.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_output_tokens,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    response_mime_type="text/plain",
                ),
            ))
        except Exception as e:
            raise GeminiAPIError(str(e))
        elapsed = time.time() - start
        text = ''.join(chunk.text for chunk in chunks)
        return {
            'plan': text,
            'latency_s': round(elapsed, 3)
        }

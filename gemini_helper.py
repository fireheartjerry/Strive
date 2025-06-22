import os
import time
from typing import List, Dict, Any
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

# -------------------- Helper Class --------------------
class GeminiHelper:
    def __init__(self, config: GeminiConfig = None):
        self.config = config or GeminiConfig()
        self.client = create_client(self.config)

    def build_workout_prompt(
        self,
        workout_type: str,
        history: List[int],
        average: float,
    ) -> List[types.Content]:
        # Prepare context summary
        history_str = ", ".join(str(x) for x in history)
        # Classify fitness level by percentiles
        sorted_hist = sorted(history)
        if len(sorted_hist) >= 3:
            p33 = sorted_hist[int(len(sorted_hist) * 0.33)]
            p66 = sorted_hist[int(len(sorted_hist) * 0.66)]
        else:
            p33, p66 = average * 0.8, average * 1.2
        if average <= p33:
            fitness_level = 'beginner'
        elif average <= p66:
            fitness_level = 'intermediate'
        else:
            fitness_level = 'advanced'

        # Detect progression trend
        trend = 'increasing' if len(history) > 1 and history[-1] > history[0] else 'variable'

        # Map target muscle groups automatically
        muscle_map = {
            'plank': ['core'],
            'vsit': ['core'],
            'pushup': ['chest', 'shoulders', 'triceps'],
        }
        muscles = muscle_map.get(workout_type, ['full-body'])

        # Build dynamic prompt
        prompt_lines = [
            "You are an elite fitness coach generating a personalized workout plan.",
            f"Workout Type: {workout_type}",
            f"Performance History: [{history_str}] (average {average:.1f})",  
            f"Detected Fitness Level: {fitness_level} ({trend} trend)",
            f"Primary Targets: {', '.join(muscles)}",  
            "",  
            "Design a structured plan with:",
            "1) Warm-up: tailored to prime the primary targets and joint mobility.",
            "2) Main Session: balanced combination of strength, endurance, and mobility exercises.",
            "   - Specify sets, reps (or duration), load intensity (% of max), and rest periods.",
            "   - Progression logic: adjust volume or intensity week-over-week.",
            "3) Cool-down: mobility and stretching focused on the engaged muscles.",
            "",  
            "Constraints & Notes:",
            "- Optimize for efficiency in a single session.",
            "- Handle limited or no equipment scenarios with bodyweight alternatives.",
            "- Ensure safety and accommodate potential joint stress.",
            "",  
            "Provide the plan in conversational coach style, explaining your reasoning briefly, and conclude with a motivational message to the user."
        ]
        prompt_text = "\n".join(prompt_lines)

        system_part = types.Part.from_text(
            text=(
                "Use chain-of-thought reasoning to justify exercise choices, scaling, and rest logic."
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
    ) -> Dict[str, Any]:
        # Build prompt with only history & average inputs
        contents = self.build_workout_prompt(workout_type, history, average)
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

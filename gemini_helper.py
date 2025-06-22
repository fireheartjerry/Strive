'''
A helper module to generate workout plans using Google Gemini API,
complete with history-based prompt construction.
''' 

import os
from typing import List
from google import genai
from google.genai import types


class GeminiAPIError(Exception):
    """Raised when the Gemini API call fails or configuration is missing."""
    pass


def create_client(api_key: str = None) -> genai.Client:
    """
    Initialize and return a Gemini API client.

    Args:
        api_key: Optional API key. If provided, uses this value; otherwise reads GENAI_API_KEY.

    Returns:
        An authenticated genai.Client instance.

    Raises:
        GeminiAPIError: If no API key is available.
    """
    key = api_key or os.getenv("GENAI_API_KEY")
    if not key:
        raise GeminiAPIError("API key not provided. Set GENAI_API_KEY environment variable.")
    return genai.Client(api_key=key)


DEFAULT_MODEL = "gemini-2.5-flash-lite-preview-06-17"

SYSTEM_INSTRUCTION_PART = types.Part.from_text(
    text=(
        "You are a personal coach that generates concise workout plans. "
        "You will receive a user's exercise history and average performance. "
        "Begin with a brief summary of their history and average, then "
        "provide a targeted workout plan including sets, reps, weight, recovery, and tips. "
        "Keep responses under 2000 characters and end with a motivational message."
    )
)


def build_workout_prompt(
    workout_type: str,
    history: List[int],
    average: float
) -> str:
    """
    Construct a prompt string containing exercise history and average.

    Args:
        workout_type: One of 'plank', 'vsit', or 'pushup'.
        history: List of past durations (seconds) or rep counts.
        average: The average of the history values.

    Returns:
        The formatted prompt string for the Gemini API.
    """
    labels = {
        'plank': 'plank hold times (sec)',
        'vsit':  'V-sit hold times (sec)',
        'pushup': 'push-up counts'
    }
    label = labels.get(workout_type, 'exercise metrics')

    history_str = ', '.join(str(x) for x in history)
    prompt = (
        f"User history for {label}: [{history_str}]. "
        f"Average {label.split(' ')[0]}: {average:.1f}. "
        "Generate a personalized workout plan based on this data."
    )
    return prompt


def generate_workout_plan(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 1.45,
    max_output_tokens: int = 5000
) -> str:
    """
    Call the Gemini API to generate a workout plan from the prompt.

    Args:
        prompt: The user-facing prompt.
        model: The Gemini model identifier.
        temperature: Sampling temperature.
        max_output_tokens: Maximum generated tokens.

    Returns:
        The generated workout plan text.

    Raises:
        GeminiAPIError: If the API call fails.
    """
    client = create_client()
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )
    ]
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        response_mime_type="text/plain",
        system_instruction=[SYSTEM_INSTRUCTION_PART]
    )

    try:
        chunks = []
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config
        ):
            chunks.append(chunk.text)
        return ''.join(chunks)
    except Exception as e:
        raise GeminiAPIError(f"Gemini API error: {e}")


def plan_for_data(
    workout_type: str,
    history: List[int],
    average: float
) -> str:
    """
    High-level function: builds prompt and returns workout plan.

    Args:
        workout_type: 'plank', 'vsit', or 'pushup'.
        history: Past performance values.
        average: Average of history.

    Returns:
        A tailored workout plan string.

    Raises:
        GeminiAPIError: If prompt build or API call fails.
    """
    prompt = build_workout_prompt(workout_type, history, average)
    return generate_workout_plan(prompt)

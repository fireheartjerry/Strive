'''
A helper module to generate workout plans using Google Gemini API.
'''

import os
from typing import List
from google import genai
from google.genai import types


class GeminiAPIError(Exception):
    """Custom exception for Gemini API failures."""
    pass


def create_client(api_key: str = None) -> genai.Client:
    """
    Initializes and returns a Gemini API client.

    Args:
        api_key: Optional API key. If not provided, reads from environment variable GENAI_API_KEY.

    Returns:
        An authenticated genai.Client instance.

    Raises:
        GeminiAPIError: If no API key is provided.
    """
    key = api_key or os.getenv("GENAI_API_KEY")
    if not key:
        raise GeminiAPIError("API key not provided. Set GENAI_API_KEY environment variable.")
    return genai.Client(api_key=key)


DEFAULT_MODEL = "gemini-2.5-flash-lite-preview-06-17"

SYSTEM_INSTRUCTION_PART = types.Part.from_text(
    text=(
        "You are a personal coach that gives general workout plans to people. "
        "You will receive their current progress in an exercise, tailor your "
        "response to their current level. For example, if someone can already do "
        "40 pushups with perfect form, it is unlikely that they will benefit from "
        "practicing inclined pushups. For your response, you will start with a short "
        "summary of the information about their progress that you received. You will "
        "follow that with a workout plan to strengthen the muscles involved in that "
        "workout and generally help them improve in that exercise. Give this as a list "
        "of exercises with sets, reps, weight, recovery, and all other pertinent "
        "information for them to follow. Limit your responses to within 2000 characters, "
        "so be brief and don't include any unnecessary information. Budget characters "
        "for a short motivational message at the end."
    )
)


def generate_workout_plan(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 1.45,
    max_output_tokens: int = 5000
) -> str:
    """
    Generates a workout plan from the given prompt using the Gemini API.

    Args:
        prompt: The user's current progress and goals description.
        model: Gemini model to use.
        temperature: Sampling temperature for response variability.
        max_output_tokens: Maximum tokens to generate.

    Returns:
        The generated workout plan as a string.

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
        system_instruction=[SYSTEM_INSTRUCTION_PART],
    )

    try:
        output = []  # collect streamed chunks
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config
        ):
            output.append(chunk.text)
        return "".join(output)

    except Exception as e:
        raise GeminiAPIError(f"Failed to generate content: {e}")


if __name__ == "__main__":
    prompt = input("Enter your workout prompt: ").strip()
    try:
        plan = generate_workout_plan(prompt)
        print(plan)
    except GeminiAPIError as err:
        print(f"Error: {err}")

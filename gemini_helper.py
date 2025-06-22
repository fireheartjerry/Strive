# file: workout_generator.py
# To run this code you need to install the following dependencies:
#   pip install google-genai tenacity

from typing import List
from google import genai
from google.genai import types


# -------------------- Public API --------------------
def generate_workout_plan(workout_type: str, history: List[int], average: float) -> str:
    """
    Build an advanced coach-style prompt from history & average,
    invoke Gemini with original API pattern, and return the plan text.
    """
    # 1) Summarize progress and derive context
    hist_str = ", ".join(str(x) for x in history)

    muscle_map = {
        "plank": ["core"],
        "vsit": ["core"],
        "pushup": ["chest", "shoulders", "triceps"],
    }
    targets = ", ".join(muscle_map.get(workout_type, ["full-body"]))

    # 2) Construct enriched prompt text
    prompt = f"""
You are an elite fitness coach using chain-of-thought reasoning.
Workout Type: {workout_type}
History: [{hist_str}] (avg {average:.1f})
Primary Targets: {targets}

Design a workout session:
1) Warm-up: dynamic drills tailored to primary targets.
2) Main: balanced strength, endurance & mobility exercises.
   - Specify sets/reps or duration, intensity (% of max), and rest intervals.
   - Include progression logic for future sessions.
3) Cool-down: mobility drills and stretching for engaged muscles.

Optimize for time efficiency and safety; provide bodyweight alternatives if no equipment.
Respond conversationally as a coach, explain reasoning briefly, and conclude with motivation.
""".strip()

    # 3) Invoke Gemini with strict original pattern
    client = genai.Client(
        api_key="AIzaSyCygKkv4M8HXsELEM1Dki4HyLfn1xWVbzw",
    )
    model = "gemini-2.5-flash-lite-preview-06-17"
    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=prompt)]),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1.45,
        max_output_tokens=5000,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(
                text="""
You are a world-class fitness coach and expert prompt engineer. When given a user's exercise history and average performance, you will:
1. Summarize their current level clearly and concisely.
2. Use chain-of-thought reasoning to explain your plan choices.
3. Provide a structured workout plan with sections:
   - Warm-up: targeted dynamic movements for the key muscle groups.
   - Main Session: exercises listing sets, reps or duration, suggested intensity (% of max), rest intervals, and clear progression steps.
   - Cool-down: mobility and stretching tailored to the engaged muscles.
4. Adapt difficulty based on inferred fitness level (beginner/intermediate/advanced) and performance trend.
5. Optimize for time efficiency and safety; always include bodyweight alternatives if no equipment is available.
6. Keep responses under 2000 characters, use a friendly, conversational 'coach' tone, and close with an uplifting motivational message.
7. VERY IMPORTANT: Return responses in HTML format with appropriate tags for each section. However, do not use like ``` html, just return the HTML directly.
8. EXTREMELY IMPORTANT: NEVER, UNDER ANY CIRCUMSTANCES, RETURN MARKDOWN OF ANY KIND. ALWAYS USE HTML.
"""
            ),
        ],
    )

    output = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        output += chunk.text
    return output


# -------------------- CLI TEST --------------------
if __name__ == "__main__":
    import json

    data = json.loads(
        input("Enter JSON like {'type':'plank','history':[30,45],'average':37.5}: ")
    )
    plan = generate_workout_plan(
        data.get("type"), data.get("history", []), data.get("average", 0)
    )
    print("\n=== GENERATED PLAN ===\n")
    print(plan)

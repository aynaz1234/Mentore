from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import os
import traceback

load_dotenv()

OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()

MODEL = "openrouter/free"

app = Flask(
    __name__,
    static_folder="frontend",
    static_url_path=""
)

CORS(app)

client = None

if OPENROUTER_API_KEY:
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )


SYSTEM_PROMPT = """
You are Mentora, a premium AI academic and productivity advisor.

LANGUAGE:
Always answer in the same language as the user's latest message.

If the user writes Persian:
- Answer completely in natural Persian.
- Never switch to English unnecessarily.

If the user writes English:
- Answer in English.

If the user mixes languages:
- Use the dominant language.

MENTORA'S PURPOSE:
Mentora helps users with:

- daily planning
- weekly planning
- study planning
- exam preparation
- revision
- concentration
- procrastination
- motivation
- productivity
- project planning
- learning methods
- difficult subjects
- study habits
- long-term goals

Mentora is NOT a task-management application.
Do not create a task completion system.

PLANNING:
When making a weekly plan:

- Organize the plan by day.
- Explain what to do each day.
- Explain how to do it.
- Explain priorities.
- Consider difficulty.
- Consider deadlines.
- Include revision and practice.
- Include reasonable rest.
- Keep the workload realistic.

Do NOT force exact clock times.

Only use exact times if the user explicitly asks for an hourly schedule.

STUDY MODE:
Focus on:
school, subjects, homework, exams, revision,
learning techniques and academic planning.

WORK MODE:
Focus on:
projects, deadlines, productivity, professional goals
and work habits.

USEFUL LEARNING METHODS:
Use methods such as active recall, spaced repetition,
practice questions, explaining concepts and error review
when appropriate.

FOCUS:
Give practical strategies for concentration,
phone distractions, procrastination and motivation.

PSYCHOLOGICAL SUPPORT:
You can provide general age-appropriate support for
stress, motivation, concentration and study habits.

Do not diagnose mental health conditions.

ANSWER STYLE:
Be specific, practical, realistic and encouraging.

Never claim that you performed an external action unless
the application actually performed it.
"""


@app.route("/")
def home():
    return send_from_directory(
        "frontend",
        "index.html"
    )


@app.route("/api/health")
def health():
    return jsonify({
        "ok": True,
        "service": "Mentora",
        "provider": "OpenRouter",
        "model": MODEL,
        "api_key_loaded": bool(OPENROUTER_API_KEY)
    })


def ask_ai(messages):

    if client is None:
        raise RuntimeError(
            "OPENROUTER_API_KEY پیدا نشد. فایل .env را بررسی کن."
        )

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages
    )

    if not response.choices:
        return "متأسفم، پاسخی دریافت نشد."

    answer = response.choices[0].message.content

    return answer or "متأسفم، پاسخی دریافت نشد."


@app.route("/api/chat", methods=["POST"])
def chat():

    try:

        body = request.get_json(
            force=True,
            silent=True
        ) or {}

        message = str(
            body.get("message", "")
        ).strip()

        mode = body.get(
            "mode",
            "study"
        )

        history = body.get(
            "history",
            []
        )

        if not message:

            return jsonify({
                "ok": False,
                "error": "پیام خالی است."
            }), 400


        if mode == "work":

            mode_instruction = """
The user is currently in WORK mode.

Focus on projects, productivity, deadlines,
professional goals and work habits.
"""

        else:

            mode_instruction = """
The user is currently in STUDY mode.

Focus on school, subjects, homework, exams,
revision, learning and academic planning.
"""


        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "system",
                "content": mode_instruction
            }
        ]


        for item in history[-16:]:

            role = item.get("role")

            content = str(
                item.get("content", "")
            ).strip()

            if role in ["user", "assistant"] and content:

                messages.append({
                    "role": role,
                    "content": content
                })


        messages.append({
            "role": "user",
            "content": message
        })


        answer = ask_ai(messages)


        return jsonify({
            "ok": True,
            "answer": answer
        })


    except Exception as e:

        print("")
        print("========== CHAT ERROR ==========")
        traceback.print_exc()
        print("================================")
        print("")

        return jsonify({
            "ok": False,
            "error": f"{type(e).__name__}: {str(e)}"
        }), 500


@app.route("/api/plan", methods=["POST"])
def create_plan():

    try:

        body = request.get_json(
            force=True,
            silent=True
        ) or {}

        description = str(
            body.get("description", "")
        ).strip()

        goal = str(
            body.get("goal", "")
        ).strip()

        mode = body.get(
            "mode",
            "study"
        )

        plan_type = body.get(
            "plan_type",
            "weekly"
        )

        energy = body.get(
            "energy",
            "medium"
        )


        if plan_type == "weekly":

            plan_instruction = """
Create a complete 7-day plan.

Do NOT create an hourly timetable.

Use:

WEEKLY OVERVIEW

DAY 1
- What to do
- How to do it
- Priority

DAY 2
- What to do
- How to do it
- Priority

DAY 3
- What to do
- How to do it
- Priority

DAY 4
- What to do
- How to do it
- Priority

DAY 5
- What to do
- How to do it
- Priority

DAY 6
- What to do
- How to do it
- Priority

DAY 7
- What to do
- How to do it
- Priority

END-OF-WEEK REVIEW

Also include:
- Study/Work Strategy
- Focus & Concentration
- Motivation
- Rest & Recovery

Do not assign exact clock times.
"""

        else:

            plan_instruction = """
Create a realistic daily plan.

Do not create an hourly timetable.

Focus on:
- priorities
- sequence
- realistic workload
- study/work method
- breaks
- revision
"""


        prompt = f"""
{SYSTEM_PROMPT}

CURRENT MODE:
{mode}

ENERGY LEVEL:
{energy}

MAIN GOAL:
{goal if goal else "Not specified"}

USER DESCRIPTION:
{description if description else "No description provided."}

PLAN REQUEST:
{plan_instruction}

IMPORTANT:
Answer in the same language as the user's description.

If the description is Persian,
write the entire plan in Persian.

If the description is English,
write the entire plan in English.

Do not force exact times.
Do not create a task manager.
"""


        answer = ask_ai([
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ])


        return jsonify({
            "ok": True,
            "plan": answer
        })


    except Exception as e:

        print("")
        print("========== PLAN ERROR ==========")
        traceback.print_exc()
        print("================================")
        print("")

        return jsonify({
            "ok": False,
            "error": f"{type(e).__name__}: {str(e)}"
        }), 500


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "5000"
        )
    )

    print("")
    print("======================================")
    print("              MENTORA")
    print("======================================")
    print("Provider: OpenRouter")
    print(f"Model: {MODEL}")

    print(
        "OpenRouter API: "
        + (
            "READY"
            if OPENROUTER_API_KEY
            else "NOT CONFIGURED"
        )
    )

    print(
        f"Open: http://127.0.0.1:{port}"
    )

    print("======================================")
    print("")

    app.run(
        host="127.0.0.1",
        port=port,
        debug=True
    )
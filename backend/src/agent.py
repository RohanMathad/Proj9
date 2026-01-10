import logging
import os
import sqlite3
from typing import Annotated, Optional, List
from dataclasses import dataclass

from dotenv import load_dotenv
from pydantic import Field

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    WorkerOptions,
    cli,
    function_tool,
    RunContext,
)

from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("interview-agent")
load_dotenv(".env.local")

DB_FILE = "interview_db.sqlite"

print("\n" + "🎤" * 40)
print("AI INTERVIEW AGENT - INITIALIZED")
print("FLOW: Name → Questions → Confidence → Store DB")
print("🎤" * 40 + "\n")

#Database
def get_db_path():
    return os.path.join(os.path.dirname(__file__), DB_FILE)

def get_conn():
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    return conn

def init_database():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS interview_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_name TEXT,
            answers TEXT,
            confidence_score INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()

init_database()

@dataclass
class InterviewData:
    candidate_name: Optional[str] = None
    answers: List[str] = None


@function_tool
async def set_candidate_name(
    ctx: RunContext[InterviewData],
    name: Annotated[str, Field(description="Candidate full name")]
) -> str:
    ctx.userdata.candidate_name = name
    ctx.userdata.answers = []
    return f"Thanks {name}. Let's begin your interview."

@function_tool
async def record_answer(
    ctx: RunContext[InterviewData],
    answer: Annotated[str, Field(description="Candidate answer")]
) -> str:
    ctx.userdata.answers.append(answer)
    return "Answer recorded."

@function_tool
async def finalize_interview(
    ctx: RunContext[InterviewData]
) -> str:
    """
    Computes confidence and stores interview in DB
    """

    answers = ctx.userdata.answers or []

    # Simple deterministic confidence logic
    total_words = sum(len(a.split()) for a in answers)

    if total_words < 40:
        confidence = 4
    elif total_words < 80:
        confidence = 6
    elif total_words < 120:
        confidence = 8
    else:
        confidence = 9

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO interview_results (candidate_name, answers, confidence_score)
        VALUES (?, ?, ?)
        """,
        (
            ctx.userdata.candidate_name,
            " | ".join(answers),
            confidence,
        ),
    )

    conn.commit()
    conn.close()

    return (
        f"Interview completed successfully.\n"
        f"Confidence Score: {confidence}/10\n"
        f"Thank you for interviewing with NovaTech Solutions."
    )

#Agent
class InterviewAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""
You are Alex, an AI interviewer at NovaTech Solutions.

STRICT FLOW (DO NOT SKIP):

1. Greet candidate.
2. Ask for full name → call set_candidate_name.
3. Introduce role: Java Software Engineer.
4. Ask exactly 3 EASY DSA questions in Java:
   - What is an array?
   - Difference between Array and ArrayList?
   - What is time complexity?
5. After each answer → call record_answer.
6. After 3 answers → call finalize_interview.
7. End politely.
""",
            tools=[
                set_candidate_name,
                record_answer,
                finalize_interview,
            ],
        )


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    userdata = InterviewData()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice="en-US-marcus",
            style="Conversational",
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        userdata=userdata,
    )

    await session.start(
        agent=InterviewAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )

    await ctx.connect()

# ------------------------------------------------------
# 🚀 RUN
# ------------------------------------------------------

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm
        )
    )

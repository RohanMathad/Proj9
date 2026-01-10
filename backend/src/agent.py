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

# --- NEW IMPORT ---
# This will look for the file we will create in Step 3. 
# Don't worry if you see an error about this missing right now.
try:
    from post_interview import process_last_interview
except ImportError:
    process_last_interview = None

logger = logging.getLogger("interview-agent")
load_dotenv(".env.local")

DB_FILE = "interview_db.sqlite"

print("\n" + "🎤" * 40)
print("AI INTERVIEW AGENT - INITIALIZED")
print("FLOW: Name → Email → Questions → Store DB → Trigger Email")
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

    # Added 'email' column here
    cur.execute("""
        CREATE TABLE IF NOT EXISTS interview_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_name TEXT,
            candidate_email TEXT,
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
    candidate_email: Optional[str] = None # Added field
    answers: List[str] = None


@function_tool
async def set_candidate_name(
    ctx: RunContext[InterviewData],
    name: Annotated[str, Field(description="Candidate full name")]
) -> str:
    ctx.userdata.candidate_name = name
    ctx.userdata.answers = []
    return f"Thanks {name}. Now, could you please state your email address for the results?"

# --- NEW TOOL ---
# ... inside backend/src/agent.py ...
@function_tool
async def set_candidate_email(
    ctx: RunContext[InterviewData],
    email: Annotated[str, Field(description="Candidate email address")]
) -> str:
    # --- BUG FIX ---
    # 1. Lowercase everything
    clean_email = email.lower()
    
    # 2. Only fix " at " if the user spoke it like "rohan at gmail"
    # We check if there is NO '@' symbol yet.
    if "@" not in clean_email:
        clean_email = clean_email.replace(" at ", "@").replace(" at", "@")
    
    # 3. Remove all remaining spaces (email shouldn't have spaces)
    clean_email = clean_email.replace(" ", "")
    
    # 4. Final Sanity Check: If they still typed "math", don't break it.
    # The previous code broke here because it blindly replaced "at".
    
    ctx.userdata.candidate_email = clean_email
    return f"Email recorded as {clean_email}. Let's begin the interview."

@function_tool
async def record_answer(
    ctx: RunContext[InterviewData],
    answer: Annotated[str, Field(description="Candidate answer")]
) -> str:
    if ctx.userdata.answers is None:
        ctx.userdata.answers = []
    ctx.userdata.answers.append(answer)
    return "Answer recorded."

@function_tool
async def finalize_interview(
    ctx: RunContext[InterviewData]
) -> str:
    """
    Stores interview in DB and triggers the Email Agent
    """
    answers = ctx.userdata.answers or []
    
    # We will let the external script handle the REAL calculation.
    # We just store a placeholder here.
    confidence_placeholder = 0 

    conn = get_conn()
    cur = conn.cursor()

    # Saving Name, Email, and Answers
    cur.execute(
        """
        INSERT INTO interview_results (candidate_name, candidate_email, answers, confidence_score)
        VALUES (?, ?, ?, ?)
        """,
        (
            ctx.userdata.candidate_name,
            ctx.userdata.candidate_email,
            " | ".join(answers),
            confidence_placeholder,
        ),
    )

    conn.commit()
    conn.close()

    # --- TRIGGER THE ANALYSIS ---
    if process_last_interview:
        print("🚀 Triggering Post-Interview Analysis...")
        # We run this quickly. In a big app, you'd use background tasks, 
        # but for this project, calling it directly is fine.
        try:
            process_last_interview()
        except Exception as e:
            print(f"Error sending email: {e}")
    else:
        print("⚠️ Post-interview script not found. Skipping email.")

    return (
        f"Interview completed. You will receive your detailed analysis via email shortly. "
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
3. (IMPORTANT) Ask for email address → call set_candidate_email.
4. Introduce role: Java Software Engineer.
5. Ask exactly 3 EASY DSA questions in Java:
   - What is an array?
   - Difference between Array and ArrayList?
   - What is time complexity?
6. After each answer → call record_answer.
7. After 3 answers → call finalize_interview.
8. End politely.
""",
            tools=[
                set_candidate_name,
                set_candidate_email, # Added tool
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

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm
        )
    )
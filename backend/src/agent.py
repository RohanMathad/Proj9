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

# Try to import the post-interview script
try:
    from post_interview import process_last_interview
except ImportError:
    process_last_interview = None

logger = logging.getLogger("interview-agent")
load_dotenv(".env.local")

DB_FILE = "interview_db.sqlite"

# --- 1. DEFINE THE PERSONALITIES (SIMPLIFIED QUESTIONS) ---
PROMPTS = {
    "GOOGLE": """
You are Alex, a Technical Interviewer at Google.
STRICT FLOW:
1. Greet the candidate warmly and mention this is a Google Interview.
2. Ask for Name -> call set_candidate_name.
3. Ask for Email -> call set_candidate_email.
4. Ask 2 SIMPLE Questions focusing on Basic Data Structures:
   - Question 1: "What is the difference between an Array and a Linked List?"
   - Question 2: "In simple terms, what is a Hash Map?"
5. Record answers.
6. Finalize interview.
""",
    "META": """
You are Alex, a Tech Lead at Meta (Facebook).
STRICT FLOW:
1. Greet the candidate and welcome them to Meta.
2. Ask for Name -> call set_candidate_name.
3. Ask for Email -> call set_candidate_email.
4. Ask 2 SIMPLE Questions focusing on Coding Basics:
   - Question 1: "How would you find the maximum number in a list of numbers?"
   - Question 2: "What is a 'For Loop' used for?"
5. Record answers.
6. Finalize interview.
""",
    "STARTUP": """
You are Alex, the CTO of a fast-paced AI Startup.
STRICT FLOW:
1. Greet the candidate energetically!
2. Ask for Name -> call set_candidate_name.
3. Ask for Email -> call set_candidate_email.
4. Ask 2 SIMPLE Questions about Core Java:
   - Question 1: "What is the difference between a Class and an Object?"
   - Question 2: "How do you print 'Hello World' in Java?"
5. Record answers.
6. Finalize interview.
"""
}

# --- DATABASE SETUP ---
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
            candidate_email TEXT,
            answers TEXT,
            confidence_score INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()

init_database()

# --- DATA MODELS ---
@dataclass
class InterviewData:
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    answers: List[str] = None

# --- TOOLS ---
@function_tool
async def set_candidate_name(ctx: RunContext[InterviewData], name: Annotated[str, Field(description="Candidate full name")]) -> str:
    ctx.userdata.candidate_name = name
    ctx.userdata.answers = []
    return f"Thanks {name}. Now, please state your email address."

@function_tool
async def set_candidate_email(ctx: RunContext[InterviewData], email: Annotated[str, Field(description="Candidate email address")]) -> str:
    clean_email = email.lower().replace(" at ", "@").replace(" at", "@").replace(" ", "")
    ctx.userdata.candidate_email = clean_email
    return f"Email recorded as {clean_email}. Let's begin the interview."

@function_tool
async def record_answer(ctx: RunContext[InterviewData], answer: Annotated[str, Field(description="Candidate answer")]) -> str:
    if ctx.userdata.answers is None:
        ctx.userdata.answers = []
    ctx.userdata.answers.append(answer)
    return "Answer recorded."

@function_tool
async def finalize_interview(ctx: RunContext[InterviewData]) -> str:
    answers = ctx.userdata.answers or []
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO interview_results (candidate_name, candidate_email, answers, confidence_score) VALUES (?, ?, ?, ?)",
        (ctx.userdata.candidate_name, ctx.userdata.candidate_email, " | ".join(answers), 0),
    )
    conn.commit()
    conn.close()

    if process_last_interview:
        print("🚀 Triggering Post-Interview Analysis...")
        try:
            process_last_interview()
        except Exception as e:
            print(f"Error sending email: {e}")
    
    return "Interview completed. You will receive your detailed analysis via email shortly."

# --- UPDATED AGENT CLASS ---
class InterviewAgent(Agent):
    def __init__(self, custom_instructions):
        # We pass the DYNAMIC instructions here
        super().__init__(
            instructions=custom_instructions,
            tools=[set_candidate_name, set_candidate_email, record_answer, finalize_interview],
        )

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    # 1. CONNECT FIRST so we can see who joined
    await ctx.connect()

    # 2. WAIT FOR USER to get their name/identity
    print("⏳ Waiting for participant to join...")
    participant = await ctx.wait_for_participant()
    
    # 3. DECODE THE TROJAN HORSE
    # The frontend sends: "Candidate__GOOGLE"
    full_identity = participant.identity or "User__STARTUP"
    print(f"🕵️ Raw Identity Received: {full_identity}")

    company_mode = "STARTUP" # Default
    if "__" in full_identity:
        parts = full_identity.split("__")
        if len(parts) > 1:
            company_mode = parts[1] # "GOOGLE" or "META"

    print(f"✅ ACTIVATING MODE: {company_mode}")

    # 4. SELECT THE MATCHING PROMPT
    selected_prompt = PROMPTS.get(company_mode, PROMPTS["STARTUP"])

    # 5. START THE AGENT WITH THAT PROMPT
    userdata = InterviewData()
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(voice="en-US-marcus", style="Conversational"),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        userdata=userdata,
    )

    # Pass the selected prompt to the Agent Class
    await session.start(
        agent=InterviewAgent(custom_instructions=selected_prompt),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm
        )
    )
import sqlite3
import os
import resend
import google.generativeai as genai
from textblob import TextBlob
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv(".env.local")

resend.api_key = os.getenv("RESEND_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

DB_FILE = "interview_db.sqlite"

IDEAL_KEYWORDS = [
    "array", "memory", "contiguous", "index", "list", "dynamic", "resize", 
    "complexity", "time", "space", "big o", "notation", "linear", "constant",
    "java", "class", "object", "system"
]

def get_db_path():
    return os.path.join(os.path.dirname(__file__), DB_FILE)

# --- VISUAL HELPERS ---
def get_color(score):
    if score >= 75: return "#16a34a" # Green
    if score >= 50: return "#ca8a04" # Yellow/Gold
    return "#dc2626" # Red

def get_status_badge(score):
    if score >= 75:
        return f'<span style="background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 99px; font-weight: bold; font-size: 12px;">HIRED RECOMMENDED</span>'
    if score >= 50:
        return f'<span style="background: #fef9c3; color: #854d0e; padding: 4px 12px; border-radius: 99px; font-weight: bold; font-size: 12px;">UNDER REVIEW</span>'
    return f'<span style="background: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 99px; font-weight: bold; font-size: 12px;">NEEDS IMPROVEMENT</span>'

def draw_bar(score):
    color = get_color(score)
    return f"""
    <div style="background: #e5e7eb; border-radius: 4px; height: 10px; width: 100%; margin-top: 5px;">
        <div style="background: {color}; width: {score}%; height: 10px; border-radius: 4px;"></div>
    </div>
    """

def calculate_scores(response_text):
    blob = TextBlob(response_text)
    confidence_score = int((blob.sentiment.polarity + 1) * 50)
    
    ideal_text = " ".join(IDEAL_KEYWORDS)
    vectorizer = CountVectorizer(stop_words='english')
    
    try:
        tfidf_matrix = vectorizer.fit_transform([ideal_text, response_text])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        knowledge_score = int(similarity[0][0] * 100)
        knowledge_score = min(knowledge_score * 3, 98) 
    except:
        knowledge_score = 15

    return confidence_score, knowledge_score

def generate_ai_feedback(name, answers, score_k, score_c):
    print("   [AI] Asking Gemini to write the detailed report...")
    # Using 2.5 Flash as determined by your check_models.py
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    You are a Senior Tech Lead. Write a short, constructive feedback report (HTML) for {name}.
    Scores: Knowledge {score_k}/100, Confidence {score_c}/100.
    Answers: "{answers}"
    
    Structure:
    <h3>🚀 Executive Summary</h3>
    <p>2 sentences summary.</p>
    <h3>💡 Key Strengths</h3>
    <ul><li>Bullet point 1</li><li>Bullet point 2</li></ul>
    <h3>🔧 Areas to Improve</h3>
    <p>Constructive feedback.</p>
    
    Keep it strictly HTML content (no <html> tags).
    """
    
    response = model.generate_content(prompt)
    return response.text

def process_last_interview():
    print("🔄 Connecting to Database...")
    
    if not resend.api_key:
        print("❌ ERROR: RESEND_API_KEY missing.")
        return

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT id, candidate_name, candidate_email, answers FROM interview_results ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("❌ No data.")
        return

    user_id, name, email, answers = row
    if not email: return

    print(f"✅ Found: {name}. Calculating Visuals...")
    
    # 1. Math
    conf, know = calculate_scores(answers)
    avg_score = int((conf + know) / 2)
    
    # 2. AI Text
    try:
        ai_feedback = generate_ai_feedback(name, answers, know, conf)
        ai_feedback = ai_feedback.replace("```html", "").replace("```", "")
    except:
        ai_feedback = "<p>AI Analysis unavailable.</p>"

    # 3. Dynamic Subject Line
    subject_emoji = "🌟" if avg_score > 75 else "📊"
    subject_text = f"{subject_emoji} Interview Result: {name} (Score: {avg_score}%)"

    print(f"📧 Sending Visual Dashboard to {email}...")

    # 4. The "Dashboard" HTML
    final_email = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; color: #1f2937;">
        
        <div style="text-align: center; padding: 20px 0; border-bottom: 1px solid #e5e7eb;">
            <h2 style="color: #111827; margin:0;">Interview Assessment Report</h2>
        </div>

        <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <strong>Overall Performance</strong>
                {get_status_badge(avg_score)}
            </div>
            
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; font-size: 14px;">
                    <span>Technical Knowledge</span>
                    <span style="font-weight: bold; color: {get_color(know)};">{know}%</span>
                </div>
                {draw_bar(know)}
            </div>

            <div>
                <div style="display: flex; justify-content: space-between; font-size: 14px;">
                    <span>Communication Confidence</span>
                    <span style="font-weight: bold; color: {get_color(conf)};">{conf}%</span>
                </div>
                {draw_bar(conf)}
            </div>
        </div>

        <div style="line-height: 1.6; color: #374151;">
            {ai_feedback}
        </div>

        <div style="text-align: center; font-size: 12px; color: #9ca3af; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
            Automated Report System • NovaTech Solutions
        </div>
    </div>
    """

    params = {
        "from": "onboarding@resend.dev",
        "to": [email],
        "subject": subject_text,
        "html": final_email,
    }

    try:
        resend.Emails.send(params)
        print("🚀 Visual Dashboard Email sent!")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    process_last_interview()
import os
import random
import re
from datetime import datetime
from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from . import _history

NAME = "interview-qa"

# Runs every day (no SCHEDULE attribute = daily).

MODEL = os.getenv("OLLAMA_MODEL", "phi4-mini:latest")

# ---------------------------------------------------------------------------
# Candidate profile — built from Metta Surendhar's resume + personal
# interview-prep notes (STAR stories, past interview questions, self-identified
# gaps). Edit this as experience grows or new interviews add new material.
# ---------------------------------------------------------------------------

CANDIDATE_PROFILE = (
    "Final-year Integrated M.Sc. IT student (CEG, Anna University), targeting SDE, "
    "full-stack, and AI/GenAI engineer roles. Two internships at Invisibl Cloud Solutions "
    "(Platform Engineering Intern). Strong in Python, TypeScript, FastAPI, Node.js/Express, "
    "React/Vite/Tailwind/Zustand/TanStack, PostgreSQL/Prisma, RAG/LLM integration "
    "(Haystack, OpenSearch, Claude, Gemini, AWS Bedrock), and observability "
    "(Prometheus, Grafana, Loki, Cribl). Weaker/less experienced areas: TensorFlow/"
    "PyTorch/Scikit-learn, Docker/Kubernetes, MLOps tools (MLflow), Spark/big data, "
    "and automated unit/integration testing (has systematic QA experience but not much "
    "test-suite writing). Also historically underprepared on sliding-window DSA problems "
    "and has said past 'tell me about yourself' answers felt weak/nervous."
)

# Real STAR-format project anchors pulled directly from the candidate's own notes.
# The model should ground technical + behavioral answers in these specifics rather
# than inventing generic detail — but ONLY when the focus area actually calls for it.
PROJECT_ANCHORS = """
1. GenAI Research Agent (Invisibl internship, 2nd half):
   - Problem: help researchers find and get summarized answers from research papers.
   - v1: Haystack, Streamlit, AWS Bedrock Knowledge Base, Gemini Flash.
   - Refactored to production based on client feedback: modular FastAPI REST API,
     OpenSearch for RAG retrieval (replacing Bedrock KB), Claude for LLM output
     (chosen over Gemini for better answer quality).
   - Improved response quality via prompt engineering + retrieval context optimization.
   - Also QA-tested a RAG search platform across 3 query modes (direct, tag-filtered,
     file-selected), evaluating answer accuracy/source relevance by query and file type.

2. Observability Infrastructure (Invisibl internship, 1st half):
   - Problem: no existing infra for monitoring Windows/Linux system LOGS (metrics infra
     already existed).
   - Built from scratch: Cribl, Prometheus, Grafana, Loki, rsyslog.
   - Designed dashboards, alerting rules, log parsing pipelines.
   - Took ~1 week to understand existing metrics setup before starting.

3. CAD Assistant PoC (Invisibl internship, later work):
   - Problem: manufacturing client needed a way to visually inspect + conversationally
     query engineering data from STEP files.
   - Built interactive 3D viewer (renders STEP files) + LLM agent for natural-language
     querying of engineering data.
   - Integration challenge: connecting the 3D viewer's state (selected parts, current
     view) with the LLM agent's context so answers were grounded in what the user was
     looking at.
   - Result: demo convinced the client to move forward with the product.

4. FinOps Cloud Cost Platform (Invisibl internship, later work):
   - Sole frontend engineer; owned stack selection: React 19, Vite, TypeScript, Tailwind,
     Zustand, TanStack Query/Table, Apexcharts.
   - Delivered multi-filter dashboards, data tables, admin workflows from scratch.
   - Bug story: browser couldn't call backend APIs sitting behind Cloud Run with IAM
     protection — CORS alone wasn't enough since requests needed auth headers browsers
     don't handle well cross-origin. Debugged via browser network tab tracing. Fixed by
     adding an nginx reverse proxy inside the Docker setup so the browser talks to the
     proxy on the same origin, and the proxy handles IAM-authenticated calls server-side.
   - Lesson before this project: on the earlier AWS Connect Unified Portal project, the
     codebase (built with heavy AI-coding-agent assistance, no architectural guardrails)
     became inconsistent and hard to follow. For FinOps, defined coding standards,
     conventions, and architecture upfront before writing features — result was a much
     more maintainable codebase. Lesson: AI coding tools are only as good as the
     constraints given to them.

5. AWS Connect Unified Portal (Invisibl internship, earlier work):
   - Built region-aware frontend modules for a multi-region AWS Connect portal,
     integrating region-specific Lambda APIs with dynamic UI adapting data/layout
     across business units.

6. Alumni Student Platform (team project, led 5 members):
   - Problem: alumni-student mentoring/networking mobile app.
   - Owned full backend: defined requirements, UML models, secure REST APIs using
     Node.js, Express.js, PostgreSQL, Prisma ORM, JWT auth, SMTP email verification.
   - Design challenge: modeling role-based access (alumni vs students need different
     permissions/visibility) — solved via roles + relationship tables rather than
     hardcoding permission checks per endpoint, so adding a new role later wouldn't mean
     rewriting every query.

7. Gen Write-Up Agent (personal project):
   - Problem: generic LLM outputs (ChatGPT/Gemini) didn't match expected tone for
     LinkedIn/Twitter posts.
   - Built with Haystack, Gemini Flash, Streamlit, in-memory RAG using category-specific
     prompts and post history.
   - Added history feature (view/add past posts by category) to keep style consistent.
   - Deployed on Streamlit Cloud with basic auth.
   - Self-identified improvement: would swap in-memory RAG for a proper vector store to
     scale past a handful of posts, and add a feedback loop from edits back into future
     generations.

8. Hackz'24 Hackathon (finalist, led team of 4):
   - Cleared ideathon round (from 500-1000+ teams) with a PoC, pitch deck, demo video for
     "INFINSA BOT" — multilingual AI chatbot for fintech customer engagement.
   - Finals (24hr onsite): built Infinsa, an AI-powered fintech app for elderly users —
     voice-based queries, AI assistant, scam awareness, easy UI for seniors — using
     FastAPI, Gemini Flash, Firebase.
   - Result: finalist, only team from CEG to reach finals.

9. Smart India Hackathon (SIH): 1 of 10 teams selected (from 500+) at college level;
   led 5-member team through requirements, architecture, PoC & pitch deck for
   "Conversational Image Recognition Chatbot" (PoW).

10. Leadership roles:
    - General Secretary, Student Association (SAAS), CEG — represented 4,000+ students,
      co-led Techofes and Utopia fests, supervised 2 digital platform rollouts,
      felicitated by the Dean.
    - Student Director of Industrial Relations, Math Colloquium — secured 20+
      sponsorships from 100+ companies contacted, co-organized a GenAI/RAG bootcamp with
      Google for Developers & Azure Developer Community TN.
    - Placement Representative, CUIC CEG — coordinating placement activities/industry
      connections for the graduating batch.
"""

# Actual questions the candidate has been asked in real interviews/screenings —
# occasionally resurface these verbatim so practice matches reality.
REAL_PAST_QUESTIONS = [
    "How is the Gen Write-Up Agent better than ChatGPT?",
    "Why OpenSearch over PostgreSQL for the research agent's retrieval layer?",
    "What are the full-stack tools/techs used in the Alumni Student Platform?",
    "What's the thing you're most proud of building?",
    "Tell me about yourself and your work experience.",
    "Explain GAN architecture, and: the generator keeps outputting the same image "
    "regardless of the input noise — what's going wrong and how would you debug it?",
    "How would you improve the CAD Assistant / Research Agent product further?",
    "Walk me through how your application works end-to-end — if a user does some UI "
    "action, how does the flow go back and forth to the backend and back?",
    "Do you have production experience building AI? Elaborate.",
    "Tell us about a time you received feedback on your code in a code review.",
    "Tell us about your experience with testing — unit/integration tests, practices.",
]

# Generic, real, industry-standard interview questions — deliberately NOT tied to
# this candidate's specific projects. Real interviews often ask these regardless of
# your resume, so practicing them cold (answered on general knowledge/reasoning,
# not forced into a project story) matters just as much as the tailored ones.
GENERIC_INDUSTRY_QUESTIONS = [
    "What is the difference between a process and a thread?",
    "Explain the CAP theorem and give an example of a system that favors "
    "availability over consistency.",
    "How would you design a URL shortener like bit.ly?",
    "What's the difference between TCP and UDP, and when would you choose one "
    "over the other?",
    "Explain how a hash table works and how collisions are handled.",
    "What is normalization in databases, and can you give an example of "
    "denormalizing for performance?",
    "What happens when you type a URL into a browser and hit enter?",
    "Explain the difference between optimistic and pessimistic locking.",
    "What is idempotency, and why does it matter for API design?",
    "How would you design a rate limiter for a public API?",
    "Explain the difference between horizontal and vertical scaling.",
    "What is a race condition, and how would you prevent one?",
    "Explain how garbage collection generally works in a managed-memory language.",
    "What's the difference between SQL and NoSQL databases, and when would you "
    "pick one over the other?",
    "How does HTTPS/TLS establish a secure connection?",
    "What is eventual consistency, and where is it an acceptable tradeoff?",
    "Describe how you'd design a notification system that scales to millions of users.",
    "What's the difference between authentication and authorization?",
    "Explain the producer-consumer problem and one way to solve it.",
    "Tell me about a time you disagreed with a decision made by your manager or "
    "team lead. How did you handle it?",
    "Describe a situation where you had to learn a completely new technology under "
    "a tight deadline, with no prior exposure to it.",
    "How do you handle being given vague or incomplete requirements?",
    "Tell me about a time a project you worked on failed or fell short. What happened?",
    "Where do you see yourself in five years?",
]

# Rotate which area of the stack gets the technical question each day.
FOCUS_AREAS = [
    "Backend & APIs (FastAPI / Node.js / Express.js)",
    "Databases (PostgreSQL, ORM design, query performance)",
    "Frontend (React, state management, performance)",
    "LLM/RAG systems (retrieval, embeddings, prompt design, evaluation)",
    "System Design (scaling a service, caching, observability)",
    "DSA weak spot: sliding window & two pointers",
    "Behavioral / project deep-dive using real STAR anchors",
    "ML fundamentals gap-filling (Docker/K8s, MLOps, TensorFlow/PyTorch basics)",
    "Revisit a real past interview question",
    "Generic real interview question (industry-standard, no project tie-in required)",
]


def pick_focus():
    day_of_year = datetime.now().timetuple().tm_yday
    return FOCUS_AREAS[day_of_year % len(FOCUS_AREAS)]


def extract_questions(text):
    """Pull out the technical + behavioral question lines for history logging."""
    tech_match = re.search(r"## Technical Question.*?\n(.+)", text)
    behav_match = re.search(r"## Behavioral Question\s*\n(.+)", text)
    tech = tech_match.group(1).strip() if tech_match else "(unparsed technical question)"
    behav = behav_match.group(1).strip() if behav_match else "(unparsed behavioral question)"
    return tech, behav


def run():
    focus = pick_focus()
    is_generic = focus == "Generic real interview question (industry-standard, no project tie-in required)"
    is_revisit = focus == "Revisit a real past interview question"

    revisit_question = random.choice(REAL_PAST_QUESTIONS) if is_revisit else None
    generic_question = random.choice(GENERIC_INDUSTRY_QUESTIONS) if is_generic else None

    # Look back at questions already generated for this same focus area so the
    # model doesn't ask a near-duplicate again.
    past_entries = _history.load_recent(NAME, limit=20)
    same_focus_questions = [
        e["summary"] for e in past_entries if e.get("topic") == focus
    ]

    if is_generic:
        # Generic mode: answer using general engineering knowledge/reasoning.
        # Do NOT force a connection to a specific project — real interviewers ask
        # these regardless of your resume, so practice answering them cold.
        system_prompt = (
            "You are an interview coach. You will be given a real, generic, "
            "industry-standard interview question that is NOT tied to any specific "
            "project. Answer it the way a strong candidate would: using general "
            "engineering/CS knowledge and clear reasoning. Do NOT force a connection "
            "to a personal project or resume detail — only mention a project if it "
            "would genuinely and naturally come up, and even then keep it brief. "
            "Produce Markdown with this structure:\n\n"
            "## Technical Question (Generic — no project tie-in required)\n"
            "(repeat the exact question given to you)\n\n"
            "### How to Approach It\n(3-4 bullet points on how to structure a strong "
            "answer using general knowledge/reasoning, not personal project references)\n\n"
            "### Sample Answer\n(a full, well-explained model answer based on solid "
            "engineering fundamentals — this is what a strong candidate would say even "
            "with no relevant project experience to lean on)\n\n"
            "## Behavioral Question\n(repeat the exact behavioral question given to you)\n\n"
            "### How to Approach It\n(1-2 bullet points on structuring the answer with "
            "STAR, using whatever real experience fits best — general life/work/college "
            "experience is fine here, it doesn't need to map to a named project)\n\n"
            "### Sample Answer\n(a full sample answer)\n\n"
            "Try answering both questions yourself first — the Sample Answer sections "
            "are there so you can compare and self-check afterward."
        )
        user_content = (
            f"Candidate background (for behavioral question context only — do NOT force "
            f"the technical question to connect to a project): {CANDIDATE_PROFILE}\n\n"
            f"Technical question to use (repeat exactly): {generic_question}\n\n"
            f"Behavioral question to use (repeat exactly): "
            f"{random.choice(GENERIC_INDUSTRY_QUESTIONS)}"
        )
    else:
        system_prompt = (
            "You are an interview coach preparing a candidate for SDE/full-stack/AI "
            "engineer interviews. You'll be given the candidate's background, a list of "
            "real STAR-format project anchors from their own notes, and today's focus area. "
            "Ground every answer in the SPECIFIC project details given — do not invent "
            "generic details when a real anchor already covers it. If given a list of "
            "questions already asked for this focus area, you MUST ask something genuinely "
            "different, not a reworded duplicate. Produce Markdown with "
            "this structure:\n\n"
            "## Technical Question ({focus})\n(one realistic interview question matched to "
            "the candidate's real experience. If a 'past question to revisit' is given, use "
            "that exact question instead of writing a new one.)\n\n"
            "### How to Approach It\n(3-4 bullet points on how to structure a strong answer, "
            "referencing the specific project anchor(s) that fit)\n\n"
            "### Sample Answer\n(a full, well-explained model answer, written as the "
            "candidate might say it, using specific details from the matching project "
            "anchor — not generic filler)\n\n"
            "## Behavioral Question\n(one behavioral/HR-style question)\n\n"
            "### STAR Approach Tip\n(1-2 bullet points on how to frame it using Situation-"
            "Task-Action-Result, tied to a specific real project anchor)\n\n"
            "### Sample Answer (STAR format)\n(a full sample answer in STAR format, using "
            "the matching project anchor's real specifics)\n\n"
            "Try answering both questions yourself first — the Sample Answer sections are "
            "there so you can compare and self-check afterward."
        ).replace("{focus}", focus)

        user_content = (
            f"Candidate background: {CANDIDATE_PROFILE}\n\n"
            f"Real STAR project anchors (use these specifics, don't invent generic ones):\n"
            f"{PROJECT_ANCHORS}\n\n"
            f"Today's focus area: {focus}"
        )
        if revisit_question:
            user_content += f"\n\nPast question to revisit (use this exact question): {revisit_question}"
        if same_focus_questions and not revisit_question:
            already_covered = "\n".join(f"- {q}" for q in same_focus_questions)
            user_content += (
                f"\n\nTechnical questions already asked for this focus area (pick something "
                f"different):\n{already_covered}"
            )

    agent = create_agent(
        model=ChatOllama(model=MODEL, temperature=0.5, num_ctx=4096),
        tools=[],
        system_prompt=system_prompt,
    )

    result = agent.invoke({
        "messages": [{"role": "user", "content": user_content}]
    })

    content = result["messages"][-1].content

    tech_q, _ = extract_questions(content)
    _history.append(NAME, {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "topic": focus,
        "summary": tech_q,
    })

    return (
        f"# Daily Interview Prep — Focus: {focus}\n\n"
        f"{content}\n"
    )

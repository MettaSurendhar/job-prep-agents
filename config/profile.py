"""
This is Metta Surendhar's real profile — used directly by the interview_qa
and job_digest agents. Update this as new projects/experience come in.
"""

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

JOB_SEARCH_QUERIES = [
    "fresher software engineer jobs India 2026",
    "entry level full stack developer jobs India React Node",
    "fresher AI engineer RAG LLM jobs India",
]
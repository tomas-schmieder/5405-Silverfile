# SilverFile

Draft 2025 tax-return preparation with human review. Fictional data only; nothing is filed and no tax advice is provided.

## Local setup
Use Python 3.12 and a virtual environment. Install `requirements.txt`. Copy `.env.example` to `.env`, enter your Anthropic key and a vision/structured-output model available to your account. Never commit `.env`.

    python -m streamlit run streamlit_app.py

Open http://localhost:8501. Alternatively use `docker compose up --build` after configuring `.env`. Docker is supplied but not yet verified in this handoff. Native OCR is disabled pending isolated validation.

## Verification and status
See docs/PERSON5_HANDOFF.md and docs/PERSON6_HANDOFF.md. The core suite passed 299 tests during packaging; live-model, browser, full image-driven evaluations, and Docker acceptance are pending. Run the documented checks before submission.

## Attribution
The original code was generated with Claude. ChatGPT/Codex prepared staged adaptations and tests. Each team member must record their actual review, testing and modifications. Report, recording, token experiment and the assignment specialization table remain team deliverables.

"""Taxpayer intake view.

Accessibility choices (assignment §4.3, docs/IMPLEMENTATION_NOTES.md):
* one question at a time in a large, high-contrast card; option buttons are
  real buttons (keyboard reachable) with plain labels;
* a short explanation under unavoidable terms;
* "I'm not sure", "Go back" and "Talk to a person" are always one click away;
* everything is saved after each answer; a case can be resumed by its number,
  with a summary of what was already covered;
* status is always written in words, never shown by colour alone.
"""

from __future__ import annotations

import streamlit as st

from src.service import DOC_TYPES, ServiceError
from src.ui.components import badge, get_service, html, md, money
from src.ui.provenance_view import render_draft
from src.ui_text import WELCOME_TEXT, SUBMITTED_TEXT, PENDING_REVIEW_TEXT, REFERRAL_TEXT
from src.ui.upload_helpers import guess_form as _guess_form


def _send(svc, case_id: str, text: str, uploads: list | None = None) -> None:
    try:
        with st.spinner("Saving your answer..."):
            svc.send_message(case_id, text, uploads)
        st.session_state.pop("sf_uploads", None)
        if uploads:  # clear the file picker so sent files are not offered again
            st.session_state["sf_upload_round"] = st.session_state.get("sf_upload_round", 0) + 1
    except ServiceError as exc:
        st.session_state["sf_flash"] = str(exc)
    st.rerun()


def _start_or_resume(svc) -> str | None:
    st.title("SilverFile")
    st.markdown("#### Help preparing a **draft** 2025 Form 1040-SR")
    st.markdown(WELCOME_TEXT)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Start a new return")
        if st.button("Start", type="primary", use_container_width=True):
            with st.spinner("Opening a new case..."):
                case_id = svc.create_case()
            st.session_state["sf_case"] = case_id
            st.session_state["sf_resumed"] = False
            st.rerun()
    with c2:
        st.markdown("##### Continue a saved return")
        code = st.text_input("Your case number", placeholder="SF-20261024-ABC123", key="sf_resume_code")
        if st.button("Continue", use_container_width=True):
            try:
                svc.view(code.strip())
                st.session_state["sf_case"] = code.strip()
                st.session_state["sf_resumed"] = True
                st.rerun()
            except ServiceError:
                st.error("I couldn't find that case number. Please check it and try again.")
    return None




def _attach(svc, case_id: str, pending: list) -> list:
    """Store the chosen files and return everything ready to send with the next message."""
    staged = st.session_state.setdefault("sf_uploads", [])
    for f, doc_type in pending:
        try:
            staged.append(svc.add_upload(case_id, f.name, f.getvalue(), doc_type))
        except ServiceError as exc:
            st.session_state["sf_flash"] = f"'{f.name}': {exc}"
            st.rerun()
    return list(staged)


def _uploads_panel(svc, case_id: str, step: dict) -> list:
    """Shows the form picker; returns the chosen files (with their form types) not yet stored."""
    missing = step.get("missing") or {}
    st.markdown("##### Add your forms")
    round_no = st.session_state.get("sf_upload_round", 0)
    files = st.file_uploader("Photo or scan of each form (PNG, JPEG or PDF)", type=["png", "jpg", "jpeg", "pdf", "gif",
                                                                                     "webp"],
                             accept_multiple_files=True, key=f"up_{case_id}_{step.get('question_id')}_{round_no}")
    staged = st.session_state.setdefault("sf_uploads", [])
    still = [t for t, n in missing.items() for _ in range(n)]
    for s_doc in staged:
        if s_doc["doc_type"] in still:
            still.remove(s_doc["doc_type"])
    pending = []
    for f in files or []:
        if any(s["file_name"] == f.name for s in staged):
            continue
        default = _guess_form(f.name) or (still[0] if still else "W-2")
        if default in still:
            still.remove(default)
        dt = st.selectbox(f"What form is '{f.name}'?", DOC_TYPES, index=DOC_TYPES.index(default),
                          key=f"type_{round_no}_{f.name}")
        pending.append((f, dt))
    with st.expander("Type in a form instead (not for W-2s)"):
        dt = st.selectbox("Form", [d for d in DOC_TYPES if d != "W-2"], key="man_type")
        payer = st.text_input("Payer name (for example, the bank)", key="man_payer")
        boxes = {"1099-INT": ["1", "3", "4", "8"], "1099-DIV": ["1a", "1b", "2a", "4", "12"],
                 "1099-R": ["1", "2a", "4"], "SSA-1099": ["3", "4", "5", "6"]}[dt]
        vals = {b: st.text_input(f"Box {b}", key=f"man_{dt}_{b}") for b in boxes}
        checks, code = [], None
        if dt == "1099-R":
            code = st.text_input("Box 7 distribution code", key="man_code")
            if st.checkbox("The IRA/SEP/SIMPLE box is checked", key="man_ira"):
                checks.append("IRA/SEP/SIMPLE")
            if st.checkbox("Box 2b 'Taxable amount not determined' is checked", key="man_2b"):
                checks.append("Taxable amount not determined")
        if st.button("Add this typed form", key="man_add"):
            try:
                staged.append(svc.add_manual_document(case_id, dt, vals, payer=payer, checkboxes=checks, code=code))
                st.rerun()
            except ServiceError as exc:
                st.error(str(exc))
    ready = [(s["doc_type"], s["file_name"]) for s in staged] + [(dt, f.name) for f, dt in pending]
    if ready:
        st.markdown(md("Ready to send: " + ", ".join(f"**{dt}** ({name})" for dt, name in ready)))
        if st.button(f"Send these forms ({len(ready)})", type="primary"):
            _send(svc, case_id, "done", _attach(svc, case_id, pending))
    return pending


def render() -> None:
    svc = get_service()
    case_id = st.session_state.get("sf_case")
    if not case_id:
        _start_or_resume(svc)
        return
    try:
        view = svc.view(case_id)
    except ServiceError:
        st.session_state.pop("sf_case", None)
        st.rerun()
        return
    top = st.columns([3, 1], vertical_alignment="center")
    top[0].markdown(f"### Your return &nbsp; {badge(view['status'])}", unsafe_allow_html=True)
    top[0].caption(f"Case number **{case_id}** - write this down to come back later. Your answers are saved as you go.")
    if top[1].button("Save and leave", use_container_width=True):
        st.session_state.pop("sf_case", None)
        st.rerun()
    flash = st.session_state.pop("sf_flash", None)
    if flash:
        st.error(md(f"{flash} Please try again, or ask for a person."))
    if view.get("error"):
        st.error("SilverFile hit a problem and has paused safely. A Kushim volunteer can see this case.")
        if st.button("Try again"):
            try:
                svc.retry(case_id)
            except ServiceError:
                pass
            st.rerun()
    if st.session_state.get("sf_resumed") and view["resume_summary"]:
        with st.container(border=True):
            st.markdown("**Welcome back.** Here is what we already covered:")
            st.markdown("\n".join(f"- {md(line)}" for line in view["resume_summary"][:30]))
        st.session_state["sf_resumed"] = False

    st.markdown('<div class="sf-large">', unsafe_allow_html=True)
    if not view["transcript"]:
        with st.chat_message("assistant"):
            st.markdown("Hello, I'm SilverFile. I'll ask you one question at a time and prepare a draft tax return "
                        "for a Kushim volunteer to check with you. I can't file anything or give tax advice. You can "
                        "say \"I'm not sure\" or ask for a person at any time.")
    for msg in view["transcript"][-14:]:
        with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
            st.markdown(md(msg["text"]))
    st.markdown("</div>", unsafe_allow_html=True)

    pend = view["pending"]
    if view["status"] == "submitted_for_internal_review":
        st.success(SUBMITTED_TEXT)
        _taxpayer_draft(view)
        return
    if view["status"] == "referred_out_of_scope":
        st.info(REFERRAL_TEXT)
        return
    if pend and pend["kind"] == "human_review":
        st.info(PENDING_REVIEW_TEXT)
        return
    if not pend:
        return
    step = pend["step"]
    prog = pend.get("progress") or {}
    if prog.get("total"):
        st.progress(min(1.0, prog["answered"] / max(prog["total"], 1)),
                    text=f"About {prog['answered']} of {prog['total']} questions answered")
    gloss = f'<div class="sf-gloss">What this means: {html(step["gloss"])}</div>' if step.get("gloss") else ""
    hint = f'<div class="sf-hint">{html(pend["hint"])}</div>' if pend.get("hint") else ""
    st.markdown(f'<div class="sf-question" role="group" aria-label="Current question">'
                f'<div class="sf-section">{html(step.get("section", ""))}</div>'
                f'<div class="sf-q">{html(step["text"])}</div>{gloss}{hint}</div>', unsafe_allow_html=True)
    pending_files = []
    if step["kind"] == "upload":
        pending_files = _uploads_panel(svc, case_id, step)
    options = step.get("options") or []
    if step["kind"] == "yes_no":
        options = [{"value": "yes", "label": "Yes"}, {"value": "no", "label": "No"}]
    if options:
        cols = st.columns(min(len(options), 3))
        for i, opt in enumerate(options):
            if cols[i % len(cols)].button(opt["label"], key=f"opt_{step['question_id']}_{i}", use_container_width=True):
                _send(svc, case_id, opt["label"] if step["kind"] == "choice" else opt["value"])
    helpers = st.columns(3)
    has_unsure = any("not sure" in o["label"].lower() for o in options)
    if not has_unsure and helpers[0].button("I'm not sure", key=f"unsure_{step['question_id']}",
                                            use_container_width=True):
        _send(svc, case_id, "I'm not sure")
    if helpers[1].button("Go back one question", key=f"back_{step['question_id']}", use_container_width=True):
        _send(svc, case_id, "go back")
    if helpers[2].button("Talk to a person", key=f"help_{step['question_id']}", use_container_width=True):
        _send(svc, case_id, "I want to talk to a person")
    if step.get("question_id") == "submit_draft":
        _taxpayer_draft(view)
    placeholder = "Type your answer here and press Enter"
    if step.get("sensitive"):
        placeholder = "Enter a fictional SSN beginning with 900-999"
    text = st.chat_input(placeholder, key=f"chat_{case_id}")
    if text:
        # typing "done" at the forms step sends the chosen files too
        _send(svc, case_id, text, _attach(svc, case_id, pending_files) if step["kind"] == "upload" else None)


def _taxpayer_draft(view: dict) -> None:
    lines = view["lines"]
    if not lines:
        return
    with st.container(border=True):
        st.markdown("**Your draft at a glance** (not filed)")
        c = st.columns(4)
        c[0].metric("Total income", money(lines.get("9", {}).get("value")))
        c[1].metric("Taxable income", money(lines.get("15", {}).get("value")))
        c[2].metric("Total tax", money(lines.get("24", {}).get("value")))
        refund = int(lines.get("34", {}).get("value") or 0)
        owed = int(lines.get("37", {}).get("value") or 0)
        c[3].metric("Refund" if refund else "Amount owed", money(refund or owed))
        with st.expander("See the full draft and where each number came from"):
            render_draft(view, key_prefix="tp_")

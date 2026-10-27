"""Product wording and actual LangGraph pause/resume, without the full app."""
import pytest
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from src.state import CaseState, new_case_state
from src.agents.intake import intake_node
from src.agents.intake_script import QUESTIONS, Invalid, v_ssn
from src.agents.human_review import human_review_node
from src.hitl import make_escalation
from src.ui_text import WELCOME_TEXT, SUBMITTED_TEXT, PENDING_REVIEW_TEXT

def one_node_graph(node, runtime):
    builder = StateGraph(CaseState)
    builder.add_node("test_node", lambda state: node(state, runtime))
    builder.add_edge(START, "test_node")
    builder.add_edge("test_node", END)
    return builder.compile(checkpointer=InMemorySaver())

def test_ssn_copy_remains_explicit_without_classroom_language():
    question = next(q for q in QUESTIONS if q.id == "tp_ssn")
    assert "classroom" not in question.text.lower()
    assert "fictional" in question.text.lower() and "900-999" in question.text
    with pytest.raises(Invalid) as err:
        v_ssn("123-45-6789")
    assert "classroom" not in str(err.value).lower()
    assert "900-999" in str(err.value)

def test_user_status_copy_does_not_promise_contact_or_active_review():
    assert "fictional" in WELCOME_TEXT.lower()
    assert "contact you" not in SUBMITTED_TEXT.lower()
    assert "waiting" in PENDING_REVIEW_TEXT.lower()
    assert "looking at your case" not in PENDING_REVIEW_TEXT.lower()

def test_intake_actually_interrupts_and_resumes(runtime):
    graph = one_node_graph(intake_node, runtime)
    config = {"configurable": {"thread_id": "intake-thread"}}
    initial = new_case_state("I", runtime.now(), 2025, 1)
    paused = graph.invoke(initial, config)
    assert paused["__interrupt__"][0].value["step"]["question_id"] == "tp_first_name"
    resumed = graph.invoke(Command(resume={"kind":"taxpayer_message", "text":"Eleanor", "uploads":[]}),config)
    assert resumed["facts"]["tp.first_name"]["value"] == "Eleanor"
    assert not graph.get_state(config).next

def test_human_review_actually_interrupts_and_records_resolution(runtime):
    graph = one_node_graph(human_review_node, runtime)
    config = {"configurable": {"thread_id": "review-thread"}}
    initial = new_case_state("R", runtime.now(), 2025, 1)
    initial["escalation"] = make_escalation("advice_request", "Advice requested", raised_by="intake")
    paused = graph.invoke(initial, config)
    event = paused["__interrupt__"][0].value["event"]
    resumed = graph.invoke(Command(resume={
        "kind":"reviewer_decision", "event_id":event["id"], "action":"note_and_continue",
        "reviewer":"Test Reviewer", "rationale":"Record the question for a human adviser.",
        "evidence":"Fictional test case"
    }),config)
    assert resumed["escalation"] is None
    assert resumed["human_events"][-1]["resolution"]["reviewer"] == "Test Reviewer"
    assert resumed["human_events"][-1]["status"] == "resolved"

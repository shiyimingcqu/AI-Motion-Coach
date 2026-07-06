"""Persist unified feedback and optional AI advice on training sessions."""

import json
import threading

from app.db.session import SessionLocal
from app.models.entities import SessionORM
from app.services.ai.ai_advice_service import generate_ai_advice


def build_feedback_data(unified_feedback: dict, formatted: dict) -> dict:
    return {
        "issues": formatted.get("errors", []),
        "suggestions": formatted.get("feedbacks", []),
        "items": [
            {
                "issue": item.get("issue", ""),
                "suggestion": item.get("suggestion", ""),
                "severity": item.get("severity", "warning"),
                "metric": item.get("metric", ""),
                "value": item.get("value", 0),
            }
            for item in unified_feedback.get("items", [])
        ],
        "metrics": formatted.get("metrics", {}),
        "score": formatted.get("score", 0),
        "level": formatted.get("level", "unknown"),
    }


def attach_ai_advice(feedback_data: dict, exercise: str) -> dict:
    """Generate AI advice once at session save time; omit field if generation fails."""
    payload = {
        "exercise": exercise,
        "errors": feedback_data.get("issues", []),
        "feedbacks": feedback_data.get("suggestions", []),
    }
    try:
        result = generate_ai_advice(payload)
        text = (result.get("text") or "").strip()
        if text:
            feedback_data["ai_advice"] = text
            feedback_data["ai_advice_source"] = result.get("source", "llm")
    except Exception as exc:
        print(f"AI advice not saved for session ({exercise}): {exc}")
    return feedback_data


def _persist_feedback_summary(session_id: str, feedback_data: dict) -> None:
    db = SessionLocal()
    try:
        sess = db.query(SessionORM).filter(SessionORM.session_id == session_id).first()
        if sess:
            sess.feedback_summary = json.dumps(feedback_data, ensure_ascii=False)
            db.commit()
    finally:
        db.close()


def schedule_background_ai_advice(
    session_id: str,
    feedback_data: dict,
    exercise: str,
) -> None:
    """Generate AI advice in a background thread so session save returns immediately."""

    def _run() -> None:
        data = dict(feedback_data)
        try:
            data = attach_ai_advice(data, exercise)
            data.pop("ai_advice_pending", None)
            if not data.get("ai_advice"):
                data["ai_advice_status"] = "failed"
        except Exception as exc:
            print(f"Background AI advice failed for session {session_id}: {exc}")
            data.pop("ai_advice_pending", None)
            data["ai_advice_status"] = "failed"
        _persist_feedback_summary(session_id, data)

    threading.Thread(target=_run, daemon=True).start()


def save_session_feedback_summary(
    session_id: str,
    feedback_data: dict,
    *,
    generate_ai: bool = False,
    generate_ai_async: bool = True,
    exercise: str = "",
) -> None:
    data = dict(feedback_data)

    if generate_ai and exercise:
        data = attach_ai_advice(data, exercise)
    elif generate_ai_async and exercise:
        data["ai_advice_pending"] = True

    _persist_feedback_summary(session_id, data)

    if generate_ai_async and exercise and not generate_ai:
        schedule_background_ai_advice(session_id, feedback_data, exercise)

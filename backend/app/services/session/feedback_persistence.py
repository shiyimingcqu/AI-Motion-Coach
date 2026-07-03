"""Persist unified feedback and optional AI advice on training sessions."""

import json

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


def save_session_feedback_summary(
    session_id: str,
    feedback_data: dict,
    *,
    generate_ai: bool = True,
    exercise: str = "",
) -> None:
    if generate_ai and exercise:
        feedback_data = attach_ai_advice(dict(feedback_data), exercise)

    db = SessionLocal()
    try:
        sess = db.query(SessionORM).filter(SessionORM.session_id == session_id).first()
        if sess:
            sess.feedback_summary = json.dumps(feedback_data, ensure_ascii=False)
            db.commit()
    finally:
        db.close()

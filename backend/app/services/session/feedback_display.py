"""Build session feedback view-model aligned with ErrorFeedbackView."""

import json
from typing import Any

from app.services.evaluation.calorie_service import get_exercise_display_name

POSITIVE_LABEL = "做得不错"
POSITIVE_SUGGESTION = "继续保持当前节奏，稳定发挥这一优势"

ISSUE_ASPECT_MAP: dict[str, str] = {
    "下降深度不稳定": "depth",
    "下降幅度整体偏浅": "depth",
    "部分动作下降过深": "depth",
    "下降幅度不足": "depth",
    "底部身体未保持直线": "body_line",
    "身体直线控制不足": "body_line",
    "左右发力明显不均": "symmetry",
    "左右略有不对称": "symmetry",
    "下降速度偏快": "tempo",
    "整体节奏略快": "tempo",
    "下蹲深度不稳定": "depth",
    "下蹲深度整体偏浅": "depth",
    "下蹲深度整体偏深": "depth",
    "部分动作深度偏浅": "depth",
    "部分动作深度偏深": "depth",
    "底部躯干前倾明显": "trunk",
    "底部躯干前倾偏大": "trunk",
    "左右膝关节明显不对称": "symmetry",
    "左右膝关节略不对称": "symmetry",
    "下蹲速度偏快": "tempo",
    "双脚打开幅度不足": "spread",
    "手臂上举幅度不足": "arms",
    "手脚配合不同步": "sync",
    "塌腰或撅臀明显，身体未保持直线": "body_line",
    "身体直线略有偏差": "body_line",
    "髋部不稳定，核心控制不足": "core",
    "支撑过程中晃动过大": "stability",
}

EXERCISE_ASPECTS: dict[str, dict[str, str]] = {
    "push_up": {
        "depth": "下降深度控制较稳定，能完成完整动作循环",
        "body_line": "身体直线保持较好，核心有参与",
        "symmetry": "左右发力较为均衡",
        "tempo": "动作节奏整体平稳",
    },
    "squat": {
        "depth": "下蹲深度整体可控，完成度不错",
        "trunk": "躯干稳定性良好，背部控制到位",
        "symmetry": "左右膝盖对称性较好",
        "tempo": "下蹲节奏比较均匀",
    },
    "jumping_jack": {
        "spread": "开合步幅基本到位",
        "arms": "手臂上举动作较完整",
        "sync": "手脚配合有一定协调性",
        "symmetry": "左右动作对称性尚可",
    },
    "plank": {
        "body_line": "身体直线维持能力不错",
        "core": "核心参与感较好",
        "stability": "支撑稳定性在可控范围内",
    },
    "lunge": {
        "depth": "弓步下蹲深度整体可控",
        "trunk": "躯干稳定性良好",
        "symmetry": "左右腿对称性较好",
    },
    "glute_bridge": {
        "extension": "髋部伸展幅度较好",
        "stability": "顶峰收缩控制稳定",
    },
    "high_knees": {
        "height": "抬膝高度基本到位",
        "tempo": "节奏较为均匀",
    },
    "burpee": {
        "depth": "下蹲与平板阶段完成度不错",
        "control": "身体控制较稳定",
    },
    "mountain_climber": {
        "body_line": "平板姿势维持较好",
        "knee_drive": "提膝动作较完整",
    },
    "pull_up": {
        "depth": "上拉幅度整体可控",
        "control": "身体摆动控制尚可",
    },
    "dumbbell_curl": {
        "depth": "弯举幅度较完整",
        "stability": "上臂稳定性较好",
    },
    "dumbbell_press": {
        "extension": "推举伸展较充分",
        "symmetry": "左右对称性尚可",
    },
    "russian_twist": {
        "rotation": "转体幅度基本到位",
        "core": "核心参与感较好",
    },
}

_SEVERITY_LABELS = {
    "high": "严重错误",
    "error": "严重错误",
    "medium": "警告",
    "warning": "警告",
    "low": "轻微错误",
}


def _parse_feedback_summary(raw: Any) -> dict:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _is_error_item(item: dict) -> bool:
    issue = (item.get("issue") or "").strip()
    severity = item.get("severity", "")
    return bool(issue) and severity not in ("info",)


def _build_strength_messages(exercise: str, issues: list[str]) -> list[str]:
    aspects = EXERCISE_ASPECTS.get(exercise) or EXERCISE_ASPECTS["squat"]
    flagged = {ISSUE_ASPECT_MAP[issue] for issue in issues if issue in ISSUE_ASPECT_MAP}
    messages = [msg for key, msg in aspects.items() if key not in flagged]
    if not messages:
        return ["训练态度积极，愿意反复尝试并调整动作"]
    return messages


def _severity_label(severity: str, issue: str) -> str:
    if severity in ("high", "error"):
        return _SEVERITY_LABELS["high"]
    if severity in ("medium", "warning"):
        return issue or _SEVERITY_LABELS["warning"]
    if severity == "low":
        return _SEVERITY_LABELS["low"]
    return issue or "提示"


def build_session_feedback_view(session) -> dict:
    """Mirror ErrorFeedbackView data for PDF / reports."""
    exercise_key = getattr(session, "exercise", "") or "squat"
    exercise_name = get_exercise_display_name(exercise_key)
    created_at = getattr(session, "created_at", None)
    time_str = created_at.strftime("%H:%M:%S") if created_at else "--:--:--"
    date_str = created_at.strftime("%Y-%m-%d") if created_at else "-"

    fb = _parse_feedback_summary(getattr(session, "feedback_summary", None))
    raw_items = fb.get("items") or []

    if not raw_items and (fb.get("issues") or fb.get("suggestions")):
        issues = fb.get("issues") or []
        suggestions = fb.get("suggestions") or []
        for index, issue in enumerate(issues):
            suggestion = suggestions[index] if index < len(suggestions) else ""
            raw_items.append({
                "issue": issue,
                "suggestion": suggestion,
                "severity": "warning" if index == 0 else "medium",
            })

    error_items = [item for item in raw_items if _is_error_item(item)]
    info_items = [
        item for item in raw_items
        if not _is_error_item(item) and (item.get("suggestion") or item.get("issue"))
    ]

    issue_texts = [(item.get("issue") or "").strip() for item in error_items]
    api_positives = [
        (item.get("suggestion") or item.get("issue") or "").strip()
        for item in info_items
        if (item.get("suggestion") or item.get("issue"))
    ]
    strength_messages = _build_strength_messages(exercise_key, [i for i in issue_texts if i])
    positive_notes = list(dict.fromkeys([*api_positives, *strength_messages]))[:5]

    cards: list[dict] = []
    for note in positive_notes:
        cards.append({
            "kind": "positive",
            "label": POSITIVE_LABEL,
            "problem": note,
            "suggestion": POSITIVE_SUGGESTION,
            "suggestion_heading": "Keep It Up / 保持建议",
        })

    for item in error_items:
        issue = (item.get("issue") or "").strip()
        suggestion = (item.get("suggestion") or "请根据纠正建议调整动作").strip()
        severity = item.get("severity", "warning")
        cards.append({
            "kind": "error",
            "label": _severity_label(severity, issue),
            "problem": issue,
            "suggestion": suggestion,
            "suggestion_heading": "Correction Suggestion / 纠正建议",
            "severity": severity,
        })

    error_counts: dict[str, int] = {}
    for issue in issue_texts:
        if issue:
            error_counts[issue] = error_counts.get(issue, 0) + 1
    max_count = max(error_counts.values()) if error_counts else 1
    error_analysis = [
        {
            "exercise": exercise_name,
            "type": err_type,
            "count": count,
            "percent": round(count / max_count * 100),
        }
        for err_type, count in sorted(error_counts.items(), key=lambda x: -x[1])
    ]

    return {
        "session_id": getattr(session, "session_id", ""),
        "exercise": exercise_key,
        "exercise_name": exercise_name,
        "date": date_str,
        "time": time_str,
        "score": getattr(session, "average_score", 0),
        "error_count": len(error_items) or getattr(session, "error_count", 0),
        "cards": cards,
        "error_analysis": error_analysis,
        "ai_advice": (fb.get("ai_advice") or "").strip(),
    }

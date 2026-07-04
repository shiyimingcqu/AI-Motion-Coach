"""Exercise evaluation report generation from session metrics."""

import json

from app.services.analysis.exercise_metrics import get_core_metrics
from app.services.evaluation.calorie_service import get_exercise_display_name

GRADE_LEVELS = [
    (90, "A", "优秀"),
    (75, "B", "良好"),
    (60, "C", "合格"),
    (0, "D", "需改进"),
]

EXERCISE_TIPS: dict[str, dict[str, list[str]]] = {
    "squat": {
        "weaknesses": ["下蹲深度不足", "膝盖内扣", "躯干前倾"],
        "recommendations": ["保持核心收紧，下蹲至大腿与地面平行", "膝盖与脚尖方向一致", "慢速完成每组动作"],
    },
    "push_up": {
        "weaknesses": ["身体塌腰", "肘部未充分弯曲", "头部位置不正确"],
        "recommendations": ["保持肩-髋-踝成一条直线", "下降时控制速度", "推起时完全伸直手臂"],
    },
    "plank": {
        "weaknesses": ["髋部下沉", "肩肘未对齐", "头部过度抬起"],
        "recommendations": ["收紧核心与臀部", "保持均匀呼吸", "减少身体晃动"],
    },
    "jumping_jack": {
        "weaknesses": ["手脚幅度不足", "节奏过快", "落地不稳"],
        "recommendations": ["手臂举过头顶，双腿充分打开", "保持均匀节奏", "落地时屈膝缓冲"],
    },
}


def score_to_grade(score: float) -> dict[str, str]:
    for threshold, letter, label in GRADE_LEVELS:
        if score >= threshold:
            return {"grade": letter, "grade_label": label}
    return {"grade": "D", "grade_label": "需改进"}


def build_evaluation(
    exercise: str,
    average_score: float,
    total_count: int,
    valid_count: int,
    error_count: int,
    duration_seconds: int,
) -> dict:
    valid_rate = (valid_count / total_count * 100) if total_count > 0 else 100.0
    grade_info = score_to_grade(average_score)
    exercise_name = get_exercise_display_name(exercise)

    metrics = get_core_metrics(exercise)
    dimension_scores: dict[str, float] = {}
    for index, metric in enumerate(metrics):
        variation = (index - (len(metrics) - 1) / 2) * 2.5
        penalty = min(error_count * 3, 15)
        dimension_scores[metric.label] = round(
            max(0, min(100, average_score + variation - penalty)), 1
        )

    if not dimension_scores:
        dimension_scores = {
            "动作规范": round(average_score, 1),
            "节奏控制": round(max(0, average_score - error_count), 1),
            "稳定性": round(max(0, average_score - error_count * 2), 1),
        }

    strengths, weaknesses, recommendations = _build_feedback(
        exercise, average_score, valid_rate, error_count, duration_seconds
    )

    return {
        **grade_info,
        "exercise": exercise,
        "exercise_name": exercise_name,
        "dimension_scores": dimension_scores,
        "valid_rate": round(valid_rate, 1),
        "error_count": error_count,
        "duration_minutes": round(max(duration_seconds, 0) / 60, 1),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "summary": _build_summary_text(
            exercise_name=exercise_name,
            exercise=exercise,
            average_score=average_score,
            grade_label=grade_info["grade_label"],
            valid_rate=valid_rate,
            error_count=error_count,
            duration_seconds=duration_seconds,
            total_count=total_count,
        ),
    }


def _build_summary_text(
    *,
    exercise_name: str,
    exercise: str,
    average_score: float,
    grade_label: str,
    valid_rate: float,
    error_count: int,
    duration_seconds: int,
    total_count: int,
) -> str:
    if exercise == "plank":
        return (
            f"本次{exercise_name}训练综合评分 {average_score:.0f} 分，"
            f"等级 {grade_label}。"
            f"有效保持时长 {duration_seconds} 秒，"
            f"共检测到 {error_count} 项姿态问题。"
        )
    return (
        f"本次{exercise_name}训练综合评分 {average_score:.0f} 分，"
        f"等级 {grade_label}。"
        f"有效动作占比 {valid_rate:.0f}%，"
        f"共检测到 {error_count} 次需改进动作。"
    )


def _build_feedback(
    exercise: str,
    average_score: float,
    valid_rate: float,
    error_count: int,
    duration_seconds: int = 0,
) -> tuple[list[str], list[str], list[str]]:
    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendations: list[str] = []

    if average_score >= 85:
        strengths.append("动作整体规范，核心控制良好")
    if valid_rate >= 80:
        strengths.append(f"有效动作占比达 {valid_rate:.0f}%，完成质量较高")
    if error_count == 0:
        strengths.append("全程未检测到明显错误动作")
    if average_score >= 70 and error_count <= 2:
        strengths.append("训练节奏稳定，可尝试增加训练量")

    tips = EXERCISE_TIPS.get(exercise, {})
    if average_score < 75:
        weaknesses.extend(tips.get("weaknesses", ["动作规范性有待提升"])[:2])
    if error_count > 3:
        weaknesses.append(f"错误动作次数偏多（{error_count} 次）")
    if valid_rate < 70:
        weaknesses.append(f"有效动作占比仅 {valid_rate:.0f}%，需加强动作质量")

    recommendations.extend(tips.get("recommendations", ["建议放慢动作速度，先保证动作质量"])[:2])
    if exercise == "plank" and duration_seconds >= 30:
        strengths.append(f"平板支撑保持 {duration_seconds} 秒，耐力表现良好")
    if average_score < 60:
        recommendations.append("建议观看标准动作示范，从低强度开始练习")
    elif average_score >= 90:
        recommendations.append("表现优秀，可尝试增加组数或提高训练强度")

    if not strengths:
        strengths.append("已完成本次训练，继续保持")
    if not weaknesses:
        weaknesses.append("暂无明显问题，建议维持当前训练节奏")
    if not recommendations:
        recommendations.append("保持规律训练，每周 3-4 次")

    return strengths[:3], weaknesses[:3], recommendations[:3]


def serialize_evaluation(evaluation: dict) -> str:
    return json.dumps(evaluation, ensure_ascii=False)


def parse_evaluation(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None

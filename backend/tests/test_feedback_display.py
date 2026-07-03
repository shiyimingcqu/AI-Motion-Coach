"""Tests for session feedback display builder."""

from types import SimpleNamespace

from app.services.session.feedback_display import build_session_feedback_view


def test_build_session_feedback_view_squat_positive_and_error():
    session = SimpleNamespace(
        session_id="s_test",
        exercise="squat",
        average_score=85,
        error_count=1,
        created_at=__import__("datetime").datetime(2026, 7, 3, 17, 22, 41),
        feedback_summary='{"issues":["左右膝关节略不对称"],"suggestions":["下蹲过程中检查左右膝盖是否同步、同向移动"],"items":[{"issue":"左右膝关节略不对称","suggestion":"下蹲过程中检查左右膝盖是否同步、同向移动","severity":"warning"}],"ai_advice":"## 🌟 整体评价\\n你完成深蹲时的专注和坚持特别棒！"}',
    )
    view = build_session_feedback_view(session)

    assert view["exercise_name"] == "深蹲"
    assert view["time"] == "17:22:41"
    assert any(c["kind"] == "positive" and "下蹲深度" in c["problem"] for c in view["cards"])
    assert any(c["kind"] == "error" and "左右膝关节" in c["problem"] for c in view["cards"])
    assert view["error_analysis"][0]["type"] == "左右膝关节略不对称"
    assert "整体评价" in view["ai_advice"]

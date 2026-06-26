from typing import TypedDict


class FeedbackResult(TypedDict):
    errors: list[str]
    suggestions: list[str]


class FeedbackService:
    """根据评分结果生成错误提示和建议"""

    def generate_template_feedback(self, score_result: dict) -> FeedbackResult:
        """
        根据模板评分结果生成错误提示和建议

        Args:
            score_result: 模板评分结果，包含 detail_scores 和 differences

        Returns:
            FeedbackResult: 包含错误和建议的字典
        """
        errors = []
        suggestions = []

        detail_scores = score_result.get("detail_scores", {})
        differences = score_result.get("differences", {})

        # 膝关节角度反馈
        knee_score = detail_scores.get("knee_angle", 0)
        knee_diff = differences.get("knee_angle", 0)

        if knee_score < 75:
            if knee_diff > 15:
                errors.append("膝关节下蹲幅度明显不足")
                suggestions.append("下蹲时继续降低重心，使膝关节弯曲更充分")
            elif knee_diff > 8:
                errors.append("膝关节下蹲幅度略不足")
                suggestions.append("尝试下蹲更深一些，保持动作完整")
            else:
                errors.append("膝关节角度不稳定")
                suggestions.append("保持下蹲深度的一致性")

        # 髋关节角度反馈
        hip_score = detail_scores.get("hip_angle", 0)
        hip_diff = differences.get("hip_angle", 0)

        if hip_score < 75:
            if hip_diff > 12:
                errors.append("髋关节活动度不足")
                suggestions.append("增加髋关节的活动范围，保持臀部向后")
            elif hip_diff > 6:
                errors.append("髋关节活动度略不足")
                suggestions.append("注意臀部向后坐的动作")
            else:
                errors.append("髋关节角度不稳定")
                suggestions.append("保持髋关节动作的连贯性")

        # 躯干角度反馈
        trunk_score = detail_scores.get("trunk_angle", 0)
        trunk_diff = differences.get("trunk_angle", 0)

        if trunk_score < 75:
            if trunk_diff > 10:
                errors.append("躯干前倾角度过大")
                suggestions.append("保持背部挺直，减少躯干前倾")
            elif trunk_diff > 5:
                errors.append("躯干前倾角度略大")
                suggestions.append("注意保持背部挺直，核心收紧")
            else:
                errors.append("躯干角度不稳定")
                suggestions.append("保持躯干角度的稳定性")

        # 左右对称性反馈
        symmetry_score = detail_scores.get("knee_symmetry_diff", 0)
        symmetry_diff = differences.get("knee_symmetry_diff", 0)

        if symmetry_score < 75:
            if symmetry_diff > 8:
                errors.append("左右膝关节明显不对称")
                suggestions.append("注意调整站姿，保持左右平衡")
            elif symmetry_diff > 4:
                errors.append("左右膝关节略不对称")
                suggestions.append("检查站姿，确保双脚平行且距离适中")
            else:
                errors.append("左右对称性不稳定")
                suggestions.append("保持动作的对称性")

        # 如果没有明显错误，给出正面反馈
        if not errors:
            total_score = score_result.get("score", 0)
            if total_score >= 90:
                suggestions.append("动作非常标准，继续保持！")
            elif total_score >= 75:
                suggestions.append("动作整体良好，可以继续提升细节")

        return {
            "errors": errors,
            "suggestions": suggestions
        }
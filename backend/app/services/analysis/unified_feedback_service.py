"""统一反馈服务 — 实时检测和视频分析共用同一套反馈逻辑。

规则：
- 深蹲深度：底部膝角 65-125° 为合理范围
- 躯干稳定：底部躯干角 <35° 良好，35-45° 略前倾，>45° 明显前倾  
- 左右对称：膝角差 <18° 良好，18-25° 略不对称，>25° 明显不对称
- 下蹲节奏：逐帧膝角变化 <16° 良好，16-28° 略快，>28° 过快
"""

from collections import Counter
from typing import TypedDict


class FeedbackItem(TypedDict):
    issue: str
    suggestion: str
    severity: str  # "error" | "warning" | "info"
    metric: str
    value: float


class UnifiedFeedbackResult(TypedDict):
    items: list[FeedbackItem]
    summary_score: float
    summary_level: str  # "excellent" | "good" | "fair" | "poor"
    total_reps: int
    valid_reps: int


class UnifiedFeedbackService:
    """基于动作特征生成统一、无矛盾的反馈。"""

    # 深蹲底部评分阈值
    SQUAT_THRESHOLDS = {
        "knee_angle": {"good": (70, 120), "fair": (55, 135)},
        "trunk_angle": {"good": (0, 35), "fair": (0, 55)},
        "knee_symmetry": {"good": (0, 18), "fair": (0, 32)},
        "tempo": {"good": (0, 16), "fair": (0, 28)},  # 逐帧膝角变化
    }

    def generate_squat_feedback(
        self,
        rep_summaries: list[dict],
        total_reps: int = 0,
        valid_reps: int = 0,
    ) -> UnifiedFeedbackResult:
        """基于多次深蹲的汇总特征生成反馈。

        Args:
            rep_summaries: 每次深蹲的汇总特征列表
            total_reps: 总次数
            valid_reps: 有效次数

        Returns:
            UnifiedFeedbackResult: 结构化反馈结果
        """
        if not rep_summaries:
            return {
                "items": [],
                "summary_score": 0.0,
                "summary_level": "invalid",
                "total_reps": total_reps,
                "valid_reps": valid_reps,
            }

        # 收集所有动作的指标
        knee_angles = [r.get("knee_angle") for r in rep_summaries if r.get("knee_angle")]
        trunk_angles = [r.get("trunk_angle") for r in rep_summaries if r.get("trunk_angle")]
        sym_diffs = [r.get("knee_symmetry_diff") for r in rep_summaries if r.get("knee_symmetry_diff")]
        tempo_steps = [r.get("max_knee_angle_step", 0) for r in rep_summaries]

        items: list[FeedbackItem] = []

        # --- 深度分析（去矛盾）---
        depth_item = self._analyze_depth(knee_angles)
        if depth_item:
            items.append(depth_item)

        # --- 躯干稳定性 ---
        trunk_item = self._analyze_trunk(trunk_angles)
        if trunk_item:
            items.append(trunk_item)

        # --- 左右对称性 ---
        sym_item = self._analyze_symmetry(sym_diffs)
        if sym_item:
            items.append(sym_item)

        # --- 节奏控制 ---
        tempo_item = self._analyze_tempo(tempo_steps)
        if tempo_item:
            items.append(tempo_item)

        # 计算总分
        scores = []
        if knee_angles:
            scores.append(self._score_by_range(
                sum(knee_angles) / len(knee_angles),
                self.SQUAT_THRESHOLDS["knee_angle"]["good"],
                self.SQUAT_THRESHOLDS["knee_angle"]["fair"],
            ))
        if trunk_angles:
            scores.append(self._score_by_range(
                sum(trunk_angles) / len(trunk_angles),
                self.SQUAT_THRESHOLDS["trunk_angle"]["good"],
                self.SQUAT_THRESHOLDS["trunk_angle"]["fair"],
            ))
        if sym_diffs:
            scores.append(self._score_by_range(
                sum(sym_diffs) / len(sym_diffs),
                self.SQUAT_THRESHOLDS["knee_symmetry"]["good"],
                self.SQUAT_THRESHOLDS["knee_symmetry"]["fair"],
            ))
        if tempo_steps:
            scores.append(self._score_by_range(
                sum(tempo_steps) / len(tempo_steps),
                self.SQUAT_THRESHOLDS["tempo"]["good"],
                self.SQUAT_THRESHOLDS["tempo"]["fair"],
            ))

        summary_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        summary_level = self._level_by_score(summary_score)

        # 无问题时给正面反馈
        if not items and valid_reps > 0:
            items.append({
                "issue": "",
                "suggestion": "深蹲动作整体规范，深度、稳定性和节奏控制良好，继续保持！",
                "severity": "info",
                "metric": "overall",
                "value": summary_score,
            })

        return {
            "items": items,
            "summary_score": summary_score,
            "summary_level": summary_level,
            "total_reps": total_reps,
            "valid_reps": valid_reps,
        }

    def _analyze_depth(self, knee_angles: list[float]) -> FeedbackItem | None:
        """分析深蹲深度，处理深浅矛盾。"""
        if not knee_angles:
            return None

        avg_knee = sum(knee_angles) / len(knee_angles)
        min_knee = min(knee_angles)
        max_knee = max(knee_angles)

        shallow_count = sum(1 for k in knee_angles if k > 125)
        deep_count = sum(1 for k in knee_angles if k < 65)
        normal_count = len(knee_angles) - shallow_count - deep_count

        # 去矛盾逻辑
        if shallow_count > 0 and deep_count > 0:
            # 既有偏浅又有偏深 → 不稳定
            return {
                "issue": "下蹲深度不稳定",
                "suggestion": "每次下蹲都控制到大腿接近水平，避免忽深忽浅",
                "severity": "warning",
                "metric": "knee_angle_range",
                "value": max_knee - min_knee,
            }

        if shallow_count > deep_count and shallow_count > normal_count:
            return {
                "issue": "下蹲深度整体偏浅",
                "suggestion": "尝试下蹲更低，使大腿接近水平或略低于水平位置",
                "severity": "warning",
                "metric": "avg_knee_angle",
                "value": avg_knee,
            }

        if deep_count > shallow_count and deep_count > normal_count:
            return {
                "issue": "下蹲深度整体偏深",
                "suggestion": "下蹲到大腿水平即可，无需过度追求深度而影响稳定",
                "severity": "warning",
                "metric": "avg_knee_angle",
                "value": avg_knee,
            }

        if shallow_count > 0:
            return {
                "issue": "部分动作深度偏浅",
                "suggestion": "注意每次下蹲都达到足够的深度，保持动作一致性",
                "severity": "warning",
                "metric": "shallow_ratio",
                "value": shallow_count / len(knee_angles),
            }

        if deep_count > 0:
            return {
                "issue": "部分动作深度偏深",
                "suggestion": "控制下蹲幅度，避免因过度下沉丢失核心稳定",
                "severity": "info",
                "metric": "deep_ratio",
                "value": deep_count / len(knee_angles),
            }

        return None

    def _analyze_trunk(self, trunk_angles: list[float]) -> FeedbackItem | None:
        """分析躯干稳定性。"""
        if not trunk_angles:
            return None

        avg_trunk = sum(trunk_angles) / len(trunk_angles)
        max_trunk = max(trunk_angles)

        if max_trunk > 45:
            return {
                "issue": "底部躯干前倾明显",
                "suggestion": "最深处收紧核心、胸口微微抬起，保持背部接近直立",
                "severity": "error",
                "metric": "max_trunk_angle",
                "value": max_trunk,
            }

        if avg_trunk > 35:
            return {
                "issue": "底部躯干前倾偏大",
                "suggestion": "下蹲到底部时保持核心收紧，避免上半身继续前倒",
                "severity": "warning",
                "metric": "avg_trunk_angle",
                "value": avg_trunk,
            }

        return None

    def _analyze_symmetry(self, sym_diffs: list[float]) -> FeedbackItem | None:
        """分析左右对称性。"""
        if not sym_diffs:
            return None

        avg_diff = sum(sym_diffs) / len(sym_diffs)
        max_diff = max(sym_diffs)

        if max_diff > 25:
            return {
                "issue": "左右膝关节明显不对称",
                "suggestion": "最深处保持左右膝盖同向对齐脚尖，重心放在两脚中间",
                "severity": "error",
                "metric": "max_symmetry_diff",
                "value": max_diff,
            }

        if avg_diff > 18:
            return {
                "issue": "左右膝关节略不对称",
                "suggestion": "下蹲过程中检查左右膝盖是否同步、同向移动",
                "severity": "warning",
                "metric": "avg_symmetry_diff",
                "value": avg_diff,
            }

        return None

    def _analyze_tempo(self, tempo_steps: list[float]) -> FeedbackItem | None:
        """分析下蹲节奏。"""
        if not tempo_steps:
            return None

        avg_step = sum(tempo_steps) / len(tempo_steps)
        max_step = max(tempo_steps)

        if max_step > 28:
            return {
                "issue": "下蹲速度偏快",
                "suggestion": "下蹲阶段放慢到约2秒完成，避免突然下坠失去控制",
                "severity": "warning",
                "metric": "max_tempo_step",
                "value": max_step,
            }

        if avg_step > 20:
            return {
                "issue": "整体节奏略快",
                "suggestion": "保持匀速下蹲，感受肌肉持续发力而非自由落体",
                "severity": "info",
                "metric": "avg_tempo_step",
                "value": avg_step,
            }

        return None

    @staticmethod
    def _score_by_range(
        value: float,
        good_range: tuple[float, float],
        fair_range: tuple[float, float],
    ) -> float:
        """基于范围的评分函数。"""
        good_min, good_max = good_range
        fair_min, fair_max = fair_range

        if good_min <= value <= good_max:
            return 100.0
        if value < fair_min or value > fair_max:
            return 40.0

        if fair_min <= value < good_min:
            ratio = (value - fair_min) / (good_min - fair_min)
            return 40.0 + ratio * 60.0
        if good_max < value <= fair_max:
            ratio = (fair_max - value) / (fair_max - good_max)
            return 40.0 + ratio * 60.0
        return 40.0

    @staticmethod
    def _level_by_score(score: float) -> str:
        if score >= 90:
            return "excellent"
        if score >= 75:
            return "good"
        if score >= 60:
            return "fair"
        return "poor"

    def format_for_ai(self, result: UnifiedFeedbackResult) -> dict:
        """将统一反馈格式化为 AI 可用的格式。"""
        errors = [item["issue"] for item in result["items"] if item["issue"]]
        feedbacks = [item["suggestion"] for item in result["items"]]

        # 收集关键指标
        metrics: dict[str, float] = {}
        for item in result["items"]:
            metrics[item["metric"]] = item["value"]

        return {
            "errors": errors,
            "feedbacks": feedbacks,
            "metrics": metrics,
            "score": result["summary_score"],
            "level": result["summary_level"],
            "total_reps": result["total_reps"],
            "valid_reps": result["valid_reps"],
        }


# 全局服务实例
unified_feedback_service = UnifiedFeedbackService()


def build_unified_feedback_from_analyzer(analyzer) -> UnifiedFeedbackResult:
    """从任意分析器实例生成统一反馈（实时 WebSocket 与视频分析共用）。"""
    summary = analyzer.get_session_summary()
    exercise = summary.get("exercise") or getattr(analyzer, "exercise_type", "squat")

    if exercise == "squat":
        rep_summaries = getattr(analyzer, "rep_summaries", [])
        return unified_feedback_service.generate_squat_feedback(
            rep_summaries=rep_summaries,
            total_reps=summary.get("total_count", 0),
            valid_reps=summary.get("valid_count", 0),
        )

    return {
        "items": [],
        "summary_score": summary.get("average_score", 0),
        "summary_level": "unknown",
        "total_reps": summary.get("total_count", 0),
        "valid_reps": summary.get("valid_count", 0),
    }

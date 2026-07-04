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

    def generate_push_up_feedback(
        self,
        rep_summaries: list[dict],
        total_reps: int = 0,
        valid_reps: int = 0,
    ) -> UnifiedFeedbackResult:
        """基于多次俯卧撑的汇总特征生成反馈。"""
        if total_reps <= 0:
            return {
                "items": [{
                    "issue": "未检测到完成的俯卧撑",
                    "suggestion": "请确保侧对摄像头，完成至少一次完整的下降与推起",
                    "severity": "warning",
                    "metric": "total_reps",
                    "value": 0,
                }],
                "summary_score": 0.0,
                "summary_level": "invalid",
                "total_reps": total_reps,
                "valid_reps": valid_reps,
            }

        if not rep_summaries:
            return {
                "items": [{
                    "issue": "动作未达到有效标准",
                    "suggestion": "关注下降深度与身体直线，每次推起时保持核心收紧",
                    "severity": "warning",
                    "metric": "valid_reps",
                    "value": float(valid_reps),
                }],
                "summary_score": 0.0,
                "summary_level": "poor",
                "total_reps": total_reps,
                "valid_reps": valid_reps,
            }

        elbow_angles = [r.get("elbow_angle") for r in rep_summaries if r.get("elbow_angle") is not None]
        body_lines = [r.get("body_line_angle") for r in rep_summaries if r.get("body_line_angle") is not None]
        sym_diffs = [r.get("symmetry_diff") for r in rep_summaries if r.get("symmetry_diff") is not None]
        tempo_steps = [r.get("max_elbow_angle_step", 0) for r in rep_summaries]

        items: list[FeedbackItem] = []

        depth_item = self._analyze_push_up_depth(elbow_angles)
        if depth_item:
            items.append(depth_item)

        body_item = self._analyze_push_up_body_line(body_lines)
        if body_item:
            items.append(body_item)

        sym_item = self._analyze_push_up_symmetry(sym_diffs)
        if sym_item:
            items.append(sym_item)

        tempo_item = self._analyze_push_up_tempo(tempo_steps)
        if tempo_item:
            items.append(tempo_item)

        scores: list[float] = []
        if elbow_angles:
            scores.append(self._score_by_range(
                sum(elbow_angles) / len(elbow_angles), (80, 100), (60, 130),
            ))
        if body_lines:
            scores.append(self._score_by_range(
                sum(body_lines) / len(body_lines), (0, 12), (0, 25),
            ))
        if sym_diffs:
            scores.append(self._score_by_range(
                sum(sym_diffs) / len(sym_diffs), (0, 10), (0, 22),
            ))
        if tempo_steps:
            scores.append(self._score_by_range(
                sum(tempo_steps) / len(tempo_steps), (0, 18), (0, 32),
            ))

        summary_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        summary_level = self._level_by_score(summary_score)

        if not items and valid_reps > 0:
            items.append({
                "issue": "",
                "suggestion": "俯卧撑动作整体规范，深度、身体直线和稳定性良好，继续保持！",
                "severity": "info",
                "metric": "overall",
                "value": summary_score,
            })

        if not items and valid_reps <= 0:
            items.append({
                "issue": "动作未达到有效标准",
                "suggestion": "下降时肘关节弯曲到接近 90°，并保持肩-髋-踝成一直线",
                "severity": "warning",
                "metric": "valid_reps",
                "value": 0,
            })

        return {
            "items": items,
            "summary_score": summary_score,
            "summary_level": summary_level,
            "total_reps": total_reps,
            "valid_reps": valid_reps,
        }

    def generate_lunge_feedback(
        self,
        rep_summaries: list[dict],
        total_reps: int = 0,
        valid_reps: int = 0,
    ) -> UnifiedFeedbackResult:
        if total_reps <= 0:
            return self._no_rep_result("弓步蹲", "侧对摄像头，完成至少一次弓步下蹲与站起", total_reps, valid_reps)

        if not rep_summaries:
            return self._weak_rep_result(
                total_reps, valid_reps,
                "动作未达到有效标准",
                "关注前腿弯曲深度与躯干稳定，每次弓步尽量做到位",
            )

        knee_angles = [r["knee_angle"] for r in rep_summaries if r.get("knee_angle") is not None]
        trunk_angles = [
            r.get("max_trunk_angle", r.get("trunk_angle"))
            for r in rep_summaries
            if r.get("max_trunk_angle") is not None or r.get("trunk_angle") is not None
        ]
        sym_diffs = [
            r.get("max_knee_symmetry_diff", r.get("knee_symmetry_diff", 0))
            for r in rep_summaries
        ]
        tempo_steps = [r.get("max_knee_angle_step", 0) for r in rep_summaries]

        items: list[FeedbackItem] = []
        shallow = sum(1 for a in knee_angles if a > 105)
        deep = sum(1 for a in knee_angles if a < 75)

        if shallow and deep:
            items.append({
                "issue": "弓步深度不稳定",
                "suggestion": "每次前腿都屈膝至约 90°，避免忽深忽浅",
                "severity": "warning",
                "metric": "knee_angle_range",
                "value": max(knee_angles) - min(knee_angles) if knee_angles else 0,
            })
        elif shallow >= max(1, len(knee_angles) / 2):
            items.append({
                "issue": "弓步下蹲深度整体偏浅",
                "suggestion": "前腿屈膝至约 90°，后腿膝盖接近地面",
                "severity": "warning",
                "metric": "avg_knee_angle",
                "value": sum(knee_angles) / len(knee_angles) if knee_angles else 0,
            })
        elif deep > 0:
            items.append({
                "issue": "部分弓步下蹲过深",
                "suggestion": "控制前腿弯曲角度，约 90° 即可，避免膝盖压力过大",
                "severity": "info",
                "metric": "min_knee_angle",
                "value": min(knee_angles) if knee_angles else 0,
            })

        if trunk_angles and max(trunk_angles) > 28:
            items.append({
                "issue": "躯干前倾明显过多",
                "suggestion": "保持上身挺直，核心收紧，减少身体向前倾倒",
                "severity": "error",
                "metric": "max_trunk_angle",
                "value": max(trunk_angles),
            })
        elif trunk_angles and sum(trunk_angles) / len(trunk_angles) > 22:
            items.append({
                "issue": "躯干前倾偏大",
                "suggestion": "下蹲时胸口微抬，避免上身过度前倒",
                "severity": "warning",
                "metric": "avg_trunk_angle",
                "value": sum(trunk_angles) / len(trunk_angles),
            })

        if sym_diffs and max(sym_diffs) > 25:
            items.append({
                "issue": "前后腿弯曲明显不对称",
                "suggestion": "前腿承担主要弯曲，后腿保持相对稳定",
                "severity": "warning",
                "metric": "max_knee_symmetry_diff",
                "value": max(sym_diffs),
            })

        if tempo_steps and max(tempo_steps) > 30:
            items.append({
                "issue": "下蹲速度偏快",
                "suggestion": "下蹲阶段放慢，控制前腿弯曲节奏",
                "severity": "warning",
                "metric": "max_knee_angle_step",
                "value": max(tempo_steps),
            })

        return self._finalize_feedback(items, rep_summaries, total_reps, valid_reps,
                                      "弓步蹲动作整体规范，深度与稳定性良好，继续保持！")

    def generate_glute_bridge_feedback(
        self,
        rep_summaries: list[dict],
        total_reps: int = 0,
        valid_reps: int = 0,
    ) -> UnifiedFeedbackResult:
        if total_reps <= 0:
            return self._no_rep_result("臀桥", "仰卧屈膝，完成至少一次抬臀与下放", total_reps, valid_reps)

        if not rep_summaries:
            return self._weak_rep_result(
                total_reps, valid_reps,
                "动作未达到有效标准",
                "顶峰时肩-髋-膝成直线，感受臀部发力",
            )

        hip_angles = [r["hip_angle"] for r in rep_summaries if r.get("hip_angle") is not None]
        body_lines = [
            r.get("min_body_line_angle", r.get("body_line_angle"))
            for r in rep_summaries
            if r.get("min_body_line_angle") is not None or r.get("body_line_angle") is not None
        ]
        tempo_steps = [r.get("max_hip_angle_step", 0) for r in rep_summaries]

        items: list[FeedbackItem] = []
        if hip_angles and sum(1 for h in hip_angles if h < 155) >= len(hip_angles) / 2:
            items.append({
                "issue": "抬臀高度整体不足",
                "suggestion": "顶峰收缩时肩-髋-膝尽量成一条直线，充分夹紧臀部",
                "severity": "warning",
                "metric": "avg_hip_angle",
                "value": sum(hip_angles) / len(hip_angles),
            })

        if body_lines and max(body_lines) > 12:
            items.append({
                "issue": "顶峰时身体未保持直线",
                "suggestion": "收紧腹部与臀部，避免腰部过度拱起代偿",
                "severity": "error",
                "metric": "max_body_line_angle",
                "value": max(body_lines),
            })
        elif body_lines and sum(body_lines) / len(body_lines) > 8:
            items.append({
                "issue": "顶峰时腰部代偿明显",
                "suggestion": "顶峰时保持肩-髋-膝一条线，不要过度挺腰",
                "severity": "warning",
                "metric": "avg_body_line_angle",
                "value": sum(body_lines) / len(body_lines),
            })

        if tempo_steps and max(tempo_steps) > 32:
            items.append({
                "issue": "抬臀速度偏快",
                "suggestion": "上抬与下放都放慢，顶峰停留 1～2 秒",
                "severity": "info",
                "metric": "max_hip_angle_step",
                "value": max(tempo_steps),
            })

        return self._finalize_feedback(items, rep_summaries, total_reps, valid_reps,
                                      "臀桥伸展幅度与控制整体较好，继续保持！")

    def generate_high_knees_feedback(
        self,
        rep_summaries: list[dict],
        total_reps: int = 0,
        valid_reps: int = 0,
    ) -> UnifiedFeedbackResult:
        if total_reps <= 0:
            return self._no_rep_result("高抬腿", "正对摄像头，完成左右腿交替抬膝", total_reps, valid_reps)

        if not rep_summaries:
            return self._weak_rep_result(
                total_reps, valid_reps,
                "动作未达到有效标准",
                "大腿抬至接近与地面平行，保持快速节奏",
            )

        heights = [r["knee_height"] for r in rep_summaries if r.get("knee_height") is not None]
        left_h = [r.get("max_left_knee_h", 0) for r in rep_summaries]
        right_h = [r.get("max_right_knee_h", 0) for r in rep_summaries]
        tempo_steps = [r.get("max_height_step", 0) for r in rep_summaries]

        items: list[FeedbackItem] = []
        if heights and sum(1 for h in heights if h < 0.12) >= len(heights) / 2:
            items.append({
                "issue": "抬膝高度整体不足",
                "suggestion": "大腿抬至接近与地面平行，脚尖朝下",
                "severity": "warning",
                "metric": "avg_knee_height",
                "value": sum(heights) / len(heights),
            })

        sym_diffs = [abs(l - r) for l, r in zip(left_h, right_h) if l > 0.05 and r > 0.05]
        if sym_diffs and max(sym_diffs) > 0.10:
            items.append({
                "issue": "左右抬膝高度明显不均",
                "suggestion": "左右腿交替时保持相近的抬膝高度",
                "severity": "warning",
                "metric": "max_leg_height_diff",
                "value": max(sym_diffs),
            })

        if tempo_steps and max(tempo_steps) > 0.14:
            items.append({
                "issue": "抬膝节奏不稳定",
                "suggestion": "保持匀速交替，避免忽高忽低",
                "severity": "info",
                "metric": "max_height_step",
                "value": max(tempo_steps),
            })

        return self._finalize_feedback(items, rep_summaries, total_reps, valid_reps,
                                      "高抬腿高度、对称性与节奏整体较好，继续保持！")

    def generate_burpee_feedback(
        self,
        rep_summaries: list[dict],
        total_reps: int = 0,
        valid_reps: int = 0,
    ) -> UnifiedFeedbackResult:
        if total_reps <= 0:
            return self._no_rep_result("波比跳", "完成至少一次下蹲-平板-跳起-站立的完整循环", total_reps, valid_reps)

        if not rep_summaries:
            return self._weak_rep_result(
                total_reps, valid_reps,
                "动作未达到有效标准",
                "确保经历下蹲、平板、跳起各阶段，动作连贯",
            )

        min_hips = [r.get("min_hip_angle", 180) for r in rep_summaries]
        plank_lines = [r.get("plank_body_line_angle", 0) for r in rep_summaries]
        jump_heights = [r.get("max_wrist_height", 0) for r in rep_summaries]

        items: list[FeedbackItem] = []
        if min_hips and sum(1 for h in min_hips if h > 115) >= len(min_hips) / 2:
            items.append({
                "issue": "下蹲阶段深度不足",
                "suggestion": "下蹲时双手触地，髋部下沉至接近深蹲深度",
                "severity": "warning",
                "metric": "avg_min_hip_angle",
                "value": sum(min_hips) / len(min_hips),
            })

        if plank_lines and max(plank_lines) > 28:
            items.append({
                "issue": "平板阶段身体未保持直线",
                "suggestion": "俯卧撑姿势时收紧核心，肩-髋-踝保持一条直线",
                "severity": "error",
                "metric": "max_plank_body_line",
                "value": max(plank_lines),
            })
        elif plank_lines and sum(plank_lines) / len(plank_lines) > 22:
            items.append({
                "issue": "平板阶段塌腰或撅臀",
                "suggestion": "平板支撑时避免髋部下沉或抬高",
                "severity": "warning",
                "metric": "avg_plank_body_line",
                "value": sum(plank_lines) / len(plank_lines),
            })

        if jump_heights and sum(1 for j in jump_heights if j < 0.12) >= len(jump_heights) / 2:
            items.append({
                "issue": "跳跃阶段爆发力不足",
                "suggestion": "最后向上跃起时双手举过头顶，全身伸展",
                "severity": "warning",
                "metric": "avg_wrist_height",
                "value": sum(jump_heights) / len(jump_heights),
            })

        return self._finalize_feedback(items, rep_summaries, total_reps, valid_reps,
                                      "波比跳各阶段连贯性与身体控制整体较好，继续保持！")

    def _no_rep_result(
        self, label: str, suggestion: str, total_reps: int = 0, valid_reps: int = 0,
    ) -> UnifiedFeedbackResult:
        return {
            "items": [{
                "issue": f"未检测到完成的{label}",
                "suggestion": suggestion,
                "severity": "warning",
                "metric": "total_reps",
                "value": 0,
            }],
            "summary_score": 0.0,
            "summary_level": "invalid",
            "total_reps": total_reps,
            "valid_reps": valid_reps,
        }

    def _weak_rep_result(
        self, total_reps: int, valid_reps: int, issue: str, suggestion: str,
    ) -> UnifiedFeedbackResult:
        return {
            "items": [{
                "issue": issue,
                "suggestion": suggestion,
                "severity": "warning",
                "metric": "valid_reps",
                "value": float(valid_reps),
            }],
            "summary_score": 0.0,
            "summary_level": "poor",
            "total_reps": total_reps,
            "valid_reps": valid_reps,
        }

    def _finalize_feedback(
        self,
        items: list[FeedbackItem],
        rep_summaries: list[dict],
        total_reps: int,
        valid_reps: int,
        positive_message: str,
    ) -> UnifiedFeedbackResult:
        scores = []
        for rep in rep_summaries:
            if rep.get("knee_angle") is not None:
                scores.append(self._score_by_range(rep["knee_angle"], (75, 105), (60, 120)))
            elif rep.get("hip_angle") is not None:
                scores.append(self._score_by_range(rep["hip_angle"], (160, 180), (145, 180)))
            elif rep.get("knee_height") is not None:
                scores.append(self._score_by_range(rep["knee_height"], (0.12, 0.28), (0.06, 0.36)))
            elif rep.get("min_hip_angle") is not None:
                scores.append(self._score_by_range(rep["min_hip_angle"], (85, 115), (70, 135)))

        summary_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        summary_level = self._level_by_score(summary_score)

        if not items and valid_reps > 0:
            items.append({
                "issue": "",
                "suggestion": positive_message,
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

    def generate_generic_rep_feedback(
        self,
        analyzer,
        rep_summaries: list[dict],
        total_reps: int = 0,
        valid_reps: int = 0,
        exercise: str = "",
    ) -> UnifiedFeedbackResult:
        """基于分析器 score_rep 为通用动作生成反馈。"""
        exercise_labels = {
            "lunge": "弓步蹲",
            "glute_bridge": "臀桥",
            "high_knees": "高抬腿",
            "burpee": "波比跳",
            "mountain_climber": "登山跑",
            "pull_up": "引体向上",
            "dumbbell_curl": "哑铃弯举",
            "dumbbell_press": "哑铃推举",
            "russian_twist": "俄罗斯转体",
            "jumping_jack": "开合跳",
            "plank": "平板支撑",
        }
        label = exercise_labels.get(exercise, exercise or "动作")

        if total_reps <= 0:
            return {
                "items": [{
                    "issue": f"未检测到完成的{label}",
                    "suggestion": f"请调整站位并完整完成至少一次{label}动作循环",
                    "severity": "warning",
                    "metric": "total_reps",
                    "value": 0,
                }],
                "summary_score": 0.0,
                "summary_level": "invalid",
                "total_reps": total_reps,
                "valid_reps": valid_reps,
            }

        items: list[FeedbackItem] = []
        scores: list[float] = []
        seen_issues: set[str] = set()

        if rep_summaries and hasattr(analyzer, "score_rep"):
            for summary in rep_summaries:
                result = analyzer.score_rep(summary)
                score = result.get("score")
                if score is not None:
                    scores.append(float(score))
                for issue in result.get("issues", []):
                    if issue in seen_issues:
                        continue
                    seen_issues.add(issue)
                    feedback_list = result.get("feedback", [])
                    suggestion = feedback_list[0] if feedback_list else f"针对「{issue}」调整动作细节"
                    items.append({
                        "issue": issue,
                        "suggestion": suggestion,
                        "severity": "warning" if "不足" in issue or "不稳" in issue else "info",
                        "metric": exercise,
                        "value": float(score or 0),
                    })

        if not rep_summaries and valid_reps <= 0:
            items.append({
                "issue": "动作未达到有效标准",
                "suggestion": f"关注{label}的关键姿态要点，每次动作尽量做到位",
                "severity": "warning",
                "metric": "valid_reps",
                "value": float(valid_reps),
            })

        summary_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        summary_level = self._level_by_score(summary_score)

        if not items and valid_reps > 0:
            items.append({
                "issue": "",
                "suggestion": f"{label}动作整体标准，继续保持",
                "severity": "info",
                "metric": "valid_reps",
                "value": float(valid_reps),
            })

        return {
            "items": items,
            "summary_score": summary_score,
            "summary_level": summary_level,
            "total_reps": total_reps,
            "valid_reps": valid_reps,
        }

    def _analyze_push_up_depth(self, elbow_angles: list[float]) -> FeedbackItem | None:
        if not elbow_angles:
            return None

        avg_elbow = sum(elbow_angles) / len(elbow_angles)
        min_elbow = min(elbow_angles)
        shallow_count = sum(1 for angle in elbow_angles if angle > 105)
        deep_count = sum(1 for angle in elbow_angles if angle < 75)

        if shallow_count > 0 and deep_count > 0:
            return {
                "issue": "下降深度不稳定",
                "suggestion": "每次下降都控制到接近 90°，避免忽深忽浅",
                "severity": "warning",
                "metric": "elbow_angle_range",
                "value": max(elbow_angles) - min_elbow,
            }

        if shallow_count >= len(elbow_angles) / 2:
            return {
                "issue": "下降幅度整体偏浅",
                "suggestion": "下降时肘关节弯曲到接近 90°，胸部接近地面",
                "severity": "warning",
                "metric": "avg_elbow_angle",
                "value": avg_elbow,
            }

        if deep_count > 0:
            return {
                "issue": "部分动作下降过深",
                "suggestion": "控制下降深度，肘关节约 90° 即可，避免过度触地",
                "severity": "info",
                "metric": "min_elbow_angle",
                "value": min_elbow,
            }

        return None

    def _analyze_push_up_body_line(self, body_lines: list[float]) -> FeedbackItem | None:
        if not body_lines:
            return None

        avg_body = sum(body_lines) / len(body_lines)
        max_body = max(body_lines)

        if max_body > 20:
            return {
                "issue": "底部身体未保持直线",
                "suggestion": "收紧核心，让肩-髋-踝保持一条直线，避免塌腰或撅臀",
                "severity": "error",
                "metric": "max_body_line_angle",
                "value": max_body,
            }

        if avg_body > 14:
            return {
                "issue": "身体直线控制不足",
                "suggestion": "推起与下降过程中保持平板姿势，核心持续发力",
                "severity": "warning",
                "metric": "avg_body_line_angle",
                "value": avg_body,
            }

        return None

    def _analyze_push_up_symmetry(self, sym_diffs: list[float]) -> FeedbackItem | None:
        if not sym_diffs:
            return None

        avg_diff = sum(sym_diffs) / len(sym_diffs)
        max_diff = max(sym_diffs)

        if max_diff > 20:
            return {
                "issue": "左右发力明显不均",
                "suggestion": "注意左右手均匀用力，保持肩膀水平",
                "severity": "error",
                "metric": "max_symmetry_diff",
                "value": max_diff,
            }

        if avg_diff > 12:
            return {
                "issue": "左右略有不对称",
                "suggestion": "调整手部位置，保持身体对称",
                "severity": "warning",
                "metric": "avg_symmetry_diff",
                "value": avg_diff,
            }

        return None

    def _analyze_push_up_tempo(self, tempo_steps: list[float]) -> FeedbackItem | None:
        if not tempo_steps:
            return None

        max_step = max(tempo_steps)
        avg_step = sum(tempo_steps) / len(tempo_steps)

        if max_step > 32:
            return {
                "issue": "下降速度偏快",
                "suggestion": "下降阶段放慢，控制动作节奏",
                "severity": "warning",
                "metric": "max_elbow_angle_step",
                "value": max_step,
            }

        if avg_step > 22:
            return {
                "issue": "整体节奏略快",
                "suggestion": "保持匀速下降与推起，感受肌肉持续发力",
                "severity": "info",
                "metric": "avg_elbow_angle_step",
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

    if exercise == "push_up":
        rep_summaries = getattr(analyzer, "rep_summaries", [])
        return unified_feedback_service.generate_push_up_feedback(
            rep_summaries=rep_summaries,
            total_reps=summary.get("total_count", 0),
            valid_reps=summary.get("valid_count", 0),
        )

    rep_summaries = getattr(analyzer, "rep_summaries", [])
    total_reps = summary.get("total_count", 0)
    valid_reps = summary.get("valid_count", 0)

    dedicated = {
        "lunge": unified_feedback_service.generate_lunge_feedback,
        "glute_bridge": unified_feedback_service.generate_glute_bridge_feedback,
        "high_knees": unified_feedback_service.generate_high_knees_feedback,
        "burpee": unified_feedback_service.generate_burpee_feedback,
    }
    if exercise in dedicated:
        return dedicated[exercise](rep_summaries, total_reps, valid_reps)

    return unified_feedback_service.generate_generic_rep_feedback(
        analyzer=analyzer,
        rep_summaries=rep_summaries,
        total_reps=summary.get("total_count", 0),
        valid_reps=summary.get("valid_count", 0),
        exercise=exercise,
    )

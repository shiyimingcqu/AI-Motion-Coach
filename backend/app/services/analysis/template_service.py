import json
from pathlib import Path
from typing import TypedDict, Optional
import numpy as np


class TemplateScoreResult(TypedDict):
    score: float
    level: str
    detail_scores: dict[str, float]
    differences: dict[str, float]


class TemplateService:
    def __init__(self, template_dir: str = "app/templates", storage_dir: str = "storage/templates"):
        backend_root = Path(__file__).resolve().parents[3]
        repo_root = backend_root.parent
        self.template_dir = self._resolve_dir(template_dir, backend_root, repo_root)
        self.storage_dir = self._resolve_dir(storage_dir, backend_root, repo_root)
        self.templates = {}

    @staticmethod
    def _resolve_dir(path: str, backend_root: Path, repo_root: Path) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate

        repo_candidate = repo_root / candidate
        backend_candidate = backend_root / candidate

        if repo_candidate.exists():
            return repo_candidate
        return backend_candidate

    def load_template(self, action: str, view: Optional[str] = None) -> dict:
        """
        加载指定动作的标准模板

        优先从 storage/templates 读取，找不到时回退到 app/templates

        Args:
            action: 动作名称（如 "squat"）
            view: 可选，拍摄角度（side/front/diagonal）

        Returns:
            模板数据字典

        Raises:
            FileNotFoundError: 模板文件不存在
            ValueError: 模板格式错误
        """
        # 构建缓存键
        cache_key = f"{action}_{view}" if view else action
        if cache_key in self.templates:
            return self.templates[cache_key]

        # 优先查找用户自定义模板
        template_path = self._find_template_path(action, view)
        if not template_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {action}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template = json.load(f)

        # 验证模板格式
        required_fields = ["action", "weights", "template_sequence", "thresholds"]
        for field in required_fields:
            if field not in template:
                raise ValueError(f"模板格式错误: 缺少字段 {field}")

        self.templates[cache_key] = template
        return template

    def load_template_by_id(self, template_id: str) -> dict:
        """
        按模板 ID 精确加载模板。

        模板 ID 对应 JSON 文件名去掉 .json 后的 stem，例如 squat_template_side_v1。
        优先查找 storage/templates，再查找内置 app/templates。
        """
        safe_template_id = Path(template_id).stem
        if safe_template_id != template_id or any(part in template_id for part in ("..", "/", "\\")):
            raise ValueError(f"无效模板 ID: {template_id}")

        cache_key = f"id:{template_id}"
        if cache_key in self.templates:
            return self.templates[cache_key]

        candidates = [
            self.storage_dir / f"{template_id}.json",
            self.template_dir / f"{template_id}.json",
        ]

        for template_path in candidates:
            if template_path.exists():
                with open(template_path, "r", encoding="utf-8") as f:
                    template = json.load(f)

                required_fields = ["action", "weights", "template_sequence", "thresholds"]
                for field in required_fields:
                    if field not in template:
                        raise ValueError(f"模板格式错误: 缺少字段 {field}")

                self.templates[cache_key] = template
                return template

        raise FileNotFoundError(f"模板文件不存在: {template_id}")

    def _find_template_path(self, action: str, view: Optional[str]) -> Path:
        """
        查找模板文件路径

        只在 storage/templates 目录查找用户自定义模板，不回退到默认模板

        Args:
            action: 动作名称
            view: 拍摄角度

        Returns:
            模板文件路径

        Raises:
            FileNotFoundError: 找不到用户自定义模板时抛出异常
        """
        # 1. 优先查找带拍摄角度的用户模板
        if view:
            # 按版本号降序查找最新版本
            version_patterns = [f"{action}_template_{view}_v*.json", f"{action}_template_{view}.json"]
            for pattern in version_patterns:
                files = sorted(self.storage_dir.glob(pattern), reverse=True)
                if files:
                    return files[0]

        # 2. 查找不带拍摄角度的用户模板
        version_patterns = [f"{action}_template_*_v*.json", f"{action}_template_*.json"]
        for pattern in version_patterns:
            files = sorted(self.storage_dir.glob(pattern), reverse=True)
            if files:
                return files[0]

        # 3. 不再回退到内置默认模板，直接抛出异常
        raise FileNotFoundError(
            f"未找到动作 '{action}' 的用户自定义模板。请先在动作规则页面上传标准动作视频生成模板。"
        )

    def resample_sequence(self, seq: list[float], target_len: int = 50) -> list[float]:
        """
        将序列重采样到指定长度

        Args:
            seq: 原始序列
            target_len: 目标长度

        Returns:
            重采样后的序列
        """
        if not seq:
            return []

        if len(seq) == 1:
            return [seq[0]] * target_len

        # 使用 numpy 进行线性插值
        original_indices = np.linspace(0, len(seq) - 1, len(seq))
        target_indices = np.linspace(0, len(seq) - 1, target_len)
        resampled = np.interp(target_indices, original_indices, seq)

        return resampled.tolist()

    def score_by_template(
        self,
        action: str,
        user_frames: list[dict[str, float]],
        template_id: Optional[str] = None
    ) -> TemplateScoreResult:
        """
        根据标准模板对用户动作进行评分

        Args:
            action: 动作名称
            user_frames: 用户动作的帧序列，每帧包含角度指标

        Returns:
            TemplateScoreResult: 评分结果
        """
        if not user_frames:
            return {
                "score": 0.0,
                "level": "invalid",
                "detail_scores": {},
                "differences": {}
            }

        template = self.load_template_by_id(template_id) if template_id else self.load_template(action)
        if template.get("action") != action:
            raise ValueError(f"模板动作不匹配: {template.get('action')} != {action}")
        weights = template["weights"]
        template_sequence = template["template_sequence"]
        thresholds = template["thresholds"]

        # 提取用户序列
        user_sequences = {}
        for metric in ["knee_angle", "hip_angle", "trunk_angle", "knee_symmetry_diff"]:
            user_sequences[metric] = [frame.get(metric, 0) for frame in user_frames]

        # 重采样到相同长度
        target_len = 50
        resampled_user = {}
        resampled_template = {}

        for metric in ["knee_angle", "hip_angle", "trunk_angle", "knee_symmetry_diff"]:
            resampled_user[metric] = self.resample_sequence(user_sequences[metric], target_len)
            resampled_template[metric] = self.resample_sequence(template_sequence[metric], target_len)

        # 计算各项指标的差异和得分
        detail_scores = {}
        differences = {}

        for metric in ["knee_angle", "hip_angle", "trunk_angle", "knee_symmetry_diff"]:
            user_seq = np.array(resampled_user[metric])
            template_seq = np.array(resampled_template[metric])

            # 计算平均绝对差异
            diff = np.mean(np.abs(user_seq - template_seq))
            differences[metric] = round(float(diff), 1)

            # 将差异转换为分数（差异越小分数越高）
            # 假设差异为0时得100分，差异为30时得0分
            max_diff = 30.0
            raw_score = max(0, 100 - (diff / max_diff) * 100)
            detail_scores[metric] = round(float(raw_score), 1)

        # 按权重计算总分
        total_score = sum(detail_scores[metric] * weights[metric] for metric in weights)
        total_score = round(total_score, 1)

        # 确定等级
        if total_score >= thresholds["excellent"]:
            level = "excellent"
        elif total_score >= thresholds["good"]:
            level = "good"
        elif total_score >= thresholds["fair"]:
            level = "fair"
        else:
            level = "poor"

        return {
            "score": total_score,
            "level": level,
            "detail_scores": detail_scores,
            "differences": differences
        }

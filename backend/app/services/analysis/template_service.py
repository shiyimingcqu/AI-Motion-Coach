"""Template service — scores user frame sequences against stored templates."""

import json
from pathlib import Path
from typing import Optional
import numpy as np


# 全局启用的模板缓存 { action: template_id }
# 由管理员在后台配置，通过 refresh_active_templates 更新
_active_template_map: dict[str, str] = {}


def refresh_active_templates(db_session=None) -> dict[str, str]:
    """从数据库重新加载启用的模板配置到全局缓存。"""
    global _active_template_map
    if db_session is None:
        return _active_template_map
    try:
        from app.models.entities import ActiveTemplateORM
        records = db_session.query(ActiveTemplateORM).all()
        _active_template_map = {r.action: r.template_id for r in records}
    except Exception:
        _active_template_map = {}
    return _active_template_map


def get_active_template_id(action: str) -> str | None:
    """获取指定动作当前启用的模板 ID。"""
    return _active_template_map.get(action)


class TemplateService:
    """Loads templates and scores user frame sequences using DTW-like matching."""

    def __init__(self, template_dir: str = "app/templates", storage_dir: str = "storage/templates"):
        backend_root = Path(__file__).resolve().parents[3]
        repo_root = backend_root.parent
        self._dirs = [
            (backend_root / storage_dir).resolve(),
            (repo_root / storage_dir).resolve(),
            (backend_root / template_dir).resolve(),
            (repo_root / template_dir).resolve(),
        ]
        self.templates: dict[str, dict] = {}

    def _find_template_file(self, action: str, view: str | None = None) -> Path | None:
        if view:
            patterns = [
                f"{action}_template_{view}_v*.json",
                f"{action}_template_{view}.json",
                f"{action}_template_*.json",
                f"{action}_template.json",
            ]
        else:
            patterns = [
                f"{action}_template_*_v*.json",
                f"{action}_template_*.json",
                f"{action}_template.json",
            ]
        for base in self._dirs:
            for pat in patterns:
                files = sorted(base.glob(pat), reverse=True)
                if files:
                    return files[0]
        return None

    def load_template(self, action: str, view: str | None = None) -> dict:
        cache_key = f"{action}_{view}" if view else action
        if cache_key in self.templates:
            return self.templates[cache_key]

        path = self._find_template_file(action, view)
        if not path or not path.exists():
            raise FileNotFoundError(f"No template found for: {action}")

        with open(path, encoding="utf-8") as f:
            tmpl = json.load(f)

        required = {"action", "weights", "template_sequence", "thresholds"}
        missing = required - set(tmpl)
        if missing:
            raise ValueError(f"Template missing fields: {missing}")

        tmpl["_template_id"] = path.stem
        tmpl["_template_path"] = str(path)
        self.templates[cache_key] = tmpl
        return tmpl

    def load_template_by_id(self, template_id: str) -> dict:
        safe = Path(template_id).stem
        if "/" in template_id or "\\" in template_id:
            raise ValueError("Invalid template_id")
        cache_key = f"id:{safe}"
        if cache_key in self.templates:
            return self.templates[cache_key]

        for base in self._dirs:
            p = base / f"{safe}.json"
            if p.exists():
                with open(p, encoding="utf-8") as f:
                    tmpl = json.load(f)
                required = {"action", "weights", "template_sequence", "thresholds"}
                if required - set(tmpl):
                    continue
                tmpl["_template_id"] = p.stem
                tmpl["_template_path"] = str(p)
                self.templates[cache_key] = tmpl
                return tmpl
        raise FileNotFoundError(f"Template not found: {template_id}")

    @staticmethod
    def resample_sequence(seq: list[float], target_len: int = 50) -> list[float]:
        if not seq:
            return []
        if len(seq) == 1:
            return [seq[0]] * target_len
        orig = np.linspace(0, len(seq) - 1, len(seq))
        tgt = np.linspace(0, len(seq) - 1, target_len)
        return np.interp(tgt, orig, seq).tolist()

    def score_by_template(
        self,
        action: str,
        user_frames: list[dict[str, float]],
        template_id: str | None = None,
    ) -> dict:
        if not user_frames:
            return {"score": 0.0, "level": "invalid", "detail_scores": {}, "differences": {}}

        # 如果未指定 template_id，检查是否有管理员启用的模板
        if template_id is None:
            active_id = get_active_template_id(action)
            if active_id:
                template_id = active_id

        template = (
            self.load_template_by_id(template_id)
            if template_id
            else self.load_template(action)
        )
        weights = template["weights"]
        tmpl_seq = template["template_sequence"]
        thresholds = template["thresholds"]

        # Determine which metrics exist in both template and frames
        metrics: list[str] = []
        user_sequences: dict[str, list[float]] = {}
        for m in tmpl_seq:
            vals = [f.get(m, 0.0) for f in user_frames]
            if any(v != 0.0 for v in vals):
                user_sequences[m] = vals
                metrics.append(m)

        if not metrics:
            return {"score": 0.0, "level": "invalid", "detail_scores": {}, "differences": {}}

        target_len = 50
        detail_scores: dict[str, float] = {}
        differences: dict[str, float] = {}

        for m in metrics:
            user_seq = np.array(self.resample_sequence(user_sequences[m], target_len))
            templ_seq = np.array(self.resample_sequence(tmpl_seq[m], target_len))
            diff = float(np.mean(np.abs(user_seq - templ_seq)))
            differences[m] = round(diff, 1)
            max_diff = 30.0
            raw = max(0.0, 100.0 - (diff / max_diff) * 100.0)
            detail_scores[m] = round(float(raw), 1)

        total = sum(detail_scores[m] * weights.get(m, 0.2) for m in metrics)
        total_w = sum(weights.get(m, 0.2) for m in metrics)
        total_score = round(total / total_w, 1) if total_w else 0.0

        if total_score >= thresholds.get("excellent", 90):
            level = "excellent"
        elif total_score >= thresholds.get("good", 75):
            level = "good"
        elif total_score >= thresholds.get("fair", 60):
            level = "fair"
        else:
            level = "poor"

        return {
            "score": total_score,
            "level": level,
            "detail_scores": detail_scores,
            "differences": differences,
        }

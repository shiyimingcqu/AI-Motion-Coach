import json
from pathlib import Path
from typing import Optional

import cv2

from app.services.analysis.analyzers.registry import ANALYZER_REGISTRY
from app.services.analysis.exercise_metrics import (
    build_default_weights,
    get_core_feature_keys,
)
from app.services.analysis.models import NormalizedKeypoint


class TemplateBuilderService:
    """
    从视频生成标准动作模板的服务。
    """

    def __init__(self, storage_root: str = "storage/templates"):
        backend_root = Path(__file__).resolve().parents[3]
        repo_root = backend_root.parent
        candidate = Path(storage_root)
        if candidate.is_absolute():
            self.storage_root = candidate
        else:
            repo_candidate = repo_root / candidate
            self.storage_root = repo_candidate if repo_candidate.exists() else backend_root / candidate
        self.builtin_root = backend_root / "app" / "templates"
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def build_from_video(
        self,
        video_path: str,
        action: str,
        view: str = "side",
        name: Optional[str] = None,
        version: str = "v1",
    ) -> dict:
        if action not in ANALYZER_REGISTRY:
            raise ValueError(
                f"暂不支持动作类型: {action}，支持 {', '.join(sorted(ANALYZER_REGISTRY.keys()))}"
            )

        template_name = name or f"标准{view}视角{action}"
        result = self._extract_features_from_video(video_path, action)

        if result["valid_frames"] < 10:
            raise ValueError(f"有效帧数不足: {result['valid_frames']} 帧，至少需要 10 帧")

        template = self._build_template(
            action=action,
            name=template_name,
            view=view,
            version=version,
            processed_frames=result["processed_frames"],
            valid_frames=result["valid_frames"],
            features=result["features"],
        )

        template_path = self._save_template(template, action, view, version)

        return {
            "template_id": f"{action}_{view}_{version}",
            "name": template_name,
            "action": action,
            "view": view,
            "version": version,
            "processed_frames": result["processed_frames"],
            "valid_frames": result["valid_frames"],
            "template_path": str(template_path).replace("\\", "/"),
            "curves_count": {key: len(values) for key, values in template["template_sequence"].items()},
        }

    def _extract_features_from_video(self, video_path: str, action: str) -> dict:
        capture = cv2.VideoCapture(video_path)
        if not capture.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")

        pose = self._create_pose()
        analyzer = ANALYZER_REGISTRY[action]
        feature_keys = get_core_feature_keys(action)
        features = {feature_key: [] for feature_key in feature_keys}

        processed_frames = 0
        valid_frames = 0

        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break

                processed_frames += 1
                keypoints = self._extract_keypoints_from_frame(frame, pose)

                if not keypoints:
                    continue

                try:
                    metrics = analyzer.extract_features(keypoints)
                except ValueError:
                    continue

                if not all(feature_key in metrics for feature_key in feature_keys):
                    continue

                for feature_key in feature_keys:
                    features[feature_key].append(metrics[feature_key])
                valid_frames += 1
        finally:
            capture.release()
            if pose is not None:
                pose.close()

        return {
            "processed_frames": processed_frames,
            "valid_frames": valid_frames,
            "features": features,
        }

    def _extract_keypoints_from_frame(self, frame, pose) -> dict:
        if pose is None:
            return {}

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb)

        if not result.pose_landmarks:
            return {}

        keypoints = {}
        landmark_names = [
            "nose", "left_eye_inner", "left_eye", "left_eye_outer",
            "right_eye_inner", "right_eye", "right_eye_outer",
            "left_ear", "right_ear", "mouth_left", "mouth_right",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_pinky", "right_pinky",
            "left_index", "right_index", "left_thumb", "right_thumb",
            "left_hip", "right_hip", "left_knee", "right_knee",
            "left_ankle", "right_ankle", "left_heel", "right_heel",
            "left_foot_index", "right_foot_index",
        ]

        for index, name in enumerate(landmark_names):
            if index >= len(result.pose_landmarks.landmark):
                break
            landmark = result.pose_landmarks.landmark[index]
            keypoints[name] = NormalizedKeypoint(
                x=landmark.x,
                y=landmark.y,
                visibility=landmark.visibility,
            )

        return keypoints

    def _build_template(
        self,
        action: str,
        name: str,
        view: str,
        version: str,
        processed_frames: int,
        valid_frames: int,
        features: dict,
    ) -> dict:
        return {
            "action": action,
            "name": name,
            "view": view,
            "version": version,
            "source": {
                "type": "video",
                "processed_frames": processed_frames,
                "valid_frames": valid_frames,
            },
            "weights": build_default_weights(action),
            "template_sequence": features,
            "thresholds": {
                "excellent": 90,
                "good": 75,
                "fair": 60,
            },
        }

    def _save_template(self, template: dict, action: str, view: str, version: str) -> Path:
        filename = f"{action}_template_{view}_{version}.json"
        template_path = self.storage_root / filename

        with open(template_path, "w", encoding="utf-8") as file:
            json.dump(template, file, ensure_ascii=False, indent=2)

        return template_path

    @staticmethod
    def _create_pose():
        try:
            import mediapipe as mp
        except ModuleNotFoundError:
            return None

        return mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def list_templates(self, action: Optional[str] = None) -> list:
        templates = []
        seen_ids = set()

        def append_template(template_file: Path, source: str):
            try:
                with open(template_file, "r", encoding="utf-8") as file:
                    template = json.load(file)

                if action is None or template.get("action") == action:
                    template_id = template_file.stem
                    if template_id in seen_ids:
                        return
                    seen_ids.add(template_id)
                    templates.append({
                        "template_id": template_id,
                        "action": template.get("action"),
                        "name": template.get("name") or template.get("description") or template_id,
                        "view": template.get("view") or "default",
                        "version": template.get("version"),
                        "valid_frames": template.get("source", {}).get("valid_frames", 0),
                        "source": source,
                    })
            except Exception:
                return

        for template_file in self.storage_root.glob("*_template*.json"):
            append_template(template_file, "storage")

        for template_file in self.builtin_root.glob("*_template*.json"):
            append_template(template_file, "builtin")

        return sorted(
            templates,
            key=lambda item: (
                item.get("source") != "storage",
                item.get("version") or "",
                item.get("template_id") or "",
            ),
        )


template_builder_service = TemplateBuilderService()

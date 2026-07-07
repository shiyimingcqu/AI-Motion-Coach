import json
import os
from pathlib import Path
from typing import Optional

import cv2
import mediapipe as mp

from app.services.analysis.analyzers.registry import ANALYZER_CLASSES, get_analyzer
from app.services.analysis.exercise_metrics import (
    build_default_weights,
    get_core_feature_keys,
)
from app.services.analysis.models import NormalizedKeypoint

_LANDMARK_NAMES = [
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

_POSE_CACHE: dict = {"instance": None, "path": None}


def _get_pose():
    """Create or reuse a PoseLandmarker (mp.tasks API)."""
    model_path = os.path.expanduser("~/.pose_eval/pose_landmarker.task")
    if _POSE_CACHE["instance"] is not None and _POSE_CACHE["path"] == model_path:
        return _POSE_CACHE["instance"]

    if not os.path.exists(model_path):
        return None

    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision

    base_options = mp_python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    instance = vision.PoseLandmarker.create_from_options(options)
    _POSE_CACHE["instance"] = instance
    _POSE_CACHE["path"] = model_path
    return instance


class TemplateBuilderService:
    """从视频生成标准动作模板的服务。"""

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
        self, video_path: str, action: str,
        view: str = "side", name: Optional[str] = None, version: str = "v1",
        video_uri: str | None = None,
    ) -> dict:
        if action not in ANALYZER_CLASSES:
            raise ValueError(
                f"暂不支持动作类型: {action}，支持 {', '.join(sorted(ANALYZER_CLASSES.keys()))}"
            )

        template_name = name or f"标准{view}视角{action}"
        result = self._extract_features_from_video(video_path, action)

        if result["valid_frames"] < 10:
            raise ValueError(f"有效帧数不足: {result['valid_frames']} 帧，至少需要 10 帧")

        template = self._build_template(
            action=action, name=template_name, view=view, version=version,
            processed_frames=result["processed_frames"],
            valid_frames=result["valid_frames"],
            features=result["features"],
            pose_replay_frames=result["pose_replay_frames"],
            video_uri=video_uri,
        )

        template_path = self._save_template(template, action, view, version)
        template_id = template_path.stem

        return {
            "template_id": template_id,
            "name": template_name, "action": action,
            "view": view, "version": version,
            "processed_frames": result["processed_frames"],
            "valid_frames": result["valid_frames"],
            "has_video": bool(video_uri),
            "has_pose_replay": bool(result["pose_replay_frames"]),
            "template_path": str(template_path).replace("\\", "/"),
            "curves_count": {key: len(values) for key, values in template["template_sequence"].items()},
        }

    def _extract_features_from_video(self, video_path: str, action: str) -> dict:
        capture = cv2.VideoCapture(video_path)
        if not capture.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")

        pose = _get_pose()
        if pose is None:
            raise RuntimeError("Pose landmarker model not found at ~/.pose_eval/pose_landmarker.task")

        fps = capture.get(cv2.CAP_PROP_FPS) or 30
        analyzer = get_analyzer(action)
        feature_keys = get_core_feature_keys(action)
        features = {feature_key: [] for feature_key in feature_keys}
        pose_replay_frames: list[dict] = []

        processed_frames = 0
        valid_frames = 0

        try:
            frame_index = 0
            while True:
                ok, frame = capture.read()
                if not ok:
                    break

                processed_frames += 1
                timestamp_ms = int(frame_index * 1000 / fps)
                keypoints, replay_landmarks = self._extract_keypoints_from_frame(frame, pose, timestamp_ms)
                frame_index += 1

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
                if replay_landmarks:
                    pose_replay_frames.append({
                        "timestamp_ms": timestamp_ms,
                        "landmarks": replay_landmarks,
                    })
                valid_frames += 1
        finally:
            capture.release()

        return {
            "processed_frames": processed_frames,
            "valid_frames": valid_frames,
            "features": features,
            "pose_replay_frames": pose_replay_frames,
        }

    @staticmethod
    def _extract_keypoints_from_frame(frame, pose, timestamp_ms: int) -> dict:
        if pose is None:
            return {}, []

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = pose.detect_for_video(mp_image, timestamp_ms)

        if not result.pose_landmarks:
            return {}, []

        landmarks = result.pose_landmarks[0]
        keypoints = {}
        replay_landmarks = []
        for index, name in enumerate(_LANDMARK_NAMES):
            if index >= len(landmarks):
                break
            lm = landmarks[index]
            keypoints[name] = NormalizedKeypoint(x=lm.x, y=lm.y, visibility=lm.visibility)
            replay_landmarks.append({
                "x": float(lm.x),
                "y": float(lm.y),
                "z": float(getattr(lm, "z", 0.0) or 0.0),
                "visibility": float(getattr(lm, "visibility", 1.0) or 0.0),
            })
        return keypoints, replay_landmarks

    def _build_template(
        self, action: str, name: str, view: str, version: str,
        processed_frames: int, valid_frames: int, features: dict,
        pose_replay_frames: list[dict] | None = None,
        video_uri: str | None = None,
    ) -> dict:
        return {
            "action": action, "name": name, "view": view, "version": version,
            "source": {"type": "video", "processed_frames": processed_frames, "valid_frames": valid_frames},
            "video_uri": video_uri,
            "pose_replay_frames": pose_replay_frames or [],
            "weights": build_default_weights(action),
            "template_sequence": features,
            "thresholds": {"excellent": 90, "good": 75, "fair": 60},
        }

    def _save_template(self, template: dict, action: str, view: str, version: str) -> Path:
        filename = f"{action}_template_{view}_{version}.json"
        template_path = self.storage_root / filename
        with open(template_path, "w", encoding="utf-8") as file:
            json.dump(template, file, ensure_ascii=False, indent=2)
        return template_path

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
                        "has_video": bool(template.get("video_uri") and Path(template.get("video_uri")).exists()),
                        "has_pose_replay": bool(template.get("pose_replay_frames")),
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

import json
from pathlib import Path
from typing import Optional

import cv2

from app.services.analysis.angle_feature_service import extract_squat_features
from app.services.analysis.models import NormalizedKeypoint


class TemplateBuilderService:
    """
    从视频生成标准动作模板的服务
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
        version: str = "v1"
    ) -> dict:
        """
        从视频生成标准动作模板

        Args:
            video_path: 视频文件路径
            action: 动作类型（如 "squat"）
            view: 拍摄角度（side/front/diagonal）
            name: 模板名称
            version: 版本号

        Returns:
            模板信息字典，包含 template_id, valid_frames, template_path 等

        Raises:
            ValueError: 动作不支持或有效帧不足
        """
        if action != "squat":
            raise ValueError(f"暂不支持动作类型: {action}，当前仅支持 squat")

        # 构建模板名称
        template_name = name or f"标准{view}视角{action}"

        # 处理视频提取关键点和角度
        result = self._extract_features_from_video(video_path)

        if result["valid_frames"] < 10:
            raise ValueError(f"有效帧数不足: {result['valid_frames']} 帧，至少需要 10 帧")

        # 构建模板数据
        template = self._build_template(
            action=action,
            name=template_name,
            view=view,
            version=version,
            processed_frames=result["processed_frames"],
            valid_frames=result["valid_frames"],
            features=result["features"]
        )

        # 保存模板
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
            "curves_count": {k: len(v) for k, v in template["template_sequence"].items()}
        }

    def _extract_features_from_video(self, video_path: str) -> dict:
        """
        从视频中提取角度特征

        Args:
            video_path: 视频文件路径

        Returns:
            包含 processed_frames, valid_frames, features 的字典
        """
        capture = cv2.VideoCapture(video_path)
        if not capture.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")

        pose = self._create_pose()
        features = {
            "knee_angle": [],
            "hip_angle": [],
            "trunk_angle": [],
            "knee_symmetry_diff": []
        }

        processed_frames = 0
        valid_frames = 0

        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break

                processed_frames += 1
                keypoints = self._extract_keypoints_from_frame(frame, pose)

                if keypoints:
                    try:
                        metrics = extract_squat_features(keypoints)
                        features["knee_angle"].append(metrics["knee_angle"])
                        features["hip_angle"].append(metrics["hip_angle"])
                        features["trunk_angle"].append(metrics["trunk_angle"])
                        features["knee_symmetry_diff"].append(metrics["knee_symmetry_diff"])
                        valid_frames += 1
                    except ValueError:
                        # 关键点不完整，跳过该帧
                        pass
        finally:
            capture.release()
            if pose is not None:
                pose.close()

        return {
            "processed_frames": processed_frames,
            "valid_frames": valid_frames,
            "features": features
        }

    def _extract_keypoints_from_frame(self, frame, pose) -> dict:
        """
        从单帧图像提取关键点

        Args:
            frame: 帧图像
            pose: MediaPipe Pose 对象

        Returns:
            关键点字典
        """
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
            "left_foot_index", "right_foot_index"
        ]

        for i, name in enumerate(landmark_names):
            if i < len(result.pose_landmarks.landmark):
                landmark = result.pose_landmarks.landmark[i]
                keypoints[name] = NormalizedKeypoint(
                    x=landmark.x,
                    y=landmark.y,
                    visibility=landmark.visibility
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
        features: dict
    ) -> dict:
        """
        构建模板数据结构

        Args:
            action: 动作类型
            name: 模板名称
            view: 拍摄角度
            version: 版本号
            processed_frames: 处理帧数
            valid_frames: 有效帧数
            features: 角度特征数据

        Returns:
            模板字典
        """
        return {
            "action": action,
            "name": name,
            "view": view,
            "version": version,
            "source": {
                "type": "video",
                "processed_frames": processed_frames,
                "valid_frames": valid_frames
            },
            "weights": {
                "knee_angle": 0.35,
                "hip_angle": 0.25,
                "trunk_angle": 0.2,
                "knee_symmetry_diff": 0.2
            },
            "template_sequence": features,
            "thresholds": {
                "excellent": 90,
                "good": 75,
                "fair": 60
            }
        }

    def _save_template(self, template: dict, action: str, view: str, version: str) -> Path:
        """
        保存模板到文件

        Args:
            template: 模板数据
            action: 动作类型
            view: 拍摄角度
            version: 版本号

        Returns:
            保存的文件路径
        """
        filename = f"{action}_template_{view}_{version}.json"
        template_path = self.storage_root / filename

        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)

        return template_path

    @staticmethod
    def _create_pose():
        """
        创建 MediaPipe Pose 对象

        Returns:
            Pose 对象或 None（如果未安装 mediapipe）
        """
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
        """
        列出所有模板

        Args:
            action: 可选，按动作类型筛选

        Returns:
            模板列表
        """
        templates = []
        seen_ids = set()

        def append_template(template_file: Path, source: str):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template = json.load(f)

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

        return sorted(templates, key=lambda x: (x.get("source") != "storage", x.get("version") or "", x.get("template_id") or ""))


template_builder_service = TemplateBuilderService()

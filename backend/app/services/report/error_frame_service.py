"""Build error/highlight pose snapshots for score-trends UI from session replay and feedback."""

import json
from datetime import timedelta

from app.models.entities import SessionORM
from app.services.analysis.exercise_metrics import get_core_metrics
from app.services.evaluation.calorie_service import get_exercise_display_name
from app.services.evaluation.evaluation_service import build_evaluation, parse_evaluation
from app.services.report.report_service import report_service

LANDMARK_INDEX_TO_PART = {
    0: "head",
    11: "left_shoulder",
    12: "right_shoulder",
    13: "left_elbow",
    14: "right_elbow",
    15: "left_wrist",
    16: "right_wrist",
    23: "left_hip",
    24: "right_hip",
    25: "left_knee",
    26: "right_knee",
    27: "left_ankle",
    28: "right_ankle",
}

PART_LABELS = {
    "head": "头颈部",
    "left_shoulder": "左肩",
    "right_shoulder": "右肩",
    "left_elbow": "左肘",
    "right_elbow": "右肘",
    "left_wrist": "左腕",
    "right_wrist": "右腕",
    "left_hip": "左髋",
    "right_hip": "右髋",
    "left_knee": "左膝",
    "right_knee": "右膝",
    "left_ankle": "左踝",
    "right_ankle": "右踝",
    "torso": "躯干核心",
}

FEATURE_PARTS = {
    "knee_angle": (["left_knee", "right_knee"], "膝关节"),
    "hip_angle": (["left_hip", "right_hip"], "髋关节"),
    "trunk_angle": (["left_shoulder", "right_shoulder", "left_hip", "right_hip"], "躯干"),
    "knee_symmetry_diff": (["left_knee", "right_knee"], "双膝对称"),
    "elbow_angle": (["left_elbow", "right_elbow"], "肘关节"),
    "shoulder_angle": (["left_shoulder", "right_shoulder"], "肩关节"),
    "body_line_angle": (["left_shoulder", "right_shoulder", "left_hip", "right_hip"], "身体直线"),
    "hip_sag_angle": (["left_hip", "right_hip"], "髋部稳定"),
    "neck_angle": (["head", "left_shoulder", "right_shoulder"], "颈部"),
    "shoulder_abduction_angle": (["left_shoulder", "right_shoulder", "left_wrist", "right_wrist"], "肩外展"),
    "leg_spread_angle": (["left_ankle", "right_ankle"], "双腿开合"),
    "wrist_height": (["left_wrist", "right_wrist"], "手腕高度"),
    "ankle_distance": (["left_ankle", "right_ankle"], "脚踝间距"),
    "knee_height": (["left_knee", "right_knee"], "抬膝高度"),
    "knee_raise": (["left_knee", "right_knee"], "提膝幅度"),
    "rotation_offset": (["left_shoulder", "right_shoulder", "left_hip", "right_hip"], "躯干旋转"),
    "symmetry_diff": (["left_shoulder", "right_shoulder", "left_hip", "right_hip"], "左右对称"),
}

ERROR_KEYWORDS = [
    (("膝", "knee"), ["left_knee", "right_knee"]),
    (("髋", "hip", "臀"), ["left_hip", "right_hip"]),
    (("肘", "elbow"), ["left_elbow", "right_elbow"]),
    (("肩", "shoulder"), ["left_shoulder", "right_shoulder"]),
    (("踝", "ankle", "脚"), ["left_ankle", "right_ankle"]),
    (("腕", "wrist", "手"), ["left_wrist", "right_wrist"]),
    (("躯干", "trunk", "腰", "塌腰", "前倾", "核心"), ["torso"]),
    (("头", "颈", "neck"), ["head"]),
]


def _load_json(raw: str | None, default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default


def _keypoints_to_landmarks(keypoints: dict) -> list[dict]:
    name_order = [
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
    landmarks: list[dict] = []
    for name in name_order:
        point = keypoints.get(name)
        if isinstance(point, dict):
            landmarks.append({
                "x": float(point.get("x", 0)),
                "y": float(point.get("y", 0)),
                "z": float(point.get("z", 0)),
                "visibility": float(point.get("visibility", 1)),
            })
        else:
            landmarks.append({"x": 0, "y": 0, "z": 0, "visibility": 0})
    return landmarks


def _normalize_landmarks(raw) -> list[dict] | None:
    if isinstance(raw, list) and len(raw) >= 11:
        normalized = []
        for item in raw[:33]:
            if not isinstance(item, dict):
                return None
            normalized.append({
                "x": float(item.get("x", 0)),
                "y": float(item.get("y", 0)),
                "z": float(item.get("z", 0)),
                "visibility": float(item.get("visibility", 1)),
            })
        while len(normalized) < 33:
            normalized.append({"x": 0, "y": 0, "z": 0, "visibility": 0})
        return normalized
    if isinstance(raw, dict):
        return _keypoints_to_landmarks(raw)
    return None


def _parts_from_errors(errors: list[str]) -> set[str]:
    parts: set[str] = set()
    text = " ".join(errors)
    for keywords, part_keys in ERROR_KEYWORDS:
        if any(kw in text for kw in keywords):
            parts.update(part_keys)
    return parts


def _parts_from_metrics(metrics: dict, exercise: str) -> dict[str, str]:
    """Map metric keys to part evaluation text."""
    comments: dict[str, str] = {}
    for metric in get_core_metrics(exercise):
        value = metrics.get(metric.feature_key)
        if value is None:
            continue
        mapping = FEATURE_PARTS.get(metric.feature_key)
        if not mapping:
            continue
        part_keys, label = mapping
        text = f"{label}当前指标 {metric.label}={value}，建议关注该部位动作控制。"
        for key in part_keys:
            comments[key] = text
    return comments


def _evaluation_parts(session: SessionORM) -> dict[str, str]:
    evaluation = parse_evaluation(session.evaluation_json)
    if not evaluation:
        evaluation = build_evaluation(
            exercise=session.exercise,
            average_score=session.average_score,
            total_count=session.total_count,
            valid_count=session.valid_count,
            error_count=session.error_count,
            duration_seconds=session.duration_seconds,
        )
    comments: dict[str, str] = {}
    dims = evaluation.get("dimension_scores", {})
    metrics = get_core_metrics(session.exercise)
    metric_labels = {m.feature_key: m.label for m in metrics}
    for dim_name, score in dims.items():
        for metric in metrics:
            if metric.label == dim_name:
                mapping = FEATURE_PARTS.get(metric.feature_key)
                if mapping:
                    part_keys, _ = mapping
                    level = "优秀" if score >= 85 else "基本达标" if score >= 70 else "有待加强" if score >= 60 else "需重点改进"
                    text = f"{dim_name}（{score:.0f}分）：{level}。"
                    for key in part_keys:
                        comments[key] = text
                break
        else:
            level = "优秀" if score >= 85 else "基本达标" if score >= 70 else "有待加强" if score >= 60 else "需重点改进"
            comments["torso"] = comments.get("torso", "") + f"{dim_name}（{score:.0f}分）：{level}。"

    for weakness in evaluation.get("weaknesses", []):
        for part in _parts_from_errors([weakness]):
            comments[part] = weakness

    feedback = _load_json(session.feedback_summary, {})
    for item in feedback.get("items", []):
        issue = item.get("issue", "")
        metric = item.get("metric", "")
        suggestion = item.get("suggestion", "")
        text = issue
        if suggestion:
            text = f"{issue}。建议：{suggestion}"
        for part in _parts_from_errors([issue]):
            comments[part] = text
        if metric in FEATURE_PARTS:
            for part in FEATURE_PARTS[metric][0]:
                comments[part] = text

    return comments


HIGHLIGHT_FRAME_SCORE = 80
SESSION_HIGHLIGHT_AVG = 80
SESSION_ERROR_AVG = 80

HIGHLIGHT_PRAISE = [
    "动作完成度很高，姿态标准优美！",
    "这一帧动作非常到位，继续保持！",
    "发力节奏与身体控制都很出色！",
    "高光时刻：动作几近完美！",
]


def _capture_datetime(session: SessionORM, timestamp_ms: int = 0) -> str:
    base = session.created_at
    if not base:
        return ""
    captured = base + timedelta(milliseconds=int(timestamp_ms or 0))
    return captured.strftime("%Y-%m-%d %H:%M:%S")


def _build_body_parts(error_parts: set[str], part_comments: dict[str, str]) -> list[dict]:
    items = []
    for part_id in sorted(error_parts):
        items.append({
            "id": part_id,
            "label": PART_LABELS.get(part_id, part_id),
            "landmark_indices": _landmark_indices_for_part(part_id),
            "evaluation": part_comments.get(part_id, "该部位存在姿态偏差，建议对照标准动作纠正。"),
            "severity": "error",
        })
    return items


def _build_highlight_body_parts(praise: str | None = None) -> list[dict]:
    text = praise or HIGHLIGHT_PRAISE[0]
    part_defs = [
        ("torso", "整体姿态", [11, 12, 23, 24], text),
        ("left_shoulder", "左肩", [11], "肩线稳定，动作舒展"),
        ("right_shoulder", "右肩", [12], "肩线稳定，动作舒展"),
        ("left_knee", "左膝", [25], "膝关节控制到位"),
        ("right_knee", "右膝", [26], "膝关节控制到位"),
        ("left_hip", "左髋", [23], "髋部发力协调"),
        ("right_hip", "右髋", [24], "髋部发力协调"),
    ]
    return [
        {
            "id": part_id,
            "label": label,
            "landmark_indices": indices,
            "evaluation": evaluation,
            "severity": "success",
        }
        for part_id, label, indices, evaluation in part_defs
    ]


def _landmark_indices_for_part(part_id: str) -> list[int]:
    mapping = {
        "head": [0, 7, 8],
        "left_shoulder": [11],
        "right_shoulder": [12],
        "left_elbow": [13],
        "right_elbow": [14],
        "left_wrist": [15],
        "right_wrist": [16],
        "left_hip": [23],
        "right_hip": [24],
        "left_knee": [25],
        "right_knee": [26],
        "left_ankle": [27],
        "right_ankle": [28],
        "torso": [11, 12, 23, 24],
    }
    return mapping.get(part_id, [])


def _pick_replay_landmarks(frames: list, timestamp_ms: int = 0) -> list[dict] | None:
    if not frames:
        return None
    if timestamp_ms:
        pick = min(
            frames,
            key=lambda f: abs(int(f.get("timestamp_ms", 0)) - timestamp_ms) if isinstance(f, dict) else 0,
        )
    else:
        pick = frames[len(frames) // 2] if len(frames) > 1 else frames[0]
    if not isinstance(pick, dict):
        return None
    return _normalize_landmarks(pick.get("landmarks"))


def _attach_replay_landmarks(snapshots: list[dict], frames: list) -> None:
    for snap in snapshots:
        if snap.get("landmarks"):
            continue
        landmarks = _pick_replay_landmarks(frames, int(snap.get("timestamp_ms", 0)))
        if landmarks:
            snap["landmarks"] = landmarks


def _session_snapshots(session: SessionORM) -> list[dict]:
    meta = _load_json(session.pose_replay_meta_json, {})
    stored = meta.get("error_snapshots") or []
    snapshots: list[dict] = []

    part_comments = _evaluation_parts(session)
    exercise_name = get_exercise_display_name(session.exercise)

    for raw in stored:
        landmarks = _normalize_landmarks(raw.get("landmarks") or raw.get("keypoints"))
        errors = raw.get("errors") or raw.get("issues") or []
        score = float(raw.get("score", session.average_score))
        timestamp_ms = int(raw.get("timestamp_ms", 0))
        error_parts = _parts_from_errors(errors)
        error_parts.update(_parts_from_metrics(raw.get("metrics") or {}, session.exercise).keys())
        if not error_parts:
            error_parts = set(_parts_from_errors(
                (parse_evaluation(session.evaluation_json) or {}).get("weaknesses", [])
            ))
        if not error_parts:
            error_parts = {"torso"}

        if not landmarks:
            landmarks = _pick_replay_landmarks(
                _load_json(session.pose_replay_json, []),
                timestamp_ms,
            )

        snapshots.append({
            "session_id": session.session_id,
            "exercise": session.exercise,
            "exercise_name": exercise_name,
            "date": _capture_datetime(session, timestamp_ms),
            "captured_at": _capture_datetime(session, timestamp_ms),
            "frame_type": "error",
            "score": round(score, 1),
            "timestamp_ms": timestamp_ms,
            "errors": errors,
            "landmarks": landmarks,
            "body_parts": _build_body_parts(error_parts, {**part_comments, **_parts_from_metrics(raw.get("metrics") or {}, session.exercise)}),
            "source": meta.get("source", "training"),
        })

    replay_frames = _load_json(session.pose_replay_json, [])
    _attach_replay_landmarks(snapshots, replay_frames)

    if snapshots:
        if all(not snap.get("landmarks") for snap in snapshots) and replay_frames:
            fallback = _make_fallback_frame(
                session,
                snapshots,
                replay_frames,
                float(session.average_score),
            )
            if fallback:
                return [fallback]
        return snapshots

    frames = replay_frames
    if frames:
        pick = frames[len(frames) // 2] if len(frames) > 1 else frames[0]
        landmarks = _normalize_landmarks(pick.get("landmarks"))
        if landmarks:
            weaknesses = (parse_evaluation(session.evaluation_json) or {}).get("weaknesses", [])
            error_parts = _parts_from_errors(weaknesses) or {"torso"}
            feedback = _load_json(session.feedback_summary, {})
            errors = feedback.get("issues", [])[:3]
            timestamp_ms = int(pick.get("timestamp_ms", 0))
            snapshots.append({
                "session_id": session.session_id,
                "exercise": session.exercise,
                "exercise_name": exercise_name,
                "date": _capture_datetime(session, timestamp_ms),
                "captured_at": _capture_datetime(session, timestamp_ms),
                "frame_type": "error",
                "score": round(float(session.average_score), 1),
                "timestamp_ms": timestamp_ms,
                "errors": errors,
                "landmarks": landmarks,
                "body_parts": _build_body_parts(error_parts, part_comments),
                "source": meta.get("source", "replay_fallback"),
            })
    elif session.error_count > 0 or session.average_score < SESSION_ERROR_AVG:
        weaknesses = (parse_evaluation(session.evaluation_json) or {}).get("weaknesses", [])
        error_parts = _parts_from_errors(weaknesses) or {"torso"}
        feedback = _load_json(session.feedback_summary, {})
        snapshots.append({
            "session_id": session.session_id,
            "exercise": session.exercise,
            "exercise_name": exercise_name,
            "date": _capture_datetime(session, 0),
            "captured_at": _capture_datetime(session, 0),
            "frame_type": "error",
            "score": round(float(session.average_score), 1),
            "timestamp_ms": 0,
            "errors": feedback.get("issues", [])[:3] or ["本次训练存在需改进的动作细节"],
            "landmarks": None,
            "body_parts": _build_body_parts(error_parts, part_comments),
            "source": "evaluation_only",
        })

    if not snapshots and float(session.average_score) < SESSION_ERROR_AVG:
        feedback = _load_json(session.feedback_summary, {})
        snapshots.append({
            "session_id": session.session_id,
            "exercise": session.exercise,
            "exercise_name": exercise_name,
            "date": _capture_datetime(session, 0),
            "captured_at": _capture_datetime(session, 0),
            "frame_type": "error",
            "score": round(float(session.average_score), 1),
            "timestamp_ms": 0,
            "errors": feedback.get("issues", [])[:3] or ["本次训练平均分偏低，建议对照标准动作纠正"],
            "landmarks": None,
            "body_parts": _build_body_parts({"torso"}, part_comments),
            "source": "score_fallback",
        })

    _attach_replay_landmarks(snapshots, replay_frames)
    return snapshots


def _make_fallback_frame(session: SessionORM, snapshots: list[dict], replay_frames: list, score: float) -> dict | None:
    """Ensure a displayable frame exists when session score is within threshold."""
    landmarks = None
    timestamp_ms = 0
    errors: list = []

    for snap in sorted(snapshots, key=lambda s: float(s.get("score", 100))):
        lm = snap.get("landmarks")
        if lm:
            landmarks = lm
            timestamp_ms = int(snap.get("timestamp_ms", 0))
            errors = snap.get("errors") or []
            break

    if not landmarks:
        landmarks = _pick_replay_landmarks(replay_frames, 0)
        if replay_frames:
            timestamp_ms = int(replay_frames[len(replay_frames) // 2].get("timestamp_ms", 0))

    if not landmarks:
        return None

    part_comments = _evaluation_parts(session)
    exercise_name = get_exercise_display_name(session.exercise)
    weaknesses = (parse_evaluation(session.evaluation_json) or {}).get("weaknesses", [])
    error_parts = _parts_from_errors(weaknesses) or {"torso"}
    if not errors:
        feedback = _load_json(session.feedback_summary, {})
        errors = feedback.get("issues", [])[:3] or [f"本次训练评分 {score:.0f} 分，建议对照标准动作改进"]

    return {
        "session_id": session.session_id,
        "exercise": session.exercise,
        "exercise_name": exercise_name,
        "date": _capture_datetime(session, timestamp_ms),
        "captured_at": _capture_datetime(session, timestamp_ms),
        "frame_type": "error",
        "score": round(float(score), 1),
        "timestamp_ms": timestamp_ms,
        "errors": errors,
        "landmarks": landmarks,
        "body_parts": _build_body_parts(error_parts, part_comments),
        "source": "session_fallback",
    }


def _resolve_session_slot_frames(session: SessionORM, picked: list[dict], raw_snapshots: list[dict]) -> tuple[dict | None, dict | None, dict | None]:
    replay_frames = _load_json(session.pose_replay_json, [])
    avg = float(session.average_score)

    frame_mid = next((f for f in picked if f.get("score_band") == "60-80"), None)
    frame_low = next((f for f in picked if f.get("score_band") == "below-60"), None)
    frame_any = min(picked, key=lambda f: float(f.get("score", 100))) if picked else None

    for frame in (frame_mid, frame_low, frame_any):
        if frame and not frame.get("landmarks"):
            _attach_replay_landmarks([frame], replay_frames)

    if avg < SESSION_ERROR_AVG:
        if not frame_any or not frame_any.get("landmarks"):
            frame_any = _make_fallback_frame(session, raw_snapshots, replay_frames, avg) or frame_any
        if 60 <= avg < 80 and (not frame_mid or not frame_mid.get("landmarks")):
            frame_mid = frame_any or _make_fallback_frame(session, raw_snapshots, replay_frames, avg)
        if avg < 60 and (not frame_low or not frame_low.get("landmarks")):
            frame_low = frame_any or _make_fallback_frame(session, raw_snapshots, replay_frames, avg)

    return frame_mid, frame_low, frame_any


def _session_highlight_snapshots(session: SessionORM) -> list[dict]:
    meta = _load_json(session.pose_replay_meta_json, {})
    stored = meta.get("highlight_snapshots") or []
    snapshots: list[dict] = []
    exercise_name = get_exercise_display_name(session.exercise)

    for raw in stored:
        landmarks = _normalize_landmarks(raw.get("landmarks"))
        if not landmarks:
            continue
        score = float(raw.get("score", session.average_score))
        timestamp_ms = int(raw.get("timestamp_ms", 0))
        praise = raw.get("praise") or raw.get("message") or HIGHLIGHT_PRAISE[0]
        snapshots.append({
            "session_id": session.session_id,
            "exercise": session.exercise,
            "exercise_name": exercise_name,
            "date": _capture_datetime(session, timestamp_ms),
            "captured_at": _capture_datetime(session, timestamp_ms),
            "frame_type": "highlight",
            "score": round(score, 1),
            "timestamp_ms": timestamp_ms,
            "errors": [],
            "praise": praise,
            "landmarks": landmarks,
            "body_parts": _build_highlight_body_parts(praise),
            "source": meta.get("source", "training"),
        })

    if snapshots:
        return snapshots

    if session.average_score < SESSION_HIGHLIGHT_AVG:
        return []

    frames = _load_json(session.pose_replay_json, [])
    if not frames:
        return []

    best = max(frames, key=lambda f: float(f.get("score", session.average_score) if isinstance(f, dict) else session.average_score))
    pick = best if isinstance(best, dict) else frames[len(frames) // 2]
    landmarks = _normalize_landmarks(pick.get("landmarks"))
    if not landmarks:
        pick = frames[len(frames) // 2] if len(frames) > 1 else frames[0]
        landmarks = _normalize_landmarks(pick.get("landmarks"))
    if not landmarks:
        return []

    timestamp_ms = int(pick.get("timestamp_ms", 0))
    praise = "本次训练整体表现优秀，值得表扬！"
    snapshots.append({
        "session_id": session.session_id,
        "exercise": session.exercise,
        "exercise_name": exercise_name,
        "date": _capture_datetime(session, timestamp_ms),
        "captured_at": _capture_datetime(session, timestamp_ms),
        "frame_type": "highlight",
        "score": round(float(session.average_score), 1),
        "timestamp_ms": timestamp_ms,
        "errors": [],
        "praise": praise,
        "landmarks": landmarks,
        "body_parts": _build_highlight_body_parts(praise),
        "source": meta.get("source", "replay_fallback"),
    })
    return snapshots


def _pick_session_band_frames(session_frames: list[dict]) -> list[dict]:
    """Each session keeps at most one lowest frame in [60, 80) and one below 60."""
    if not session_frames:
        return []

    def score_of(frame: dict) -> float:
        return float(frame.get("score", 100))

    band_mid = [f for f in session_frames if 60 <= score_of(f) < 80]
    band_low = [f for f in session_frames if score_of(f) < 60]
    picked: list[dict] = []

    if band_mid:
        best = min(band_mid, key=score_of)
        best = {**best, "score_band": "60-80"}
        picked.append(best)
    if band_low:
        worst = min(band_low, key=score_of)
        worst = {**worst, "score_band": "below-60"}
        picked.append(worst)

    if not picked:
        below_80 = [f for f in session_frames if score_of(f) < 80]
        if below_80:
            fallback = min(below_80, key=score_of)
            band = "60-80" if 60 <= score_of(fallback) < 80 else "below-60"
            picked.append({**fallback, "score_band": band})

    return picked


def _balance_frames_by_exercise(frames: list[dict], limit: int) -> list[dict]:
    """Round-robin across exercises so one action type does not dominate the list."""
    if not frames:
        return []

    buckets: dict[str, list[dict]] = {}
    for frame in frames:
        key = frame.get("exercise") or "unknown"
        buckets.setdefault(key, []).append(frame)

    for bucket in buckets.values():
        bucket.sort(key=lambda f: (f.get("captured_at", ""), f.get("timestamp_ms", 0)), reverse=True)

    balanced: list[dict] = []
    exercises = sorted(buckets.keys())
    while len(balanced) < limit and exercises:
        progressed = False
        for exercise in exercises:
            bucket = buckets.get(exercise) or []
            if not bucket:
                continue
            balanced.append(bucket.pop(0))
            progressed = True
            if len(balanced) >= limit:
                break
        if not progressed:
            break
    return balanced


class ErrorFrameService:
    THRESHOLDS = [80, 60]

    def list_error_frames(
        self,
        user_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        exercise: str | None = None,
        include_all_users: bool = False,
        limit: int = 120,
        session_scan: int = 200,
    ) -> dict:
        sessions = report_service._query_sessions(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            include_all_users=include_all_users,
            exercise=exercise,
        )
        all_frames: list[dict] = []
        session_slots: list[dict] = []
        for session in sessions[:session_scan]:
            raw_frames = _session_snapshots(session)
            picked = _pick_session_band_frames(raw_frames)
            all_frames.extend(picked)

            frame_mid, frame_low, frame_any = _resolve_session_slot_frames(session, picked, raw_frames)
            captured = session.created_at.strftime("%Y-%m-%d %H:%M:%S") if session.created_at else ""

            session_slots.append({
                "session_id": session.session_id,
                "exercise": session.exercise,
                "exercise_name": get_exercise_display_name(session.exercise),
                "average_score": round(float(session.average_score), 1),
                "captured_at": captured,
                "frame_mid": frame_mid,
                "frame_low": frame_low,
                "frame_any": frame_any,
            })

        all_frames.sort(key=lambda f: (f.get("captured_at", ""), f.get("timestamp_ms", 0)), reverse=True)

        grouped = {
            "80": [f for f in all_frames if 60 <= float(f.get("score", 100)) < 80],
            "60": [f for f in all_frames if float(f.get("score", 100)) < 60],
        }

        latest_session_id = sessions[0].session_id if sessions else None
        return {
            "items": all_frames,
            "session_slots": session_slots,
            "highlights": [],
            "grouped_by_threshold": grouped,
            "thresholds": self.THRESHOLDS,
            "latest_session_id": latest_session_id,
            "total": len(session_slots),
            "highlight_total": 0,
        }


def ensure_meta_error_snapshots(
    meta: dict | None,
    replay_frames: list[dict] | None,
    session_score: float,
) -> dict:
    """Guarantee error_snapshots with landmarks exist for sub-threshold sessions."""
    payload = dict(meta or {})
    snapshots = list(payload.get("error_snapshots") or [])

    if any(
        isinstance(item.get("landmarks"), list) and len(item["landmarks"]) >= 11
        for item in snapshots
    ):
        payload["error_snapshots"] = snapshots[-30:]
        return payload

    frames = replay_frames or []
    score = float(session_score)
    if score >= SESSION_ERROR_AVG or not frames:
        payload["error_snapshots"] = snapshots[-30:]
        return payload

    candidates: list[tuple[dict, list]] = []
    for frame in frames:
        landmarks = _normalize_landmarks(frame.get("landmarks"))
        if landmarks:
            candidates.append((frame, landmarks))

    if not candidates:
        payload["error_snapshots"] = snapshots[-30:]
        return payload

    pick_frame, pick_landmarks = candidates[len(candidates) // 2]
    snapshots.append({
        "timestamp_ms": int(pick_frame.get("timestamp_ms", 0)),
        "score": round(score, 1),
        "landmarks": pick_landmarks,
        "errors": [f"本次训练平均分 {score:.0f} 分低于 {SESSION_ERROR_AVG} 分阈值"],
        "capture_type": "replay_derived",
    })
    payload["error_snapshots"] = snapshots[-30:]
    return payload


error_frame_service = ErrorFrameService()


def extract_video_error_snapshots(frame_results: list[dict], session_score: float) -> list[dict]:
    snapshots: list[dict] = []
    for frame in frame_results:
        score = float(frame.get("score", session_score))
        errors = frame.get("errors") or frame.get("issues") or []
        landmarks = _normalize_landmarks(frame.get("keypoints") or frame.get("landmarks"))
        if not landmarks:
            continue
        visible = sum(1 for lm in landmarks if lm.get("visibility", 0) > 0.3)
        if visible < 8:
            continue
        if errors or score < SESSION_ERROR_AVG:
            snapshots.append({
                "timestamp_ms": int(frame.get("frame_index", 0)) * 100,
                "score": score,
                "landmarks": landmarks,
                "errors": errors[:5],
                "metrics": frame.get("metrics") or frame.get("features") or {},
            })
    if not snapshots and session_score < SESSION_ERROR_AVG and frame_results:
        for frame in reversed(frame_results):
            landmarks = _normalize_landmarks(frame.get("keypoints") or frame.get("landmarks"))
            if landmarks:
                snapshots.append({
                    "timestamp_ms": int(frame.get("frame_index", 0)) * 100,
                    "score": session_score,
                    "landmarks": landmarks,
                    "errors": ["本次训练平均分偏低，建议对照反馈重点改进"],
                    "capture_type": "session_summary",
                })
                break
    return snapshots[-50:]


def extract_video_highlight_snapshots(frame_results: list[dict], session_score: float) -> list[dict]:
    snapshots: list[dict] = []
    for frame in frame_results:
        score = float(frame.get("score", session_score))
        landmarks = _normalize_landmarks(frame.get("keypoints") or frame.get("landmarks"))
        if not landmarks or score < HIGHLIGHT_FRAME_SCORE:
            continue
        visible = sum(1 for lm in landmarks if lm.get("visibility", 0) > 0.3)
        if visible < 8:
            continue
        snapshots.append({
            "timestamp_ms": int(frame.get("frame_index", 0)) * 100,
            "score": score,
            "landmarks": landmarks,
            "praise": HIGHLIGHT_PRAISE[len(snapshots) % len(HIGHLIGHT_PRAISE)],
        })
    if not snapshots and session_score >= SESSION_HIGHLIGHT_AVG and frame_results:
        best = max(frame_results, key=lambda f: float(f.get("score", session_score)))
        landmarks = _normalize_landmarks(best.get("keypoints"))
        if landmarks:
            snapshots.append({
                "timestamp_ms": int(best.get("frame_index", 0)) * 100,
                "score": session_score,
                "landmarks": landmarks,
                "praise": "本次训练整体表现优秀，值得表扬！",
                "capture_type": "session_summary",
            })
    return snapshots[-15:]

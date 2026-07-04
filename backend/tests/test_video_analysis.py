from pathlib import Path

import cv2
import numpy as np

from app.services.analysis.models import NormalizedKeypoint
from app.services.video.video_analysis_service import video_analysis_service


def _make_test_video(path: Path):
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        8,
        (160, 120),
    )
    for index in range(6):
        frame = np.zeros((120, 160, 3), dtype=np.uint8)
        cv2.circle(frame, (40 + index * 12, 60), 18, (0, 220, 120), -1)
        writer.write(frame)
    writer.release()


def test_video_analysis_generates_readable_output_video(tmp_path):
    source = tmp_path / "source.mp4"
    _make_test_video(source)

    result = video_analysis_service.analyze_video(
        source_uri=str(source),
        exercise="squat",
    )

    output = Path(result["output_uri"])
    assert output.exists()
    assert output != source
    assert output.suffix == ".webm"

    capture = cv2.VideoCapture(str(output))
    ok, frame = capture.read()
    capture.release()

    assert ok
    assert frame is not None


def test_realtime_video_test_returns_frame_results_and_summary(tmp_path):
    source = tmp_path / "source.mp4"
    _make_test_video(source)
    shoulders = {
        "left_shoulder": NormalizedKeypoint(x=0.45, y=0.20, visibility=0.99),
        "right_shoulder": NormalizedKeypoint(x=0.55, y=0.20, visibility=0.99),
    }
    frames = [
        {
            **shoulders,
            "left_hip": NormalizedKeypoint(x=0.45, y=0.72, visibility=0.99),
            "left_knee": NormalizedKeypoint(x=0.47, y=0.66, visibility=0.99),
            "left_ankle": NormalizedKeypoint(x=0.47, y=0.82, visibility=0.99),
            "right_hip": NormalizedKeypoint(x=0.55, y=0.72, visibility=0.99),
            "right_knee": NormalizedKeypoint(x=0.53, y=0.66, visibility=0.99),
            "right_ankle": NormalizedKeypoint(x=0.53, y=0.82, visibility=0.99),
        },
        {
            **shoulders,
            "left_hip": NormalizedKeypoint(x=0.45, y=0.24, visibility=0.99),
            "left_knee": NormalizedKeypoint(x=0.47, y=0.58, visibility=0.99),
            "left_ankle": NormalizedKeypoint(x=0.47, y=0.82, visibility=0.99),
            "right_hip": NormalizedKeypoint(x=0.55, y=0.24, visibility=0.99),
            "right_knee": NormalizedKeypoint(x=0.53, y=0.58, visibility=0.99),
            "right_ankle": NormalizedKeypoint(x=0.53, y=0.82, visibility=0.99),
        },
    ]

    def keypoint_extractor(frame, pose):
        return frames.pop(0) if frames else {}

    result = video_analysis_service.run_realtime_video_test(
        source_uri=str(source),
        exercise="squat",
        max_frames=2,
        keypoint_extractor=keypoint_extractor,
    )

    assert result["exercise"] == "squat"
    assert result["processed_frames"] == 2
    assert result["frames"][1]["count"] == 1
    assert result["summary"]["total_count"] == 1

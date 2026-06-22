from pathlib import Path

import cv2
import numpy as np

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

    output_uri = video_analysis_service.analyze_video(
        source_uri=str(source),
        exercise="squat",
    )

    output = Path(output_uri)
    assert output.exists()
    assert output != source

    capture = cv2.VideoCapture(str(output))
    ok, frame = capture.read()
    capture.release()

    assert ok
    assert frame is not None

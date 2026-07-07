from app.services.pose.engine import PoseEngine


class YoloPoseEngine(PoseEngine):
    def infer(self, frame):
        raise NotImplementedError("YOLO-Pose engine is reserved for phase two.")

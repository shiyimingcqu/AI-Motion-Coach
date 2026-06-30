"""Lunge analyzer — stage detection, angle scoring, and DTW final scoring."""

from app.services.analysis.analyzers.base_analyzer import (BaseExerciseAnalyzer, Keypoints, calculate_angle)
from app.services.analysis.template_service import TemplateService

REQUIRED = {"left_shoulder","right_shoulder","left_hip","right_hip","left_knee","right_knee","left_ankle","right_ankle"}

LUNGE_TEMPLATE_SEQUENCE = {"knee_angle":[170,140,110,95,90,110,140,170],"hip_angle":[175,155,130,115,105,130,155,175],"trunk_angle":[5,8,12,15,15,12,8,5]}
DTW_FEATURE_WEIGHTS = {"knee_angle":0.4,"hip_angle":0.3,"trunk_angle":0.2,"knee_symmetry_diff":0.1}

class LungeAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "lunge"

    def __init__(self, smooth_window=5):
        super().__init__(smooth_window)
        self.template_service = TemplateService()
        self.current_rep_frames = []
        self.last_rep_result = None
        self._rep_started = False
        self._seen_bottom = False

    def extract_features(self, landmarks):
        if not REQUIRED.issubset(landmarks): raise ValueError("Missing keypoints")
        lk = calculate_angle(landmarks["left_hip"].to_tuple(),landmarks["left_knee"].to_tuple(),landmarks["left_ankle"].to_tuple())
        rk = calculate_angle(landmarks["right_hip"].to_tuple(),landmarks["right_knee"].to_tuple(),landmarks["right_ankle"].to_tuple())
        knee = min(lk,rk)  # 用更弯的那条腿
        lh = calculate_angle(landmarks["left_shoulder"].to_tuple(),landmarks["left_hip"].to_tuple(),landmarks["left_knee"].to_tuple())
        rh = calculate_angle(landmarks["right_shoulder"].to_tuple(),landmarks["right_hip"].to_tuple(),landmarks["right_knee"].to_tuple())
        hip = (lh+rh)/2
        hx=(landmarks["left_hip"].x+landmarks["right_hip"].x)/2
        hy=(landmarks["left_hip"].y+landmarks["right_hip"].y)/2
        sx=(landmarks["left_shoulder"].x+landmarks["right_shoulder"].x)/2
        sy=(landmarks["left_shoulder"].y+landmarks["right_shoulder"].y)/2
        trunk = calculate_angle((hx,hy-0.1),(hx,hy),(sx,sy))
        return {"knee_angle":round(knee,1),"hip_angle":round(hip,1),"trunk_angle":round(trunk,1),"torso_lean":round(trunk,1),"knee_symmetry_diff":round(abs(lk-rk),1)}

    def detect_phase(self, features, state):
        knee = features.get("knee_angle",170)
        prev = state.get("prev_knee",knee)
        delta = knee - prev
        state["prev_knee"] = knee
        if knee > 155: return "standing"
        if 60 <= knee <= 110 and abs(delta) <= 3: return "bottom"
        if delta < -2: return "down"
        if delta > 2: return "up"
        return "down"

    def score_frame(self, features, phase):
        rules = {"standing":{"knee_angle":170,"hip_angle":175,"trunk_angle":5},"down":{"knee_angle":140,"hip_angle":155,"trunk_angle":10},"bottom":{"knee_angle":90,"hip_angle":105,"trunk_angle":15},"up":{"knee_angle":140,"hip_angle":155,"trunk_angle":10}}
        t = rules.get(phase, rules["standing"])
        ds = {k:self._metric_score(v,t.get(k,0),45) for k,v in features.items() if k in t}
        score = round(sum(ds.values())/len(ds),1) if ds else 0
        return {"score":score,"issues":[],"detail_scores":ds,"feedback":[]}

    def analyze_frame(self, landmarks, state):
        f = self.extract_features(landmarks)
        phase = self.detect_phase(f, state); prev_stage = self.stage
        self.feature_history.append(f); s = self._smooth_features()
        sr = self.score_frame(s, phase)

        if prev_stage in ("bottom","down") and phase in ("up","standing"):
            self.count += 1
            if len(sr["issues"])==0: self.valid_count += 1
            self.scores_history.append(sr["score"])

        self._track_rep_motion(s, phase)
        is_rep = self._is_rep_finished(prev_stage, phase)
        self.previous_stage = prev_stage; self.stage = phase

        r = {"exercise_type":self.exercise_type,"phase":phase,"stage":phase,"count":self.count,"valid_count":self.valid_count,"features":s,"metrics":s,"score":sr["score"],"current_score":sr["score"],"issues":sr["issues"],"errors":sr["issues"],"feedback":sr["feedback"],"detail_scores":sr["detail_scores"],"is_rep_finished":is_rep}

        if is_rep:
            rr = self._score_completed_rep()
            self.last_rep_result = rr
            if rr["score"]>=75: self.valid_count = min(self.valid_count+1, self.count)
            r.update({"stage":"finished","rep_score":rr["score"],"score":rr["score"],"feedback":rr["feedback"],"errors":rr["feedback"],"detail":rr["detail"],"level":rr["level"]})
            self._reset_rep_state()
        return r

    def _track_rep_motion(self, f, phase):
        if phase in {"down","bottom"}: self._rep_started = True
        if phase == "bottom": self._seen_bottom = True
        if self._rep_started:
            self.current_rep_frames.append({"knee_angle":f.get("knee_angle",0),"hip_angle":f.get("hip_angle",0),"trunk_angle":f.get("trunk_angle",0),"knee_symmetry_diff":f.get("knee_symmetry_diff",0)})

    def _is_rep_finished(self, ps, phase):
        return self._rep_started and self._seen_bottom and phase=="standing" and ps in ("up","bottom")

    def _score_completed_rep(self):
        fs = self.current_rep_frames
        if len(fs)<2: return {"score":0,"level":"invalid","feedback":["数据不足"],"detail":{}}
        wd=0;tw=0;diffs={}
        for m,w in DTW_FEATURE_WEIGHTS.items():
            if m=="knee_symmetry_diff": continue
            us=[f.get(m,0) for f in fs]
            dist=self.template_service.dtw_distance(us, LUNGE_TEMPLATE_SEQUENCE.get(m,[]))
            diffs[m]=round(dist,1); wd+=dist*w; tw+=w
        ds=wd/tw if tw else 0; dt=round(max(0,min(100,100-ds*2.5)),1)
        mk=max(f.get("knee_angle",0) for f in fs); mn=min(f.get("knee_angle",0) for f in fs)
        kp=round(max(0,min(100,100-max(0,170-mk)*1.5-max(0,mn-60)*2)),1)
        fs2=round(dt*0.6+kp*0.3+85*0.1,1)
        lv="excellent" if fs2>=90 else "good" if fs2>=75 else "normal" if fs2>=60 else "poor"
        return {"score":fs2,"level":lv,"feedback":[],"detail":{"similarity_score":dt,"dtw_distance":round(ds,1),"key_posture_score":kp,"differences":diffs}}

    def _reset_rep_state(self):
        self.current_rep_frames = []; self._rep_started = False; self._seen_bottom = False

    def get_session_summary(self):
        s = super().get_session_summary()
        if self.last_rep_result: s["last_rep_score"] = self.last_rep_result["score"]
        return s

    @staticmethod
    def _metric_score(v,t,tol): return round(max(0,min(100,100-abs(v-t)/tol*100)),1)

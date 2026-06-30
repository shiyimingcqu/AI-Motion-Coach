"""High-knees analyzer — knee height tracking and DTW final scoring."""

import math
from app.services.analysis.analyzers.base_analyzer import (BaseExerciseAnalyzer, Keypoints, calculate_angle)
from app.services.analysis.template_service import TemplateService

REQUIRED = {"left_shoulder","right_shoulder","left_hip","right_hip","left_knee","right_knee","left_ankle","right_ankle"}
HK_TEMPLATE = {"knee_height":[0.02,0.18,0.02,0.18,0.02],"knee_angle":[175,100,175,100,175]}
DTW_WEIGHTS = {"knee_height":0.6,"knee_angle":0.4}

class HighKneesAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "high_knees"

    def __init__(self, smooth_window=5):
        super().__init__(smooth_window)
        self.template_service = TemplateService()
        self.current_rep_frames = []
        self._left_up = False
        self._right_up = False

    def extract_features(self, landmarks):
        if not REQUIRED.issubset(landmarks): raise ValueError("Missing keypoints")
        lh=landmarks["left_hip"]; rh=landmarks["right_hip"]; hy=(lh.y+rh.y)/2
        lk=landmarks["left_knee"]; rk=landmarks["right_knee"]
        lkh=hy-lk.y; rkh=hy-rk.y
        knee_h=(lkh+rkh)/2
        lka=calculate_angle(lh.to_tuple(),lk.to_tuple(),landmarks["left_ankle"].to_tuple())
        rka=calculate_angle(rh.to_tuple(),rk.to_tuple(),landmarks["right_ankle"].to_tuple())
        return {"knee_height":round(knee_h,4),"knee_angle":round((lka+rka)/2,1),"left_knee_h":round(lkh,4),"right_knee_h":round(rkh,4)}

    def detect_phase(self, features, state):
        lh=features.get("left_knee_h",0); rh=features.get("right_knee_h",0)
        if lh>0.12: return "left_up"
        if rh>0.12: return "right_up"
        if lh<0.04 and rh<0.04: return "stand"
        return "switch"

    def score_frame(self, features, phase):
        kh=features.get("knee_height",0)
        s=round(max(0,min(100,kh/0.2*100)),1)
        return {"score":s,"issues":[],"detail_scores":{"knee_height":s},"feedback":[]}

    def analyze_frame(self, landmarks, state):
        f=self.extract_features(landmarks); phase=self.detect_phase(f,state); ps=self.stage
        self.feature_history.append(f); s=self._smooth_features(); sr=self.score_frame(s,phase)

        if ps in ("left_up","right_up","switch") and phase=="stand":
            self.count+=1
            if self._left_up and self._right_up: self.valid_count+=1
            self.scores_history.append(sr["score"])

        self._track(s,phase); is_rep=self._is_rep(ps,phase)
        self.previous_stage=ps; self.stage=phase

        r={"exercise_type":self.exercise_type,"phase":phase,"stage":phase,"count":self.count,"valid_count":self.valid_count,"features":s,"metrics":s,"score":sr["score"],"current_score":sr["score"],"issues":[],"errors":[],"feedback":[],"detail_scores":sr["detail_scores"],"is_rep_finished":is_rep}
        if is_rep:
            rr=self._dwt_score()
            if rr["score"]>=75: self.valid_count=min(self.valid_count+1,self.count)
            r.update({"stage":"finished","rep_score":rr["score"],"score":rr["score"],"feedback":[],"errors":[],"detail":rr["detail"],"level":rr["level"]})
            self._reset()
        return r

    def _track(self,f,phase):
        if phase=="left_up": self._left_up=True
        if phase=="right_up": self._right_up=True
        self.current_rep_frames.append({"knee_height":f.get("knee_height",0),"knee_angle":f.get("knee_angle",0)})

    def _is_rep(self,ps,phase): return (self._left_up and self._right_up) and phase=="stand" and ps in ("left_up","right_up","switch")

    def _dwt_score(self):
        fs=self.current_rep_frames
        if len(fs)<2: return {"score":0,"level":"invalid","feedback":["数据不足"],"detail":{}}
        wd=0;tw=0
        for m,w in DTW_WEIGHTS.items():
            us=[f.get(m,0) for f in fs]; dist=self.template_service.dtw_distance(us,HK_TEMPLATE.get(m,[]))
            wd+=dist*w; tw+=w
        ds=wd/tw if tw else 0; dt=round(max(0,min(100,100-ds*2.5)),1)
        mx=max(f.get("knee_height",0) for f in fs)
        kp=round(max(0,min(100,mx/0.2*100)),1)
        fs2=round(dt*0.6+kp*0.3+85*0.1,1)
        lv="excellent" if fs2>=90 else "good" if fs2>=75 else "normal" if fs2>=60 else "poor"
        return {"score":fs2,"level":lv,"feedback":[],"detail":{"similarity_score":dt,"dtw_distance":round(ds,1),"key_posture_score":kp}}

    def _reset(self): self.current_rep_frames=[]; self._left_up=False; self._right_up=False

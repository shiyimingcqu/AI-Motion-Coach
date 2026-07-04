"""Glute-bridge analyzer — hip extension tracking and DTW final scoring."""

from app.services.analysis.analyzers.base_analyzer import (BaseExerciseAnalyzer, Keypoints, calculate_angle)
from app.services.analysis.template_service import TemplateService

REQUIRED = {"left_shoulder","right_shoulder","left_hip","right_hip","left_knee","right_knee","left_ankle","right_ankle"}
GLUTE_TEMPLATE = {"hip_angle":[90,105,135,165,175,165,135,105,90],"body_line_angle":[20,15,8,3,2,3,8,15,20]}
DTW_WEIGHTS = {"hip_angle":0.6,"body_line_angle":0.4}

class GluteBridgeAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "glute_bridge"

    def __init__(self, smooth_window=5):
        super().__init__(smooth_window)
        self.template_service = TemplateService()
        self.current_rep_frames = []
        self._rep_started = False
        self._seen_top = False

    def extract_features(self, landmarks):
        if not REQUIRED.issubset(landmarks): raise ValueError("Missing keypoints")
        lv=landmarks["left_shoulder"].visibility; rv=landmarks["right_shoulder"].visibility
        side="left" if lv>=rv else "right"
        s=landmarks[f"{side}_shoulder"]; h=landmarks[f"{side}_hip"]; k=landmarks[f"{side}_knee"]
        ha=calculate_angle(s.to_tuple(),h.to_tuple(),k.to_tuple())
        bl=180-calculate_angle(s.to_tuple(),h.to_tuple(),landmarks[f"{side}_ankle"].to_tuple())
        return {"hip_angle":round(ha,1),"body_line_angle":round(bl,1)}

    def detect_phase(self, features, state):
        hip=features.get("hip_angle",90); prev=state.get("prev_hip",hip)
        delta=hip-prev; state["prev_hip"]=hip
        if hip>=165 and abs(delta)<=5: return "top_hold"
        if hip<=100 and delta<=0: return "lying"
        if delta>2: return "lifting"
        if delta<-2: return "lowering"
        return "lying"

    def score_frame(self, features, phase):
        rules={"lying":{"hip_angle":90,"body_line_angle":20},"top_hold":{"hip_angle":175,"body_line_angle":2}}
        t=rules.get(phase,{"hip_angle":135,"body_line_angle":10})
        ha_s=round(max(0,min(100,100-abs(features.get("hip_angle",90)-t["hip_angle"])/40*100)),1)
        bl_s=round(max(0,min(100,100-abs(features.get("body_line_angle",20)-t["body_line_angle"])/35*100)),1)
        return {"score":round(ha_s*0.6+bl_s*0.4,1),"issues":[],"detail_scores":{"hip_angle":ha_s,"body_line_angle":bl_s},"feedback":[]}

    def analyze_frame(self, landmarks, state):
        f=self.extract_features(landmarks); phase=self.detect_phase(f,state); ps=self.stage
        self.feature_history.append(f); s=self._smooth_features(); sr=self.score_frame(s,phase)
        if ps in ("lowering","top_hold") and phase=="lying": self.count+=1
        self._track(s,phase); is_rep=self._is_rep(ps,phase)
        self.previous_stage=ps; self.stage=phase
        r={"exercise_type":self.exercise_type,"phase":phase,"stage":phase,"count":self.count,"valid_count":self.count,"features":s,"metrics":s,"score":sr["score"],"current_score":sr["score"],"issues":[],"errors":[],"feedback":[],"detail_scores":sr["detail_scores"],"is_rep_finished":is_rep}
        if is_rep:
            rr=self._dwt_score()
            if rr["score"]>=75: self.valid_count=min(self.valid_count+1,self.count)
            r.update({"stage":"finished","rep_score":rr["score"],"score":rr["score"],"feedback":rr["feedback"],"errors":rr["feedback"],"detail":rr["detail"],"level":rr["level"]})
            self._reset()
        return r

    def _track(self,f,phase):
        if phase in ("lifting","top_hold"): self._rep_started=True
        if phase=="top_hold": self._seen_top=True
        if self._rep_started: self.current_rep_frames.append({"hip_angle":f.get("hip_angle",0),"body_line_angle":f.get("body_line_angle",0)})

    def _is_rep(self,ps,phase): return self._rep_started and self._seen_top and phase=="lying" and ps in ("lowering","top_hold")

    def _dwt_score(self):
        fs=self.current_rep_frames
        if len(fs)<2: return {"score":0,"level":"invalid","feedback":["数据不足"],"detail":{}}
        wd=0;tw=0
        for m,w in DTW_WEIGHTS.items():
            us=[f.get(m,0) for f in fs]; dist=self.template_service.dtw_distance(us,GLUTE_TEMPLATE.get(m,[]))
            wd+=dist*w; tw+=w
        ds=wd/tw if tw else 0; dt=round(max(0,min(100,100-ds*2.5)),1)
        mx=max(f.get("hip_angle",0) for f in fs)
        kp=round(max(0,min(100,100-max(0,175-mx)*2)),1)
        fs2=round(dt*0.6+kp*0.3+85*0.1,1)
        lv="excellent" if fs2>=90 else "good" if fs2>=75 else "normal" if fs2>=60 else "poor"
        return {"score":fs2,"level":lv,"feedback":[],"detail":{"similarity_score":dt,"dtw_distance":round(ds,1),"key_posture_score":kp}}

    def _reset(self): self.current_rep_frames=[]; self._rep_started=False; self._seen_top=False

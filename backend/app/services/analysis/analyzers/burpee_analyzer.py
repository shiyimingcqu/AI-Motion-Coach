"""Burpee analyzer — full-body multi-phase tracking and DTW final scoring."""

from app.services.analysis.analyzers.base_analyzer import (BaseExerciseAnalyzer, Keypoints, calculate_angle)
from app.services.analysis.template_service import TemplateService

REQUIRED = {"left_shoulder","right_shoulder","left_elbow","right_elbow","left_wrist","right_wrist","left_hip","right_hip","left_knee","right_knee","left_ankle","right_ankle"}
BURPEE_TEMPLATE = {"hip_angle":[170,140,100,90,150,175,170],"body_line_angle":[3,12,20,20,8,2,3]}
DTW_WEIGHTS = {"hip_angle":0.5,"body_line_angle":0.5}

class BurpeeAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "burpee"

    def __init__(self, smooth_window=5):
        super().__init__(smooth_window)
        self.template_service = TemplateService()
        self.current_rep_frames = []
        self._rep_started = False
        self._seen_plank = False
        self._seen_jump = False

    def extract_features(self, landmarks):
        if not REQUIRED.issubset(landmarks): raise ValueError("Missing keypoints")
        lv=landmarks["left_shoulder"].visibility; rv=landmarks["right_shoulder"].visibility
        side="left" if lv>=rv else "right"
        s=landmarks[f"{side}_shoulder"]; h=landmarks[f"{side}_hip"]; k=landmarks[f"{side}_knee"]; a=landmarks[f"{side}_ankle"]
        ha=calculate_angle(s.to_tuple(),h.to_tuple(),k.to_tuple())
        bl=180-calculate_angle(s.to_tuple(),h.to_tuple(),a.to_tuple())
        wh=h.y-landmarks[f"{side}_wrist"].y
        return {"hip_angle":round(ha,1),"body_line_angle":round(bl,1),"wrist_height":round(wh,4)}

    def detect_phase(self, features, state):
        hip=features.get("hip_angle",170); bl=features.get("body_line_angle",3)
        wh=features.get("wrist_height",0); prev=state.get("prev_hip",hip)
        delta=hip-prev; state["prev_hip"]=hip
        if hip>=170 and wh>0.15: return "jump"
        if hip<=100 and bl>=15: return "plank"
        if hip<=130 and delta<-2: return "squat_down"
        if hip>=150 and delta>2: return "squat_up"
        if hip>=160 and delta<=0: return "standing"
        return "standing"

    def score_frame(self, features, phase):
        hip=features.get("hip_angle",170); bl=features.get("body_line_angle",3)
        rules={"standing":(170,3),"plank":(90,20),"jump":(175,2)}
        t=rules.get(phase,(135,10))
        hs=round(max(0,min(100,100-abs(hip-t[0])/45*100)),1)
        bs=round(max(0,min(100,100-abs(bl-t[1])/35*100)),1)
        return {"score":round(hs*0.5+bs*0.5,1),"issues":[],"detail_scores":{"hip":hs,"body_line":bs},"feedback":[]}

    def analyze_frame(self, landmarks, state):
        f=self.extract_features(landmarks); phase=self.detect_phase(f,state); ps=self.stage
        self.feature_history.append(f); s=self._smooth_features(); sr=self.score_frame(s,phase)
        if ps in ("squat_up","jump") and phase=="standing": self.count+=1
        self._track(s,phase); is_rep=self._is_rep(ps,phase)
        self.previous_stage=ps; self.stage=phase
        r={"exercise_type":self.exercise_type,"phase":phase,"stage":phase,"count":self.count,"valid_count":self.count,"features":s,"metrics":s,"score":sr["score"],"current_score":sr["score"],"issues":[],"errors":[],"feedback":[],"detail_scores":sr["detail_scores"],"is_rep_finished":is_rep}
        if is_rep:
            rr=self._dwt_score()
            if rr["score"]>=75: self.valid_count=min(self.valid_count+1,self.count)
            r.update({"stage":"finished","rep_score":rr["score"],"score":rr["score"],"feedback":[],"errors":[],"detail":rr["detail"],"level":rr["level"]})
            self._reset()
        return r

    def _track(self,f,phase):
        if phase in ("squat_down","plank"): self._rep_started=True
        if phase=="plank": self._seen_plank=True
        if phase=="jump": self._seen_jump=True
        if self._rep_started: self.current_rep_frames.append({"hip_angle":f.get("hip_angle",0),"body_line_angle":f.get("body_line_angle",0)})

    def _is_rep(self,ps,phase): return self._rep_started and self._seen_plank and self._seen_jump and phase=="standing" and ps in ("squat_up","jump")

    def _dwt_score(self):
        fs=self.current_rep_frames
        if len(fs)<3: return {"score":0,"level":"invalid","feedback":["数据不足"],"detail":{}}
        wd=0;tw=0
        for m,w in DTW_WEIGHTS.items():
            us=[f.get(m,0) for f in fs]; dist=self.template_service.dtw_distance(us,BURPEE_TEMPLATE.get(m,[]))
            wd+=dist*w; tw+=w
        ds=wd/tw if tw else 0; dt=round(max(0,min(100,100-ds*2.5)),1)
        mn=min(f.get("hip_angle",0) for f in fs)
        kp=round(max(0,min(100,100-max(0,mn-90)*1.5)),1)
        fs2=round(dt*0.6+kp*0.3+85*0.1,1)
        lv="excellent" if fs2>=90 else "good" if fs2>=75 else "normal" if fs2>=60 else "poor"
        return {"score":fs2,"level":lv,"feedback":[],"detail":{"similarity_score":dt,"dtw_distance":round(ds,1),"key_posture_score":kp}}

    def _reset(self): self.current_rep_frames=[]; self._rep_started=False; self._seen_plank=False; self._seen_jump=False

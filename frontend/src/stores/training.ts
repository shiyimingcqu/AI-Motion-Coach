import { defineStore } from "pinia";

export interface Exercise {
  key: string;
  name: string;
  category: string;
  level: string;
  duration: string;
  modes: string[];
  errors: string[];
  accent: string;
}

export interface Session {
  session_id: string;
  exercise: string;
  date: string;
  created_at?: string;
  duration_seconds: number;
  total_count: number;
  valid_count: number;
  error_count: number;
  average_score: number;
}

export interface LiveAnalysisResult {
  stage: string;
  count: number;
  valid_count: number;
  score: number;
  errors: string[];
  feedback: string[];
}

export const exercises: Exercise[] = [
  {
    key: "squat",
    name: "深蹲",
    category: "下肢力量",
    level: "中级",
    duration: "12 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["下蹲深度不足", "膝盖内扣"],
    accent: "#22c55e"
  },
  {
    key: "push_up",
    name: "俯卧撑",
    category: "上肢力量",
    level: "中级",
    duration: "10 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["手臂未伸直", "身体塌腰"],
    accent: "#0ea5e9"
  },
  {
    key: "jumping_jack",
    name: "开合跳",
    category: "心肺训练",
    level: "初级",
    duration: "8 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["节奏过快", "手脚幅度不足"],
    accent: "#f59e0b"
  },
  {
    key: "plank",
    name: "平板支撑",
    category: "核心稳定",
    level: "高级",
    duration: "6 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["髋部下沉", "肩肘未对齐"],
    accent: "#14b8a6"
  },
  {
    key: "lunge",
    name: "弓步蹲",
    category: "下肢力量",
    level: "中级",
    duration: "10 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["膝盖超过脚尖", "身体前倾"],
    accent: "#8b5cf6"
  },
  {
    key: "burpee",
    name: "波比跳",
    category: "全身",
    level: "高级",
    duration: "8 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["动作不连贯", "核心松散"],
    accent: "#ef4444"
  },
  {
    key: "mountain_climber",
    name: "登山跑",
    category: "核心稳定",
    level: "中级",
    duration: "8 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["臀部抬高", "节奏不稳"],
    accent: "#f97316"
  },
  {
    key: "pull_up",
    name: "引体向上",
    category: "上肢力量",
    level: "高级",
    duration: "10 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["摆动借力", "下降过快"],
    accent: "#06b6d4"
  },
  {
    key: "bench_press",
    name: "卧推",
    category: "上肢力量",
    level: "中级",
    duration: "10 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["推起幅度不足", "手腕肘部不对齐"],
    accent: "#2563eb"
  },
  {
    key: "barbell_squat",
    name: "杠铃深蹲",
    category: "下肢力量",
    level: "高级",
    duration: "12 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["躯干前倾过大", "杠铃路径偏移"],
    accent: "#16a34a"
  },
  {
    key: "dumbbell_fly",
    name: "哑铃飞鸟",
    category: "上肢力量",
    level: "中级",
    duration: "8 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["打开幅度异常", "左右轨迹不对称"],
    accent: "#db2777"
  },
  {
    key: "lat_pulldown",
    name: "高位下拉",
    category: "上肢力量",
    level: "中级",
    duration: "10 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["身体后仰借力", "下拉幅度不足"],
    accent: "#0891b2"
  },
  {
    key: "dumbbell_shoulder_press",
    name: "哑铃推肩",
    category: "上肢力量",
    level: "中级",
    duration: "10 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["腰背后仰", "左右推举不同步"],
    accent: "#7c3aed"
  },
  {
    key: "dumbbell_curl",
    name: "哑铃弯举",
    category: "上肢力量",
    level: "初级",
    duration: "8 分钟",
    modes: ["视频上传分析"],
    errors: ["身体晃动", "肘部前移"],
    accent: "#ec4899"
  },
  {
    key: "dumbbell_press",
    name: "哑铃推举",
    category: "上肢力量",
    level: "中级",
    duration: "10 分钟",
    modes: ["视频上传分析"],
    errors: ["腰部反弓", "手臂未完全伸直"],
    accent: "#a855f7"
  },
  {
    key: "high_knees",
    name: "高抬腿",
    category: "心肺训练",
    level: "初级",
    duration: "6 分钟",
    modes: ["摄像头实时检测", "视频上传分析"],
    errors: ["节奏不稳", "膝盖抬起高度不足"],
    accent: "#eab308"
  },
  {
    key: "russian_twist",
    name: "俄罗斯转体",
    category: "核心稳定",
    level: "中级",
    duration: "8 分钟",
    modes: ["视频上传分析"],
    errors: ["身体晃动", "背部未挺直"],
    accent: "#f97316"
  },
  {
    key: "glute_bridge",
    name: "臀桥",
    category: "下肢力量",
    level: "初级",
    duration: "8 分钟",
    modes: ["视频上传分析"],
    errors: ["腰部代偿", "抬臀高度不足"],
    accent: "#14b8a6"
  }
];

export const demoSessions: Session[] = [
  {
    session_id: "s-0622-01",
    exercise: "squat",
    date: "2026-06-22",
    duration_seconds: 720,
    total_count: 20,
    valid_count: 18,
    error_count: 2,
    average_score: 86
  },
  {
    session_id: "s-0621-01",
    exercise: "pushup",
    date: "2026-06-21",
    duration_seconds: 540,
    total_count: 15,
    valid_count: 12,
    error_count: 3,
    average_score: 78
  },
  {
    session_id: "s-0620-01",
    exercise: "jumping_jack",
    date: "2026-06-20",
    duration_seconds: 480,
    total_count: 50,
    valid_count: 45,
    error_count: 5,
    average_score: 92
  },
  {
    session_id: "s-0619-01",
    exercise: "squat",
    date: "2026-06-19",
    duration_seconds: 660,
    total_count: 18,
    valid_count: 15,
    error_count: 3,
    average_score: 81
  }
];

export const useTrainingStore = defineStore("training", {
  state: () => ({
    currentExercise: "squat",
    stage: "下蹲",
    count: 12,
    validCount: 10,
    score: 86,
    errors: ["下蹲深度不足", "膝盖内扣"],
    feedbacks: ["动作整体标准，保持当前节奏与稳定性"],
    taskStatus: "running",
    trend: [78, 82, 80, 86, 88, 84, 91],
    errorStats: [
      { name: "下蹲深度不足", value: 32 },
      { name: "膝盖内扣", value: 21 },
      { name: "手臂未伸直", value: 18 },
      { name: "节奏过快", value: 14 },
      { name: "核心不稳", value: 9 }
    ]
  }),
  getters: {
    currentExerciseMeta: (state) => exercises.find((item) => item.key === state.currentExercise) ?? exercises[0],
    todayScore: () => 86,
    validRate: () => "88%"
  },
  actions: {
    setExercise(exercise: string) {
      this.currentExercise = exercise;
      const meta = exercises.find((item) => item.key === exercise);
      if (meta) {
        this.errors = meta.errors;
      }
    },
    updateLiveMetrics(result: LiveAnalysisResult) {
      this.stage = result.stage;
      this.count = result.count;
      this.validCount = result.valid_count;
      this.score = result.score;
      this.errors = result.errors;
      this.feedbacks = result.feedback;
    },
    resetLiveMetrics() {
      this.stage = "ready";
      this.count = 0;
      this.validCount = 0;
      this.score = 0;
      this.errors = [];
      this.feedbacks = [];
    }
  }
});

// 常量定义（开发者工具默认连本机后端）
// 注意：微信开发者工具对 127.0.0.1 会触发域名校验，必须使用局域网 IP
const API_BASE_HOST = '192.168.43.113';
const API_PORT = 8000;

function getApiBaseUrl() {
  return `http://${API_BASE_HOST}:${API_PORT}`;
}

// 兼容旧引用；请求时请优先用 getApiBaseUrl()
const API_BASE_URL = getApiBaseUrl();

// 动作配置
const EXERCISE_CONFIG = {
  squat: {
    key: 'squat',
    name: '深蹲',
    category: '下肢力量',
    level: '中级',
    accentColor: '#22c55e',
    icon: '🦵',
    keypointsNeeded: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
    phases: ['standing', 'down', 'bottom', 'up']
  },
  push_up: {
    key: 'push_up',
    name: '俯卧撑',
    category: '上肢力量',
    level: '中级',
    accentColor: '#0ea5e9',
    icon: '💪',
    keypointsNeeded: ['nose', 'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'left_hip', 'right_hip', 'left_ankle', 'right_ankle'],
    phases: ['top_support', 'down', 'bottom', 'up']
  },
  jumping_jack: {
    key: 'jumping_jack',
    name: '开合跳',
    category: '心肺训练',
    level: '初级',
    accentColor: '#f59e0b',
    icon: '🏃',
    keypointsNeeded: ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
    phases: ['closed', 'opening', 'open', 'closing']
  },
  plank: {
    key: 'plank',
    name: '平板支撑',
    category: '核心稳定',
    level: '高级',
    accentColor: '#14b8a6',
    icon: '🏋️',
    keypointsNeeded: ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
    phases: ['hold']
  },
  lunge: {
    key: 'lunge',
    name: '弓步蹲',
    category: '下肢力量',
    level: '中级',
    accentColor: '#8b5cf6',
    icon: '🦵',
    keypointsNeeded: ['left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
    phases: ['standing', 'down', 'bottom', 'up']
  },
  glute_bridge: {
    key: 'glute_bridge',
    name: '臀桥',
    category: '下肢力量',
    level: '初级',
    accentColor: '#14b8a6',
    icon: '🍑',
    keypointsNeeded: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee'],
    phases: ['lying', 'up', 'top', 'down']
  },
  high_knees: {
    key: 'high_knees',
    name: '高抬腿',
    category: '心肺训练',
    level: '初级',
    accentColor: '#eab308',
    icon: '🏃',
    keypointsNeeded: ['left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
    phases: ['standing', 'knee_up', 'knee_down']
  },
  burpee: {
    key: 'burpee',
    name: '波比跳',
    category: '全身',
    level: '高级',
    accentColor: '#ef4444',
    icon: '🔥',
    keypointsNeeded: ['nose', 'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
    phases: ['standing', 'squat_down', 'plank', 'push_up', 'squat_up', 'jump']
  },
  pull_up: {
    key: 'pull_up',
    name: '引体向上',
    category: '上肢力量',
    level: '高级',
    accentColor: '#06b6d4',
    icon: '💪',
    keypointsNeeded: ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'left_hip', 'right_hip'],
    phases: ['hanging', 'pulling', 'top', 'lowering']
  },
  bench_press: {
    key: 'bench_press',
    name: '卧推',
    category: '上肢力量',
    level: '中级',
    accentColor: '#2563eb',
    icon: '💪',
    keypointsNeeded: ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'left_hip', 'right_hip'],
    phases: ['bottom', 'moving', 'top']
  },
  barbell_squat: {
    key: 'barbell_squat',
    name: '杠铃深蹲',
    category: '下肢力量',
    level: '高级',
    accentColor: '#16a34a',
    icon: '🏋️',
    keypointsNeeded: ['left_shoulder', 'right_shoulder', 'left_wrist', 'right_wrist', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
    phases: ['standing', 'descending', 'bottom', 'ascending']
  },
  dumbbell_fly: {
    key: 'dumbbell_fly',
    name: '哑铃飞鸟',
    category: '上肢力量',
    level: '中级',
    accentColor: '#db2777',
    icon: '💪',
    keypointsNeeded: ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'left_hip', 'right_hip'],
    phases: ['closed', 'moving', 'open']
  },
  lat_pulldown: {
    key: 'lat_pulldown',
    name: '高位下拉',
    category: '上肢力量',
    level: '中级',
    accentColor: '#0891b2',
    icon: '💪',
    keypointsNeeded: ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'left_hip', 'right_hip'],
    phases: ['top', 'moving', 'bottom']
  },
  dumbbell_shoulder_press: {
    key: 'dumbbell_shoulder_press',
    name: '哑铃推肩',
    category: '上肢力量',
    level: '中级',
    accentColor: '#7c3aed',
    icon: '💪',
    keypointsNeeded: ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'left_hip', 'right_hip'],
    phases: ['rack', 'moving', 'top']
  }
};

// MediaPipe 33 关键点索引
const KEYPOINT_INDEX = {
  nose: 0,
  left_eye_inner: 1,
  left_eye: 2,
  left_eye_outer: 3,
  right_eye_inner: 4,
  right_eye: 5,
  right_eye_outer: 6,
  left_ear: 7,
  right_ear: 8,
  mouth_left: 9,
  mouth_right: 10,
  left_shoulder: 11,
  right_shoulder: 12,
  left_elbow: 13,
  right_elbow: 14,
  left_wrist: 15,
  right_wrist: 16,
  left_pinky: 17,
  right_pinky: 18,
  left_index: 19,
  right_index: 20,
  left_thumb: 21,
  right_thumb: 22,
  left_hip: 23,
  right_hip: 24,
  left_knee: 25,
  right_knee: 26,
  left_ankle: 27,
  right_ankle: 28,
  left_heel: 29,
  right_heel: 30,
  left_foot_index: 31,
  right_foot_index: 32
};

// 骨架连线定义
const SKELETON_CONNECTIONS = [
  // 躯干
  [11, 12], [11, 23], [12, 24], [23, 24],
  // 左臂
  [11, 13], [13, 15],
  // 右臂
  [12, 14], [14, 16],
  // 左腿
  [23, 25], [25, 27],
  // 右腿
  [24, 26], [26, 28]
];

// 评分等级
const SCORE_LEVELS = {
  excellent: { min: 90, label: '优秀', color: '#22c55e' },
  good: { min: 75, label: '良好', color: '#3b82f6' },
  fair: { min: 60, label: '一般', color: '#f59e0b' },
  poor: { min: 0, label: '需改进', color: '#ef4444' }
};

function getScoreLevel(score) {
  if (score >= 90) return SCORE_LEVELS.excellent;
  if (score >= 75) return SCORE_LEVELS.good;
  if (score >= 60) return SCORE_LEVELS.fair;
  return SCORE_LEVELS.poor;
}

module.exports = {
  getApiBaseUrl,
  API_BASE_URL,
  EXERCISE_CONFIG,
  KEYPOINT_INDEX,
  SKELETON_CONNECTIONS,
  SCORE_LEVELS,
  getScoreLevel
};

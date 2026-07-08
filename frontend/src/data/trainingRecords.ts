// 训练记录相关工具函数（得分等级、格式化等）

export type ScoreLevel = "excellent" | "good" | "mid" | "low";

export interface ScoreLevelInfo {
  key: ScoreLevel;
  label: string;
  color: string;
  bgColor: string;
  textColor: string;
  min: number;
  max: number;
}

export const SCORE_LEVELS: ScoreLevelInfo[] = [
  { key: "excellent", label: "优秀", color: "#10b981", bgColor: "#d1fae5", textColor: "#059669", min: 90, max: 100 },
  { key: "good",      label: "良好", color: "#3b82f6", bgColor: "#dbeafe", textColor: "#2563eb", min: 70, max: 89 },
  { key: "mid",       label: "中等", color: "#f59e0b", bgColor: "#fef3c7", textColor: "#d97706", min: 50, max: 69 },
  { key: "low",       label: "较差", color: "#ef4444", bgColor: "#fee2e2", textColor: "#dc2626", min: 0,  max: 49 },
];

export function getScoreLevel(score: number): ScoreLevelInfo {
  if (score >= 90) return SCORE_LEVELS[0];
  if (score >= 70) return SCORE_LEVELS[1];
  if (score >= 50) return SCORE_LEVELS[2];
  return SCORE_LEVELS[3];
}

// 格式化时长（秒 -> mm:ss）
export function formatDuration(sec: number): string {
  if (!sec || sec <= 0) return "00:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

// 格式化小时（分钟 -> X.X 小时）
export function formatHours(minutes: number): string {
  return (minutes / 60).toFixed(1);
}

// 格式化日期时间（ISO -> 2024/07/06 19:30）
export function formatDateTime(iso: string): string {
  if (!iso) return "-";
  const d = new Date(iso);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  return `${yyyy}/${mm}/${dd} ${hh}:${mi}`;
}

// 格式化日期（ISO -> 2024/07/06）
export function formatDate(iso: string): string {
  if (!iso) return "-";
  const d = new Date(iso);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}/${mm}/${dd}`;
}

// 提取日期 key（用于日历聚合）
export function getDateKey(iso: string): string {
  if (!iso) return "";
  return iso.split("T")[0];
}

// 数字千分位
export function formatNumber(n: number): string {
  return new Intl.NumberFormat("zh-CN").format(Math.round(n));
}

// 缩略运动配图（按动作 key 决定小图标背景色）
export const EXERCISE_META: Record<string, { name: string; level: string; equipment: string; camera_view: string; accent: string; }> = {
  squat:                       { name: "深蹲",     level: "入门", equipment: "无器械",     camera_view: "侧面",   accent: "#ecfdf5" },
  push_up:                     { name: "俯卧撑",   level: "入门", equipment: "无器械",     camera_view: "侧面",   accent: "#fef2f2" },
  jumping_jack:                { name: "开合跳",   level: "入门", equipment: "无器械",     camera_view: "正面",   accent: "#eff6ff" },
  plank:                       { name: "平板支撑", level: "入门", equipment: "无器械",     camera_view: "侧面",   accent: "#f5f3ff" },
  lunge:                       { name: "侧弓步",   level: "中级", equipment: "无器械",     camera_view: "正面",   accent: "#ecfdf5" },
  burpee:                      { name: "波比跳",   level: "进阶", equipment: "无器械",     camera_view: "正面",   accent: "#f5f3ff" },
  high_knees:                  { name: "高抬腿",   level: "入门", equipment: "无器械",     camera_view: "正面",   accent: "#eff6ff" },
  glute_bridge:                { name: "臀桥",     level: "入门", equipment: "瑜伽垫",     camera_view: "侧面",   accent: "#fdf2f8" },
  mountain_climber:            { name: "登山跑",   level: "进阶", equipment: "无器械",     camera_view: "正面",   accent: "#ecfdf5" },
  pull_up:                     { name: "引体向上", level: "进阶", equipment: "单杠",       camera_view: "侧面",   accent: "#fefce8" },
  bench_press:                 { name: "卧推",     level: "中等", equipment: "哑铃/杠铃", camera_view: "侧面",   accent: "#fef3c7" },
  barbell_squat:               { name: "杠铃深蹲", level: "进阶", equipment: "杠铃",       camera_view: "侧面",   accent: "#f5f3ff" },
  dumbbell_fly:                { name: "哑铃飞鸟", level: "中等", equipment: "哑铃",       camera_view: "侧面",   accent: "#fef2f2" },
  lat_pulldown:                { name: "高位下拉", level: "中等", equipment: "拉力器",     camera_view: "正面",   accent: "#eff6ff" },
  dumbbell_curl:               { name: "哑铃弯举", level: "入门", equipment: "哑铃",       camera_view: "侧面",   accent: "#fefce8" },
  dumbbell_press:              { name: "哑铃卧推", level: "中等", equipment: "哑铃",       camera_view: "侧面",   accent: "#eff6ff" },
  dumbbell_shoulder_press:     { name: "哑铃推肩", level: "中等", equipment: "哑铃",       camera_view: "正面",   accent: "#ecfdf5" },
  russian_twist:               { name: "仰卧起坐", level: "入门", equipment: "无器械",     camera_view: "正面",   accent: "#fdf2f8" },
};

export function getExerciseMeta(key: string) {
  return EXERCISE_META[key] || { name: key, level: "入门", equipment: "无器械", camera_view: "正面", accent: "#f1f5f9" };
}

// 模拟数据 —— 接口无数据时使用
export const MOCK_SESSIONS = [
  { session_id: "m1", exercise: "plank",            created_at: "2024-07-06T19:30:00", duration_seconds: 72,  total_count: 1,  valid_count: 1,  error_count: 0, average_score: 85 },
  { session_id: "m2", exercise: "lunge",            created_at: "2024-07-06T18:10:00", duration_seconds: 92,  total_count: 12, valid_count: 10, error_count: 2, average_score: 76 },
  { session_id: "m3", exercise: "push_up",          created_at: "2024-07-05T20:15:00", duration_seconds: 65,  total_count: 15, valid_count: 13, error_count: 2, average_score: 82 },
  { session_id: "m4", exercise: "glute_bridge",     created_at: "2024-07-05T18:45:00", duration_seconds: 80,  total_count: 20, valid_count: 18, error_count: 2, average_score: 88 },
  { session_id: "m5", exercise: "russian_twist",    created_at: "2024-07-04T21:00:00", duration_seconds: 75,  total_count: 30, valid_count: 24, error_count: 6, average_score: 72 },
  { session_id: "m6", exercise: "mountain_climber", created_at: "2024-07-04T19:20:00", duration_seconds: 100, total_count: 40, valid_count: 36, error_count: 4, average_score: 90 },
  { session_id: "m7", exercise: "squat",            created_at: "2024-07-03T20:00:00", duration_seconds: 110, total_count: 20, valid_count: 17, error_count: 3, average_score: 84 },
  { session_id: "m8", exercise: "jumping_jack",     created_at: "2024-07-02T19:00:00", duration_seconds: 60,  total_count: 60, valid_count: 55, error_count: 5, average_score: 87 },
  { session_id: "m9", exercise: "plank",            created_at: "2024-07-01T18:30:00", duration_seconds: 80,  total_count: 1,  valid_count: 1,  error_count: 0, average_score: 91 },
];

// 月份切换/日历辅助
export const WEEK_LABELS = ["一", "二", "三", "四", "五", "六", "日"];

export function buildCalendarGrid(year: number, month: number): Array<{ day: number | null; dateKey: string | null; inMonth: boolean }> {
  const firstDay = new Date(year, month, 1);
  const firstWeekday = (firstDay.getDay() + 6) % 7; // 0 = Monday
  const lastDay = new Date(year, month + 1, 0).getDate();

  const cells: Array<{ day: number | null; dateKey: string | null; inMonth: boolean }> = [];
  // Leading blanks
  for (let i = 0; i < firstWeekday; i++) {
    cells.push({ day: null, dateKey: null, inMonth: false });
  }
  for (let d = 1; d <= lastDay; d++) {
    const dateKey = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    cells.push({ day: d, dateKey, inMonth: true });
  }
  // Trailing blanks to fill last row
  while (cells.length % 7 !== 0) {
    cells.push({ day: null, dateKey: null, inMonth: false });
  }
  return cells;
}

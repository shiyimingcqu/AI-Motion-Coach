<template>
  <div class="sessions-page">
    <header class="section-page-header">
      <div>
        <h1>Training Sessions / 训练记录</h1>
        <p>Complete history of all training sessions</p>
      </div>
      <button class="blue-action-button" type="button">
        New Session / 新建训练
      </button>
    </header>

    <section class="summary-card-grid">
      <article v-for="item in summaryCards" :key="item.label" class="summary-card">
        <span>{{ item.label }}</span>
        <strong :class="item.tone">{{ item.value }}</strong>
      </article>
    </section>

    <section class="filter-card">
      <label class="session-search">
        <Search :size="20" />
        <input v-model="keyword" type="search" placeholder="Search sessions... / 搜索训练记录..." />
      </label>
      <select v-model="statusFilter">
        <option value="all">All Status / 所有状态</option>
        <option value="excellent">Excellent / 优秀</option>
        <option value="good">Good / 良好</option>
      </select>
      <select v-model="periodFilter">
        <option value="week">This Week / 本周</option>
        <option value="month">This Month / 本月</option>
        <option value="all">All Time / 全部</option>
      </select>
    </section>

    <section class="sessions-table-card">
      <div v-if="loading" class="loading-text">正在加载训练记录...</div>
      <table v-else class="sessions-table">
        <thead>
          <tr>
            <th>DATE & TIME / 日期时间</th>
            <th>EXERCISES / 动作</th>
            <th>DURATION / 时长</th>
            <th>REPS / 次数</th>
            <th>SCORE / 分数</th>
            <th>CALORIES / 卡路里</th>
            <th>ACTIONS / 操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="session in filteredSessions" :key="session.id">
            <td>
              <div class="date-cell">
                <CalendarDays :size="17" />
                <div>
                  <strong>{{ session.date }}</strong>
                  <span>
                    <Clock3 :size="13" />
                    {{ session.time }}
                  </span>
                </div>
              </div>
            </td>
            <td>
              <div class="exercise-tags">
                <span v-for="exercise in session.exercises" :key="exercise">{{ exercise }}</span>
              </div>
            </td>
            <td>{{ session.duration }} min</td>
            <td>{{ session.reps }}</td>
            <td>
              <div class="score-progress">
                <i :class="scoreTone(session.score)" :style="{ width: `${session.score}%` }" />
                <strong>{{ session.score }}</strong>
              </div>
            </td>
            <td>{{ session.calories }} kcal</td>
            <td>
              <button class="link-button" type="button">View Details</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="streak-card">
      <span class="streak-icon">
        <Medal :size="34" />
      </span>
      <div>
        <h2>5-Day Streak! / 连续5天训练!</h2>
        <p>Amazing consistency! Keep up the great work.</p>
      </div>
      <strong>
        <TrendingUp :size="18" />
        +12% vs last week
      </strong>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  CalendarDays,
  Clock3,
  Medal,
  Search,
  TrendingUp
} from "lucide-vue-next";

import { apiGet } from "../api/client";
import { demoSessions, exercises, type Session } from "../stores/training";

type ApiSession = Session & { created_at?: string };

interface DisplaySession {
  id: string;
  date: string;
  time: string;
  exercises: string[];
  duration: number;
  reps: number;
  score: number;
  calories: number;
}

const sessions = ref<ApiSession[]>([]);
const loading = ref(true);
const keyword = ref("");
const statusFilter = ref("all");
const periodFilter = ref("week");

const fallbackSessions: DisplaySession[] = [
  {
    id: "session-0625",
    date: "2026-06-25",
    time: "14:30",
    exercises: ["Squat", "Push-up", "Plank"],
    duration: 45,
    reps: 120,
    score: 92,
    calories: 245
  },
  {
    id: "session-0624",
    date: "2026-06-24",
    time: "15:15",
    exercises: ["Lunge", "Burpee", "Mountain Climber"],
    duration: 38,
    reps: 95,
    score: 88,
    calories: 220
  },
  {
    id: "session-0623",
    date: "2026-06-23",
    time: "10:00",
    exercises: ["Squat", "Deadlift", "Bench Press"],
    duration: 52,
    reps: 85,
    score: 90,
    calories: 280
  },
  {
    id: "session-0622",
    date: "2026-06-22",
    time: "16:45",
    exercises: ["Pull-up", "Dip", "Plank"],
    duration: 40,
    reps: 78,
    score: 85,
    calories: 195
  },
  {
    id: "session-0621",
    date: "2026-06-21",
    time: "14:00",
    exercises: ["Jump Squat", "Push-up", "Crunch"],
    duration: 35,
    reps: 110,
    score: 87,
    calories: 210
  }
];

const displaySessions = computed<DisplaySession[]>(() => {
  if (sessions.value.length === 0) return fallbackSessions;
  return sessions.value.map((session, index) => ({
    id: session.session_id,
    date: sessionDate(session).slice(0, 10) || `2026-06-${25 - index}`,
    time: formatTime(session.created_at) || ["14:30", "15:15", "10:00", "16:45"][index % 4],
    exercises: [getExerciseName(session.exercise)],
    duration: Math.max(1, Math.round(session.duration_seconds / 60)),
    reps: session.total_count,
    score: session.average_score,
    calories: Math.round(session.duration_seconds * 0.34)
  }));
});

const filteredSessions = computed(() => {
  const query = keyword.value.trim().toLowerCase();
  return displaySessions.value.filter((session) => {
    const matchesKeyword =
      !query ||
      session.date.toLowerCase().includes(query) ||
      session.exercises.some((exercise) => exercise.toLowerCase().includes(query));
    const matchesStatus =
      statusFilter.value === "all" ||
      (statusFilter.value === "excellent" && session.score >= 90) ||
      (statusFilter.value === "good" && session.score >= 80 && session.score < 90);
    return matchesKeyword && matchesStatus;
  });
});

const summaryCards = computed(() => {
  const totalSessions = displaySessions.value.length;
  const totalDuration = displaySessions.value.reduce((sum, item) => sum + item.duration, 0);
  const averageScore =
    displaySessions.value.reduce((sum, item) => sum + item.score, 0) / Math.max(totalSessions, 1);
  const totalCalories = displaySessions.value.reduce((sum, item) => sum + item.calories, 0);

  return [
    { label: "Total Sessions / 总训练次数", value: totalSessions, tone: "tone-text-blue" },
    { label: "Total Duration / 总时长", value: `${totalDuration} min`, tone: "tone-text-green" },
    { label: "Avg Score / 平均分数", value: averageScore.toFixed(1), tone: "tone-text-purple" },
    { label: "Total Calories / 总消耗", value: totalCalories.toLocaleString(), tone: "tone-text-orange" }
  ];
});

async function loadSessions() {
  try {
    const data = await apiGet<{ items: ApiSession[] }>("/sessions");
    sessions.value = data.items || [];
  } catch (error) {
    console.warn("加载训练记录失败，使用演示数据。", error);
    sessions.value = [];
  } finally {
    loading.value = false;
  }
}

function getExerciseName(exercise: string): string {
  const name = exercises.find((item) => item.key === exercise)?.name ?? exercise;
  const readableMap: Record<string, string> = {
    squat: "Squat",
    pushup: "Push-up",
    jumping_jack: "Jumping Jack",
    plank: "Plank",
    深蹲: "Squat",
    俯卧撑: "Push-up",
    开合跳: "Jumping Jack",
    平板支撑: "Plank"
  };
  return readableMap[name] ?? readableMap[exercise] ?? name;
}

function scoreTone(score: number) {
  return score >= 90 ? "progress-green" : "progress-blue";
}

function sessionDate(session: ApiSession): string {
  return session.date || session.created_at || "";
}

function formatTime(value?: string) {
  if (!value) return "";
  const match = value.match(/T(\d{2}:\d{2})/);
  return match?.[1] ?? "";
}

onMounted(loadSessions);
</script>

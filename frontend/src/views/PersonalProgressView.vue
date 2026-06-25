<template>
  <div class="progress-page">
    <header class="section-page-header">
      <div>
        <h1>Personal Progress / 个人进步趋势</h1>
        <p>Track your improvement journey over time</p>
      </div>
    </header>

    <section class="gradient-stat-grid">
      <article v-for="card in cards" :key="card.label" :class="['gradient-stat-card', card.tone]">
        <component :is="card.icon" :size="18" />
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <small>{{ card.hint }}</small>
      </article>
    </section>

    <section class="progress-card">
      <h2>6-Month Score Trend / 6个月分数趋势</h2>
      <div class="wide-line-chart">
        <svg viewBox="0 0 1000 210" preserveAspectRatio="none">
          <defs>
            <linearGradient id="progressArea" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="#4f7df3" stop-opacity="0.18" />
              <stop offset="100%" stop-color="#4f7df3" stop-opacity="0" />
            </linearGradient>
          </defs>
          <path d="M0 138 L200 126 L400 114 L600 94 L800 78 L1000 62 L1000 210 L0 210 Z" fill="url(#progressArea)" />
          <polyline points="0,138 200,126 400,114 600,94 800,78 1000,62" fill="none" stroke="#5d84ff" stroke-width="3" />
        </svg>
        <div class="chart-axis months"><span>Jan</span><span>Feb</span><span>Mar</span><span>Apr</span><span>May</span><span>Jun</span></div>
      </div>
    </section>

    <section class="progress-card">
      <h2>Exercise-Specific Progress / 各动作进步情况</h2>
      <div class="exercise-progress-list">
        <article v-for="exercise in exercises" :key="exercise.name">
          <header>
            <strong>{{ exercise.name }}</strong>
            <span>4-Week Improvement: <b>+{{ exercise.gain }}%</b></span>
          </header>
          <div class="week-grid">
            <div v-for="(score, index) in exercise.scores" :key="index" :class="{ current: index === 3 }">
              <small>Week {{ index + 1 }}</small>
              <strong>{{ score }}</strong>
            </div>
          </div>
        </article>
      </div>
    </section>

    <section class="progress-card">
      <h2>Training Volume / 训练量</h2>
      <div class="volume-bars">
        <span v-for="bar in volume" :key="bar.month" :style="{ height: `${bar.value * 4}px` }"><b>{{ bar.month }}</b></span>
      </div>
    </section>

    <section class="progress-card">
      <h2>Milestones & Achievements / 里程碑与成就</h2>
      <div class="milestone-list">
        <article v-for="item in milestones" :key="item.title">
          <span>{{ item.icon }}</span>
          <div><strong>{{ item.title }}</strong><small>{{ item.desc }}</small></div>
          <time>{{ item.date }}</time>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Award, CalendarDays, Target, TrendingUp } from "lucide-vue-next";

const cards = [
  { label: "Overall Progress", value: "+22%", hint: "vs. last month", icon: TrendingUp, tone: "blue-gradient" },
  { label: "Achievements", value: "24", hint: "milestones reached", icon: Award, tone: "green-gradient" },
  { label: "Current Score", value: "88", hint: "average rating", icon: Target, tone: "purple-gradient" },
  { label: "Training Days", value: "142", hint: "total sessions", icon: CalendarDays, tone: "orange-gradient" }
];

const exercises = [
  { name: "Squat", scores: [75, 78, 82, 88], gain: 13 },
  { name: "Push-up", scores: [70, 74, 79, 85], gain: 15 },
  { name: "Plank", scores: [68, 72, 76, 82], gain: 14 },
  { name: "Lunge", scores: [72, 75, 79, 84], gain: 12 }
];

const volume = [
  { month: "Jan", value: 8 },
  { month: "Feb", value: 12 },
  { month: "Mar", value: 15 },
  { month: "Apr", value: 18 },
  { month: "May", value: 20 },
  { month: "Jun", value: 22 }
];

const milestones = [
  { icon: "🏆", title: "First Perfect Score / 首次满分", desc: "Plank · Score: 100", date: "2026-06-20" },
  { icon: "🔥", title: "30-Day Streak / 30天连续训练", desc: "Completed training for 30 consecutive days", date: "2026-06-15" },
  { icon: "💯", title: "100 Sessions Milestone / 100次训练里程碑", desc: "Reached 100 total training sessions", date: "2026-06-10" },
  { icon: "⭐", title: "Master Level Achieved / 达到大师级别", desc: "Squat · Score: 95", date: "2026-06-05" }
];
</script>

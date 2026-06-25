<template>
  <div class="library-page">
    <header class="section-page-header">
      <div>
        <h1>Exercise Library / 动作库</h1>
        <p>Browse and learn exercises with proper form guidance</p>
      </div>
      <button class="blue-action-button" type="button">
        <Plus :size="20" />
        Add Exercise
      </button>
    </header>

    <section class="filter-card library-filter-card">
      <label class="session-search">
        <Search :size="20" />
        <input type="search" placeholder="Search exercises... / 搜索动作..." />
      </label>
      <select><option>All / 全部</option></select>
      <select><option>All / 全部</option></select>
    </section>

    <section class="library-grid">
      <article v-for="exercise in libraryExercises" :key="exercise.name" class="library-card">
        <div class="exercise-hero">
          <span>{{ exercise.emoji }}</span>
        </div>
        <div class="library-card-body">
          <header>
            <div>
              <h2>{{ exercise.name }}</h2>
              <p>{{ exercise.category }}</p>
            </div>
            <span class="level-pill" :class="exercise.level.toLowerCase()">{{ exercise.level }}</span>
          </header>
          <p>{{ exercise.desc }}</p>
          <div class="library-meta-grid">
            <div><span>Duration</span><strong>{{ exercise.duration }}</strong></div>
            <div><span>Calories</span><strong>{{ exercise.calories }}</strong></div>
          </div>
          <div class="key-points-box">
            <strong>◎ Key Points / 要点</strong>
            <span v-for="point in exercise.points" :key="point">• {{ point }}</span>
          </div>
          <footer>
            <button class="tutorial-button" type="button">
              <Play :size="17" />
              Tutorial
            </button>
            <button class="details-button" type="button">
              <BookOpen :size="17" />
              Details
            </button>
          </footer>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { BookOpen, Play, Plus, Search } from "lucide-vue-next";

const libraryExercises = [
  { name: "Squat / 深蹲", category: "Lower Body / 下肢", level: "Intermediate", emoji: "🏋️", desc: "Basic lower body compound exercise", duration: "3-5 min", calories: "~45 kcal", points: ["Keep back straight", "Knees behind toes", "Full depth"] },
  { name: "Push-up / 俯卧撑", category: "Upper Body / 上肢", level: "Beginner", emoji: "💪", desc: "Classic upper body exercise", duration: "2-4 min", calories: "~35 kcal", points: ["Straight body line", "Elbows at 45°", "Full range of motion"] },
  { name: "Plank / 平板支撑", category: "Core / 核心", level: "Beginner", emoji: "🧘", desc: "Core stability exercise", duration: "2-3 min", calories: "~25 kcal", points: ["Engage core", "Neutral spine", "Hold steady"] },
  { name: "Lunge / 弓步蹲", category: "Lower Body / 下肢", level: "Intermediate", emoji: "🦵", desc: "Single leg lower body exercise", duration: "4-6 min", calories: "~50 kcal", points: ["Long enough step", "Knee stable", "Torso upright"] },
  { name: "Burpee / 波比跳", category: "Full Body / 全身", level: "Advanced", emoji: "🔥", desc: "High-intensity full body exercise", duration: "3-5 min", calories: "~65 kcal", points: ["Soft landing", "Core tight", "Explosive jump"] },
  { name: "Mountain Climber / 登山跑", category: "Core / 核心", level: "Intermediate", emoji: "⛰️", desc: "Dynamic core exercise", duration: "2-4 min", calories: "~55 kcal", points: ["Stable shoulders", "Fast knees", "Flat back"] }
];
</script>

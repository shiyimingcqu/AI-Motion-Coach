<template>
  <div class="exercise-library-page">
    <header class="section-page-header">
      <div>
        <h1>Exercise Library / 动作库</h1>
        <p>Browse and learn exercises with proper form guidance</p>
      </div>
      <div class="header-actions">
        <button class="blue-action-button" type="button" @click="showGallery = !showGallery">
          <component :is="showGallery ? 'Grid' : 'Layers'" :size="20" />
          {{ showGallery ? 'Grid View' : 'Gallery View' }}
        </button>
      </div>
    </header>

    <section class="filter-card library-filter-card">
      <label class="session-search">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input v-model="searchQuery" type="search" placeholder="Search exercises... / 搜索动作..." />
      </label>
      <select v-model="categoryFilter">
        <option value="">All / 全部</option>
        <option value="lower">Lower Body / 下肢</option>
        <option value="upper">Upper Body / 上肢</option>
        <option value="core">Core / 核心</option>
        <option value="full">Full Body / 全身</option>
      </select>
      <select v-model="levelFilter">
        <option value="">All / 全部</option>
        <option value="beginner">Beginner / 初级</option>
        <option value="intermediate">Intermediate / 中级</option>
        <option value="advanced">Advanced / 高级</option>
      </select>
    </section>

    <!-- Gallery View -->
    <section v-if="showGallery" class="gallery-section">
      <StateDisplay v-if="loading" type="loading" skeleton="cards" text="加载动作库..." />
      <StateDisplay v-else-if="galleryItems.length === 0" type="empty" title="暂无动作数据" text="后端服务未连接或动作库为空，请在管理页面添加动作" />
      <template v-else>
        <div class="gallery-container">
          <CircularGallery
            :items="galleryItems"
            :bend="3"
            textColor="#f8fafc"
            :borderRadius="0.06"
            font="bold 28px 'Microsoft YaHei', sans-serif"
            :scrollSpeed="2"
            :scrollEase="0.05"
            @on-item-click="handleGalleryClick"
          />
        </div>
        <div class="gallery-footer">
          <span class="gallery-hint">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
            Scroll or drag to explore
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
          </span>
        </div>
      </template>
    </section>

    <!-- Grid View -->
    <section v-else class="library-grid">
      <StateDisplay v-if="loading" type="loading" skeleton="cards" text="加载动作库..." />
      <StateDisplay v-else-if="filteredExercises.length === 0" type="empty" title="暂无匹配动作" text="尝试调整筛选条件或检查后端服务是否运行" />
      <article v-for="exercise in filteredExercises" :key="exercise.name" class="library-card">
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
            <button class="tutorial-button" type="button" @click="startTraining(exercise.exerciseKey)">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
              开始训练
            </button>
            <button class="details-button" type="button">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
              Details
            </button>
          </footer>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import CircularGallery from "@/components/CircularGallery.vue";
import { useTrainingStore } from "@/stores/training";
import { getSimpleExercises, type ExerciseLibItem } from "@/api/exercises";
import StateDisplay from "@/components/StateDisplay.vue";

const router = useRouter();
const store = useTrainingStore();
const showGallery = ref(true);
const searchQuery = ref("");
const categoryFilter = ref("");
const levelFilter = ref("");
const loading = ref(true);
const backendExercises = ref<ExerciseLibItem[]>([]);

const libraryExercises = computed(() =>
  backendExercises.value.length > 0
    ? backendExercises.value.map(e => {
        const catMap: Record<string, string> = {
          squat: "Lower Body / 下肢", push_up: "Upper Body / 上肢",
          jumping_jack: "Cardio / 心肺", plank: "Core / 核心",
          lunge: "Lower Body / 下肢", burpee: "Full Body / 全身",
          mountain_climber: "Core / 核心", pull_up: "Upper Body / 上肢",
          dumbbell_curl: "Upper Body / 上肢", dumbbell_press: "Upper Body / 上肢",
          high_knees: "Cardio / 心肺", russian_twist: "Core / 核心",
          glute_bridge: "Lower Body / 下肢",
        };
        const catKeyMap: Record<string, string> = {
          squat: "lower", push_up: "upper", jumping_jack: "cardio", plank: "core",
          lunge: "lower", burpee: "full", mountain_climber: "core", pull_up: "upper",
          dumbbell_curl: "upper", dumbbell_press: "upper",
          high_knees: "cardio", russian_twist: "core", glute_bridge: "lower",
        };
        const levelMap: Record<string, string> = {
          squat: "Intermediate", push_up: "Intermediate",
          jumping_jack: "Beginner", plank: "Advanced",
          lunge: "Intermediate", burpee: "Advanced",
          mountain_climber: "Intermediate", pull_up: "Advanced",
          dumbbell_curl: "Beginner", dumbbell_press: "Intermediate",
          high_knees: "Beginner", russian_twist: "Intermediate", glute_bridge: "Beginner",
        };
        const levelKeyMap: Record<string, string> = {
          squat: "intermediate", push_up: "intermediate",
          jumping_jack: "beginner", plank: "advanced",
          lunge: "intermediate", burpee: "advanced",
          mountain_climber: "intermediate", pull_up: "advanced",
          dumbbell_curl: "beginner", dumbbell_press: "intermediate",
          high_knees: "beginner", russian_twist: "intermediate", glute_bridge: "beginner",
        };
        const emojiMap: Record<string, string> = {
          squat: "🦵", push_up: "💪", jumping_jack: "🔥", plank: "🧘",
          lunge: "🦵", burpee: "🔥", mountain_climber: "⛰️", pull_up: "💪",
          dumbbell_curl: "💪", dumbbell_press: "💪",
          high_knees: "🏃", russian_twist: "🧘", glute_bridge: "🦵",
        };
        // 使用真实运动图片 Unsplash
        const imgMap: Record<string, string> = {
          squat: "https://images.unsplash.com/photo-1574680178050-55c6a6a96e0a?w=800&h=600&fit=crop",
          push_up: "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=800&h=600&fit=crop",
          jumping_jack: "https://images.unsplash.com/photo-1534258936925-c58bed479fcb?w=800&h=600&fit=crop",
          plank: "https://images.unsplash.com/photo-1566241142559-40e1dab0cec6?w=800&h=600&fit=crop",
          lunge: "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?w=800&h=600&fit=crop",
          burpee: "https://images.unsplash.com/photo-1534258936925-c58bed479fcb?w=800&h=600&fit=crop",
          mountain_climber: "https://images.unsplash.com/photo-1599058917765-a780eda07a3e?w=800&h=600&fit=crop",
          pull_up: "https://images.unsplash.com/photo-1598971639058-abcdab3c3b0a?w=800&h=600&fit=crop",
          dumbbell_curl: "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&h=600&fit=crop",
          dumbbell_press: "https://images.unsplash.com/photo-1534367610401-9f5b681c06f6?w=800&h=600&fit=crop",
          high_knees: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop",
          russian_twist: "https://images.unsplash.com/photo-1566241142559-40e1dab0cec6?w=800&h=600&fit=crop",
          glute_bridge: "https://images.unsplash.com/photo-1574680178050-55c6a6a96e0a?w=800&h=600&fit=crop",
        };
        return {
          name: e.name,
          category: catMap[e.key] || "General / 通用",
          categoryKey: catKeyMap[e.key] || "general",
          level: levelMap[e.key] || "Intermediate",
          levelKey: levelKeyMap[e.key] || "intermediate",
          exerciseKey: e.key,
          emoji: emojiMap[e.key] || "🏋️",
          desc: e.description || "Exercise with proper form guidance",
          duration: "3-5 min",
          calories: "~45 kcal",
          points: ["Good form", "Full range", "Control"],
          image: imgMap[e.key] || "https://images.unsplash.com/photo-1574680178050-55c6a6a96e0a?w=800&h=600&fit=crop",
        };
      })
    : []
);

const galleryItems = computed(() =>
  libraryExercises.value.map(e => ({
    image: e.image,
    text: e.name.split(" / ")[0],
    category: e.category,
    level: e.level,
    emoji: e.emoji,
    exerciseKey: e.exerciseKey,
  }))
);

function startTraining(exerciseKey: string) {
  store.setExercise(exerciseKey);
  router.push("/realtime");
}

function handleGalleryClick(index: number) {
  const item = galleryItems.value[index];
  if (item?.exerciseKey) {
    startTraining(item.exerciseKey);
  }
}

const filteredExercises = computed(() =>
  libraryExercises.value.filter(e => {
    const matchesSearch = !searchQuery.value || e.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || e.category.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchesCategory = !categoryFilter.value || e.categoryKey === categoryFilter.value;
    const matchesLevel = !levelFilter.value || e.levelKey === levelFilter.value;
    return matchesSearch && matchesCategory && matchesLevel;
  })
);

onMounted(async () => {
  try {
    const data = await getSimpleExercises();
    backendExercises.value = data.items;
  } catch {
    // fallback to empty — StateDisplay will show
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
/* ── layout ── */
.exercise-library-page { display: grid; gap: 26px; }

.library-page-header {
  display: flex; align-items: center; justify-content: space-between; gap: 18px;
}

/* ── gallery section ── */
.gallery-section { display: grid; gap: 16px; }

.gallery-container {
  width: 100%; height: 520px; position: relative;
  border-radius: 16px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(8,13,26,0.5), rgba(15,23,42,0.3));
  border: 1px solid rgba(59,130,246,0.08);
  box-shadow: 0 8px 40px rgba(0,0,0,0.3);
}

.gallery-footer {
  display: flex; justify-content: center;
}

.gallery-hint {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 8px 20px;
  border-radius: 999px;
  background: rgba(15,23,42,0.7);
  color: #64748b; font-size: 13px;
  border: 1px solid rgba(59,130,246,0.08);
}

.gallery-hint svg { color: #475569; }

/* ── header ── */
:deep(.section-page-header) {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 18px;
}
:deep(.section-page-header h1) { color: #071225; font-size: 34px; letter-spacing: -0.045em; }
:deep(.section-page-header p) { margin-top: 5px; color: #536179; font-size: 15px; }

.header-actions { display: flex; gap: 10px; flex-shrink: 0; }

/* ── filter ── */
.filter-card {
  display: grid; grid-template-columns: minmax(360px, 1fr) 180px 140px;
  gap: 16px; padding: 16px;
  background: rgba(15,23,42,0.92); border: 1px solid rgba(59,130,246,0.12);
  border-radius: 12px; align-items: center;
}
.session-search {
  min-height: 42px; display: flex; align-items: center; gap: 10px;
  padding: 0 16px; border: 1px solid rgba(59,130,246,0.1);
  border-radius: 9px; background: rgba(8,13,26,0.8); color: #64748b;
}
.session-search svg { color: #475569; flex-shrink: 0; }
.session-search input {
  width: 100%; min-width: 0; border: 0; outline: 0;
  background: transparent; color: #f8fafc; font-size: 14px;
}
.session-search input::placeholder { color: #475569; }
.filter-card select {
  min-height: 42px; border: 1px solid rgba(59,130,246,0.1);
  border-radius: 9px; background: rgba(8,13,26,0.8);
  color: #cbd5e1; padding: 0 14px; font-size: 14px;
}

/* ── grid cards ── */
.library-grid { display: grid; grid-template-columns: repeat(3, minmax(280px, 1fr)); gap: 24px; }
.library-card { overflow: hidden; border-radius: 14px; background: rgba(15,23,42,0.96); border: 1px solid rgba(59,130,246,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.2); }
.exercise-hero { height: 200px; display: grid; place-items: center; background: linear-gradient(135deg, #3b82f6, #8b5cf6); }
.exercise-hero span { font-size: 52px; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.3)); }
.library-card-body { display: grid; gap: 16px; padding: 24px; }
.library-card-body header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.library-card-body h2 { font-size: 20px; color: #f8fafc; margin: 0; }
.library-card-body p { color: #64748b; margin: 0; font-size: 14px; }
.level-pill { min-height: 24px; padding: 0 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.level-pill { background: rgba(16,185,129,0.12); color: #34d399; }
.level-pill.intermediate { background: rgba(59,130,246,0.12); color: #93c5fd; }
.level-pill.advanced { background: rgba(239,68,68,0.12); color: #f87171; }
.library-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.library-meta-grid div { display: grid; gap: 6px; padding: 12px; border-radius: 8px; background: rgba(8,13,26,0.4); }
.library-meta-grid span { color: #64748b; font-size: 12px; }
.library-meta-grid strong { color: #f8fafc; font-size: 15px; }
.key-points-box { display: grid; gap: 6px; padding: 14px; border-radius: 8px; background: rgba(59,130,246,0.06); color: #93c5fd; font-size: 13px; border: 1px solid rgba(59,130,246,0.08); }
.key-points-box strong { font-size: 13px; }
.library-card footer { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.tutorial-button, .details-button {
  min-height: 38px; display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer;
}
.tutorial-button { border: 0; background: linear-gradient(135deg, #3b82f6, #6366f1); color: #fff; }
.details-button { border: 1px solid rgba(59,130,246,0.1); background: rgba(8,13,26,0.5); color: #cbd5e1; }

.blue-action-button {
  min-height: 42px; display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 0 18px; border: 0; border-radius: 9px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff; font-size: 14px; font-weight: 600; cursor: pointer;
  white-space: nowrap;
}

@media (max-width: 1200px) { .library-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 900px) { .library-grid { grid-template-columns: 1fr; } }
@media (max-width: 1100px) {
  .filter-card { grid-template-columns: 1fr; }
  .gallery-container { height: 380px; }
}
</style>

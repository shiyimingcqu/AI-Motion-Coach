<template>
  <div class="exercise-library-page">
    <header class="section-page-header">
      <div>
        <h1>{{ $t("exerciseLibrary.title") }}</h1>
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
        <input v-model="searchQuery" type="search" :placeholder="$t('exerciseLibrary.search')" />
      </label>
      <select v-model="categoryFilter">
        <option value="">{{ $t("exerciseLibrary.category_all") }}</option>
        <option value="lower">{{ $t("exerciseLibrary.category_lower") }}</option>
        <option value="upper">{{ $t("exerciseLibrary.category_upper") }}</option>
        <option value="core">{{ $t("exerciseLibrary.category_core") }}</option>
        <option value="full">{{ $t("exerciseLibrary.category_full") }}</option>
      </select>
      <select v-model="levelFilter">
        <option value="">{{ $t("exerciseLibrary.level_all") }}</option>
        <option value="beginner">{{ $t("exerciseLibrary.level_beginner") }}</option>
        <option value="intermediate">{{ $t("exerciseLibrary.level_intermediate") }}</option>
        <option value="advanced">{{ $t("exerciseLibrary.level_advanced") }}</option>
      </select>
    </section>

    <!-- Gallery View -->
    <section v-if="showGallery" class="gallery-section">
      <StateDisplay v-if="loading" type="loading" skeleton="cards" :text="$t('exerciseLibrary.loading')" />
      <StateDisplay v-else-if="galleryItems.length === 0" type="empty" :title="$t('exerciseLibrary.noData')" :text="$t('exerciseLibrary.noDataText')" />
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
      <StateDisplay v-if="loading" type="loading" skeleton="cards" :text="$t('exerciseLibrary.loading')" />
      <StateDisplay v-else-if="filteredExercises.length === 0" type="empty" :title="$t('exerciseLibrary.noMatch')" :text="$t('exerciseLibrary.noMatchText')" />
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
            <span class="level-pill" :class="exercise.levelKey">{{ exercise.level }}</span>
          </header>
          <p>{{ exercise.desc }}</p>
          <div class="library-meta-grid">
            <div><span>Duration</span><strong>{{ exercise.duration }}</strong></div>
            <div><span>Calories</span><strong>{{ exercise.calories }}</strong></div>
          </div>
          <div class="key-points-box">
            <strong>◎ {{ $t("exerciseLibrary.keyPoints") }}</strong>
            <span v-for="point in exercise.points" :key="point">• {{ point }}</span>
          </div>
          <footer>
            <button class="tutorial-button" type="button" @click="startTraining(exercise.exerciseKey)">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
              {{ $t("exerciseLibrary.startTraining") }}
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
import { useI18n } from "vue-i18n";
import CircularGallery from "@/components/CircularGallery.vue";
import { exercises, SUPPORTED_EXERCISE_KEYS, useTrainingStore } from "@/stores/training";
import { getSimpleExercises, type ExerciseLibItem } from "@/api/exercises";
import StateDisplay from "@/components/StateDisplay.vue";

const { t } = useI18n();
const router = useRouter();
const store = useTrainingStore();
const showGallery = ref(true);
const searchQuery = ref("");
const categoryFilter = ref("");
const levelFilter = ref("");
const loading = ref(true);
const backendExercises = ref<ExerciseLibItem[]>([]);

const libraryExercises = computed(() => {
  const allowed = new Set<string>(SUPPORTED_EXERCISE_KEYS);
  const source = backendExercises.value.length > 0
    ? backendExercises.value.filter((item) => allowed.has(item.key))
    : exercises;
  return source.map(e => {
        const catMap: Record<string, string> = {
          squat: t("categories.lower_body"), push_up: t("categories.upper_body"),
          jumping_jack: t("categories.cardio"), plank: t("categories.core"),
          lunge: t("categories.lower_body"), burpee: t("categories.full_body"),
          mountain_climber: t("categories.core"), pull_up: t("categories.upper_body"),
          dumbbell_curl: t("categories.upper_body"), dumbbell_press: t("categories.upper_body"),
          high_knees: t("categories.cardio"), russian_twist: t("categories.core"),
          glute_bridge: t("categories.lower_body"),
        };
        const catKeyMap: Record<string, string> = {
          squat: "lower", push_up: "upper", jumping_jack: "cardio", plank: "core",
          lunge: "lower", burpee: "full", mountain_climber: "core", pull_up: "upper",
          dumbbell_curl: "upper", dumbbell_press: "upper",
          high_knees: "cardio", russian_twist: "core", glute_bridge: "lower",
        };
        const levelMap: Record<string, string> = {
          squat: t("exerciseLibrary.level_intermediate"), push_up: t("exerciseLibrary.level_intermediate"),
          jumping_jack: t("exerciseLibrary.level_beginner"), plank: t("exerciseLibrary.level_advanced"),
          lunge: t("exerciseLibrary.level_intermediate"), burpee: t("exerciseLibrary.level_advanced"),
          mountain_climber: t("exerciseLibrary.level_intermediate"), pull_up: t("exerciseLibrary.level_advanced"),
          dumbbell_curl: t("exerciseLibrary.level_beginner"), dumbbell_press: t("exerciseLibrary.level_intermediate"),
          high_knees: t("exerciseLibrary.level_beginner"), russian_twist: t("exerciseLibrary.level_intermediate"), glute_bridge: t("exerciseLibrary.level_beginner"),
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
          category: catMap[e.key] || t("common.all"),
          categoryKey: catKeyMap[e.key] || "general",
          level: levelMap[e.key] || t("exerciseLibrary.level_intermediate"),
          levelKey: levelKeyMap[e.key] || "intermediate",
          exerciseKey: e.key,
          emoji: emojiMap[e.key] || "🏋️",
          desc: e.description || "Exercise with proper form guidance",
          duration: "3-5 min",
          calories: "~45 kcal",
          points: ["Good form", "Full range", "Control"],
          image: imgMap[e.key] || "https://images.unsplash.com/photo-1574680178050-55c6a6a96e0a?w=800&h=600&fit=crop",
        };
      });
});

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
  background: linear-gradient(180deg, #f8fbff, #ffffff);
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.gallery-footer {
  display: flex; justify-content: center;
}

.gallery-hint {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 8px 20px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #64748b; font-size: 13px;
  border: 1px solid #e2e8f0;
}

.gallery-hint svg { color: #94a3b8; }

/* ── header ── */
:deep(.section-page-header) {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 18px;
}
:deep(.section-page-header h1) { color: #0f172a; font-size: 34px; letter-spacing: -0.045em; }
:deep(.section-page-header p) { margin-top: 5px; color: #64748b; font-size: 15px; }

.header-actions { display: flex; gap: 10px; flex-shrink: 0; }

/* ── filter ── */
.filter-card {
  display: grid; grid-template-columns: minmax(360px, 1fr) 180px 140px;
  gap: 16px; padding: 16px;
  background: #ffffff; border: 1px solid #e2e8f0;
  border-radius: 12px; align-items: center;
}
.session-search {
  min-height: 42px; display: flex; align-items: center; gap: 10px;
  padding: 0 16px; border: 1px solid #e2e8f0;
  border-radius: 9px; background: #f8fbff; color: #94a3b8;
}
.session-search svg { color: #94a3b8; flex-shrink: 0; }
.session-search input {
  width: 100%; min-width: 0; border: 0; outline: 0;
  background: transparent; color: #0f172a; font-size: 14px;
}
.session-search input::placeholder { color: #94a3b8; }
.filter-card select {
  min-height: 42px; border: 1px solid #e2e8f0;
  border-radius: 9px; background: #f8fbff;
  color: #0f172a; padding: 0 14px; font-size: 14px;
}

/* ── grid cards ── */
.library-grid { display: grid; grid-template-columns: repeat(3, minmax(280px, 1fr)); gap: 24px; }
.library-card { overflow: hidden; border-radius: 14px; background: #ffffff; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.exercise-hero { height: 200px; display: grid; place-items: center; background: linear-gradient(135deg, #5b8cff, #8b5cf6); }
.exercise-hero span { font-size: 52px; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.1)); }
.library-card-body { display: grid; gap: 16px; padding: 24px; }
.library-card-body header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.library-card-body h2 { font-size: 20px; color: #0f172a; margin: 0; }
.library-card-body p { color: #64748b; margin: 0; font-size: 14px; }
.level-pill { min-height: 24px; padding: 0 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.level-pill { background: rgba(16,185,129,0.12); color: #25b87b; }
.level-pill.intermediate { background: rgba(91,140,255,0.12); color: #5b8cff; }
.level-pill.advanced { background: rgba(239,68,68,0.12); color: #ef4444; }
.library-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.library-meta-grid div { display: grid; gap: 6px; padding: 12px; border-radius: 8px; background: #f8fbff; }
.library-meta-grid span { color: #94a3b8; font-size: 12px; }
.library-meta-grid strong { color: #0f172a; font-size: 15px; }
.key-points-box { display: grid; gap: 6px; padding: 14px; border-radius: 8px; background: rgba(91,140,255,0.06); color: #5b8cff; font-size: 13px; border: 1px solid #d6e3ff; }
.key-points-box strong { font-size: 13px; }
.library-card footer { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.tutorial-button, .details-button {
  min-height: 38px; display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer;
}
.tutorial-button { border: 0; background: linear-gradient(135deg, #5b8cff, #4f46e5); color: #fff; }
.details-button { border: 1px solid #e2e8f0; background: #f8fbff; color: #475569; }

.blue-action-button {
  min-height: 42px; display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 0 18px; border: 0; border-radius: 9px;
  background: linear-gradient(135deg, #5b8cff, #4f46e5);
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

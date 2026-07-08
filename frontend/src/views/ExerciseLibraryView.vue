<template>
  <div class="el-page">
    <!-- 顶部 -->
    <header class="el-header">
      <p class="el-subtitle">科学动作，改善姿态，练出更好的自己</p>
    </header>

    <!-- 搜索 + 筛选 -->
    <section class="el-bar">
      <div class="el-search">
        <Search :size="16" />
        <input v-model="searchQuery" type="search" placeholder="搜索动作名称，如：深蹲、俯卧撑" />
      </div>
      <div class="el-tabs">
        <button
          v-for="cat in categories"
          :key="cat.key"
          type="button"
          class="el-tab"
          :class="{ active: categoryFilter === cat.key }"
          @click="categoryFilter = cat.key"
        >
          {{ cat.label }}
        </button>
      </div>
    </section>

    <!-- 加载/空状态 -->
    <StateDisplay v-if="loading" type="loading" skeleton="cards" :skeleton-rows="2" text="加载动作库..." />
    <StateDisplay v-else-if="allExercises.length === 0" type="empty" title="暂无动作数据" text="请检查网络连接后重试" />

    <template v-else>
      <!-- 推荐给你 -->
      <section v-if="recommendedExercises.length > 0" class="el-section">
        <div class="el-section-header">
          <h2 class="el-section-title">
            <Star :size="16" class="el-star" />
            推荐给你
          </h2>
          <button class="el-refresh" type="button" @click="refreshRecommended">
            <RefreshCw :size="14" />
            换一批
          </button>
        </div>
        <div class="el-grid">
          <article
            v-for="ex in recommendedExercises"
            :key="ex.key"
            class="el-card"
            @click="goToDetail(ex.key)"
          >
            <div class="el-card-img" :style="{ background: ex.accent || '#f1f5f9' }">
              <ExerciseIllustration :key="ex.key" :type="ex.key" />
            </div>
            <div class="el-card-body">
              <div class="el-card-top">
                <h3>{{ ex.name }}</h3>
                <span class="el-badge" :class="ex.supported ? 'badge-on' : 'badge-off'">
                  {{ ex.supported ? '已支持' : '测试中' }}
                </span>
              </div>
              <p class="el-card-desc">{{ ex.description }}</p>
              <div class="el-card-tags">
                <span class="el-tag">{{ ex.level }}</span>
                <span class="el-tag" v-if="ex.equipment">{{ ex.equipment }}</span>
                <span class="el-tag" v-if="ex.camera_view">{{ cameraLabels[ex.camera_view] || ex.camera_view }}拍摄</span>
              </div>
              <div class="el-card-actions">
                <button class="el-btn-detail" type="button" @click.stop="goToDetail(ex.key)">
                  查看教学
                </button>
                <button class="el-btn-train" type="button" @click.stop="startTraining(ex.key)">
                  开始训练
                </button>
              </div>
            </div>
          </article>
        </div>
      </section>

      <!-- 全部动作 -->
      <section class="el-section">
        <h2 class="el-section-title">全部动作</h2>
        <div class="el-grid">
          <article
            v-for="ex in filteredExercises"
            :key="ex.key"
            class="el-card"
            @click="goToDetail(ex.key)"
          >
            <div class="el-card-img" :style="{ background: ex.accent || '#f1f5f9' }">
              <ExerciseIllustration :key="ex.key" :type="ex.key" />
            </div>
            <div class="el-card-body">
              <div class="el-card-top">
                <h3>{{ ex.name }}</h3>
                <span class="el-badge" :class="ex.supported ? 'badge-on' : 'badge-off'">
                  {{ ex.supported ? '已支持' : '测试中' }}
                </span>
              </div>
              <p class="el-card-desc">{{ ex.description }}</p>
              <div class="el-card-tags">
                <span class="el-tag">{{ ex.level }}</span>
                <span class="el-tag" v-if="ex.equipment">{{ ex.equipment }}</span>
                <span class="el-tag" v-if="ex.camera_view">{{ cameraLabels[ex.camera_view] || ex.camera_view }}拍摄</span>
              </div>
              <div class="el-card-actions">
                <button class="el-btn-detail" type="button" @click.stop="goToDetail(ex.key)">
                  查看教学
                </button>
                <button class="el-btn-train" type="button" @click.stop="startTraining(ex.key)">
                  开始训练
                </button>
              </div>
            </div>
          </article>
        </div>
      </section>
    </template>

    <!-- 二维码弹窗 -->
    <TrainQRModal
      v-if="showQR"
      :exercise-name="qrExercise.name"
      :exercise-key="qrExercise.key"
      :camera-view="qrExercise.cameraView"
      @close="showQR = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { RefreshCw, Search, Star } from "lucide-vue-next";
import StateDisplay from "@/components/StateDisplay.vue";
import TrainQRModal from "@/components/TrainQRModal.vue";
import ExerciseIllustration from "@/components/ExerciseIllustration.vue";
import { getSimpleExercises, type ExerciseLibItem } from "@/api/exercises";

const { t } = useI18n();
const router = useRouter();

const searchQuery = ref("");
const categoryFilter = ref("");
const loading = ref(true);
const showQR = ref(false);
const qrExercise = ref<{ key: string; name: string; cameraView: string }>({ key: "", name: "", cameraView: "front" });
const backendExercises = ref<ExerciseLibItem[]>([]);

const categories = [
  { key: "", label: "全部" },
  { key: "lower", label: "下肢" },
  { key: "upper", label: "上肢" },
  { key: "core", label: "核心" },
  { key: "full", label: "全身" },
  { key: "cardio", label: "心肺" },
];

const cameraLabels: Record<string, string> = {
  side: "侧面",
  front: "正面",
  "45deg": "45°",
};

const exerciseMeta: Record<string, {
  catKey: string;
  level: string;
  emoji: string;
  equipment: string;
  camera_view: string;
  supported: boolean;
  accent: string;
  recommended: boolean;
}> = {
  squat: { catKey: "lower", level: "入门", emoji: "🦵", equipment: "无器械", camera_view: "side", supported: true, accent: "#ecfdf5", recommended: true },
  push_up: { catKey: "upper", level: "入门", emoji: "💪", equipment: "无器械", camera_view: "side", supported: true, accent: "#fef2f2", recommended: true },
  jumping_jack: { catKey: "cardio", level: "入门", emoji: "🔥", equipment: "无器械", camera_view: "front", supported: true, accent: "#eff6ff", recommended: true },
  plank: { catKey: "core", level: "入门", emoji: "🧘", equipment: "瑜伽垫", camera_view: "side", supported: true, accent: "#f5f3ff", recommended: false },
  lunge: { catKey: "lower", level: "入门", emoji: "🦵", equipment: "无器械", camera_view: "side", supported: true, accent: "#e9f4eb", recommended: false },
  burpee: { catKey: "full", level: "进阶", emoji: "🔥", equipment: "无器械", camera_view: "front", supported: true, accent: "#f0e4ed", recommended: false },
  high_knees: { catKey: "cardio", level: "入门", emoji: "🏃", equipment: "无器械", camera_view: "front", supported: true, accent: "#d9e3f0", recommended: false },
  glute_bridge: { catKey: "lower", level: "入门", emoji: "🦵", equipment: "瑜伽垫", camera_view: "side", supported: true, accent: "#f0dcd8", recommended: false },
  bench_press: { catKey: "upper", level: "中等", emoji: "💪", equipment: "哑铃/杠铃", camera_view: "side", supported: false, accent: "#fceadf", recommended: false },
  pull_up: { catKey: "upper", level: "进阶", emoji: "💪", equipment: "单杠", camera_view: "side", supported: false, accent: "#dfdacd", recommended: false },
  barbell_squat: { catKey: "lower", level: "进阶", emoji: "🦵", equipment: "杠铃", camera_view: "side", supported: false, accent: "#f0e7f8", recommended: false },
  mountain_climber: { catKey: "cardio", level: "中等", emoji: "⛰️", equipment: "无器械", camera_view: "side", supported: false, accent: "#e6f5f5", recommended: false },
  dumbbell_fly: { catKey: "upper", level: "中等", emoji: "💪", equipment: "哑铃", camera_view: "side", supported: false, accent: "#e6f5eb", recommended: false },
  lat_pulldown: { catKey: "upper", level: "中等", emoji: "💪", equipment: "拉力器", camera_view: "side", supported: false, accent: "#e5f0fb", recommended: false },
  dumbbell_curl: { catKey: "upper", level: "入门", emoji: "💪", equipment: "哑铃", camera_view: "side", supported: false, accent: "#fef6e5", recommended: false },
  dumbbell_press: { catKey: "upper", level: "中等", emoji: "💪", equipment: "哑铃", camera_view: "side", supported: false, accent: "#fcebea", recommended: false },
  dumbbell_shoulder_press: { catKey: "upper", level: "中等", emoji: "💪", equipment: "哑铃", camera_view: "side", supported: false, accent: "#e4eef8", recommended: false },
  russian_twist: { catKey: "core", level: "中等", emoji: "🧘", equipment: "无器械", camera_view: "front", supported: false, accent: "#fefce8", recommended: false },
};

const allExercises = computed(() =>
  backendExercises.value.map(e => {
    const meta = exerciseMeta[e.key] || { catKey: "general", level: "入门", emoji: "🏋️", equipment: "无器械", camera_view: "front", supported: false, accent: "#f1f5f9", recommended: false };
    return {
      key: e.key,
      name: e.name,
      description: e.description || getDefaultDesc(e.key),
      catKey: meta.catKey,
      level: meta.level,
      emoji: meta.emoji,
      equipment: meta.equipment,
      camera_view: meta.camera_view,
      supported: meta.supported,
      accent: meta.accent,
      recommended: meta.recommended,
    };
  })
);

const recommendedExercises = computed(() =>
  allExercises.value.filter(e => e.recommended)
);

const filteredExercises = computed(() => {
  let list = allExercises.value;
  if (categoryFilter.value) {
    list = list.filter(e => e.catKey === categoryFilter.value);
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase();
    list = list.filter(e =>
      e.name.toLowerCase().includes(q) || e.description.toLowerCase().includes(q)
    );
  }
  return list;
});

function goToDetail(key: string) {
  router.push(`/exercises/${key}`);
}

function startTraining(key: string) {
  const ex = allExercises.value.find(e => e.key === key);
  qrExercise.value = {
    key,
    name: ex?.name || key,
    cameraView: ex?.camera_view || "front",
  };
  showQR.value = true;
}

function refreshRecommended() {}

function getDefaultDesc(key: string): string {
  const m: Record<string, string> = {
    squat: "强化下肢力量，改善体态稳定性。",
    push_up: "增强上肢力量，提升身体控制力。",
    jumping_jack: "提升心肺耐力，促进全身协调。",
    plank: "增强核心力量，改善身体稳定性。",
    lunge: "锻炼腿部力量与平衡，改善体态。",
    burpee: "全身高强度燃脂，提升心肺功能。",
    high_knees: "提升心率，锻炼下肢爆发力。",
    glute_bridge: "激活臀部与核心，改善体态。",
    bench_press: "胸肌与上肢力量训练。",
    pull_up: "背部与上肢力量训练。",
    barbell_squat: "负重深蹲，增强下肢力量。",
    mountain_climber: "核心与心肺训练。",
    dumbbell_fly: "胸肌塑形训练。",
    lat_pulldown: "背部肌群训练。",
    dumbbell_curl: "肱二头肌训练。",
    dumbbell_press: "肩部与上肢训练。",
    dumbbell_shoulder_press: "肩部塑形训练。",
    russian_twist: "核心旋转稳定性训练。",
  };
  return m[key] || "标准动作训练";
}

onMounted(async () => {
  try {
    const data = await getSimpleExercises();
    backendExercises.value = data.items || [];
  } catch {
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
/* ===== 页面容器 ===== */
.el-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ===== 顶部 ===== */
.el-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.el-subtitle {
  font-size: 13px;
  color: #64748b;
  margin: 4px 0 0;
}

/* ===== 搜索 + 筛选 ===== */
.el-bar {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.el-search {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 480px;
  padding: 10px 16px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #fff;
  transition: border-color 0.2s;
}

.el-search:focus-within {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.08);
}

.el-search input {
  border: 0;
  outline: 0;
  flex: 1;
  font-size: 14px;
  color: #334155;
  background: transparent;
}

.el-search input::placeholder {
  color: #94a3b8;
}

.el-search svg {
  color: #94a3b8;
  flex-shrink: 0;
}

.el-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.el-tab {
  padding: 5px 18px;
  border-radius: 20px;
  border: 1px solid transparent;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.el-tab:hover {
  color: #8b5cf6;
  background: #f5f3ff;
}

.el-tab.active {
  background: #8b5cf6;
  color: #fff;
  border-color: #8b5cf6;
}

/* ===== 分区 ===== */
.el-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.el-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.el-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 700;
  color: #101828;
  margin: 0;
}

.el-star {
  color: #f59e0b;
}

.el-refresh {
  display: flex;
  align-items: center;
  gap: 4px;
  background: transparent;
  border: 0;
  color: #8b5cf6;
  font-size: 13px;
  cursor: pointer;
  transition: color 0.2s;
}

.el-refresh:hover {
  color: #6d28d9;
}

/* ===== 卡片网格：4 列竖版 ===== */
.el-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 22px;
}

@media (max-width: 1280px) {
  .el-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 960px) {
  .el-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 560px) {
  .el-grid {
    grid-template-columns: 1fr;
  }
}

/* ===== 竖版卡片 ===== */
.el-card {
  position: relative;
  border-radius: 18px;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: 0 12px 30px rgba(87, 102, 140, 0.08);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  flex-direction: column;
  min-height: 376px;
}

.el-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(139, 92, 246, 0.18);
  border-color: #c4b5fd;
}

.el-card-img {
  position: relative;
  width: 100%;
  aspect-ratio: 370 / 208;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.el-card-body {
  padding: 16px 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fff;
  flex: 1;
}

.el-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.el-card-top h3 {
  font-size: 19px;
  font-weight: 900;
  color: #101828;
  margin: 0;
  line-height: 1.2;
}

.el-card-desc {
  font-size: 13px;
  color: #64748b;
  margin: 0;
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.el-card-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.el-card-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f1f5f9;
}

/* ===== 通用标签 ===== */
.el-badge {
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
}

.badge-on {
  background: #dcfce7;
  color: #16a34a;
}

.badge-off {
  background: #fef3c7;
  color: #d97706;
}

.el-tag {
  padding: 5px 12px;
  border-radius: 9px;
  background: #f1f5f9;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

/* ===== 按钮 ===== */
.el-btn-detail,
.el-btn-train {
  flex: 1;
  min-width: 0;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
  text-align: center;
}

.el-btn-detail {
  background: #fff;
  color: #475569;
  border-color: #e2e8f0;
}

.el-btn-detail:hover {
  background: #f1f5f9;
  color: #334155;
  border-color: #cbd5e1;
}

.el-btn-train {
  background: #8b5cf6;
  color: #fff;
}

.el-btn-train:hover {
  background: #7c3aed;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}
</style>

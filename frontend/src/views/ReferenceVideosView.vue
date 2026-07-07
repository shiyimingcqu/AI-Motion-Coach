<template>
  <div class="ref-videos-page">
    <header class="ref-header">
      <button class="back-btn" @click="router.push('/')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M19 12H5" /><path d="m12 5-7 7 7 7" />
        </svg>
        返回
      </button>
      <div class="ref-header-info">
        <h1>标准视频参考</h1>
        <p>观看标准动作示范，对照自己的分析视频进行改进</p>
      </div>
    </header>

    <!-- 过滤栏 -->
    <div class="filter-bar">
      <select v-model="filterExercise" class="filter-select">
        <option value="">全部动作</option>
        <option value="squat">深蹲</option>
        <option value="push_up">俯卧撑</option>
        <option value="plank">平板支撑</option>
        <option value="lunge">弓步蹲</option>
        <option value="jumping_jack">开合跳</option>
        <option value="burpee">波比跳</option>
        <option value="high_knees">高抬腿</option>
      </select>
      <select v-model="filterView" class="filter-select">
        <option value="">全部视角</option>
        <option value="front">正面</option>
        <option value="side">侧面</option>
      </select>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="ref-empty">
      <div class="loading-ring"></div>
      <span>加载中...</span>
    </div>

    <!-- 空状态 -->
    <div v-else-if="filteredVideos.length === 0" class="ref-empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.5">
        <rect x="2" y="2" width="20" height="20" rx="4" /><polygon points="10,8 16,12 10,16" fill="#cbd5e1" />
      </svg>
      <p>暂无标准视频</p>
      <small>请联系管理员上传标准参考视频</small>
    </div>

    <!-- 视频网格 -->
    <div v-else class="ref-grid">
      <div
        v-for="v in filteredVideos"
        :key="v.id"
        class="ref-card"
        :class="{ active: activeId === v.id }"
        @click="selectVideo(v)"
      >
        <div class="ref-card-preview">
          <video
            v-if="activeId === v.id && previewUrl"
            :src="previewUrl"
            class="ref-video-thumb"
            autoplay
            loop
            muted
            playsinline
          />
          <div v-else class="ref-card-placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5">
              <rect x="2" y="2" width="20" height="20" rx="4" /><polygon points="10,8 16,12 10,16" fill="#94a3b8" />
            </svg>
            <span class="ref-play-hint">点击播放</span>
          </div>
        </div>
        <div class="ref-card-info">
          <strong class="ref-card-title">{{ v.title }}</strong>
          <div class="ref-card-tags">
            <span class="ref-tag">{{ exerciseName(v.exercise) }}</span>
            <span class="ref-tag view-tag">{{ v.camera_view === 'front' ? '正面' : '侧面' }}</span>
          </div>
          <p v-if="v.description" class="ref-card-desc">{{ v.description }}</p>
        </div>
      </div>
    </div>

    <!-- 大视频播放器 -->
    <div v-if="activeVideo && previewUrl" class="ref-player-overlay" @click.self="closePlayer">
      <div class="ref-player-card">
        <button class="player-close" @click="closePlayer">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
        <h3 class="player-title">{{ activeVideo.title }}</h3>
        <div class="player-meta">
          <span class="ref-tag">{{ exerciseName(activeVideo.exercise) }}</span>
          <span class="ref-tag view-tag">{{ activeVideo.camera_view === 'front' ? '正面' : '侧面' }}</span>
        </div>
        <video
          :src="previewUrl"
          class="ref-player-video"
          controls
          autoplay
          loop
        />
        <p v-if="activeVideo.description" class="player-desc">{{ activeVideo.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { apiGet } from "@/api/client";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

interface RefVideo {
  id: number;
  title: string;
  exercise: string;
  camera_view: string;
  description?: string;
  file_uri: string;
  is_active: boolean;
  created_at: string;
}

const videos = ref<RefVideo[]>([]);
const loading = ref(true);
const filterExercise = ref("");
const filterView = ref("");
const activeId = ref<number | null>(null);
const activeVideo = ref<RefVideo | null>(null);
const previewUrl = ref<string>("");

const filteredVideos = computed(() => {
  return videos.value.filter(v => {
    if (filterExercise.value && v.exercise !== filterExercise.value) return false;
    if (filterView.value && v.camera_view !== filterView.value) return false;
    return true;
  });
});

async function loadVideos() {
  loading.value = true;
  try {
    const data = await apiGet<{ items: RefVideo[] }>("/reference-videos");
    videos.value = data.items || [];
  } catch {
    videos.value = [];
  } finally {
    loading.value = false;
  }
}

async function selectVideo(v: RefVideo) {
  if (activeId.value === v.id && previewUrl.value) {
    // Already loaded, just ensure overlay shows
    return;
  }
  // Clear previous
  if (previewUrl.value.startsWith("blob:")) URL.revokeObjectURL(previewUrl.value);
  previewUrl.value = "";
  activeId.value = v.id;
  activeVideo.value = v;
  try {
    const apiBase = (import.meta.env.VITE_API_BASE ?? "/api").replace(/\/$/, "");
    const token = authStore.token || "";
    const resp = await fetch(`${apiBase}/reference-videos/${v.id}/stream`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!resp.ok) throw new Error("fetch failed");
    const blob = await resp.blob();
    previewUrl.value = URL.createObjectURL(blob);
  } catch {
    previewUrl.value = "";
  }
}

function closePlayer(clearActive = true) {
  if (previewUrl.value.startsWith("blob:")) URL.revokeObjectURL(previewUrl.value);
  previewUrl.value = "";
  if (clearActive) {
    activeId.value = null;
    activeVideo.value = null;
  }
}

function exerciseName(key: string): string {
  const map: Record<string, string> = {
    squat: "深蹲", push_up: "俯卧撑", plank: "平板支撑", lunge: "弓步蹲",
    jumping_jack: "开合跳", burpee: "波比跳", high_knees: "高抬腿",
    mountain_climber: "登山跑", pull_up: "引体向上", bench_press: "卧推",
    barbell_squat: "杠铃深蹲", dumbbell_fly: "哑铃飞鸟", lat_pulldown: "高位下拉",
    dumbbell_curl: "哑铃弯举", dumbbell_shoulder_press: "哑铃推肩",
  };
  return map[key] || key;
}

onMounted(loadVideos);
onUnmounted(() => closePlayer());
</script>

<style scoped>
.ref-videos-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 28px 24px 60px;
}

/* Header */
.ref-header {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 28px;
}
.back-btn {
  display: flex; align-items: center; gap: 6px;
  background: none; border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 8px 14px; cursor: pointer; color: #64748b; font-size: 14px;
  transition: background 0.18s, border-color 0.18s;
}
.back-btn:hover { background: #f1f5f9; border-color: #94a3b8; }
.ref-header-info h1 { font-size: 24px; font-weight: 700; margin: 0 0 4px; color: #1e293b; }
.ref-header-info p { font-size: 14px; color: #64748b; margin: 0; }

/* Filter */
.filter-bar {
  display: flex; gap: 12px; margin-bottom: 24px;
}
.filter-select {
  padding: 8px 14px; border: 1.5px solid #e2e8f0; border-radius: 8px;
  font-size: 14px; color: #374151; background: #fff; cursor: pointer;
  outline: none; transition: border-color 0.2s;
}
.filter-select:focus { border-color: #3b82f6; }

/* Empty */
.ref-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 60px 0; gap: 12px; color: #94a3b8;
}
.ref-empty p { font-size: 16px; margin: 0; }
.ref-empty small { font-size: 13px; }
.loading-ring {
  width: 36px; height: 36px;
  border: 3px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Grid */
.ref-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 18px;
}
.ref-card {
  border: 1.5px solid #e2e8f0; border-radius: 14px; overflow: hidden;
  cursor: pointer; background: #fff; transition: box-shadow 0.2s, border-color 0.2s;
}
.ref-card:hover { box-shadow: 0 4px 16px rgba(59,130,246,0.12); border-color: #93c5fd; }
.ref-card.active { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.15); }

.ref-card-preview {
  height: 160px; background: #f1f5f9; overflow: hidden; position: relative;
  display: flex; align-items: center; justify-content: center;
}
.ref-video-thumb { width: 100%; height: 100%; object-fit: cover; }
.ref-card-placeholder {
  display: flex; flex-direction: column; align-items: center; gap: 8px; color: #94a3b8;
}
.ref-play-hint { font-size: 12px; }

.ref-card-info { padding: 14px 16px; }
.ref-card-title { font-size: 15px; font-weight: 600; color: #1e293b; display: block; margin-bottom: 8px; }
.ref-card-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 6px; }
.ref-tag {
  font-size: 12px; padding: 2px 8px; border-radius: 99px;
  background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe;
}
.view-tag { background: #f0fdf4; color: #16a34a; border-color: #bbf7d0; }
.ref-card-desc { font-size: 13px; color: #64748b; margin: 6px 0 0; line-height: 1.5; }

/* Full-screen player overlay */
.ref-player-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.65);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.ref-player-card {
  background: #fff; border-radius: 18px; padding: 28px 28px 24px;
  width: 700px; max-width: 96vw; position: relative;
  box-shadow: 0 16px 60px rgba(0,0,0,0.22);
}
.player-close {
  position: absolute; top: 14px; right: 14px;
  background: none; border: none; cursor: pointer; color: #94a3b8;
  padding: 4px; border-radius: 6px; transition: color 0.18s;
}
.player-close:hover { color: #374151; }
.player-title { font-size: 18px; font-weight: 700; margin: 0 0 10px; color: #1e293b; }
.player-meta { display: flex; gap: 8px; margin-bottom: 14px; }
.ref-player-video {
  width: 100%; border-radius: 10px; background: #000;
  max-height: 420px; object-fit: contain;
}
.player-desc { font-size: 14px; color: #64748b; margin: 12px 0 0; }
</style>

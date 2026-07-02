<template>
  <div class="sessions-page">
    <header class="section-page-header">
      <div>
        <h1>Training Sessions / 训练记录</h1>
        <p>Complete history of all training sessions</p>
      </div>
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
      <select v-model="exerciseFilter">
        <option value="">All / 全部</option>
        <option value="squat">深蹲</option>
        <option value="push_up">俯卧撑</option>
        <option value="jumping_jack">开合跳</option>
        <option value="plank">平板支撑</option>
      </select>
      <select v-model="sortOrder">
        <option value="desc">Newest / 最新</option>
        <option value="asc">Oldest / 最早</option>
      </select>
    </section>

    <section class="sessions-table-card">
      <StateDisplay v-if="loading" type="loading" skeleton="table" :skeleton-rows="5" text="正在加载训练记录..." />
      <StateDisplay v-else-if="error" type="error" :title="'加载失败'" :text="error" @retry="loadSessions" />
      <StateDisplay v-else-if="filteredSessions.length === 0" type="empty" title="暂无训练记录" text="完成一次训练后，记录将在此处展示" />
      <table v-else class="sessions-table">
        <thead>
          <tr>
            <th>DATE & TIME / 日期时间</th>
            <th>EXERCISE / 动作</th>
            <th>DURATION / 时长</th>
            <th>REPS / 次数</th>
            <th>SCORE / 分数</th>
            <th>ACTIONS / 操作</th>
          </tr>
        </thead>
        <tbody>
            <tr v-for="s in filteredSessions" :key="s.session_id"
              :data-session-id="s.session_id"
              :class="{ 'session-highlight': s.session_id === highlightId }"
            >
            <td>
              <div class="date-cell">
                <CalendarDays :size="17" />
                <div>
                  <strong>{{ formatDate(s.created_at) }}</strong>
                  <span>
                    <Clock3 :size="13" />
                    {{ formatTime(s.created_at) }}
                  </span>
                </div>
              </div>
            </td>
            <td>
              <div class="exercise-tags">
                <span>{{ exerciseName(s.exercise) }}</span>
              </div>
            </td>
            <td>{{ Math.round(s.duration_seconds / 60) }} min</td>
            <td>{{ s.total_count }}</td>
            <td>
              <div class="score-progress">
                <i :class="scoreTone(s.average_score)" :style="{ width: s.average_score + '%' }" />
                <strong>{{ s.average_score }}</strong>
              </div>
            </td>
            <td>
              <button class="link-button" type="button" @click="viewSession(s.session_id)">View Details</button>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination v-if="!loading && !error && filteredSessions.length > 0" :current="page" :total="totalCount" :page-size="pageSize" @update:current="onPageChange" />
    </section>

    <section class="streak-card">
      <span class="streak-icon">
        <Medal :size="34" />
      </span>
      <div>
        <h2>{{ streakLabel }}</h2>
        <p>{{ streakSubtext }}</p>
      </div>
      <strong>
        <TrendingUp :size="18" />
        {{ trendLabel }}
      </strong>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, nextTick, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { CalendarDays, Clock3, Medal, Search, TrendingUp } from "lucide-vue-next";
import StateDisplay from "../components/StateDisplay.vue";
import Pagination from "../components/Pagination.vue";
import { getSessions, deleteSession, type SessionRecord } from "../api/sessions";

const router = useRouter();
const route = useRoute();

const sessions = ref<SessionRecord[]>([]);
const loading = ref(true);
const error = ref("");
const keyword = ref("");
const exerciseFilter = ref("");
const sortOrder = ref("desc");
const page = ref(1);
const pageSize = ref(20);
const totalCount = ref(0);
const deleting = ref<string | null>(null);
const highlightId = ref(route.query.highlight as string || "");

function onPageChange(p: number) {
  page.value = p;
  loadSessions();
}

const filteredSessions = computed(() => {
  let list = sessions.value;
  if (exerciseFilter.value) {
    list = list.filter(s => s.exercise === exerciseFilter.value);
  }
  const query = keyword.value.trim().toLowerCase();
  if (query) {
    list = list.filter(s =>
      formatDate(s.created_at).includes(query) ||
      exerciseName(s.exercise).toLowerCase().includes(query)
    );
  }
  list = [...list].sort((a, b) => {
    const diff = a.created_at.localeCompare(b.created_at);
    return sortOrder.value === "desc" ? -diff : diff;
  });
  return list;
});

const summaryCards = computed(() => {
  const total = sessions.value.length;
  const totalDuration = sessions.value.reduce((s, item) => s + item.duration_seconds, 0);
  const avgScore = total > 0
    ? (sessions.value.reduce((s, item) => s + item.average_score, 0) / total).toFixed(1) : "0";
  return [
    { label: "Total Sessions / 总训练次数", value: total, tone: "tone-text-blue" },
    { label: "Total Duration / 总时长", value: `${Math.round(totalDuration / 60)} min`, tone: "tone-text-green" },
    { label: "Avg Score / 平均分数", value: avgScore, tone: "tone-text-purple" },
    { label: "Valid Rate / 有效率", value: validRate.value, tone: "tone-text-orange" },
  ];
});

const validRate = computed(() => {
  const total = sessions.value.reduce((s, item) => s + item.total_count, 0);
  const valid = sessions.value.reduce((s, item) => s + item.valid_count, 0);
  if (total === 0) return "0%";
  return `${Math.round((valid / total) * 100)}%`;
});

const streakLabel = computed(() => {
  const count = sessions.value.length;
  if (count === 0) return "开始你的第一次训练吧！";
  const days = Math.min(count, 7);
  return `${days}-Day Streak! / 连续${days}天训练!`;
});

const streakSubtext = computed(() => {
  if (sessions.value.length === 0) return "完成训练后，你的连续记录将在此展示。";
  return "坚持训练，保持良好习惯！";
});

const trendLabel = computed(() => {
  if (sessions.value.length < 2) return "继续加油！";
  const sorted = [...sessions.value].sort((a, b) => a.created_at.localeCompare(b.created_at));
  const recent = sorted.slice(-2);
  const diff = recent[1].average_score - recent[0].average_score;
  const sign = diff >= 0 ? "+" : "";
  return `${sign}${diff} vs last session`;
});

function exerciseName(key: string): string {
  const map: Record<string, string> = {
    squat: "深蹲", push_up: "俯卧撑", jumping_jack: "开合跳", plank: "平板支撑",
  };
  return map[key] ?? key;
}

function scoreTone(score: number) {
  if (score >= 90) return "progress-green";
  if (score >= 75) return "progress-blue";
  return "progress-orange";
}

function formatDate(iso?: string): string {
  if (!iso) return "";
  return iso.slice(0, 10);
}

function formatTime(iso?: string): string {
  if (!iso) return "";
  const m = iso.match(/T(\d{2}:\d{2})/);
  return m?.[1] ?? "";
}

function viewSession(session_id: string) {
  router.push({ path: "/reports", query: { session: session_id } });
}

async function handleDelete(session_id: string) {
  if (!confirm("确定删除这条训练记录？")) return;
  deleting.value = session_id;
  try {
    await deleteSession(session_id);
    sessions.value = sessions.value.filter(s => s.session_id !== session_id);
  } catch (err: any) {
    alert("删除失败: " + (err.message || "网络错误"));
  } finally {
    deleting.value = null;
  }
}

async function loadSessions() {
  loading.value = true;
  error.value = "";
  try {
    const data = await getSessions({ limit: pageSize.value, offset: (page.value - 1) * pageSize.value });
    sessions.value = data.items || [];
    totalCount.value = data.total || 0;
  } catch (err: any) {
    error.value = err.message || "网络错误";
    sessions.value = [];
  } finally {
    loading.value = false;
    if (highlightId.value) {
      highlightToSession(highlightId.value);
    }
  }
}

onMounted(loadSessions);

// 当从其他页面导航过来且 highlight 参数存在时，重新加载并滚动
watch(
  () => route.query.highlight,
  (newHighlight) => {
    if (newHighlight && typeof newHighlight === 'string') {
      highlightId.value = newHighlight;
      if (sessions.value.length > 0) {
        // 数据已存在，直接滚动
        highlightToSession(newHighlight);
      } else {
        // 数据尚未加载，重新加载
        loadSessions();
      }
    }
  }
);

function highlightToSession(id: string) {
  nextTick(() => {
    const el = document.querySelector(`[data-session-id="${id}"]`);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
}

</script>

<style scoped>
.session-highlight {
  outline: 2px solid rgba(59, 130, 246, 0.6);
  outline-offset: -2px;
  animation: highlight-fade 3s ease-out;
}
@keyframes highlight-fade {
  0% { background: rgba(59, 130, 246, 0.15); }
  100% { background: transparent; }
}
</style>

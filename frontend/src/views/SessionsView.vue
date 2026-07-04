<template>
  <div class="sessions-page">
    <header class="section-page-header">
      <div>
        <h1>Training Sessions / 训练记录</h1>
        <p>Complete history of all training sessions</p>
      </div>
    </header>

    <section class="filter-card">
      <label class="session-search">
        <Search :size="20" />
        <input v-model="keyword" type="search" placeholder="Search sessions..." />
      </label>
      <select v-model="exerciseFilter">
        <option value="">All</option>
        <option value="squat">深蹲</option>
        <option value="push_up">俯卧撑</option>
        <option value="jumping_jack">开合跳</option>
        <option value="plank">平板支撑</option>
      </select>
      <select v-model="sortOrder">
        <option value="desc">Newest</option>
        <option value="asc">Oldest</option>
      </select>
    </section>

    <section class="sessions-table-card">
      <StateDisplay v-if="loading" type="loading" skeleton="table" :skeleton-rows="5" text="正在加载..." />
      <StateDisplay v-else-if="error" type="error" :title="'加载失败'" :text="error" @retry="onRetry" />
      <StateDisplay v-else-if="filteredSessions.length === 0" type="empty" title="暂无训练记录" text="完成一次训练后，记录将在此处展示" />
      <table v-else class="sessions-table">
        <thead>
          <tr>
            <th>DATE & TIME</th>
            <th>EXERCISE</th>
            <th>DURATION</th>
            <th>REPS</th>
            <th>SCORE</th>
            <th>REPLAY</th>
            <th>ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in filteredSessions" :key="s.session_id">
            <td>{{ formatDate(s.created_at) }} {{ formatTime(s.created_at) }}</td>
            <td>{{ exerciseName(s.exercise) }}</td>
            <td>{{ Math.round(s.duration_seconds / 60) }} min</td>
            <td>{{ s.total_count }}</td>
            <td>{{ s.average_score }}</td>
            <td>
              <span v-if="s.has_pose_replay" title="有 3D 回放">🎬</span>
              <span v-else>—</span>
            </td>
            <td>
              <button @click="viewSession(s.session_id)">查看</button>
              <button v-if="s.has_pose_replay" @click="viewReplay(s.session_id)">3D 回放</button>
              <button class="delete-btn" @click="handleDelete(s.session_id)" :disabled="deleting === s.session_id">{{ deleting === s.session_id ? '删除中...' : '删除' }}</button>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination v-if="!loading && !error && filteredSessions.length > 0" :current="page" :total="totalCount" :page-size="pageSize" @update:current="onPageChange" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Search } from "lucide-vue-next";
import StateDisplay from "../components/StateDisplay.vue";
import Pagination from "../components/Pagination.vue";
import { getSessions, deleteSession, type SessionRecord } from "../api/sessions";

const router = useRouter();

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

function onPageChange(p: number) {
  page.value = p;
  loadSessions();
}

function onRetry() {
  loadSessions();
}

const filteredSessions = computed(() => {
  let list = sessions.value;
  if (exerciseFilter.value) {
    list = list.filter(s => s.exercise === exerciseFilter.value);
  }
  const query = keyword.value.trim().toLowerCase();
  if (query) {
    list = list.filter(s => formatDate(s.created_at).includes(query));
  }
  list = [...list].sort((a, b) => {
    const diff = a.created_at.localeCompare(b.created_at);
    return sortOrder.value === "desc" ? -diff : diff;
  });
  return list;
});

function exerciseName(key: string): string {
  const map: Record<string, string> = { squat: "深蹲", push_up: "俯卧撑", jumping_jack: "开合跳", plank: "平板支撑" };
  return map[key] ?? key;
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
  router.push("/reports?session=" + session_id);
}

function viewReplay(session_id: string) {
  router.push("/?replay=" + session_id);
}

async function handleDelete(session_id: string) {
  if (!confirm("确定要删除这条训练记录？（回放数据也会一并删除）")) return;
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
  }
}

onMounted(loadSessions);
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

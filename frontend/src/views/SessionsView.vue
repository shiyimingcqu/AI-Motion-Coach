<template>
  <div class="evaluation-page">
    <header class="section-page-header">
      <div>
        <h1>{{ $t("sessions.title") }}</h1>
      </div>
    </header>

    <section class="filter-card report-filter-card">
      <label class="session-search">
        <Filter :size="18" />
        <input v-model="keyword" type="search" :placeholder="$t('sessions.search')" />
      </label>
      <select v-model="exerciseFilter">
        <option value="">{{ $t("common.all") }}</option>
        <option v-for="(name, key) in exerciseLabels" :key="key" :value="key">{{ name }}</option>
      </select>
      <select v-model="sortOrder">
        <option value="desc">{{ $t("sessions.newest") }}</option>
        <option value="asc">{{ $t("sessions.oldest") }}</option>
      </select>
    </section>

    <section class="report-table-card">
      <StateDisplay v-if="loading" type="loading" skeleton="table" :skeleton-rows="6" :text="$t('sessions.loading')" />
      <StateDisplay v-else-if="error" type="error" :title="$t('common.loadFailed')" :text="error" />
      <StateDisplay v-else-if="filteredSessions.length === 0" type="empty" :title="$t('sessions.noSessions')" :text="$t('sessions.noSessionsText')" />
      <table v-else class="report-table">
        <thead>
          <tr>
            <th>{{ $t("sessions.tableHead_datetime") }}</th>
            <th>{{ $t("sessions.tableHead_exercise") }}</th>
            <th>{{ $t("sessions.tableHead_duration") }}</th>
            <th>{{ $t("sessions.tableHead_reps") }}</th>
            <th>{{ $t("sessions.tableHead_score") }}</th>
            <th>REPLAY</th>
            <th>{{ $t("sessions.tableHead_actions") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="session in filteredSessions" :key="session.session_id" class="report-row">
            <td>{{ formatDate(session.created_at) }}</td>
            <td>{{ exerciseLabels[session.exercise] || session.exercise }}</td>
            <td>{{ formatDuration(session.duration_seconds) }}</td>
            <td>{{ session.total_count }} / {{ session.valid_count }}</td>
            <td>
              <span :class="session.average_score >= 70 ? 'pill score-good' : 'pill score-warn'">
                {{ session.average_score }}
              </span>
            </td>
            <td>
              <span v-if="session.has_pose_replay" title="有 3D 回放">🎬</span>
              <span v-else>—</span>
            </td>
            <td>
              <button @click="viewSession(session.session_id)">查看</button>
              <button v-if="session.has_pose_replay" @click="viewReplay(session.session_id)">3D 回放</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="summary-card-grid" style="margin-top: 16px;">
      <article class="summary-card compact-summary" v-for="card in summaryCards" :key="card.label">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
      </article>
    </section>

    <!-- Streak -->
    <section class="blue-shadow-card" style="margin-top:16px;padding:14px 20px;">
      <span class="blue-solid"><Flame :size="28" /></span>
      <div style="margin-left:10px">
        <strong v-if="streakDays > 0">{{ $t("sessions.streak", { count: streakDays }) }}</strong>
        <strong v-else>{{ $t("sessions.noStreakYet") }}</strong>
        <p style="margin:4px 0 0;font-size:13px;color:#64748b">
          {{ streakDays > 0 ? $t("sessions.keepGoing") : $t("sessions.startFirst") }}
        </p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { Filter, Flame, Trash2 } from "lucide-vue-next";
import StateDisplay from "../components/StateDisplay.vue";
import { getSessions } from "../api/sessions";

const router = useRouter();
const { t } = useI18n();

interface SessionItem {
  session_id: string;
  exercise: string;
  created_at: string;
  duration_seconds: number;
  total_count: number;
  valid_count: number;
  error_count: number;
  average_score: number;
}

const sessions = ref<SessionItem[]>([]);
const loading = ref(true);
const error = ref("");
const keyword = ref("");
const exerciseFilter = ref("");
const sortOrder = ref<"asc" | "desc">("desc");

const exerciseLabels: Record<string, string> = {
  squat: t("exercises.squat"),
  push_up: t("exercises.push_up"),
  plank: t("exercises.plank"),
  lunge: t("exercises.lunge"),
  jumping_jack: t("exercises.jumping_jack"),
  burpee: t("exercises.burpee"),
  high_knees: t("exercises.high_knees"),
  glute_bridge: t("exercises.glute_bridge"),
};

function onRetry() {
  loadSessions();
}

const filteredSessions = computed(() => {
  let list = [...sessions.value];
  if (exerciseFilter.value) list = list.filter(s => s.exercise === exerciseFilter.value);
  if (keyword.value.trim()) {
    const q = keyword.value.trim().toLowerCase();
    list = list.filter(s =>
      (exerciseLabels[s.exercise] || s.exercise).toLowerCase().includes(q)
    );
  }
  return list.sort((a, b) => {
    const diff = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
    return sortOrder.value === "desc" ? -diff : diff;
  });
});

function viewSession(session_id: string) {
  router.push("/reports?session=" + session_id);
}

function viewReplay(session_id: string) {
  router.push("/?replay=" + session_id);
}

const summaryCards = computed(() => {
  const total = sessions.value.length;
  const avgScore = total > 0 ? sessions.value.reduce((s, r) => s + r.average_score, 0) / total : 0;
  const totalSec = sessions.value.reduce((s, r) => s + (r.duration_seconds || 0), 0);
  const allTotal = sessions.value.reduce((s, r) => s + r.total_count, 0);
  const allValid = sessions.value.reduce((s, r) => s + r.valid_count, 0);
  const validRate = allTotal > 0 ? Math.round((allValid / allTotal) * 100) + "%" : "-";
  const mins = Math.floor(totalSec / 60);
  return [
    { label: t("sessions.summary_total"), value: total },
    { label: t("sessions.summary_duration"), value: mins + " " + t("common.minute") },
    { label: t("sessions.summary_score"), value: avgScore.toFixed(1) },
    { label: t("sessions.summary_rate"), value: validRate },
  ];
});

const streakDays = computed(() => {
  if (sessions.value.length === 0) return 0;
  const dates = [...new Set(sessions.value.map(s => s.created_at.split("T")[0]))].sort().reverse();
  let streak = 1;
  for (let i = 1; i < dates.length; i++) {
    const prev = new Date(dates[i - 1]);
    const curr = new Date(dates[i]);
    const diff = (prev.getTime() - curr.getTime()) / (86400000);
    if (Math.abs(diff - 1) < 0.1) streak++;
    else break;
  }
  return streak;
});

function formatDate(iso: string) {
  if (!iso) return "-";
  return new Date(iso).toLocaleString(undefined, { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function formatDuration(sec: number) {
  if (!sec || sec <= 0) return "0 " + t("common.second");
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return m > 0 ? `${m} ${t("common.minute")} ${s} ${t("common.second")}` : `${s} ${t("common.second")}`;
}

onMounted(async () => {
  try {
    const data = await getSessions();
    sessions.value = data.items || [];
  } catch (e: any) {
    error.value = e?.message || t("common.networkError");
  } finally {
    loading.value = false;
  }
});

async function loadSessions() {
  try {
    const data = await getSessions();
    sessions.value = data.items || [];
  } catch (e: any) {
    error.value = e?.message || t("common.networkError");
  } finally {
    loading.value = false;
  }
}
</script>

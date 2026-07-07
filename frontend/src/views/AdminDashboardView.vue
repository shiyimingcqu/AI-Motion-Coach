<template>
  <div class="page admin-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Admin Overview</p>
        <h1>管理首页</h1>
        <p class="subtle">查看用户、训练、报告和动作规则的整体运行情况。</p>
      </div>
      <button class="refresh-btn" @click="loadStats" :disabled="loading">
        <RefreshCw :size="16" :class="{ spin: loading }" />
        刷新
      </button>
    </header>

    <StateDisplay v-if="loading && !stats" type="loading" skeleton="cards" text="加载管理数据..." />

    <template v-else>
      <section class="metrics-grid">
        <MetricTile :label="'用户总数'" :value="stats.user_count" :hint="`管理员 ${stats.admin_count} 人，本周新增 ${stats.new_users_week} 人`" />
        <MetricTile :label="'今日训练'" :value="stats.today_sessions" :hint="`累计 ${stats.total_sessions} 次`" />
        <MetricTile :label="'视频分析'" :value="stats.video_success" :hint="`共 ${stats.video_total} 个任务`" />
        <MetricTile :label="'系统平均分'" :value="stats.average_score" :hint="`较上周 ${stats.average_score_change >= 0 ? '+' : ''}${stats.average_score_change}`" />
      </section>

      <section class="admin-grid">
        <article class="panel">
          <div class="section-title">
            <div>
              <p class="eyebrow">Recent Activity</p>
              <h2>最近训练动态</h2>
            </div>
          </div>
          <div v-if="stats.recent_sessions.length === 0" class="empty-hint">暂无训练记录</div>
          <div v-else class="admin-list">
            <div v-for="item in stats.recent_sessions" :key="item.session_id" class="admin-list-row">
              <span class="status-pill" :class="item.score >= 80 ? 'good' : item.score >= 60 ? 'idle' : 'danger'">
                {{ item.score >= 80 ? '优秀' : item.score >= 60 ? '一般' : '需关注' }}
              </span>
              <div>
                <strong>{{ item.user }} 完成{{ exerciseLabel(item.exercise) }}训练，平均分 {{ item.score }}</strong>
                <small>{{ formatRelative(item.created_at) }}</small>
              </div>
            </div>
          </div>
        </article>

        <article class="panel">
          <div class="section-title">
            <div>
              <p class="eyebrow">Risk Focus</p>
              <h2>高频动作问题</h2>
            </div>
          </div>
          <div v-if="stats.error_stats.length === 0" class="empty-hint">暂无错误统计数据</div>
          <div v-else class="error-panel-body">
            <div class="error-total">
              <span class="error-total-num">{{ stats.total_errors }}</span>
              <span class="error-total-label">累计错误次数</span>
            </div>
            <div class="distribution-list">
              <div v-for="item in stats.error_stats" :key="item.name" class="dist-item">
                <div class="dist-header">
                  <span class="dist-exercise">{{ exerciseLabel(item.name) }}</span>
                  <span class="dist-count" :class="severityClass(item.count)">{{ item.count }} 次</span>
                </div>
                <div class="dist-bar-track">
                  <div class="dist-bar-fill" :class="severityClass(item.count)" :style="{ width: `${item.rate}%` }"></div>
                </div>
                <div class="dist-footer">
                  <span>{{ item.sessions || 0 }} 次训练</span>
                  <span>{{ item.rate }}% 占比</span>
                </div>
              </div>
            </div>
          </div>
        </article>
      </section>

      <section class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Work Queue</p>
            <h2>待处理事项</h2>
          </div>
        </div>
        <div v-if="stats.work_queue.length === 0" class="empty-hint">暂无待处理事项，系统运行良好。</div>
        <div v-else class="admin-action-grid">
          <div v-for="item in stats.work_queue" :key="item.title" class="admin-action-card" @click="navigateTo(item.link)">
            <strong>{{ item.title }}</strong>
            <span>{{ item.desc }}</span>
            <small class="card-action-hint">点击前往 →</small>
          </div>
        </div>
      </section>

    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { apiGet } from "@/api/client";
import { RefreshCw } from "lucide-vue-next";
import MetricTile from "../components/MetricTile.vue";
import StateDisplay from "@/components/StateDisplay.vue";

const router = useRouter();
const loading = ref(false);
const stats = reactive({
  user_count: 0,
  admin_count: 0,
  new_users_week: 0,
  today_sessions: 0,
  total_sessions: 0,
  average_score: 0,
  average_score_change: 0,
  total_duration_minutes: 0,
  video_total: 0,
  video_success: 0,
  exercise_count: 0,
  total_errors: 0,
  recent_sessions: [] as any[],
  error_stats: [] as any[],
  work_queue: [] as any[],
});

const EXERCISE_MAP: Record<string, string> = {
  squat: "深蹲",
  push_up: "俯卧撑",
  jumping_jack: "开合跳",
  plank: "平板支撑",
  lunge: "弓步",
  high_knee: "高抬腿",
  side_raise: "侧平举",
};

function exerciseLabel(key: string): string {
  return EXERCISE_MAP[key] || key;
}

function severityClass(count: number): string {
  if (count >= 100) return "severe";
  if (count >= 30) return "moderate";
  return "low";
}

function formatRelative(iso?: string): string {
  if (!iso) return "未知时间";
  const d = new Date(iso);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes} 分钟前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} 小时前`;
  return `${Math.floor(hours / 24)} 天前`;
}

function navigateTo(path: string) {
  if (path) router.push(path);
}

async function loadStats() {
  loading.value = true;
  try {
    const data = await apiGet("/admin/dashboard");
    Object.assign(stats, data);
  } catch { /* keep existing data */ }
  finally { loading.value = false; }
}

onMounted(loadStats);
</script>

<style scoped>
.page { display: grid; gap: 24px; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
}
.page-header h1 { color: #0f172a; font-size: 28px; margin: 0; }
.page-header p { margin: 4px 0 0; color: #64748b; }
.eyebrow { color: #5b8cff; font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em; }
.subtle { color: #64748b; font-size: 14px; }

.refresh-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; border: 1px solid #d6e3ff;
  border-radius: 8px; background: #f8fbff; color: #5b8cff;
  font-size: 13px; cursor: pointer; white-space: nowrap;
}
.refresh-btn:hover { background: #e8f0ff; border-color: #5b8cff; }
.refresh-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.admin-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}
@media (max-width: 860px) { .admin-grid { grid-template-columns: 1fr; } }

.panel {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 22px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
.section-title h2 { color: #0f172a; font-size: 18px; margin: 0; }

.empty-hint {
  color: #94a3b8; font-size: 14px; text-align: center; padding: 20px;
}

/* Recent Activity */
.admin-list { display: grid; gap: 10px; }
.admin-list-row {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 12px;
  border-radius: 10px;
  background: #f8fbff;
  border: 1px solid #e2e8f0;
}
.admin-list-row strong { display: block; color: #1e293b; font-size: 13px; margin-bottom: 2px; }
.admin-list-row small { color: #94a3b8; font-size: 11px; }

.status-pill {
  flex-shrink: 0; padding: 3px 10px; border-radius: 999px;
  font-size: 11px; font-weight: 600;
}
.status-pill.good { background: rgba(16,185,129,0.12); color: #25b87b; }
.status-pill.idle { background: rgba(245,158,11,0.12); color: #f97316; }
.status-pill.danger { background: rgba(239,68,68,0.12); color: #ef4444; }

/* Error Stats Panel */
.error-panel-body { display: grid; gap: 16px; }
.error-total {
  display: flex; align-items: baseline; gap: 10px;
  padding: 12px 14px; border-radius: 10px;
  background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.12);
}
.error-total-num { color: #ef4444; font-size: 28px; font-weight: 700; }
.error-total-label { color: #94a3b8; font-size: 13px; }

.distribution-list { display: grid; gap: 14px; }
.dist-item {
  display: grid; gap: 6px;
  padding: 10px 12px; border-radius: 9px;
  background: #f8fbff; border: 1px solid #e2e8f0;
}
.dist-header { display: flex; justify-content: space-between; align-items: center; }
.dist-exercise { color: #1e293b; font-size: 13px; font-weight: 600; }
.dist-count { font-size: 14px; font-weight: 700; }
.dist-count.severe { color: #ef4444; }
.dist-count.moderate { color: #f97316; }
.dist-count.low { color: #25b87b; }

.dist-bar-track {
  height: 6px; border-radius: 3px;
  background: #f1f5f9;
  overflow: hidden;
}
.dist-bar-fill {
  height: 100%; border-radius: 3px; transition: width 0.5s ease;
}
.dist-bar-fill.severe { background: linear-gradient(90deg, #ef4444, #f87171); }
.dist-bar-fill.moderate { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.dist-bar-fill.low { background: linear-gradient(90deg, #5b8cff, #4f46e5); }

.dist-footer {
  display: flex; justify-content: space-between;
  color: #94a3b8; font-size: 11px;
}

/* Work Queue */
.admin-action-grid { display: grid; gap: 10px; }
.admin-action-card {
  padding: 14px 16px; border-radius: 10px;
  background: #f8fbff; border: 1px solid #e2e8f0;
  display: grid; gap: 4px; cursor: pointer; transition: border-color 0.2s;
}
.admin-action-card:hover { border-color: #5b8cff; }
.admin-action-card strong { color: #1e293b; font-size: 14px; }
.admin-action-card span { color: #94a3b8; font-size: 13px; }
.card-action-hint { color: #5b8cff; font-size: 11px; }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>

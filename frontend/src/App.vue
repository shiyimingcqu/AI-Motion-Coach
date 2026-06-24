<template>
  <RouterView v-if="!authStore.isAuthenticated" />

  <div v-else class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">P</span>
        <div>
          <strong>PoseOps</strong>
          <small>运动姿态评估与纠错系统</small>
        </div>
      </div>

      <nav class="side-nav" aria-label="主导航">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path">
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <div>
          <strong>{{ pageTitle }}</strong>
          <span v-if="!authStore.isAdmin">今天 3 次训练 · 平均分 86</span>
          <span v-else>管理后台 · 动作规则与模板管理</span>
        </div>
        <label class="search-box">
          <Search :size="16" />
          <input type="search" placeholder="搜索动作、训练记录或报告" />
        </label>
        <div class="topbar-actions">
          <button class="icon-button" type="button" aria-label="通知">
            <Bell :size="18" />
          </button>
          <div class="user-info">
            <span class="avatar">{{ userInitial }}</span>
            <div class="user-meta">
              <span class="username">{{ authStore.username }}</span>
              <span class="role">{{ roleText }}</span>
            </div>
            <button class="logout-button" type="button" @click="handleLogout">
              退出
            </button>
          </div>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import {
  Activity,
  BarChart3,
  Bell,
  ClipboardList,
  Dumbbell,
  Gauge,
  Search,
  UploadCloud
} from "lucide-vue-next";

const router = useRouter();
const authStore = useAuthStore();

const pageTitle = computed(() =>
  authStore.isAdmin ? "管理后台" : "学生训练端"
);

const roleText = computed(() =>
  authStore.isAdmin ? "管理员" : "学生用户"
);

const userInitial = computed(() =>
  authStore.username ? authStore.username.charAt(0).toUpperCase() : "?"
);

const baseNavItems = [
  { path: "/", label: "首页总览", icon: Gauge },
  { path: "/realtime", label: "实时检测", icon: Activity },
  { path: "/upload", label: "视频分析", icon: UploadCloud },
  { path: "/sessions", label: "训练记录", icon: ClipboardList },
  { path: "/reports", label: "个人报告", icon: BarChart3 },
];

const adminNavItems = [
  ...baseNavItems,
  { path: "/rules", label: "动作规则", icon: Dumbbell }
];

const navItems = computed(() =>
  authStore.isAdmin ? adminNavItems : baseNavItems
);

function handleLogout() {
  authStore.logout();
  router.push("/login");
}
</script>

<style scoped>
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 8px;
}

.user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.user-meta .username {
  font-size: 13px;
  font-weight: 500;
  color: #0f172a;
}

.user-meta .role {
  font-size: 11px;
  color: #64748b;
}

.logout-button {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #fff;
  color: #64748b;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.logout-button:hover {
  border-color: #ef4444;
  color: #ef4444;
}
</style>

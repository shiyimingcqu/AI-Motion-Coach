<template>
  <div class="layout-stage">
    <Transition
      :name="layoutTransitionName"
      mode="out-in"
      @before-leave="lockPageScroll"
      @after-enter="unlockPageScroll"
    >
      <main v-if="!authStore.isAuthenticated || isStandalonePage" key="standalone" class="standalone-content">
        <RouterView />
      </main>

      <div v-else key="shell" class="shell">
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
              <span v-else>用户、训练、报告与规则管理</span>
            </div>
            <label class="search-box">
              <Search :size="16" />
              <input type="search" :placeholder="searchPlaceholder" />
            </label>
            <div class="topbar-actions">
              <div v-if="settings.notificationsEnabled" class="action-menu">
                <button class="icon-button" type="button" aria-label="通知" @click="toggleNotifications">
                  <Bell :size="18" />
                  <span class="notification-dot" aria-hidden="true"></span>
                </button>
                <div v-if="showNotifications" class="dropdown-panel notification-panel">
                  <strong>消息通知</strong>
                  <p>今日训练报告已生成，可前往个人报告查看。</p>
                  <p>深蹲动作规则已更新，建议训练前先阅读。</p>
                  <p>本周平均分较上周提升 6 分，继续保持。</p>
                </div>
              </div>
              <button
                v-if="!authStore.isAdmin"
                class="icon-button"
                type="button"
                aria-label="系统设置"
                @click="goToSettings"
              >
                <Settings :size="18" />
              </button>
              <button
                v-if="!authStore.isAdmin"
                class="avatar avatar-button"
                type="button"
                aria-label="个人资料"
                @click="goToProfile"
              >
                <UserAvatar size="sm" />
              </button>
              <div v-if="authStore.isAdmin" class="user-info">
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
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref } from "vue";
import { storeToRefs } from "pinia";
import { useRoute, useRouter } from "vue-router";
import {
  Activity,
  BarChart3,
  Bell,
  ClipboardList,
  Dumbbell,
  FileText,
  Gauge,
  Layers,
  Shield,
  Search,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  UploadCloud,
  Users
} from "lucide-vue-next";

import UserAvatar from "./components/UserAvatar.vue";
import { useAuthStore } from "./stores/auth";
import { useSettingsStore } from "./stores/settings";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const { settings } = storeToRefs(useSettingsStore());
const standalonePaths = ["/profile", "/settings"];
const isStandalonePage = computed(() => standalonePaths.includes(route.path));
const layoutTransitionName = computed(() => route.meta.layoutTransition ?? "layout-instant");

function lockPageScroll() {
  if (layoutTransitionName.value !== "layout-instant") {
    document.documentElement.classList.add("page-transition-lock");
  }
}

function unlockPageScroll() {
  document.documentElement.classList.remove("page-transition-lock");
}

onUnmounted(unlockPageScroll);

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
  { path: "/admin", label: "管理首页", icon: ShieldCheck },
  { path: "/admin/users", label: "用户管理", icon: Users },
  { path: "/admin/admins", label: "管理员管理", icon: Shield },
  { path: "/admin/sessions", label: "训练记录", icon: ClipboardList },
  { path: "/admin/reports", label: "评估报告", icon: FileText },
  { path: "/admin/rules", label: "动作规则", icon: Dumbbell },
  { path: "/admin/templates", label: "模板管理", icon: Layers },
  { path: "/admin/settings", label: "系统设置", icon: SlidersHorizontal }
];

const navItems = computed(() =>
  authStore.isAdmin ? adminNavItems : baseNavItems
);

const searchPlaceholder = computed(() =>
  authStore.isAdmin ? "搜索用户、报告或规则" : "搜索动作、训练记录或报告"
);

const showNotifications = ref(false);

function toggleNotifications() {
  showNotifications.value = !showNotifications.value;
}

function closeMenus() {
  showNotifications.value = false;
}

function goToProfile() {
  closeMenus();
  router.push("/profile");
}

function goToSettings() {
  closeMenus();
  router.push("/settings");
}

function handleLogout() {
  closeMenus();
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

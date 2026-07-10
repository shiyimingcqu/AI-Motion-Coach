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

      <div v-else key="shell" class="shell" :class="{ 'user-shell': !authStore.isAdmin }">
        <aside class="sidebar">
          <div class="brand">
            <img class="brand-mark" src="@/assets/logo-poseprism.png" alt="姿态棱镜" />
            <div>
              <strong v-if="authStore.isAdmin">管理后台</strong>
              <GradientText
                v-else
                class-name="brand-gradient-title"
                :colors="['#4f6cff', '#7c5cff', '#25c99b', '#4f6cff']"
                :animation-speed="4"
                direction="horizontal"
                pause-on-hover
              >
                姿态棱镜
              </GradientText>
              <small>{{ authStore.isAdmin ? "系统管理中心" : "你的专属动作教练" }}</small>
            </div>
          </div>

          <div class="sidebar-divider"></div>

          <nav class="side-nav side-nav-scroll" aria-label="主导航">
            <RouterLink v-for="item in navItems" :key="item.path" :to="item.path">
              <component :is="item.icon" :size="20" />
              <span>{{ item.label }}</span>
            </RouterLink>
          </nav>

          <SidebarTipCarousel v-if="!authStore.isAdmin" />

          <div class="sidebar-utils">
            <button
              v-if="!authStore.isAdmin"
              class="side-util-btn"
              type="button"
              @click="goToSettings"
            >
              <span class="side-icon-wrap"><Settings :size="16" /></span>
              <span>设置</span>
            </button>

            <button
              v-if="!authStore.isAdmin"
              class="side-profile-card"
              type="button"
              @click="goToProfile"
            >
              <UserAvatar size="sm" />
              <span>个人中心</span>
              <ChevronRight :size="18" />
            </button>

            <div v-if="authStore.isAdmin" class="sidebar-user-info">
              <span class="avatar">{{ userInitial }}</span>
              <div class="sidebar-user-meta">
                <span class="username">{{ authStore.username }}</span>
                <span class="role">{{ roleText }}</span>
              </div>
              <button class="sidebar-logout-btn" type="button" @click="handleLogout">退出</button>
            </div>
          </div>
        </aside>

        <div class="workspace" :class="{ 'workspace-home': !showShellTopbar }">
          <header v-if="showShellTopbar" class="topbar">
            <div class="topbar-title-block">
              <strong>{{ pageTitle }}</strong>
              <span>坚持每一次训练，身体会给你最好的回报。</span>
            </div>
          </header>

          <main :class="['content', { 'dashboard-content': route.path === '/start/playback', 'home-content': route.path === '/' }]">
            <RouterView />
          </main>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  Activity,
  ClipboardList,
  Dumbbell,
  FileText,
  Home,
  Layers,
  Settings,
  Shield,
  ShieldCheck,
  SlidersHorizontal,
  Target,
  Users,
  ChevronRight,
} from "lucide-vue-next";

import UserAvatar from "./components/UserAvatar.vue";
import GradientText from "./components/GradientText.vue";
import SidebarTipCarousel from "./components/SidebarTipCarousel.vue";
import { useAuthStore } from "./stores/auth";
import { useSettingsStore } from "./stores/settings";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
useSettingsStore();

const standalonePaths = ["/profile", "/settings"];
const isStandalonePage = computed(() => standalonePaths.includes(route.path));
const showShellTopbar = computed(() => {
  if (authStore.isAdmin) return true;
  if (route.path.startsWith("/exercises/")) return false;
  return !["/", "/start/playback", "/sessions", "/export"].includes(route.path);
});
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

const pageTitleMap: Record<string, string> = {
  "/": "首页",
  "/start": "开始评估",
  "/feedback": "训练反馈",
  "/sessions": "训练记录",
  "/exercises": "动作库",
  "/export": "我的报告",
  "/rules": "动作规则配置",
  "/users": "用户管理",
  "/settings": "设置",
  "/admin": "管理首页",
  "/admin/users": "用户管理",
  "/admin/admins": "管理员管理",
  "/admin/sessions": "训练记录",
  "/admin/reports": "评估报告",
  "/admin/rules": "动作规则",
  "/admin/templates": "模板管理",
  "/admin/settings": "系统设置",
};

const pageTitle = computed(() => pageTitleMap[route.path] ?? "姿态棱镜");

const roleText = computed(() => (authStore.isAdmin ? "管理员" : "学员用户"));
const userInitial = computed(() => (authStore.username ? authStore.username.charAt(0).toUpperCase() : "?"));

const baseNavItems = [
  { path: "/", label: "首页", icon: Home },
  { path: "/start", label: "开始评估", icon: Activity },
  { path: "/exercises", label: "动作库", icon: Dumbbell },
  { path: "/sessions", label: "训练记录", icon: ClipboardList },
  { path: "/export", label: "我的报告", icon: FileText },
];

const adminNavItems = [
  { path: "/admin", label: "管理首页", icon: ShieldCheck },
  { path: "/admin/users", label: "用户管理", icon: Users },
  { path: "/admin/admins", label: "管理员管理", icon: Shield },
  { path: "/admin/sessions", label: "训练记录", icon: ClipboardList },
  { path: "/admin/reports", label: "评估报告", icon: FileText },
  { path: "/admin/rules", label: "动作规则", icon: Dumbbell },
  { path: "/admin/templates", label: "模板管理", icon: Layers },
  { path: "/admin/settings", label: "系统设置", icon: SlidersHorizontal },
];

const navItems = computed(() => (authStore.isAdmin ? adminNavItems : baseNavItems));
function goToProfile() {
  router.push("/profile");
}

function goToSettings() {
  router.push("/settings");
}

function handleLogout() {
  authStore.logout();
  router.push("/login");
}
</script>

<style scoped>
.topbar-title-block {
  display: grid;
  gap: 4px;
}

.topbar-title-block strong {
  color: #101828;
  font-size: 26px;
  letter-spacing: 0;
}

.topbar-title-block span {
  color: #667085;
  font-size: 14px;
}

.topbar-coach-stats {
  display: flex;
  align-items: center;
  gap: 14px;
}

.coach-stat {
  min-width: 132px;
  min-height: 64px;
  display: grid;
  align-content: center;
  gap: 4px;
  padding: 10px 18px;
  border: 1px solid rgba(214, 227, 255, 0.88);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 12px 26px rgba(37, 99, 235, 0.08);
}

.coach-stat span {
  color: #6b7280;
  font-size: 13px;
}

.coach-stat strong {
  color: #101828;
  font-size: 25px;
  line-height: 1;
}

.coach-stat small {
  margin-left: 4px;
  font-size: 13px;
  font-weight: 700;
}

.coach-stat.green {
  background: linear-gradient(135deg, #ffffff, #ecfdf5);
}

.coach-stat.blue {
  background: linear-gradient(135deg, #ffffff, #eef4ff);
}

.coach-stat.violet {
  background: linear-gradient(135deg, #ffffff, #f5f0ff);
}

.user-shell {
  grid-template-columns: 280px 1fr;
  background: #f4f7ff;
}

.user-shell .sidebar {
  padding: 32px 16px 18px;
  background: rgba(255, 255, 255, 0.9);
  color: #243149;
  border-right: 1px solid #e2e9f7;
  box-shadow: 18px 0 34px rgba(79, 119, 190, 0.08);
  backdrop-filter: blur(18px);
}

.user-shell .brand {
  gap: 12px;
  padding: 0 12px;
}

.user-shell .brand-mark {
  width: 50px;
  height: 50px;
  border: 0;
  border-radius: 14px;
  background: #eef3ff;
}

.user-shell .brand strong {
  color: #15213a;
  font-size: 22px;
}

.user-shell .brand :deep(.brand-gradient-title) {
  font-size: 32px;
  font-weight: 900;
  line-height: 1.08;
  letter-spacing: 0;
}

.user-shell .brand small {
  color: #708098;
  font-size: 14px;
}

.user-shell .sidebar-divider {
  margin: 18px 12px 28px;
  background: #e4ebf7;
}

.user-shell .side-nav-scroll {
  gap: 12px;
  padding: 0 0 18px;
}

.user-shell .side-nav a,
.user-shell .side-util-btn {
  min-height: 58px;
  border-radius: 14px;
  color: #33415f;
  font-size: 17px;
  font-weight: 800;
}

.user-shell .side-nav a {
  padding: 0 18px;
}

.user-shell .side-nav a.router-link-active,
.user-shell .side-nav a:hover {
  border-color: #dce5ff;
  background: linear-gradient(135deg, #edf3ff, #f4f1ff);
  color: #3f5cf5;
  box-shadow: inset 0 0 0 1px rgba(91, 140, 255, 0.1);
}

.user-shell .sidebar-utils {
  border-color: #e4ebf7;
  gap: 10px;
}

.user-shell .side-util-btn {
  justify-content: flex-start;
  padding: 0 18px;
  background: transparent;
}

.user-shell .side-util-btn:hover {
  background: #f1f5ff;
  color: #3f5cf5;
}

.side-profile-card {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 64px;
  padding: 0 14px;
  border: 0;
  border-radius: 999px;
  background: linear-gradient(135deg, #f2f6ff, #ffffff);
  color: #33415f;
  font-size: 16px;
  font-weight: 800;
  box-shadow: inset 0 0 0 1px rgba(218, 228, 250, 0.8);
  cursor: pointer;
}

.side-profile-card svg {
  margin-left: auto;
  color: #60718d;
}

.user-shell .workspace {
  grid-template-rows: 126px 1fr;
  background: #f4f7ff;
}

.user-shell .workspace.workspace-home {
  grid-template-rows: 1fr;
}

.user-shell .topbar {
  align-items: center;
  min-height: 126px;
  padding: 24px 34px 14px;
  background: transparent;
  border-bottom: 0;
  backdrop-filter: none;
}

.user-shell .content.home-content {
  padding: 0;
  height: 100%;
  overflow-y: auto;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 8px;
}

.user-meta {
  display: flex;
  flex-direction: column;
}

.username {
  color: #1b1f2a;
  font-weight: 800;
}

.role {
  color: #667085;
  font-size: 12px;
}

@media (max-width: 1180px) {
  .topbar-coach-stats {
    display: none;
  }
}
</style>

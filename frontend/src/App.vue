<template>
  <div class="layout-stage">
    <Transition
      :name="layoutTransitionName"
      mode="out-in"
      @before-leave="lockPageScroll"
      @after-enter="unlockPageScroll"
    >
      <main v-if="isStandalonePage" key="standalone" class="standalone-content">
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
          <strong>学生训练端</strong>
          <span>今天 3 次训练 · 平均分 86</span>
        </div>
        <label class="search-box">
          <Search :size="16" />
          <input type="search" placeholder="搜索动作、训练记录或报告" />
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
          <button class="icon-button" type="button" aria-label="系统设置" @click="goToSettings">
            <Settings :size="18" />
          </button>
          <button class="avatar avatar-button" type="button" aria-label="个人资料" @click="goToProfile">
            <UserAvatar size="sm" />
          </button>
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
  Gauge,
  Search,
  Settings,
  UploadCloud
} from "lucide-vue-next";

import UserAvatar from "./components/UserAvatar.vue";
import { useSettingsStore } from "./stores/settings";

const route = useRoute();
const router = useRouter();
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

const navItems = [
  { path: "/", label: "首页总览", icon: Gauge },
  { path: "/realtime", label: "实时检测", icon: Activity },
  { path: "/upload", label: "视频分析", icon: UploadCloud },
  { path: "/sessions", label: "训练记录", icon: ClipboardList },
  { path: "/reports", label: "个人报告", icon: BarChart3 },
  { path: "/rules", label: "动作规则", icon: Dumbbell }
];

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
</script>

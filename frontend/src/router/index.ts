import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

import DashboardView from "../views/DashboardView.vue";
import RealtimeDetectView from "../views/RealtimeDetectView.vue";
import VideoUploadView from "../views/VideoUploadView.vue";
import SessionsView from "../views/SessionsView.vue";
import ReportsView from "../views/ReportsView.vue";
import ExerciseRulesView from "../views/ExerciseRulesView.vue";
import ProfileView from "../views/ProfileView.vue";
import SettingsView from "../views/SettingsView.vue";
import LoginView from "../views/LoginView.vue";

const STANDALONE_PATHS = ["/profile", "/settings"];

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: LoginView, meta: { public: true } },
    { path: "/", component: DashboardView },
    { path: "/realtime", component: RealtimeDetectView },
    { path: "/upload", component: VideoUploadView },
    { path: "/sessions", component: SessionsView },
    { path: "/reports", component: ReportsView },
    { path: "/rules", component: ExerciseRulesView, meta: { adminOnly: true } },
    { path: "/profile", component: ProfileView },
    { path: "/settings", component: SettingsView }
  ]
});

router.beforeEach(async (to, from, next) => {
  const toStandalone = STANDALONE_PATHS.includes(to.path);
  const fromStandalone = STANDALONE_PATHS.includes(from.path);

  if (toStandalone && !fromStandalone) {
    to.meta.layoutTransition = "page-soft-forward";
  } else if (!toStandalone && fromStandalone) {
    to.meta.layoutTransition = "page-soft-back";
  } else {
    to.meta.layoutTransition = undefined;
  }

  const authStore = useAuthStore();

  if (authStore.token && !authStore.user) {
    await authStore.fetchCurrentUser();
  }

  const isAuthenticated = authStore.isAuthenticated;
  const isAdmin = authStore.isAdmin;

  if (to.meta.public) {
    if (isAuthenticated) {
      next(isAdmin ? "/rules" : "/");
    } else {
      next();
    }
    return;
  }

  if (!isAuthenticated) {
    next("/login");
    return;
  }

  if (to.meta.adminOnly && !isAdmin) {
    next("/");
    return;
  }

  next();
});

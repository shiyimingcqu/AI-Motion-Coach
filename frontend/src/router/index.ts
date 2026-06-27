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
import AdminDashboardView from "../views/AdminDashboardView.vue";
import AdminUsersView from "../views/AdminUsersView.vue";
import AdminAdminsView from "../views/AdminAdminsView.vue";
import AdminSessionsView from "../views/AdminSessionsView.vue";
import AdminReportsView from "../views/AdminReportsView.vue";
import AdminTemplatesView from "../views/AdminTemplatesView.vue";
import AdminSettingsView from "../views/AdminSettingsView.vue";

const STANDALONE_PATHS = ["/profile", "/settings"];

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: LoginView, meta: { public: true } },
    { path: "/", component: DashboardView, meta: { userOnly: true } },
    { path: "/realtime", component: RealtimeDetectView, meta: { userOnly: true } },
    { path: "/upload", component: VideoUploadView, meta: { userOnly: true } },
    { path: "/sessions", component: SessionsView, meta: { userOnly: true } },
    { path: "/reports", component: ReportsView, meta: { userOnly: true } },
    { path: "/rules", redirect: "/admin/rules" },
    { path: "/profile", component: ProfileView, meta: { userOnly: true } },
    { path: "/settings", component: SettingsView, meta: { userOnly: true } },
    { path: "/admin", component: AdminDashboardView, meta: { adminOnly: true } },
    { path: "/admin/users", component: AdminUsersView, meta: { adminOnly: true } },
    { path: "/admin/admins", component: AdminAdminsView, meta: { adminOnly: true } },
    { path: "/admin/sessions", component: AdminSessionsView, meta: { adminOnly: true } },
    { path: "/admin/reports", component: AdminReportsView, meta: { adminOnly: true } },
    { path: "/admin/rules", component: ExerciseRulesView, meta: { adminOnly: true } },
    { path: "/admin/templates", component: AdminTemplatesView, meta: { adminOnly: true } },
    { path: "/admin/settings", component: AdminSettingsView, meta: { adminOnly: true } }
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
      next(isAdmin ? "/admin" : "/");
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

  if (to.meta.userOnly && isAdmin) {
    next("/admin");
    return;
  }

  next();
});

<template>
  <div class="page admin-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">User Management</p>
        <h1>普通用户管理</h1>
        <p class="subtle">查看数据库中的普通用户账号、启用状态和训练概况。管理员账号不在此模块管理。</p>
      </div>
      <button class="primary-button" type="button" @click="openCreateModal">新增用户</button>
    </header>

    <section class="admin-toolbar panel">
      <label class="search-box admin-search">
        <Search :size="16" />
        <input v-model="keyword" type="search" placeholder="搜索用户名、角色或状态" />
      </label>
      <select v-model="statusFilter">
        <option value="all">全部状态</option>
        <option value="active">启用中</option>
        <option value="inactive">已禁用</option>
      </select>
      <span v-if="actionMessage" class="settings-status-message">{{ actionMessage }}</span>
    </section>

    <section class="admin-table panel">
      <div class="admin-table-head admin-users-grid">
        <span>用户</span>
        <span>角色</span>
        <span>状态</span>
        <span>最近训练</span>
        <span>平均分</span>
        <span>操作</span>
      </div>
      <div v-if="loading" class="loading-text">正在加载用户列表...</div>
      <div v-else-if="loadError" class="settings-status-message danger">{{ loadError }}</div>
      <template v-else>
        <div v-if="filteredUsers.length === 0" class="loading-text">暂无匹配用户。</div>
        <div v-for="user in filteredUsers" :key="user.id" class="admin-table-row admin-users-grid">
          <div>
            <strong>{{ user.username }}</strong>
            <small>@{{ user.username }}</small>
          </div>
          <span>{{ user.role === "admin" ? "管理员" : "普通用户" }}</span>
          <span class="status-pill" :class="user.is_active ? 'good' : 'danger'">
            {{ user.is_active ? "启用中" : "已禁用" }}
          </span>
          <span>{{ formatDate(user.created_at) }}</span>
          <strong>-</strong>
          <div class="admin-row-actions">
            <button class="secondary-button" type="button" @click="openDetailModal(user)">查看</button>
            <button
              class="text-button"
              type="button"
              :disabled="busyUserId === user.id"
              @click="toggleUserStatus(user)"
            >
              {{ user.is_active ? "禁用" : "启用" }}
            </button>
            <button
              class="danger-text-button"
              type="button"
              :disabled="busyUserId === user.id"
              @click="deleteUser(user)"
            >
              删除
            </button>
          </div>
        </div>
      </template>
    </section>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeCreateModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>新增普通用户</h3>
          <button class="close-button" type="button" aria-label="关闭" @click="closeCreateModal">
            <X :size="20" />
          </button>
        </div>

        <form class="template-form" @submit.prevent="createUser">
          <label class="form-field">
            <span>用户名</span>
            <input v-model.trim="createForm.username" type="text" minlength="3" maxlength="32" required />
          </label>

          <label class="form-field">
            <span>初始密码</span>
            <input v-model="createForm.password" type="password" minlength="6" maxlength="64" required />
          </label>

          <p class="settings-note">该入口只创建普通用户，管理员账号请在“管理员管理”中单独维护。</p>
          <p v-if="createError" class="error-message">{{ createError }}</p>

          <button class="primary-button" type="submit" :disabled="creatingUser">
            {{ creatingUser ? "创建中..." : "创建用户" }}
          </button>
        </form>
      </div>
    </div>

    <div v-if="selectedUser" class="modal-overlay" @click.self="closeDetailModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>用户详情</h3>
          <button class="close-button" type="button" aria-label="关闭" @click="closeDetailModal">
            <X :size="20" />
          </button>
        </div>

        <dl class="info-list info-list-readonly">
          <div>
            <dt>用户名</dt>
            <dd>{{ selectedUser.username }}</dd>
          </div>
          <div>
            <dt>角色</dt>
            <dd>{{ selectedUser.role === "admin" ? "管理员" : "普通用户" }}</dd>
          </div>
          <div>
            <dt>账号状态</dt>
            <dd>{{ selectedUser.is_active ? "启用中" : "已禁用" }}</dd>
          </div>
          <div>
            <dt>创建时间</dt>
            <dd>{{ formatDate(selectedUser.created_at) }}</dd>
          </div>
          <div>
            <dt>训练次数</dt>
            <dd>待接入训练记录</dd>
          </div>
          <div>
            <dt>平均评分</dt>
            <dd>待接入评估报告</dd>
          </div>
        </dl>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { Search, X } from "lucide-vue-next";
import { apiDelete, apiGet, apiPatch, apiPost } from "../api/client";

interface AdminUser {
  id: number;
  username: string;
  role: "user" | "admin";
  is_active: boolean;
  created_at: string | null;
}

const keyword = ref("");
const statusFilter = ref("all");
const users = ref<AdminUser[]>([]);
const loading = ref(true);
const loadError = ref("");
const actionMessage = ref("");
const busyUserId = ref<number | null>(null);
const selectedUser = ref<AdminUser | null>(null);
const showCreateModal = ref(false);
const creatingUser = ref(false);
const createError = ref("");
const createForm = reactive({
  username: "",
  password: "",
});

const filteredUsers = computed(() => {
  const text = keyword.value.trim().toLowerCase();
  return users.value.filter((user) => {
    const matchStatus =
      statusFilter.value === "all" ||
      (statusFilter.value === "active" && user.is_active) ||
      (statusFilter.value === "inactive" && !user.is_active);
    const matchKeyword =
      !text ||
      user.username.toLowerCase().includes(text) ||
      user.role.toLowerCase().includes(text) ||
      (user.is_active ? "启用中" : "已禁用").includes(text);
    return matchStatus && matchKeyword;
  });
});

function formatDate(value: string | null) {
  if (!value) return "-";
  return value.slice(0, 10);
}

async function loadUsers() {
  loading.value = true;
  loadError.value = "";
  actionMessage.value = "";

  try {
    const data = await apiGet<{ items: AdminUser[] }>("/admin/users");
    users.value = data.items ?? [];
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : "加载用户列表失败";
  } finally {
    loading.value = false;
  }
}

async function toggleUserStatus(user: AdminUser) {
  const nextActive = !user.is_active;
  const actionText = nextActive ? "启用" : "禁用";

  if (!window.confirm(`确定要${actionText}用户 ${user.username} 吗？`)) {
    return;
  }

  busyUserId.value = user.id;
  actionMessage.value = "";

  try {
    const updatedUser = await apiPatch<AdminUser>(`/admin/users/${user.id}`, {
      is_active: nextActive,
    });
    users.value = users.value.map((item) =>
      item.id === updatedUser.id ? updatedUser : item
    );
    actionMessage.value = `已${actionText}用户 ${updatedUser.username}。`;
  } catch (error) {
    actionMessage.value = error instanceof Error ? error.message : `${actionText}用户失败`;
  } finally {
    busyUserId.value = null;
  }
}

async function deleteUser(user: AdminUser) {
  if (!window.confirm(`确定要删除用户 ${user.username} 吗？删除后无法恢复。`)) {
    return;
  }

  busyUserId.value = user.id;
  actionMessage.value = "";

  try {
    await apiDelete(`/admin/users/${user.id}`);
    users.value = users.value.filter((item) => item.id !== user.id);
    if (selectedUser.value?.id === user.id) {
      selectedUser.value = null;
    }
    actionMessage.value = `已删除用户 ${user.username}。`;
  } catch (error) {
    actionMessage.value = error instanceof Error ? error.message : "删除用户失败";
  } finally {
    busyUserId.value = null;
  }
}

function openDetailModal(user: AdminUser) {
  selectedUser.value = user;
}

function closeDetailModal() {
  selectedUser.value = null;
}

function openCreateModal() {
  createForm.username = "";
  createForm.password = "";
  createError.value = "";
  showCreateModal.value = true;
}

function closeCreateModal() {
  if (creatingUser.value) {
    return;
  }
  showCreateModal.value = false;
}

async function createUser() {
  creatingUser.value = true;
  createError.value = "";
  actionMessage.value = "";

  try {
    const createdUser = await apiPost<AdminUser>("/admin/users", {
      username: createForm.username,
      password: createForm.password,
    });
    users.value = [...users.value, createdUser];
    actionMessage.value = `已创建普通用户 ${createdUser.username}。`;
    showCreateModal.value = false;
  } catch (error) {
    createError.value = error instanceof Error ? error.message : "创建用户失败";
  } finally {
    creatingUser.value = false;
  }
}

onMounted(loadUsers);
</script>

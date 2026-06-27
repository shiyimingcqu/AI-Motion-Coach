<template>
  <div class="page admin-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Administrator Management</p>
        <h1>管理员管理</h1>
        <p class="subtle">查看系统管理员账号。管理员账号默认平级，不在普通用户管理中禁用。</p>
      </div>
    </header>

    <section class="panel admin-note-list">
      <p>当前版本先提供管理员账号只读展示。新增管理员、移除管理员和权限分级可以后续单独设计。</p>
    </section>

    <section class="admin-table panel">
      <div class="admin-table-head admin-admins-grid">
        <span>管理员</span>
        <span>状态</span>
        <span>创建时间</span>
        <span>权限说明</span>
      </div>
      <div v-if="loading" class="loading-text">正在加载管理员列表...</div>
      <div v-else-if="loadError" class="settings-status-message danger">{{ loadError }}</div>
      <template v-else>
        <div v-if="admins.length === 0" class="loading-text">暂无管理员账号。</div>
        <div v-for="admin in admins" :key="admin.id" class="admin-table-row admin-admins-grid">
          <div>
            <strong>{{ admin.username }}</strong>
            <small>@{{ admin.username }}</small>
          </div>
          <span class="status-pill" :class="admin.is_active ? 'good' : 'danger'">
            {{ admin.is_active ? "启用中" : "已禁用" }}
          </span>
          <span>{{ formatDate(admin.created_at) }}</span>
          <span>拥有后台管理权限</span>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { apiGet } from "../api/client";

interface AdminAccount {
  id: number;
  username: string;
  role: "admin";
  is_active: boolean;
  created_at: string | null;
}

const admins = ref<AdminAccount[]>([]);
const loading = ref(true);
const loadError = ref("");

function formatDate(value: string | null) {
  if (!value) return "-";
  return value.slice(0, 10);
}

async function loadAdmins() {
  loading.value = true;
  loadError.value = "";

  try {
    const data = await apiGet<{ items: AdminAccount[] }>("/admin/admins");
    admins.value = data.items ?? [];
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : "加载管理员列表失败";
  } finally {
    loading.value = false;
  }
}

onMounted(loadAdmins);
</script>

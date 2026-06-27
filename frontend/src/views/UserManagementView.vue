<template>
  <div class="users-page">
    <header class="section-page-header">
      <div>
        <h1>User Management / 用户管理</h1>
        <p>Manage users, roles, and permissions</p>
      </div>
      <button class="blue-action-button" type="button">
        <UserPlus :size="20" />
        Add User
      </button>
    </header>

    <section class="summary-card-grid">
      <article v-for="item in summaryCards" :key="item.label" class="summary-card">
        <span>{{ item.label }}</span>
        <strong :class="item.tone">{{ item.value }}</strong>
      </article>
    </section>

    <section class="filter-card user-filter-card">
      <label class="session-search">
        <Search :size="20" />
        <input v-model="keyword" type="search" placeholder="Search users... / 搜索用户..." />
      </label>
      <select v-model="roleFilter">
        <option value="">All Roles</option>
        <option value="admin">Admin</option>
        <option value="user">User</option>
      </select>
      <select v-model="statusFilter">
        <option value="">All Status</option>
        <option value="active">Active</option>
        <option value="inactive">Inactive</option>
      </select>
    </section>

    <section class="users-table-card">
      <StateDisplay v-if="loading" type="loading" size="sm" />
      <StateDisplay v-else-if="filteredUsers.length === 0" type="empty" title="暂无用户" size="sm" />
      <table v-else class="users-table">
        <thead>
          <tr>
            <th>USER / 用户</th>
            <th>ROLE / 角色</th>
            <th>STATUS / 状态</th>
            <th>JOINED / 加入时间</th>
            <th>ACTIONS / 操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in filteredUsers" :key="u.id">
            <td>
              <div class="user-table-cell">
                <span>{{ u.username.charAt(0).toUpperCase() }}</span>
                <div>
                  <strong>{{ u.username }}</strong>
                </div>
              </div>
            </td>
            <td><span class="role-pill" :class="u.role">{{ u.role }}</span></td>
            <td><span class="status-badge" :class="{ inactive: !u.is_active }">{{ u.is_active ? "Active" : "Inactive" }}</span></td>
            <td>{{ u.created_at?.slice(0, 10) || "-" }}</td>
            <td>
              <div class="action-cell">
                <button class="link-button" type="button" @click="toggleActive(u)">{{ u.is_active ? 'Deactivate' : 'Activate' }}</button>
                <button class="delete-button" type="button" @click="handleDelete(u)">Delete</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Search, UserPlus } from "lucide-vue-next";
import StateDisplay from "../components/StateDisplay.vue";
import { getUsers, updateUser, deleteUser, type UserRecord } from "../api/admin";

const users = ref<UserRecord[]>([]);
const keyword = ref("");
const roleFilter = ref("");
const statusFilter = ref("");
const loading = ref(true);

const filteredUsers = computed(() => {
  let list = users.value;
  if (roleFilter.value) list = list.filter(u => u.role === roleFilter.value);
  if (statusFilter.value === "active") list = list.filter(u => u.is_active);
  if (statusFilter.value === "inactive") list = list.filter(u => !u.is_active);
  const q = keyword.value.trim().toLowerCase();
  if (q) list = list.filter(u => u.username.toLowerCase().includes(q));
  return list;
});

const summaryCards = computed(() => {
  const total = users.value.length;
  const admins = users.value.filter(u => u.role === "admin").length;
  const active = users.value.filter(u => u.is_active).length;
  return [
    { label: "Total Users / 总用户数", value: total, tone: "tone-text-blue" },
    { label: "Admins / 管理员", value: admins, tone: "tone-text-purple" },
    { label: "Active / 活跃", value: active, tone: "tone-text-green" },
    { label: "Inactive / 未激活", value: total - active, tone: "tone-text-orange" },
  ];
});

async function toggleActive(u: UserRecord) {
  try {
    const updated = await updateUser(u.id, { is_active: !u.is_active });
    const idx = users.value.findIndex(x => x.id === u.id);
    if (idx >= 0) users.value[idx] = updated;
  } catch (err: any) {
    alert("操作失败: " + (err.message || "网络错误"));
  }
}

async function handleDelete(u: UserRecord) {
  if (!confirm(`确定删除用户 "${u.username}"？此操作不可撤销。`)) return;
  try {
    await deleteUser(u.id);
    users.value = users.value.filter(x => x.id !== u.id);
  } catch (err: any) {
    alert("删除失败: " + (err.message || "网络错误"));
  }
}

onMounted(async () => {
  try {
    const data = await getUsers();
    users.value = data.items || [];
  } catch {
    users.value = [];
  } finally {
    loading.value = false;
  }
});
</script>

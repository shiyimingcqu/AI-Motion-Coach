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
      <article v-for="item in stats" :key="item.label" class="summary-card">
        <span>{{ item.label }}</span>
        <strong :class="item.tone">{{ item.value }}</strong>
      </article>
    </section>

    <section class="filter-card user-filter-card">
      <label class="session-search">
        <Search :size="20" />
        <input type="search" placeholder="Search users... / 搜索用户..." />
      </label>
      <select><option>All Roles</option></select>
      <select><option>All Status</option></select>
    </section>

    <section class="users-table-card">
      <table class="users-table">
        <thead>
          <tr>
            <th>USER / 用户</th>
            <th>ROLE / 角色</th>
            <th>SESSIONS / 训练次数</th>
            <th>AVG SCORE / 平均分</th>
            <th>STATUS / 状态</th>
            <th>JOINED / 加入时间</th>
            <th>ACTIONS / 操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.email">
            <td>
              <div class="user-table-cell">
                <span>{{ user.initial }}</span>
                <div>
                  <strong>{{ user.name }}</strong>
                  <small>
                    <Mail :size="13" />
                    {{ user.email }}
                  </small>
                </div>
              </div>
            </td>
            <td><span class="role-pill" :class="user.role.toLowerCase()">{{ user.role }}</span></td>
            <td>{{ user.sessions }}</td>
            <td>
              <div class="score-progress">
                <i :class="user.score >= 90 ? 'progress-green' : user.score < 80 ? 'progress-orange' : 'progress-blue'" :style="{ width: `${user.score}%` }" />
                <strong>{{ user.score }}</strong>
              </div>
            </td>
            <td><span class="status-badge" :class="{ inactive: user.status === 'Inactive' }">{{ user.status }}</span></td>
            <td>{{ user.joined }}</td>
            <td><MoreVertical :size="18" /></td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Mail, MoreVertical, Search, UserPlus } from "lucide-vue-next";

const stats = [
  { label: "Total Users / 总用户", value: 127, tone: "" },
  { label: "Active / 活跃", value: 118, tone: "tone-text-green" },
  { label: "Coaches / 教练", value: 8, tone: "" },
  { label: "New This Month / 本月新增", value: 12, tone: "tone-text-blue" }
];

const users = [
  { initial: "Z", name: "Zhang Wei / 张伟", email: "zhang.wei@example.com", role: "Admin", sessions: 142, score: 88, status: "Active", joined: "2026-01-15" },
  { initial: "L", name: "Li Na / 李娜", email: "li.na@example.com", role: "User", sessions: 95, score: 85, status: "Active", joined: "2026-02-20" },
  { initial: "W", name: "Wang Ming / 王明", email: "wang.ming@example.com", role: "Coach", sessions: 78, score: 92, status: "Active", joined: "2026-03-10" },
  { initial: "C", name: "Chen Jing / 陈静", email: "chen.jing@example.com", role: "User", sessions: 56, score: 82, status: "Active", joined: "2026-04-05" },
  { initial: "L", name: "Liu Yang / 刘洋", email: "liu.yang@example.com", role: "User", sessions: 23, score: 78, status: "Inactive", joined: "2026-05-12" }
];
</script>

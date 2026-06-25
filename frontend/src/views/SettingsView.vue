<template>
  <div class="settings-page">
    <header class="section-page-header">
      <div>
        <h1>Settings / 系统设置</h1>
        <p>Configure system preferences and options</p>
      </div>
    </header>

    <section class="settings-layout">
      <div class="settings-main">
        <article class="settings-card">
          <header>
            <span class="settings-icon tone-blue">
              <Camera :size="22" />
            </span>
            <h2>Camera Settings / 摄像头设置</h2>
          </header>
          <label>
            Default Camera / 默认摄像头
            <select>
              <option>Front Camera</option>
              <option>External USB Camera</option>
            </select>
          </label>
          <label>
            Resolution / 分辨率
            <select>
              <option>1920x1080 (Full HD)</option>
              <option>1280x720 (HD)</option>
            </select>
          </label>
          <label class="settings-check">
            <input type="checkbox" checked />
            Enable auto-focus / 启用自动对焦
          </label>
        </article>

        <article class="settings-card">
          <header>
            <span class="settings-icon tone-purple">
              <Settings2 :size="22" />
            </span>
            <h2>Detection Settings / 检测设置</h2>
          </header>
          <div class="range-row">
            <span>Detection Sensitivity / 检测灵敏度</span>
            <strong>High</strong>
            <input type="range" min="0" max="100" value="80" />
          </div>
          <div class="range-row">
            <span>Error Threshold / 错误阈值</span>
            <strong>Medium</strong>
            <input type="range" min="0" max="100" value="60" />
          </div>
          <label class="settings-check">
            <input type="checkbox" checked />
            Real-time feedback / 实时反馈
          </label>
        </article>

        <article class="settings-card">
          <header>
            <span class="settings-icon tone-orange">
              <Bell :size="22" />
            </span>
            <h2>Notifications / 通知设置</h2>
          </header>
          <label v-for="item in notifications" :key="item" class="settings-toggle-row">
            <span>{{ item }}</span>
            <input type="checkbox" :checked="item !== 'Weekly reports / 周报'" />
          </label>
        </article>

        <article class="settings-card">
          <header>
            <span class="settings-icon tone-green">
              <Database :size="22" />
            </span>
            <h2>Data & Storage / 数据与存储</h2>
          </header>
          <div class="storage-row">
            <span>Storage Used / 已使用存储</span>
            <strong>2.4 GB / 10 GB</strong>
          </div>
          <label class="settings-check">
            <input type="checkbox" checked />
            Auto-backup / 自动备份
          </label>
          <button class="outline-wide-button" type="button">Clear Cache / 清除缓存</button>
        </article>
      </div>

      <aside class="settings-side">
        <article class="settings-side-card blue-side-card">
          <span class="side-icon blue-solid">
            <Globe2 :size="26" />
          </span>
          <h2>Language / 语言</h2>
          <select>
            <option>English / 英语</option>
            <option>Chinese / 中文</option>
          </select>
        </article>

        <article class="settings-side-card purple-side-card">
          <span class="side-icon purple-solid">
            <Shield :size="26" />
          </span>
          <h2>Privacy / 隐私</h2>
          <label><input type="checkbox" checked /> Data analytics / 数据分析</label>
          <label><input type="checkbox" /> Share progress / 分享进度</label>
        </article>

        <article class="settings-side-card">
          <h2>System Info / 系统信息</h2>
          <dl class="system-info-list">
            <div><dt>Version</dt><dd>v2.1.0</dd></div>
            <div><dt>Last Updated</dt><dd>Jun 25, 2026</dd></div>
            <div><dt>AI Model</dt><dd>PoseNet v4</dd></div>
          </dl>
        </article>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import {
  Bell,
  Camera,
  Database,
  Globe2,
  Settings2,
  Shield
} from "lucide-vue-next";

const notifications = [
  "Training reminders / 训练提醒",
  "Achievement alerts / 成就提醒",
  "Error notifications / 错误通知",
  "Weekly reports / 周报"
];
</script>

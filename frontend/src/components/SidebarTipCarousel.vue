<template>
  <aside class="tip-carousel" aria-label="训练小贴士" @mouseenter="pause" @mouseleave="resume">
    <div class="tip-window">
      <div class="tip-track" :style="trackStyle">
        <div
          v-for="(tip, i) in tips"
          :key="i"
          class="tip-card"
          :style="{ background: tip.bg }"
        >
          <div class="tip-icon-area" :style="{ background: tip.accent }">
            <component :is="tip.icon" :size="28" :color="tip.iconColor" />
          </div>
          <div class="tip-text">
            <strong>{{ tip.title }}</strong>
            <p>{{ tip.desc }}</p>
          </div>
        </div>
      </div>
    </div>
    <div class="tip-dots" v-if="tips.length > 1">
      <button
        v-for="(_, i) in tips"
        :key="i"
        :class="['tip-dot', { active: i === current }]"
        :aria-label="`第 ${i + 1} 条`"
        @click="goTo(i)"
      />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { Flame, Sparkles, Timer, ShieldCheck, Zap } from 'lucide-vue-next'

const tips = [
  {
    title: '镜头对准全身',
    desc: '将手机放置在1.5-2米处，确保全身入镜，AI识别更精准',
    icon: Sparkles,
    iconColor: '#6366f1',
    accent: 'linear-gradient(135deg, #eef2ff, #e0e7ff)',
    bg: 'linear-gradient(135deg, #ffffff 60%, #eef2ff)',
  },
  {
    title: '每周训练3-5次',
    desc: '每次选择2-3个动作，坚持打卡，系统会追踪你的进步曲线',
    icon: Timer,
    iconColor: '#0ea5e9',
    accent: 'linear-gradient(135deg, #f0f9ff, #e0f2fe)',
    bg: 'linear-gradient(135deg, #ffffff 60%, #f0f9ff)',
  },
  {
    title: '深蹲膝盖不内扣',
    desc: '下蹲时膝盖朝向脚尖方向，保持与肩同宽，避免膝关节损伤',
    icon: ShieldCheck,
    iconColor: '#f97316',
    accent: 'linear-gradient(135deg, #fff7ed, #ffedd5)',
    bg: 'linear-gradient(135deg, #ffffff 60%, #fff7ed)',
  },
  {
    title: '平板支撑不塌腰',
    desc: '身体保持一条直线，核心持续收紧，从30秒开始逐步增加时长',
    icon: Flame,
    iconColor: '#ef4444',
    accent: 'linear-gradient(135deg, #fef2f2, #fee2e2)',
    bg: 'linear-gradient(135deg, #ffffff 60%, #fef2f2)',
  },
  {
    title: '查看训练反馈',
    desc: '每次训练后查看动作评分和纠正建议，用数据让每一次进步看得见',
    icon: Zap,
    iconColor: '#10b981',
    accent: 'linear-gradient(135deg, #ecfdf5, #d1fae5)',
    bg: 'linear-gradient(135deg, #ffffff 60%, #ecfdf5)',
  },
]

const current = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const trackStyle = computed(() => ({
  transform: `translateX(-${current.value * 100}%)`,
}))

function goTo(index: number) {
  current.value = index
}

function next() {
  current.value = (current.value + 1) % tips.length
}

function resume() {
  stop()
  timer = setInterval(next, 3500)
}

function pause() {
  stop()
}

function stop() {
  if (timer !== null) {
    clearInterval(timer)
    timer = null
  }
}

resume()

onBeforeUnmount(stop)
</script>

<style scoped>
.tip-carousel {
  flex-shrink: 0;
  margin: 20px 0 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tip-window {
  overflow: hidden;
  border-radius: 16px;
  border: 1px solid #e8ecf4;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.03);
  background: #fff;
}

.tip-track {
  display: flex;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  will-change: transform;
}

.tip-card {
  min-width: 100%;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  box-sizing: border-box;
}

.tip-icon-area {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: grid;
  place-items: center;
}

.tip-text {
  flex: 1;
  min-width: 0;
}

.tip-text strong {
  display: block;
  color: #1e293b;
  font-size: 14px;
  font-weight: 800;
  line-height: 1.3;
  margin-bottom: 3px;
}

.tip-text p {
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
}

.tip-dots {
  display: flex;
  justify-content: center;
  gap: 6px;
}

.tip-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  border: 0;
  padding: 0;
  background: #d1d5db;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tip-dot.active {
  width: 20px;
  background: #6366f1;
  border-radius: 999px;
}

.tip-dot:hover {
  background: #a5b4fc;
}
</style>

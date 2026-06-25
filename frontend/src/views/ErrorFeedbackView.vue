<template>
  <div class="feedback-page">
    <header class="section-page-header">
      <div>
        <h1>Error Feedback / 动作错误反馈</h1>
        <p>Real-time error detection and correction suggestions</p>
      </div>
    </header>

    <section class="feedback-stats-grid">
      <article v-for="item in stats" :key="item.label" class="feedback-stat-card" :class="item.tone">
        <span>
          <component :is="item.icon" :size="18" />
        </span>
        <div>
          <p>{{ item.label }}</p>
          <strong>{{ item.value }}</strong>
        </div>
      </article>
    </section>

    <section class="feedback-card">
      <h2>Recent Error Detections / 最近检测到的错误</h2>
      <div class="error-detection-list">
        <article v-for="item in detections" :key="item.time" class="error-detection-row" :class="item.tone">
          <header>
            <div>
              <strong>{{ item.exercise }}</strong>
              <span>{{ item.type }}</span>
            </div>
            <time>{{ item.time }}</time>
          </header>
          <p>{{ item.problem }}</p>
          <div>
            <strong>Correction Suggestion / 纠正建议:</strong>
            <span>{{ item.suggestion }}</span>
          </div>
        </article>
      </div>
    </section>

    <section class="feedback-card">
      <h2>Common Mistakes Analysis / 常见错误分析</h2>
      <div class="mistake-list">
        <article v-for="item in mistakes" :key="item.exercise" class="mistake-row">
          <header>
            <strong>{{ item.exercise }}</strong>
            <span>Frequency: <b>{{ item.errors }} errors</b></span>
          </header>
          <div class="mistake-tags">
            <span v-for="tag in item.tags" :key="tag">{{ tag }}</span>
          </div>
          <div class="mistake-bar">
            <i :style="{ width: `${item.percent}%` }" />
            <strong>{{ item.percent }}%</strong>
          </div>
        </article>
      </div>
    </section>

    <section class="ai-recommend-card">
      <span class="blue-solid">
        <Info :size="20" />
      </span>
      <div>
        <h2>AI Recommendations / AI 建议</h2>
        <p>• Focus on knee alignment during squats - 35% of errors detected in this area</p>
        <p>• Review push-up form video tutorial to reduce elbow flare incidents</p>
        <p>• Consider adding plank progression exercises to improve core stability</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import {
  AlertTriangle,
  CheckCircle2,
  Info,
  ShieldAlert
} from "lucide-vue-next";

const stats = [
  { label: "Critical / 严重错误", value: 3, icon: ShieldAlert, tone: "critical" },
  { label: "Warning / 警告", value: 7, icon: AlertTriangle, tone: "warning" },
  { label: "Minor / 轻微错误", value: 12, icon: Info, tone: "minor" },
  { label: "Correct / 正确动作", value: 45, icon: CheckCircle2, tone: "correct" }
];

const detections = [
  { exercise: "Squat / 深蹲", type: "Knee alignment / 膝盖对齐", problem: "Knees extending beyond toes / 膝盖超过脚尖", suggestion: "Keep knees aligned with toes, push hips back / 保持膝盖与脚尖对齐，臀部后推", time: "14:32:15", tone: "critical" },
  { exercise: "Push-up / 俯卧撑", type: "Back posture / 背部姿态", problem: "Lower back sagging / 下背部下垂", suggestion: "Engage core muscles, maintain straight line / 收紧核心肌群，保持身体直线", time: "14:30:42", tone: "warning" },
  { exercise: "Plank / 平板支撑", type: "Hip position / 髋部位置", problem: "Hips too high / 髋部过高", suggestion: "Lower hips to neutral position / 将髋部降至中立位置", time: "14:28:10", tone: "warning" },
  { exercise: "Lunge / 弓步蹲", type: "Step distance / 步幅距离", problem: "Step too short / 步幅过小", suggestion: "Increase step distance for better form / 增加步幅以获得更好的动作形态", time: "14:25:33", tone: "minor" }
];

const mistakes = [
  { exercise: "Squat / 深蹲", tags: ["Knee valgus / 膝盖内扣", "Incomplete depth / 深度不足", "Forward lean / 身体前倾"], errors: 28, percent: 93 },
  { exercise: "Push-up / 俯卧撑", tags: ["Elbow flare / 肘部外展", "Incomplete range / 幅度不足", "Head position / 头部位置"], errors: 22, percent: 73 },
  { exercise: "Plank / 平板支撑", tags: ["Hip sag / 髋部下沉", "Shoulder misalignment / 肩部错位", "Head dropping / 头部下垂"], errors: 18, percent: 60 }
];
</script>

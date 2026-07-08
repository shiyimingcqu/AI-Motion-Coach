<template>
  <div class="home-page">
    <header class="home-top">
      <div>
        <SplitText
          tag="h1"
          text="早上好，继续加油！"
          className="home-greeting"
          :delay="40"
          :duration="0.7"
          splitType="chars"
          :from="{ opacity: 0, y: 30 }"
          :to="{ opacity: 1, y: 0 }"
        />
        <SplitText
          tag="p"
          text="好姿态，让你更自信、更轻松、更健康。"
          className="home-greeting-sub"
          :delay="30"
          :duration="0.5"
          splitType="words"
          :from="{ opacity: 0, y: 20 }"
          :to="{ opacity: 1, y: 0 }"
        />
      </div>

      <div class="home-top-actions">
        <div class="reminder-pill">
          <Bell :size="18" />
          <span>久坐提醒：每 45 分钟起来活动一下哦</span>
        </div>
        <UserAvatar size="md" />
        <ChevronDown :size="18" />
      </div>
    </header>

    <section class="overview-grid" aria-label="今日训练概览">
      <article class="overview-card">
        <div class="overview-icon blue">
          <Activity :size="30" />
        </div>
        <div>
          <span>今日训练</span>
          <strong>
            <CountUp :to="todayMinutes" :duration="1.2" class-name="count-up-text" />
            <small> 分钟</small>
          </strong>
          <p>已完成</p>
        </div>
        <CheckCircle2 class="overview-check" :size="28" />
      </article>

      <article class="overview-card">
        <div class="overview-icon violet">
          <Star :size="30" />
        </div>
        <div>
          <span>平均得分</span>
          <strong>
            <CountUp :to="averageScore" :duration="1.3" class-name="count-up-text" />
            <small> 分</small>
          </strong>
          <p>比昨天 <b>+{{ scoreChange }} 分</b></p>
        </div>
      </article>

      <article class="overview-card">
        <div class="overview-icon green">
          <CalendarDays :size="30" />
        </div>
        <div>
          <span>最近练习</span>
          <strong class="text-value">{{ recentExerciseLabel }}</strong>
          <p>{{ recentTimeLabel }}</p>
        </div>
      </article>
    </section>

    <section class="assessment-banner">
      <div class="assessment-copy">
        <h2>看清动作问题，练出更好的自己</h2>
        <p>智能还原训练过程，分析动作质量并给出个性化建议。</p>
        <button type="button" class="primary-cta" @click="router.push('/start')">
          <span>开始评估</span>
          <ArrowRight :size="22" />
        </button>
      </div>
      <img class="assessment-figure" :src="heroPostureImg" alt="" />
    </section>

    <section class="home-content-grid">
      <button class="feature-card exercise-card" type="button" @click="router.push('/exercises')">
        <div class="card-title">
          <h3>动作库</h3>
          <p>精选动作，随时跟练</p>
        </div>
        <img :src="exerciseImg" alt="" />
        <span class="soft-link">
          查看全部动作
          <ChevronRight :size="18" />
        </span>
      </button>

      <button class="feature-card record-card" type="button" @click="router.push('/sessions')">
        <div class="card-title">
          <h3>训练记录</h3>
          <p>回顾历史，保持进步</p>
        </div>
        <div class="streak-ring">
          <div class="streak-center">
            <strong>
              <CountUp :to="streakDays" :duration="1.1" class-name="count-up-text" />
              <span>天</span>
            </strong>
            <small>连续训练</small>
          </div>
        </div>
        <div class="week-dots" aria-hidden="true">
          <i v-for="day in weekDays" :key="day" :class="{ active: day !== '五' }">{{ day }}</i>
        </div>
        <span class="soft-link">
          查看记录
          <ChevronRight :size="18" />
        </span>
      </button>

      <button class="feature-card report-card" type="button" @click="router.push('/export')">
        <div class="card-title">
          <h3>我的报告</h3>
          <p>了解变化，见证成长</p>
        </div>
        <div class="report-preview" aria-hidden="true">
          <div class="report-bars">
            <i></i>
            <i></i>
            <i></i>
          </div>
          <svg viewBox="0 0 220 96" role="img">
            <path d="M10 76 C38 66, 42 54, 68 58 S106 45, 124 34 S160 52, 174 36 S202 24, 214 18" />
          </svg>
        </div>
        <p class="last-report">上次评估：3 天前</p>
        <span class="soft-link">
          查看报告
          <ChevronRight :size="18" />
        </span>
      </button>

      <div class="side-stack">
        <article class="mini-card progress-card">
          <div>
            <div class="mini-title">
              <TrendingUp :size="18" />
              <h3>最近进步</h3>
            </div>
            <p>含胸程度</p>
            <strong>改善了 15%</strong>
            <span>继续保持，你很棒！</span>
          </div>
          <img :src="thumbImg" alt="" />
        </article>

        <article class="mini-card coach-card">
          <div>
            <div class="mini-title">
              <Lightbulb :size="18" />
              <h3>训练小贴士</h3>
            </div>
            <p>站立时，想象头顶有根绳子</p>
            <span>轻轻向上提，帮助你保持挺拔。</span>
          </div>
          <img :src="coachBustImg" alt="" />
        </article>
      </div>
    </section>

    <section class="encourage-card">
      <img class="heart-icon" :src="heartIconImg" alt="" />
      <div>
        <h2>你已经很棒了！</h2>
        <p>每一次训练，都是在为更好的自己努力。坚持下去，你会看到更大的改变！</p>
      </div>
      <img class="heart-character" :src="heartCharacterImg" alt="" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import SplitText from "@/components/SplitText.vue";
import {
  Activity,
  ArrowRight,
  Bell,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Lightbulb,
  Star,
  TrendingUp,
} from "lucide-vue-next";

import UserAvatar from "@/components/UserAvatar.vue";
import CountUp from "@/components/CountUp.vue";
import { getDashboardStats, type DashboardStats } from "@/api/dashboard";
import { exercises } from "@/stores/training";
import heroPostureImg from "@/assets/home-hero-posture.png";
import exerciseImg from "@/assets/home-exercise-bird-dog.png";
import thumbImg from "@/assets/home-progress-thumb.png";
import heartCharacterImg from "@/assets/home-heart-character-soft.png";
import heartIconImg from "@/assets/home-heart-icon-soft.png";
import coachBustImg from "@/assets/home-coach-bust.png";

const router = useRouter();
const stats = ref<DashboardStats | null>(null);
const weekDays = ["一", "二", "三", "四", "五", "六", "日"];
const streakDays = 7;

const exerciseName = (key: string): string =>
  exercises.find((exercise) => exercise.key === key)?.name ?? key;

const todayMinutes = computed(() => {
  const minutes = Math.round(stats.value?.total_duration_minutes ?? 8);
  return minutes > 0 ? Math.min(minutes, 99) : 8;
});

const averageScore = computed(() => Math.round(stats.value?.average_score ?? 83));
const scoreChange = computed(() => Math.max(1, Math.round(stats.value?.average_score_change ?? 6)));

const recentExerciseLabel = computed(() => {
  const recent = stats.value?.recent_sessions?.[0];
  return recent ? exerciseName(recent.exercise) : "挺胸开肩";
});

const recentTimeLabel = computed(() => {
  const recent = stats.value?.recent_sessions?.[0];
  if (!recent?.created_at) return "今天 09:12";

  const createdAt = new Date(recent.created_at);
  if (Number.isNaN(createdAt.getTime())) return "今天 09:12";

  return `今天 ${createdAt.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })}`;
});

onMounted(async () => {
  try {
    stats.value = await getDashboardStats();
  } catch (error) {
    console.warn("[HomeView] dashboard stats unavailable, using friendly defaults", error);
  }
});
</script>

<style scoped>
.home-page {
  display: grid;
  gap: 22px;
  padding: 38px 48px 24px;
  min-height: 100vh;
  background:
    radial-gradient(circle at 72% 8%, rgba(226, 236, 255, 0.72), transparent 34%),
    linear-gradient(180deg, #fbfdff 0%, #f3f7ff 100%);
  color: #14213d;
}

.home-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.home-top h1 {
  margin: 0;
  font-size: 33px;
  line-height: 1.2;
  letter-spacing: 0;
}

.home-top p,
.home-greeting-sub {
  margin: 10px 0 0;
  color: #78849b;
  font-size: 17px;
}

.home-top-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #4b5b78;
}

.reminder-pill {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 58px;
  padding: 0 24px;
  border-radius: 30px;
  background: rgba(241, 246, 255, 0.92);
  box-shadow: inset 0 0 0 1px rgba(213, 226, 255, 0.78);
  color: #334566;
  font-weight: 700;
}

.reminder-pill svg {
  color: #3d6cf6;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 24px;
}

.overview-card,
.feature-card,
.mini-card,
.encourage-card {
  border: 1px solid rgba(210, 222, 247, 0.92);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 18px 38px rgba(84, 112, 166, 0.08);
}

.overview-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 22px;
  min-height: 126px;
  padding: 24px;
  border-radius: 22px;
}

.overview-icon {
  display: grid;
  place-items: center;
  width: 74px;
  height: 74px;
  flex: 0 0 auto;
  border-radius: 50%;
  color: #fff;
}

.overview-icon.blue {
  background: linear-gradient(135deg, #6aa8ff, #3d65f4);
}

.overview-icon.violet {
  background: linear-gradient(135deg, #c2a5ff, #8057ec);
}

.overview-icon.green {
  background: linear-gradient(135deg, #7fe0a2, #35b76a);
}

.overview-card > div > span {
  display: block;
  color: #42506a;
  font-size: 16px;
  font-weight: 700;
}

.overview-card strong {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-top: 8px;
  color: #17213a;
  font-size: 46px;
  line-height: 1.1;
}

.overview-card :deep(.count-up-text) {
  display: inline-block;
  min-width: 1.2ch;
  font-variant-numeric: tabular-nums;
  font-size: 1em;
  font-weight: 950;
}

.overview-card strong.text-value {
  font-size: 25px;
}

.overview-card small {
  font-size: 18px;
  font-weight: 800;
}

.overview-card p {
  margin: 8px 0 0;
  color: #8190aa;
  font-size: 14px;
}

.overview-card b {
  color: #5b63f5;
}

.overview-check {
  margin-left: auto;
  color: #5d8cf6;
}

.assessment-banner {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 440px;
  min-height: 250px;
  overflow: hidden;
  border-radius: 24px;
  background:
    linear-gradient(90deg, rgba(232, 235, 255, 0.98) 0%, rgba(238, 244, 255, 0.96) 42%, rgba(224, 236, 255, 0.96) 100%);
  box-shadow: inset 0 0 0 1px rgba(207, 220, 255, 0.64);
}

.assessment-banner::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, transparent 0 58%, rgba(232, 238, 255, 0.42) 72%, transparent 100%);
}

.assessment-copy {
  position: relative;
  z-index: 1;
  display: grid;
  align-content: center;
  justify-items: start;
  padding: 38px 54px;
}

.assessment-copy h2 {
  margin: 0;
  font-size: 31px;
  line-height: 1.25;
  letter-spacing: 0;
}

.assessment-copy p {
  margin: 12px 0 26px;
  color: #74829d;
  font-size: 17px;
}

.primary-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  min-width: 220px;
  min-height: 62px;
  border: 0;
  border-radius: 16px;
  background: linear-gradient(135deg, #6890ff, #8755f0);
  color: #fff;
  font-size: 19px;
  font-weight: 800;
  box-shadow: 0 18px 32px rgba(94, 109, 241, 0.28);
  cursor: pointer;
}

.assessment-figure {
  position: absolute;
  right: 0;
  bottom: 0;
  width: min(38%, 430px);
  height: 100%;
  object-fit: cover;
  object-position: center right;
  mix-blend-mode: multiply;
  opacity: 0.92;
  -webkit-mask-image: linear-gradient(90deg, transparent 0%, #000 18%, #000 100%);
  mask-image: linear-gradient(90deg, transparent 0%, #000 18%, #000 100%);
}

.home-content-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) minmax(280px, 1.08fr);
  gap: 18px;
  align-items: stretch;
}

.feature-card {
  display: grid;
  gap: 14px;
  min-height: 298px;
  padding: 24px 18px 16px;
  border-radius: 18px;
  text-align: left;
  cursor: pointer;
}

.card-title h3,
.mini-title h3,
.encourage-card h2 {
  margin: 0;
  color: #17213a;
  letter-spacing: 0;
}

.card-title h3 {
  color: #315cf6;
  font-size: 21px;
}

.card-title p {
  margin: 8px 0 0;
  color: #7a879e;
  font-size: 15px;
}

.exercise-card img {
  width: 100%;
  max-height: 112px;
  object-fit: contain;
  mix-blend-mode: multiply;
}

.soft-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 48px;
  margin-top: auto;
  border-radius: 14px;
  background: #f0f3ff;
  color: #3345a8;
  font-weight: 800;
}

.streak-ring {
  position: relative;
  display: grid;
  place-items: center;
  justify-self: center;
  width: 116px;
  height: 116px;
  margin-top: 2px;
  border-radius: 50%;
  background:
    radial-gradient(circle, #fff 52%, transparent 53%),
    conic-gradient(#4f7cff 0 82%, #edf1ff 82% 100%);
  color: #23375d;
}

.streak-center {
  display: grid;
  place-items: center;
  gap: 3px;
  transform: translateY(2px);
}

.streak-center strong {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 2px;
  color: #23375d;
  font-size: 31px;
  line-height: 1;
}

.streak-center :deep(.count-up-text) {
  font-size: 31px;
  font-weight: 950;
  font-variant-numeric: tabular-nums;
}

.streak-center span {
  color: #6e7d97;
  font-size: 17px;
  font-weight: 900;
}

.streak-center small {
  color: #8090ab;
  font-size: 12px;
  line-height: 1;
}

.week-dots {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.week-dots i {
  display: grid;
  place-items: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #eef2ff;
  color: #9aa6bd;
  font-size: 11px;
  font-style: normal;
}

.week-dots i.active {
  background: #5d7ff4;
  color: #fff;
}

.report-preview {
  position: relative;
  min-height: 112px;
  overflow: hidden;
  border-radius: 14px;
  background: linear-gradient(135deg, #f4f7ff, #edf2ff);
}

.report-preview svg {
  position: absolute;
  inset: 10px 12px 8px 44px;
  width: calc(100% - 56px);
  height: calc(100% - 18px);
  fill: none;
  stroke: #9aa5ff;
  stroke-width: 4;
  filter: drop-shadow(0 8px 16px rgba(101, 115, 245, 0.18));
}

.report-bars {
  position: absolute;
  top: 28px;
  left: 20px;
  display: grid;
  gap: 12px;
}

.report-bars i {
  width: 13px;
  height: 13px;
  border-radius: 4px;
  background: #dfe5ff;
}

.last-report {
  margin: -4px 0 0;
  color: #8490a8;
  font-size: 14px;
}

.side-stack {
  display: grid;
  gap: 18px;
}

.mini-card {
  position: relative;
  min-height: 140px;
  overflow: hidden;
  padding: 24px;
  border-radius: 18px;
}

.mini-title {
  display: flex;
  align-items: center;
  gap: 9px;
}

.mini-title svg {
  color: #28a765;
}

.mini-title h3 {
  font-size: 20px;
}

.mini-card p {
  margin: 16px 0 6px;
  color: #717f98;
  font-size: 15px;
}

.mini-card strong {
  display: block;
  color: #2aaf61;
  font-size: 24px;
  line-height: 1.1;
}

.mini-card span {
  display: block;
  margin-top: 10px;
  color: #7d89a0;
  font-size: 14px;
}

.progress-card img {
  position: absolute;
  right: 6px;
  bottom: 6px;
  width: 104px;
  mix-blend-mode: multiply;
}

.coach-card {
  min-height: 140px;
}

.coach-card img {
  position: absolute;
  right: 12px;
  bottom: 8px;
  width: 92px;
  mix-blend-mode: multiply;
}

.coach-card > div {
  position: relative;
  z-index: 1;
  max-width: calc(100% - 104px);
}

.encourage-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 24px;
  min-height: 92px;
  overflow: hidden;
  padding: 18px 30px;
  border-radius: 18px;
  background: #f1f7ff;
}

.heart-icon {
  width: 42px;
  height: 42px;
  object-fit: contain;
  background: #f1f7ff;
}

.encourage-card h2 {
  font-size: 22px;
}

.encourage-card p {
  margin: 8px 0 0;
  color: #66738d;
  font-size: 15px;
}

.heart-character {
  margin-left: auto;
  width: 92px;
  object-fit: contain;
  background: #f1f7ff;
}

@media (max-width: 1280px) {
  .home-page {
    padding: 30px 28px 22px;
  }

  .home-content-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .side-stack {
    grid-column: 1 / -1;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .home-top,
  .overview-grid,
  .assessment-banner,
  .home-content-grid,
  .side-stack {
    grid-template-columns: 1fr;
  }

  .home-top {
    align-items: flex-start;
  }

  .home-top-actions {
    flex-wrap: wrap;
  }

  .assessment-banner {
    min-height: 420px;
  }

  .assessment-figure {
    width: 100%;
    height: 210px;
    top: auto;
  }

  .coach-card > div {
    max-width: calc(100% - 110px);
  }
}
</style>

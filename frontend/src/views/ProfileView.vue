<template>
  <div class="page">
    <button class="back-link" type="button" @click="goHome">
      <ArrowLeft :size="24" />
      返回首页
    </button>

    <header class="page-header">
      <div>
        <p class="eyebrow">Profile</p>
        <h1>个人资料</h1>
        <p class="subtle">查看当前训练者的基础信息、训练目标和阶段性表现。</p>
      </div>
    </header>

    <section class="profile-hero panel">
      <div class="profile-avatar">林</div>
      <div>
        <p class="eyebrow">Trainee</p>
        <h2>林同学</h2>
        <p class="subtle">目标：提升下肢稳定性与动作标准度</p>
      </div>
    </section>

    <section class="profile-grid">
      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Basic Info</p>
            <h2>基础信息</h2>
          </div>
        </div>
        <dl class="info-list">
          <div>
            <dt>姓名</dt>
            <dd>林同学</dd>
          </div>
          <div>
            <dt>身份</dt>
            <dd>学生</dd>
          </div>
          <div>
            <dt>身高</dt>
            <dd>172 cm</dd>
          </div>
          <div>
            <dt>体重</dt>
            <dd>62 kg</dd>
          </div>
        </dl>
      </article>

      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Training</p>
            <h2>训练概况</h2>
          </div>
        </div>
        <dl class="info-list">
          <div>
            <dt>累计训练</dt>
            <dd>36 次</dd>
          </div>
          <div>
            <dt>平均评分</dt>
            <dd>86 分</dd>
          </div>
          <div>
            <dt>最常训练</dt>
            <dd>深蹲</dd>
          </div>
          <div>
            <dt>重点纠正</dt>
            <dd>下蹲深度不足</dd>
          </div>
        </dl>
      </article>
    </section>

    <section class="panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Goal</p>
          <h2>阶段目标</h2>
        </div>
      </div>
      <div class="goal-list">
        <span>连续 7 天完成训练</span>
        <span>深蹲有效率提升到 92%</span>
        <span>减少膝关节角度过小问题</span>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft } from "lucide-vue-next";
import { useRouter } from "vue-router";

const router = useRouter();

function goHome() {
  router.push("/");
}
</script>

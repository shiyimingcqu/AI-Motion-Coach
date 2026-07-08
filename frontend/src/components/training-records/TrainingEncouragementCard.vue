<template>
  <section class="tr-encourage">
    <div class="tr-encourage-text">
      <h4>保持节奏，继续加油！</h4>
      <p>你的努力正在让身体变得更好</p>
      <button type="button" class="tr-encourage-btn" @click="$emit('goal')">
        设定新目标
      </button>
    </div>
    <div class="tr-encourage-illustration" aria-hidden="true">
      <svg viewBox="0 0 130 130" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="enc-bg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#E9DEFE" />
            <stop offset="100%" stop-color="#C4A8FF" />
          </linearGradient>
        </defs>
        <circle cx="65" cy="65" r="55" fill="url(#enc-bg)" />
        <!-- Thumbs up icon -->
        <g transform="translate(35,30)" fill="#6C3BFF">
          <path d="M16 36V20c0-3.3 2.7-6 6-6h2c1.1 0 2 .9 2 2v8h14c2.2 0 4 1.8 4 4l-3 12c-.4 1.7-1.9 3-3.7 3H22c-3.3 0-6-2.7-6-6zM8 20h6v22H8c-1.1 0-2-.9-2-2V22c0-1.1.9-2 2-2z" />
        </g>
        <!-- 装饰 -->
        <circle cx="22" cy="32" r="3" fill="#6C3BFF" opacity="0.5" />
        <circle cx="108" cy="44" r="2.5" fill="#6C3BFF" opacity="0.4" />
        <circle cx="100" cy="98" r="2" fill="#6C3BFF" opacity="0.4" />
        <circle cx="20" cy="100" r="2" fill="#6C3BFF" opacity="0.3" />
      </svg>
    </div>
  </section>
</template>

<script setup lang="ts">
defineEmits<{
  (e: "goal"): void;
}>();
</script>

<style scoped>
.tr-encourage {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 22px 22px;
  background: linear-gradient(135deg, #F2EDFF 0%, #FAF8FF 100%);
  border: 1px solid #e6dbff;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(108, 59, 255, 0.08);
}

.tr-encourage-text { flex: 1; min-width: 0; }

.tr-encourage-text h4 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 800;
  color: #15172A;
}

.tr-encourage-text p {
  margin: 0 0 12px;
  font-size: 12px;
  color: #667085;
}

.tr-encourage-btn {
  display: inline-flex;
  align-items: center;
  height: 32px;
  padding: 0 16px;
  background: #6C3BFF;
  color: #ffffff;
  border: 0;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s;
}

.tr-encourage-btn:hover {
  background: #5B2BE8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(108, 59, 255, 0.3);
}

.tr-encourage-illustration {
  width: 80px;
  height: 80px;
  flex-shrink: 0;
}

.tr-encourage-illustration svg { width: 100%; height: 100%; display: block; }
</style>

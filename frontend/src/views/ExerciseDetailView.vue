<template>
  <div class="ed-page">
    <header class="ed-top">
      <button class="ed-back" type="button" @click="router.push('/exercises')">
        <ChevronLeft :size="18" />
        <span>返回动作库</span>
      </button>
    </header>

    <section class="ed-guide-card">
      <div class="ed-guide-frame" :class="{ 'is-static-page': Boolean(staticGuideImage) }">
        <img
          v-if="guideImage"
          :src="guideImage"
          :alt="`${exerciseInfo.name} 教学图`"
          class="ed-guide-image"
          :class="{ 'is-static-page': Boolean(staticGuideImage), 'is-fallback': !staticGuideImage }"
        />

        <button
          v-if="staticGuideImage"
          class="ed-overlay-train-btn"
          type="button"
          @click="showQR = true"
        >
          <Smartphone :size="18" />
          <span>扫码开始训练</span>
        </button>

        <button
          v-else
          class="ed-floating-train-btn"
          type="button"
          @click="showQR = true"
        >
          <Smartphone :size="18" />
          <span>扫码开始训练</span>
        </button>
      </div>
    </section>

    <TrainQRModal
      v-if="showQR"
      :exercise-name="exerciseInfo.name"
      :exercise-key="exerciseKey"
      :camera-view="exerciseInfo.cameraView"
      @close="showQR = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ChevronLeft, Smartphone } from "lucide-vue-next";
import TrainQRModal from "@/components/TrainQRModal.vue";
import jumpingJackGuide from "@/assets/exercise-detail-static/jumping-jack-guide.png";
import lungeGuide from "@/assets/exercise-detail-static/lunge-guide.png";
import plankGuide from "@/assets/exercise-detail-static/plank-guide.png";
import pushUpGuide from "@/assets/exercise-detail-static/push-up-guide.png";
import squatGuide from "@/assets/exercise-detail-static/squat-guide.png";

const route = useRoute();
const router = useRouter();

const showQR = ref(false);
const exerciseKey = computed(() => (route.params.key as string) || "squat");

type ExerciseInfo = {
  name: string;
  cameraView: string;
};

const exerciseMap: Record<string, ExerciseInfo> = {
  squat: { name: "深蹲", cameraView: "side" },
  push_up: { name: "俯卧撑", cameraView: "side" },
  plank: { name: "平板支撑", cameraView: "side" },
  lunge: { name: "弓步蹲", cameraView: "side" },
  jumping_jack: { name: "开合跳", cameraView: "front" },
  burpee: { name: "波比跳", cameraView: "front" },
  high_knees: { name: "高抬腿", cameraView: "front" },
  glute_bridge: { name: "臀桥", cameraView: "side" },
  mountain_climber: { name: "登山跑", cameraView: "side" },
  pull_up: { name: "引体向上", cameraView: "side" },
  bench_press: { name: "卧推", cameraView: "side" },
  barbell_squat: { name: "杠铃深蹲", cameraView: "side" },
  dumbbell_fly: { name: "哑铃飞鸟", cameraView: "side" },
  lat_pulldown: { name: "高位下拉", cameraView: "side" },
  dumbbell_curl: { name: "哑铃弯举", cameraView: "side" },
  dumbbell_press: { name: "哑铃推举", cameraView: "side" },
  dumbbell_shoulder_press: { name: "哑铃推肩", cameraView: "side" },
};

const exerciseInfo = computed(() => {
  return exerciseMap[exerciseKey.value] || { name: exerciseKey.value, cameraView: "front" };
});

const staticGuideMap: Record<string, string> = {
  squat: squatGuide,
  push_up: pushUpGuide,
  plank: plankGuide,
  lunge: lungeGuide,
  jumping_jack: jumpingJackGuide,
};

const staticGuideImage = computed(() => staticGuideMap[exerciseKey.value] || "");
const guideImage = computed(() => staticGuideImage.value || `/exercises/${exerciseKey.value}.png`);
</script>

<style scoped>
.ed-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0 0 24px;
}

.ed-top {
  display: flex;
  align-items: center;
}

.ed-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: transparent;
  color: #64748b;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
}

.ed-back:hover {
  color: #6c3bff;
}

.ed-guide-card {
  background: #ffffff;
  border: 1px solid #e9edfb;
  border-radius: 24px;
  box-shadow: 0 12px 30px rgba(81, 61, 168, 0.06);
  padding: 14px;
}

.ed-guide-frame {
  position: relative;
  border-radius: 20px;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #edf1fb;
  aspect-ratio: 1.5 / 1;
}

.ed-guide-image {
  display: block;
  width: 150%;
  height: auto;
}

.ed-guide-frame.is-static-page {
  aspect-ratio: 1.5 / 1;
}

.ed-guide-image.is-static-page {
  width: 100%;
  height: auto;
  max-width: none;
  transform: translate(0%, 0%);
  transform-origin: top left;
}

.ed-guide-image.is-fallback {
  min-height: 560px;
  max-height: 78vh;
  object-fit: contain;
  padding: 24px;
}

.ed-overlay-train-btn,
.ed-floating-train-btn {
  position: absolute;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 52px;
  padding: 0 20px;
  border: 0;
  border-radius: 14px;
  background: linear-gradient(180deg, #703dff 0%, #5d28ed 100%);
  color: #ffffff;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 14px 28px rgba(108, 59, 255, 0.26);
  z-index: 2;
}

.ed-overlay-train-btn {
  right: 11.1%;
  top: 49.6%;
  min-width: 210px;
}

.ed-floating-train-btn {
  right: 24px;
  bottom: 24px;
}

@media (max-width: 900px) {
  .ed-overlay-train-btn {
    right: 11.4%;
    top: 50.3%;
    min-width: 176px;
    height: 46px;
    padding: 0 16px;
    font-size: 14px;
  }
}

@media (max-width: 640px) {
  .ed-guide-card {
    padding: 10px;
    border-radius: 18px;
  }

  .ed-guide-frame {
    border-radius: 14px;
    aspect-ratio: 1.28 / 1;
  }

  .ed-overlay-train-btn {
    right: 9.8%;
    top: 52.2%;
    min-width: 156px;
    height: 42px;
    padding: 0 14px;
    border-radius: 12px;
    font-size: 13px;
  }

  .ed-guide-image.is-fallback {
    min-height: 320px;
  }
}
</style>

<template>
  <div class="ei-wrap">
    <img
      v-if="imageMap[type]"
      :src="imageMap[type]"
      :alt="type"
      class="ei-img"
      loading="lazy"
    />
    <svg
      v-else
      viewBox="0 0 140 140"
      xmlns="http://www.w3.org/2000/svg"
      class="ei-svg"
      :style="{ background: getBg() }"
    >
      <circle cx="70" cy="70" r="55" fill="rgba(160,174,192,0.06)" />
      <g transform="translate(45,35)" fill="none" stroke-linecap="round">
        <rect x="15" y="20" width="24" height="40" rx="10" stroke-width="4" stroke="#a0aec0" fill="rgba(160,174,192,0.1)" />
        <line x1="25" y1="60" x2="25" y2="90" stroke-width="4" stroke="#a0aec0" />
        <line x1="35" y1="60" x2="35" y2="90" stroke-width="4" stroke="#a0aec0" />
        <line x1="20" y1="25" x2="5" y2="45" stroke-width="4" stroke="#a0aec0" />
        <line x1="40" y1="25" x2="55" y2="45" stroke-width="4" stroke="#a0aec0" />
        <circle cx="27" cy="10" r="10" stroke-width="4" stroke="#a0aec0" fill="#f7fafc" />
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  type: string;
}>();

const imageMap: Record<string, string> = {
  squat: "/exercises/squat.png",
  push_up: "/exercises/push_up.png",
  jumping_jack: "/exercises/jumping_jack.png",
  plank: "/exercises/plank.png",
  lunge: "/exercises/lunge.png",
  burpee: "/exercises/burpee.png",
  high_knees: "/exercises/high_knees.png",
  glute_bridge: "/exercises/glute_bridge.png",
  bench_press: "/exercises/bench_press.png",
  pull_up: "/exercises/pull_up.png",
  barbell_squat: "/exercises/barbell_squat.png",
  mountain_climber: "/exercises/mountain_climber.png",
  dumbbell_fly: "/exercises/dumbbell_fly.png",
  lat_pulldown: "/exercises/lat_pulldown.png",
  dumbbell_curl: "/exercises/dumbbell_curl.png",
  dumbbell_press: "/exercises/dumbbell_press.png",
  dumbbell_shoulder_press: "/exercises/dumbbell_shoulder_press.png",
  russian_twist: "/exercises/russian_twist.png",
};

function getBg() {
  const map: Record<string, string> = {
    squat: "#ecfdf5",
    push_up: "#fef2f2",
    jumping_jack: "#eff6ff",
    plank: "#f5f3ff",
    lunge: "#ecfdf5",
    burpee: "#f5f3ff",
    high_knees: "#eff6ff",
    glute_bridge: "#fdf2f8",
    bench_press: "#fef3c7",
    pull_up: "#fefce8",
    barbell_squat: "#f5f3ff",
    mountain_climber: "#ecfdf5",
    dumbbell_fly: "#fef2f2",
    lat_pulldown: "#eff6ff",
    dumbbell_curl: "#fefce8",
    dumbbell_press: "#eff6ff",
    dumbbell_shoulder_press: "#ecfdf5",
    russian_twist: "#fdf2f8",
  };
  return map[props.type] || "#f1f5f9";
}
</script>

<style scoped>
.ei-wrap {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.ei-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  display: block;
}

.ei-svg {
  width: 100%;
  height: 100%;
  display: block;
}
</style>

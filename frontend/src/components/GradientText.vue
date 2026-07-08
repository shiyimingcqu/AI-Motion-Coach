<template>
  <span
    class="animated-gradient-text"
    :class="[
      showBorder ? 'with-border' : '',
      pauseOnHover ? 'pause-on-hover' : '',
      directionClass,
      className,
    ]"
    :style="gradientVars"
  >
    <span v-if="showBorder" class="gradient-overlay"></span>
    <span class="text-content">
      <slot />
    </span>
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    colors?: string[];
    animationSpeed?: number;
    direction?: "horizontal" | "vertical" | "diagonal";
    pauseOnHover?: boolean;
    yoyo?: boolean;
    showBorder?: boolean;
    className?: string;
  }>(),
  {
    colors: () => ["#40ffaa", "#4079ff", "#7c5cff", "#40ffaa"],
    animationSpeed: 3,
    direction: "horizontal",
    pauseOnHover: false,
    yoyo: true,
    showBorder: false,
    className: "",
  },
);

const directionClass = computed(() => `direction-${props.direction}`);

const gradientVars = computed(() => {
  const colors = [...props.colors, props.colors[0]].join(", ");
  const angle =
    props.direction === "vertical"
      ? "to bottom"
      : props.direction === "diagonal"
        ? "to bottom right"
        : "to right";

  return {
    "--gradient-image": `linear-gradient(${angle}, ${colors})`,
    "--gradient-speed": `${props.animationSpeed}s`,
    "--gradient-direction": props.yoyo ? "alternate" : "normal",
  };
});
</script>

<style scoped>
.animated-gradient-text {
  position: relative;
  display: inline-flex;
  max-width: fit-content;
  align-items: center;
  justify-content: center;
  overflow: visible;
  border-radius: 0;
}

.animated-gradient-text.with-border {
  padding: 0.35rem 0.75rem;
}

.gradient-overlay {
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  pointer-events: none;
  background-image: var(--gradient-image);
  background-size: 300% 100%;
  animation: gradient-pan var(--gradient-speed) linear infinite var(--gradient-direction);
}

.gradient-overlay::before {
  content: "";
  position: absolute;
  inset: 1px;
  z-index: -1;
  border-radius: inherit;
  background: rgba(255, 255, 255, 0.9);
}

.text-content {
  position: relative;
  z-index: 2;
  display: inline-block;
  color: transparent;
  background-image: var(--gradient-image);
  background-repeat: repeat;
  background-size: 300% 100%;
  background-clip: text;
  -webkit-background-clip: text;
  animation: gradient-pan var(--gradient-speed) linear infinite var(--gradient-direction);
}

.direction-vertical .text-content,
.direction-vertical .gradient-overlay {
  background-size: 100% 300%;
  animation-name: gradient-pan-vertical;
}

.direction-diagonal .text-content,
.direction-diagonal .gradient-overlay {
  background-size: 300% 300%;
}

.pause-on-hover:hover .text-content,
.pause-on-hover:hover .gradient-overlay {
  animation-play-state: paused;
}

@keyframes gradient-pan {
  from {
    background-position: 0% 50%;
  }

  to {
    background-position: 100% 50%;
  }
}

@keyframes gradient-pan-vertical {
  from {
    background-position: 50% 0%;
  }

  to {
    background-position: 50% 100%;
  }
}
</style>

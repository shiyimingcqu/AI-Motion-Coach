<template>
  <div class="stepper-host">
    <!-- Dots -->
    <div class="step-dots">
      <template v-for="(_, i) in total" :key="i">
        <div class="dot-wrap" :class="{ click: !noClick }" @click="goTo(i)">
          <div class="dot" :class="'dot-' + st(i)">
            <svg v-if="st(i) === 'done'" class="chk" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            <span v-else-if="st(i) === 'cur'" class="d" />
            <span v-else class="num">{{ i+1 }}</span>
          </div>
        </div>
        <div v-if="i < total-1" class="bar"><div class="bar-fill" :class="{ on: cur > i+1 }" /></div>
      </template>
    </div>

    <!-- Content -->
    <div class="box" :style="{ height: h + 'px' }">
      <div ref="bx">
        <Transition :name="dir >= 0 ? 'fw' : 'bw'" mode="out-in">
          <div :key="cur" class="pg">
            <component :is="currentComp" />
          </div>
        </Transition>
      </div>
    </div>

    <!-- Footer -->
    <div v-if="cur <= total" class="foot">
      <div class="row" :class="cur > 1 ? 'btw' : 'end'">
        <button v-if="cur > 1" class="b b-back" @click="prev">{{ bk }}</button>
        <button v-if="!last" class="b b-next" @click="nxt">{{ nx }}</button>
        <button v-else class="b b-go" :disabled="ld" @click="fin">{{ ld ? '…' : fn }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, useSlots, watch, nextTick } from 'vue';

const props = withDefaults(defineProps<{
  start?: number
  bk?: string
  nx?: string
  fn?: string
  noClick?: boolean
  ld?: boolean
}>(), { start: 1, bk: '← Back', nx: 'Next →', fn: 'Done', noClick: false, ld: false });

const emit = defineEmits<{ (e: 'change', n: number): void; (e: 'finish'): void }>();

const slots = useSlots();
const bx = ref<HTMLDivElement | null>(null);
const h = ref(100);
const cur = ref(props.start);
const dir = ref(1);

const kids = computed(() => slots.default?.() || []);
const total = computed(() => kids.value.length);
const last = computed(() => cur.value === total.value);

const currentComp = computed(() => ({
  render() { return kids.value[cur.value - 1]; },
}));

function st(i: number) {
  const n = i + 1;
  if (cur.value === n) return 'cur';
  if (cur.value > n) return 'done';
  return 'idle';
}

function remeasure() { nextTick(() => { if (bx.value) h.value = bx.value.offsetHeight; }); }
watch([cur, kids], remeasure, { immediate: true });

function goTo(i: number) {
  const n = i + 1;
  if (n === cur.value || props.noClick) return;
  dir.value = n > cur.value ? 1 : -1; cur.value = n;
  emit('change', n);
}
function prev() {
  if (cur.value <= 1) return;
  dir.value = -1; cur.value--; emit('change', cur.value);
}
function nxt() {
  if (last.value) return;
  dir.value = 1; cur.value++; emit('change', cur.value);
}
function fin() { emit('finish'); }
</script>

<style scoped>
.stepper-host {
  width: 100%; max-width: 36rem;
  border-radius: 1.75rem;
  background: rgba(18,18,28,0.88);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 24px 80px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06);
}

.step-dots { display: flex; align-items: center; padding: 2.5rem 2.5rem 0; }
.dot-wrap { display: flex; align-items: center; justify-content: center; }
.dot-wrap.click { cursor: pointer; }

.dot {
  display: flex; align-items: center; justify-content: center;
  width: 2.5rem; height: 2.5rem; border-radius: 9999px;
  font-weight: 700; font-size: 1rem;
  transition: all 0.35s;
}
.dot-idle { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.35); }
.dot-cur {
  background: #5227ff; color: #5227ff; transform: scale(1.08);
  box-shadow: 0 0 16px rgba(82,39,255,0.4);
}
.dot-done { background: #5227ff; color: #fff; }

.d { width: 0.9rem; height: 0.9rem; border-radius: 9999px; background: #fff; }
.chk { width: 1.125rem; height: 1.125rem; color: #fff; }

.bar { flex: 1; height: 0.1875rem; margin: 0 0.75rem; border-radius: 0.25rem; background: rgba(255,255,255,0.08); }
.bar-fill { height: 100%; width: 0%; border-radius: 0.25rem; background: #5227ff; transition: width 0.4s ease; }
.bar-fill.on { width: 100%; }

.box { position: relative; overflow: hidden; transition: height 0.4s cubic-bezier(0.34,1.56,0.64,1); }
.pg { padding: 2rem 2.5rem; }

.fw-enter-active { animation: fr .35s ease; }
.fw-leave-active  { animation: fl .25s ease; }
.bw-enter-active { animation: br .35s ease; }
.bw-leave-active  { animation: bl .25s ease; }
@keyframes fr { from { opacity:0; transform:translateX(28px) } to { opacity:1; transform:translateX(0) } }
@keyframes fl { from { opacity:1; transform:translateX(0) } to { opacity:0; transform:translateX(-28px) } }
@keyframes br { from { opacity:0; transform:translateX(-28px) } to { opacity:1; transform:translateX(0) } }
@keyframes bl { from { opacity:1; transform:translateX(0) } to { opacity:0; transform:translateX(28px) } }

.foot { padding: 0 2.5rem 2.5rem; }
.row { margin-top:2rem; display:flex; }
.row.btw { justify-content:space-between; }
.row.end { justify-content:flex-end; }

.b {
  font:inherit; font-size:1rem; border:none; cursor:pointer;
  display:inline-flex; align-items:center; justify-content:center;
  border-radius:9999px; font-weight:600; letter-spacing:-.01em;
  padding:.625rem 1.5rem; transition:all .2s;
}

.b-back { background:rgba(255,255,255,0.06); color:rgba(255,255,255,0.6); }
.b-back:hover { background:rgba(255,255,255,0.1); color:rgba(255,255,255,0.8); }

.b-next, .b-go { background:#5227ff; color:#fff; }
.b-next:hover, .b-go:hover { background:#461ee8; }
.b-go:disabled { opacity:.5; cursor:not-allowed; }
</style>

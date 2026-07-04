<template>
  <div ref="containerRef" class="pose-particle-viewer">
    <div v-if="!hasFrames" class="pose-particle-empty">
      <strong>暂无 3D 回放数据</strong>
      <span>完成一次网页实时训练后，这里会显示全息人体回放。</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import type { PoseReplayFrame, PoseReplayLandmark } from "../api/sessions";

type ParticleBinding = {
  boneIndex: number;
  t: number;
  angle: number;
  radiusScale: number;
};

type TorsoBinding = { u: number; v: number; shell: number };
type HeadBinding = { theta: number; phi: number; radiusScale: number };
type PalmBinding = { side: "left" | "right"; u: number; v: number; depth: number };
type FootBinding = { side: "left" | "right"; u: number; v: number; depth: number };
type BodyBone = { start: number; end: number; radius: number; particleCount: number };

const props = defineProps<{
  frames: PoseReplayFrame[];
  playing: boolean;
  speed: number;
  progress: number;
  backgroundImage?: string;
}>();
const emit = defineEmits<{
  "update:progress": [value: number];
  frameChange: [frame: PoseReplayFrame | null];
}>();

const HOLOGRAM_THEME = { background: "#01040a", body: "#77ddff", bodyCore: "#e9fbff", glow: "#38d5ff" };
const PARTICLE_TONES = {
  torso: new THREE.Color("#1b7fa8"), head: new THREE.Color("#b8f5ff"),
  arms: new THREE.Color("#f4fdff"), hands: new THREE.Color("#ffffff"),
  legs: new THREE.Color("#36e6c3"), feet: new THREE.Color("#74ffe5"),
};
const PARTICLE_HALO_TONES = {
  torso: new THREE.Color("#0f8fc5"), head: new THREE.Color("#59e7ff"),
  arms: new THREE.Color("#c8f9ff"), hands: new THREE.Color("#e9feff"),
  legs: new THREE.Color("#19d8b7"), feet: new THREE.Color("#48f6d6"),
};
const FRONT_DEPTH_TINT = new THREE.Color("#ffffff");
const BACK_DEPTH_TINT = new THREE.Color("#22254f");

const BODY_BONES: BodyBone[] = [
  { start: -1, end: 0, radius: 0.07, particleCount: 260 },
  { start: 11, end: 13, radius: 0.085, particleCount: 360 },
  { start: 13, end: 15, radius: 0.062, particleCount: 300 },
  { start: 12, end: 14, radius: 0.085, particleCount: 360 },
  { start: 14, end: 16, radius: 0.062, particleCount: 300 },
  { start: 23, end: 25, radius: 0.105, particleCount: 430 },
  { start: 25, end: 27, radius: 0.082, particleCount: 360 },
  { start: 24, end: 26, radius: 0.105, particleCount: 430 },
  { start: 26, end: 28, radius: 0.082, particleCount: 360 },
  { start: 11, end: 23, radius: 0.145, particleCount: 420 },
  { start: 12, end: 24, radius: 0.145, particleCount: 420 },
  { start: 11, end: 12, radius: 0.12, particleCount: 320 },
  { start: 23, end: 24, radius: 0.13, particleCount: 320 },
  { start: -2, end: -2, radius: 0, particleCount: 1500 },
];

const SKELETON_BONES: Array<[number, number]> = [
  [11, 13], [13, 15], [12, 14], [14, 16],
  [11, 23], [12, 24], [23, 24],
  [23, 25], [25, 27], [24, 26], [26, 28],
  [27, 31], [28, 32],
];

const RIB_COUNT = 6;
const RIB_SEGMENTS_PER_SIDE = 4;
const SPINE_SEGMENTS = 8;
const PALM_PARTICLE_COUNT = 140;
const FOOT_PARTICLE_COUNT = 190;
const PALM_LINE_SEGMENTS = 14;
const FOOT_LINE_SEGMENTS = 12;
const ANATOMY_SEGMENT_COUNT = SPINE_SEGMENTS + 4 + RIB_COUNT * RIB_SEGMENTS_PER_SIDE * 2 + 8 + 8 + PALM_LINE_SEGMENTS + FOOT_LINE_SEGMENTS;

const containerRef = ref<HTMLDivElement | null>(null);
const hasFrames = computed(() => props.frames.length > 0);

let renderer: THREE.WebGLRenderer | null = null;
let scene: THREE.Scene | null = null;
let camera: THREE.PerspectiveCamera | null = null;
let controls: OrbitControls | null = null;
let skeletonGroup: THREE.Group | null = null;
let floorGlow: THREE.Mesh | null = null;
let floorGrid: THREE.GridHelper | null = null;
let animationId = 0;
let resizeObserver: ResizeObserver | null = null;
let lastTick = 0;
let playbackMs = 0;

let particleGeometry: THREE.BufferGeometry | null = null;
let particleHaloGeometry: THREE.BufferGeometry | null = null;
let particlePositions: Float32Array | null = null;
let particleHaloPositions: Float32Array | null = null;
let particleColors: Float32Array | null = null;
let particleHaloColors: Float32Array | null = null;
let jointGeometry: THREE.BufferGeometry | null = null;
let jointPositions: Float32Array | null = null;
let lineGeometry: THREE.BufferGeometry | null = null;
let lineGlowGeometry: THREE.BufferGeometry | null = null;
let linePositions: Float32Array | null = null;
let lineGlowPositions: Float32Array | null = null;
let anatomyGeometry: THREE.BufferGeometry | null = null;
let anatomyGlowGeometry: THREE.BufferGeometry | null = null;
let anatomyPositions: Float32Array | null = null;
let anatomyGlowPositions: Float32Array | null = null;
let backgroundTexture: THREE.Texture | null = null;
let backgroundLoadToken = 0;
let _replayPrevPoints: THREE.Vector3[] | null = null;
let _replayPrevTime = 0;

let bodyParticles: THREE.Points | null = null;
let bodyParticleHalo: THREE.Points | null = null;
let jointParticles: THREE.Points | null = null;
const sunglassLensMeshes: THREE.Mesh[] = [];
let sunglassBridgeMesh: THREE.Mesh | null = null;
let skeletonLines: THREE.LineSegments | null = null;
let skeletonGlowLines: THREE.LineSegments | null = null;
let anatomyLines: THREE.LineSegments | null = null;
let anatomyGlowLines: THREE.LineSegments | null = null;

const particleBindings: ParticleBinding[] = [];
const torsoBindings: TorsoBinding[] = [];
const headBindings: HeadBinding[] = [];
const palmBindings: PalmBinding[] = [];
const footBindings: FootBinding[] = [];
const tempDirection = new THREE.Vector3();
const tempReference = new THREE.Vector3();
const tempNormalA = new THREE.Vector3();
const tempNormalB = new THREE.Vector3();
const tempCenter = new THREE.Vector3();

function initScene() {
  const container = containerRef.value;
  if (!container || renderer) return;

  scene = new THREE.Scene();
  scene.background = null;
  scene.fog = new THREE.Fog("#01040a", 6, 12);
  camera = new THREE.PerspectiveCamera(45, 1, 0.01, 100);
  camera.position.set(0, -5.0, 5.2);
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setClearColor(0x01040a, 0);
  container.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0, -5.0, 0);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.enablePan = false;
  controls.enableZoom = true;
  controls.enableRotate = true;
  controls.minDistance = 1.8;
  controls.maxDistance = 8;
  controls.minPolarAngle = Math.PI * 0.18;
  controls.maxPolarAngle = Math.PI * 0.82;

  scene.add(new THREE.AmbientLight(0x8ce9ff, 0.72));
  const rimLight = new THREE.DirectionalLight(0xe9fbff, 1.5);
  rimLight.position.set(2.8, 4, 4);
  scene.add(rimLight);

  updateSceneBackground(props.backgroundImage || "");
  addFloorGlow();
  createParticleSystems();
  resizeRenderer();
  resizeObserver = new ResizeObserver(resizeRenderer);
  resizeObserver.observe(container);
  animationId = window.requestAnimationFrame(animate);
}

function addFloorGlow() {
  if (!scene) return;
  floorGrid = new THREE.GridHelper(4.2, 18, 0x2ed7ff, 0x142844);
  floorGrid.position.y = -6.7;
  floorGrid.material.transparent = true;
  floorGrid.material.opacity = 0.1;
  scene.add(floorGrid);

  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const context = canvas.getContext("2d");
  if (context) {
    const gradient = context.createRadialGradient(128, 128, 8, 128, 128, 124);
    gradient.addColorStop(0, "rgba(126, 232, 255, 0.24)");
    gradient.addColorStop(0.34, "rgba(56, 213, 255, 0.1)");
    gradient.addColorStop(1, "rgba(56, 213, 255, 0)");
    context.fillStyle = gradient;
    context.fillRect(0, 0, 256, 256);
  }
  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.MeshBasicMaterial({ map: texture, transparent: true, opacity: 0.42, depthWrite: false, blending: THREE.AdditiveBlending });
  floorGlow = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 0.55), material);
  floorGlow.rotation.x = -Math.PI / 2;
  floorGlow.position.y = -6.7;
  scene.add(floorGlow);
}

function updateSceneBackground(imageUrl: string) {
  if (!scene) return;
  backgroundLoadToken += 1;
  const token = backgroundLoadToken;
  if (!imageUrl) { clearSceneBackground(); return; }
  const loader = new THREE.TextureLoader();
  loader.load(imageUrl, (texture) => {
    if (token !== backgroundLoadToken || !scene) { texture.dispose(); return; }
    clearSceneBackground();
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;
    texture.mapping = THREE.EquirectangularReflectionMapping;
    backgroundTexture = texture;
    scene.background = texture;
    scene.fog = null;
  });
}

function clearSceneBackground() {
  if (scene) { scene.background = null; scene.fog = new THREE.Fog("#01040a", 6, 12); }
  backgroundTexture?.dispose();
  backgroundTexture = null;
}

function createParticleSystems() {
  if (!scene) return;
  createBindings();
  skeletonGroup = new THREE.Group();
  skeletonGroup.rotation.y = Math.PI;
  skeletonGroup.position.y = 0;
  scene.add(skeletonGroup);

  const particleCount = particleBindings.length + headBindings.length + palmBindings.length + footBindings.length;
  particlePositions = new Float32Array(particleCount * 3);
  particleHaloPositions = new Float32Array(particleCount * 3);
  particleColors = new Float32Array(particleCount * 3);
  particleHaloColors = new Float32Array(particleCount * 3);
  particleGeometry = new THREE.BufferGeometry();
  particleHaloGeometry = new THREE.BufferGeometry();
  particleGeometry.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));
  particleHaloGeometry.setAttribute("position", new THREE.BufferAttribute(particleHaloPositions, 3));
  particleGeometry.setAttribute("color", new THREE.BufferAttribute(particleColors, 3));
  particleHaloGeometry.setAttribute("color", new THREE.BufferAttribute(particleHaloColors, 3));
  paintParticleColors();

  bodyParticleHalo = new THREE.Points(particleHaloGeometry, new THREE.PointsMaterial({ color: "#ffffff", size: 0.052, transparent: true, opacity: 0.16, depthWrite: false, vertexColors: true, blending: THREE.AdditiveBlending, sizeAttenuation: true }));
  skeletonGroup.add(bodyParticleHalo);
  bodyParticles = new THREE.Points(particleGeometry, new THREE.PointsMaterial({ color: "#ffffff", size: 0.019, transparent: true, opacity: 0.7, depthWrite: false, vertexColors: true, blending: THREE.AdditiveBlending, sizeAttenuation: true }));
  skeletonGroup.add(bodyParticles);

  jointPositions = new Float32Array(33 * 3);
  jointGeometry = new THREE.BufferGeometry();
  jointGeometry.setAttribute("position", new THREE.BufferAttribute(jointPositions, 3));
  jointParticles = new THREE.Points(jointGeometry, new THREE.PointsMaterial({ color: "#c9f8ff", size: 0.032, transparent: true, opacity: 0.1, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: true }));
  skeletonGroup.add(jointParticles);

  sunglassLensMeshes.length = 0;
  const sunglassMaterial = new THREE.MeshBasicMaterial({ color: "#010101", transparent: true, opacity: 0.96, side: THREE.DoubleSide, depthWrite: false, depthTest: false });
  for (let index = 0; index < 2; index += 1) {
    const lens = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), sunglassMaterial);
    lens.position.set(9999, 9999, 9999);
    lens.scale.set(0.19, 0.105, 1);
    lens.renderOrder = 30;
    sunglassLensMeshes.push(lens);
    skeletonGroup.add(lens);
  }
  sunglassBridgeMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), sunglassMaterial);
  sunglassBridgeMesh.position.set(9999, 9999, 9999);
  sunglassBridgeMesh.scale.set(0.08, 0.014, 1);
  sunglassBridgeMesh.renderOrder = 30;
  skeletonGroup.add(sunglassBridgeMesh);

  linePositions = new Float32Array(SKELETON_BONES.length * 2 * 3);
  lineGlowPositions = new Float32Array(SKELETON_BONES.length * 2 * 3);
  lineGeometry = new THREE.BufferGeometry();
  lineGlowGeometry = new THREE.BufferGeometry();
  lineGeometry.setAttribute("position", new THREE.BufferAttribute(linePositions, 3));
  lineGlowGeometry.setAttribute("position", new THREE.BufferAttribute(lineGlowPositions, 3));
  skeletonGlowLines = new THREE.LineSegments(lineGlowGeometry, new THREE.LineBasicMaterial({ color: HOLOGRAM_THEME.glow, transparent: true, opacity: 0.22, blending: THREE.AdditiveBlending }));
  skeletonGroup.add(skeletonGlowLines);
  skeletonLines = new THREE.LineSegments(lineGeometry, new THREE.LineBasicMaterial({ color: HOLOGRAM_THEME.bodyCore, transparent: true, opacity: 0.52, blending: THREE.AdditiveBlending }));
  skeletonGroup.add(skeletonLines);

  anatomyPositions = new Float32Array(ANATOMY_SEGMENT_COUNT * 2 * 3);
  anatomyGlowPositions = new Float32Array(ANATOMY_SEGMENT_COUNT * 2 * 3);
  anatomyGeometry = new THREE.BufferGeometry();
  anatomyGlowGeometry = new THREE.BufferGeometry();
  anatomyGeometry.setAttribute("position", new THREE.BufferAttribute(anatomyPositions, 3));
  anatomyGlowGeometry.setAttribute("position", new THREE.BufferAttribute(anatomyGlowPositions, 3));
  anatomyGlowLines = new THREE.LineSegments(anatomyGlowGeometry, new THREE.LineBasicMaterial({ color: HOLOGRAM_THEME.glow, transparent: true, opacity: 0.24, blending: THREE.AdditiveBlending }));
  skeletonGroup.add(anatomyGlowLines);
  anatomyLines = new THREE.LineSegments(anatomyGeometry, new THREE.LineBasicMaterial({ color: HOLOGRAM_THEME.bodyCore, transparent: true, opacity: 0.48, blending: THREE.AdditiveBlending }));
  skeletonGroup.add(anatomyLines);
}

function createBindings() {
  particleBindings.length = 0; torsoBindings.length = 0; headBindings.length = 0; palmBindings.length = 0; footBindings.length = 0;
  BODY_BONES.forEach((bone, boneIndex) => {
    if (bone.start === -2) {
      for (let index = 0; index < bone.particleCount; index += 1) { torsoBindings.push({ u: Math.random(), v: Math.random(), shell: Math.random() }); particleBindings.push({ boneIndex, t: 0, angle: 0, radiusScale: 1 }); }
      return;
    }
    for (let index = 0; index < bone.particleCount; index += 1) { particleBindings.push({ boneIndex, t: Math.random(), angle: Math.random() * Math.PI * 2, radiusScale: 0.38 + Math.random() * 0.62 }); }
  });
  for (let index = 0; index < 1050; index += 1) { headBindings.push({ theta: Math.random() * Math.PI * 2, phi: Math.acos(2 * Math.random() - 1), radiusScale: 0.72 + Math.random() * 0.28 }); }
  (["left", "right"] as const).forEach((side) => { for (let i = 0; i < PALM_PARTICLE_COUNT; i++) { const a = Math.random() * Math.PI * 2; const r = Math.sqrt(Math.random()); palmBindings.push({ side, u: Math.cos(a) * r, v: Math.sin(a) * r, depth: (Math.random() - 0.5) * 0.7 }); } });
  (["left", "right"] as const).forEach((side) => { for (let i = 0; i < FOOT_PARTICLE_COUNT; i++) { const a = Math.random() * Math.PI * 2; const r = Math.sqrt(Math.random()); footBindings.push({ side, u: Math.cos(a) * r, v: Math.sin(a) * r, depth: (Math.random() - 0.5) * 0.9 }); } });
}

function paintParticleColors() {
  if (!particleColors || !particleHaloColors) return;
  const bodyColorBuffer = particleColors; const haloColorBuffer = particleHaloColors;
  particleBindings.forEach((binding, index) => { const bone = BODY_BONES[binding.boneIndex]; const tone = getBoneTone(bone, binding.boneIndex); writeColor(bodyColorBuffer, index, PARTICLE_TONES[tone]); writeColor(haloColorBuffer, index, PARTICLE_HALO_TONES[tone]); });
  const headStart = particleBindings.length;
  for (let i = 0; i < headBindings.length; i++) { writeColor(bodyColorBuffer, headStart + i, PARTICLE_TONES.head); writeColor(haloColorBuffer, headStart + i, PARTICLE_HALO_TONES.head); }
  const palmStart = headStart + headBindings.length;
  for (let i = 0; i < palmBindings.length; i++) { writeColor(bodyColorBuffer, palmStart + i, PARTICLE_TONES.hands); writeColor(haloColorBuffer, palmStart + i, PARTICLE_HALO_TONES.hands); }
  const footStart = palmStart + palmBindings.length;
  for (let i = 0; i < footBindings.length; i++) { writeColor(bodyColorBuffer, footStart + i, PARTICLE_TONES.feet); writeColor(haloColorBuffer, footStart + i, PARTICLE_HALO_TONES.feet); }
  const ca = particleGeometry?.getAttribute("color") as THREE.BufferAttribute | undefined;
  const hca = particleHaloGeometry?.getAttribute("color") as THREE.BufferAttribute | undefined;
  if (ca) ca.needsUpdate = true;
  if (hca) hca.needsUpdate = true;
}

function getBoneTone(bone: BodyBone, boneIndex: number): keyof typeof PARTICLE_TONES {
  if (bone.start === -2 || boneIndex >= 9) return "torso";
  if (bone.start === -1) return "head";
  if ((bone.start >= 11 && bone.start <= 16) || (bone.end >= 11 && bone.end <= 16)) return "arms";
  if ((bone.start >= 23 && bone.start <= 32) || (bone.end >= 23 && bone.end <= 32)) return "legs";
  return "torso";
}

function getParticleTone(index: number): keyof typeof PARTICLE_TONES {
  if (index < particleBindings.length) { const bone = BODY_BONES[particleBindings[index].boneIndex]; return getBoneTone(bone, particleBindings[index].boneIndex); }
  const headStart = particleBindings.length; const palmStart = headStart + headBindings.length; const footStart = palmStart + palmBindings.length;
  if (index < palmStart) return "head"; if (index < footStart) return "hands"; return "feet";
}

function animate(now: number) {
  animationId = window.requestAnimationFrame(animate);
  updatePlayback(now);
  controls?.update();
  if (floorGlow && !Array.isArray(floorGlow.material)) { floorGlow.material.opacity = 0.34 + Math.sin(now * 0.002) * 0.05; }
  if (renderer && scene && camera) { renderer.render(scene, camera); }
}

function updatePlayback(now: number) {
  if (!hasFrames.value) { setVisible(false); lastTick = now; emit("frameChange", null); return; }
  setVisible(true);
  const duration = getDuration();
  if (props.playing && duration > 0) { const delta = lastTick ? now - lastTick : 0; playbackMs = (playbackMs + delta * props.speed) % duration; emit("update:progress", playbackMs / duration); }
  else { playbackMs = props.progress * duration; }
  lastTick = now;
  const frame = getFrameAt(playbackMs);
  emit("frameChange", frame);
  updatePose(frame);
}

function updatePose(frame: PoseReplayFrame | null) {
  if (!frame || !particlePositions || !particleHaloPositions || !jointPositions || !linePositions || !lineGlowPositions || !anatomyPositions || !anatomyGlowPositions) return;

  const bodyBuffer = particlePositions;
  const bodyHaloBuffer = particleHaloPositions;
  const jointBuffer = jointPositions;
  const skeletonBuffer = linePositions;
  const skeletonGlowBuffer = lineGlowPositions;
  const points = frame.landmarks.map(convertLandmark);

  // One Euro Filter — 静止时强平滑，快速运动时低延迟
  const now = performance.now();
  const dt = _replayPrevTime > 0 ? Math.min((now - _replayPrevTime) / 1000, 0.05) : 0.016;
  _replayPrevTime = now;

  if (!_replayPrevPoints) { _replayPrevPoints = points.map(p => p.clone()); }
  else {
    const minCutoff = 0.8;
    const baseCutoff = 2.0;
    const beta = 0.3;
    for (let i = 0; i < points.length; i++) {
      if (points[i] && _replayPrevPoints[i]) {
        const dx = points[i].x - _replayPrevPoints[i].x;
        const dy = points[i].y - _replayPrevPoints[i].y;
        const dz = points[i].z - _replayPrevPoints[i].z;
        const speed = Math.sqrt(dx * dx + dy * dy + dz * dz) / (dt || 0.016);
        const cutoff = Math.max(minCutoff, baseCutoff + beta * speed);
        const tau = 1 / (2 * Math.PI * cutoff);
        const alpha = 1 / (1 + tau / (dt || 0.016));
        _replayPrevPoints[i].x += alpha * (points[i].x - _replayPrevPoints[i].x);
        _replayPrevPoints[i].y += alpha * (points[i].y - _replayPrevPoints[i].y);
        _replayPrevPoints[i].z += alpha * (points[i].z - _replayPrevPoints[i].z);
        points[i].copy(_replayPrevPoints[i]);
      }
    }
  }

  const shoulderMid = getMidpoint(points, frame.landmarks, 11, 12);
  const hipMid = getMidpoint(points, frame.landmarks, 23, 24);
  let torsoIndex = 0;

  particleBindings.forEach((binding, particleIndex) => {
    const bone = BODY_BONES[binding.boneIndex];
    const bufferIndex = particleIndex * 3;
    const endLandmark = frame.landmarks[bone.end];
    const endPoint = points[bone.end];

    if (bone.start === -2) {
      const p11 = points[11]; const p12 = points[12]; const p23 = points[23]; const p24 = points[24];
      const l11 = frame.landmarks[11]; const l12 = frame.landmarks[12]; const l23 = frame.landmarks[23]; const l24 = frame.landmarks[24];
      const tb = torsoBindings[torsoIndex]; torsoIndex++;
      if (!p11 || !p12 || !p23 || !p24 || !isVisible(l11) || !isVisible(l12) || !isVisible(l23) || !isVisible(l24)) { hidePoint(bodyBuffer, bufferIndex); hidePoint(bodyHaloBuffer, bufferIndex); return; }
      const top = new THREE.Vector3().lerpVectors(p11, p12, tb.u);
      const bottom = new THREE.Vector3().lerpVectors(p23, p24, tb.u);
      const pos = new THREE.Vector3().lerpVectors(top, bottom, tb.v);
      writePoint(bodyBuffer, bufferIndex, pos);
      writePoint(bodyHaloBuffer, bufferIndex, pos);
    } else if (bone.start === -1) {
      if (!shoulderMid || !endLandmark || !isVisible(endLandmark)) { hidePoint(bodyBuffer, bufferIndex); hidePoint(bodyHaloBuffer, bufferIndex); return; }
      const position = calculateParticlePosition(shoulderMid, endPoint, binding.t, binding.angle, bone.radius * binding.radiusScale);
      writePoint(bodyBuffer, bufferIndex, position);
      writePoint(bodyHaloBuffer, bufferIndex, position);
    } else {
      const startLandmark = frame.landmarks[bone.start];
      const startPoint = points[bone.start];
      if (!startLandmark || !isVisible(startLandmark) || !endLandmark || !isVisible(endLandmark)) { hidePoint(bodyBuffer, bufferIndex); hidePoint(bodyHaloBuffer, bufferIndex); return; }
      const position = calculateParticlePosition(startPoint, endPoint, binding.t, binding.angle, bone.radius * binding.radiusScale);
      writePoint(bodyBuffer, bufferIndex, position);
      writePoint(bodyHaloBuffer, bufferIndex, position);
    }
  });

  const headCenter = getHeadCenter(points);
  const headStart = particleBindings.length;
  const palmStart = headStart + headBindings.length;
  const footStart = palmStart + palmBindings.length;
  headBindings.forEach((binding, index) => { const position = getSphereParticlePosition(headCenter, 0.19 * binding.radiusScale, binding.theta, binding.phi); writePoint(bodyBuffer, (headStart + index) * 3, position); writePoint(bodyHaloBuffer, (headStart + index) * 3, position); });

  const palmMap = [15, 16];
  palmMap.forEach((wristIdx, handSide) => {
    const wristPoint = points[wristIdx];
    const wristLandmark = frame.landmarks[wristIdx];
    if (!wristPoint || !wristLandmark || !isVisible(wristLandmark)) { for (let i = 0; i < PALM_PARTICLE_COUNT; i++) { const bi = palmStart + handSide * PALM_PARTICLE_COUNT + i; hidePoint(bodyBuffer, bi * 3); hidePoint(bodyHaloBuffer, bi * 3); } return; }
    for (let i = 0; i < PALM_PARTICLE_COUNT; i++) { const p = palmBindings[handSide * PALM_PARTICLE_COUNT + i]; const bi = palmStart + handSide * PALM_PARTICLE_COUNT + i; writePoint(bodyBuffer, bi * 3, new THREE.Vector3(wristPoint.x + p.u * 0.08, wristPoint.y + p.v * 0.08, wristPoint.z + p.depth * 0.08)); writePoint(bodyHaloBuffer, bi * 3, new THREE.Vector3(wristPoint.x + p.u * 0.08, wristPoint.y + p.v * 0.08, wristPoint.z + p.depth * 0.08)); }
  });

  const footMap = [27, 28];
  footMap.forEach((ankleIdx, footSide) => {
    const anklePoint = points[ankleIdx];
    const ankleLandmark = frame.landmarks[ankleIdx];
    if (!anklePoint || !ankleLandmark || !isVisible(ankleLandmark)) { for (let i = 0; i < FOOT_PARTICLE_COUNT; i++) { const bi = footStart + footSide * FOOT_PARTICLE_COUNT + i; hidePoint(bodyBuffer, bi * 3); hidePoint(bodyHaloBuffer, bi * 3); } return; }
    for (let i = 0; i < FOOT_PARTICLE_COUNT; i++) { const f = footBindings[footSide * FOOT_PARTICLE_COUNT + i]; const bi = footStart + footSide * FOOT_PARTICLE_COUNT + i; writePoint(bodyBuffer, bi * 3, new THREE.Vector3(anklePoint.x + f.u * 0.1, anklePoint.y + f.v * 0.1 - 0.06, anklePoint.z + f.depth * 0.1)); writePoint(bodyHaloBuffer, bi * 3, new THREE.Vector3(anklePoint.x + f.u * 0.1, anklePoint.y + f.v * 0.1 - 0.06, anklePoint.z + f.depth * 0.1)); }
  });

  frame.landmarks.forEach((landmark, index) => { const offset = index * 3; if (!isVisible(landmark)) { hidePoint(jointBuffer, offset); } else { writePoint(jointBuffer, offset, points[index]); } });
  updateSunglasses(points, frame.landmarks);

  SKELETON_BONES.forEach(([from, to], index) => {
    const offset = index * 6;
    if (!isVisible(frame.landmarks[from]) || !isVisible(frame.landmarks[to])) { hidePoint(skeletonBuffer, offset); hidePoint(skeletonGlowBuffer, offset); hidePoint(skeletonBuffer, offset + 3); hidePoint(skeletonGlowBuffer, offset + 3); }
    else { writePoint(skeletonBuffer, offset, points[from]); writePoint(skeletonGlowBuffer, offset, points[from]); writePoint(skeletonBuffer, offset + 3, points[to]); writePoint(skeletonGlowBuffer, offset + 3, points[to]); }
  });

  updateDepthParticleColors(bodyBuffer, points, frame.landmarks);
  markNeedsUpdate(particleGeometry); markNeedsUpdate(particleHaloGeometry); markNeedsUpdate(jointGeometry); markNeedsUpdate(lineGeometry); markNeedsUpdate(lineGlowGeometry);
}

function convertLandmark(point: PoseReplayLandmark): THREE.Vector3 {
  const scale = 3.2;
  return new THREE.Vector3((point.x - 0.5) * scale, -(point.y - 0.5) * scale - 5, -(point.z || 0) * 0.5);
}

function getMidpoint(points: THREE.Vector3[], landmarks: PoseReplayLandmark[], idxA: number, idxB: number): THREE.Vector3 | null {
  const la = landmarks[idxA]; const lb = landmarks[idxB];
  if (!la || !lb || (la.visibility ?? 1) < 0.35 || (lb.visibility ?? 1) < 0.35) return null;
  return new THREE.Vector3().addVectors(points[idxA], points[idxB]).multiplyScalar(0.5);
}

function calculateParticlePosition(start: THREE.Vector3, end: THREE.Vector3, t: number, angle: number, radius: number) {
  tempDirection.subVectors(end, start);
  if (tempDirection.lengthSq() < 0.0001) return tempCenter.copy(start);
  tempDirection.normalize();
  tempReference.set(Math.abs(tempDirection.y) < 0.9 ? 0 : 1, Math.abs(tempDirection.y) < 0.9 ? 1 : 0, 0);
  tempNormalA.crossVectors(tempDirection, tempReference).normalize();
  tempNormalB.crossVectors(tempDirection, tempNormalA).normalize();
  tempCenter.lerpVectors(start, end, t);
  return tempCenter.clone().addScaledVector(tempNormalA, Math.cos(angle) * radius).addScaledVector(tempNormalB, Math.sin(angle) * radius);
}

function getHeadCenter(points: THREE.Vector3[]) {
  if (points[7] && points[8] && points[0]) { return new THREE.Vector3().add(points[7]).add(points[8]).add(points[0]).divideScalar(3); }
  return points[0] ?? new THREE.Vector3();
}

function getSphereParticlePosition(center: THREE.Vector3, radius: number, theta: number, phi: number) {
  return new THREE.Vector3(center.x + radius * Math.sin(phi) * Math.cos(theta), center.y + radius * Math.cos(phi), center.z + radius * Math.sin(phi) * Math.sin(theta));
}

function updateSunglasses(points: THREE.Vector3[], landmarks: PoseReplayLandmark[]) {
  const leftEyeBase = points[2];
  const rightEyeBase = points[5];
  const nosePoint = points[0];
  if (!leftEyeBase || !rightEyeBase || !isVisible(landmarks[2]) || !isVisible(landmarks[5])) {
    hideSunglasses();
    return;
  }

  let facePushZ = 0.18;
  if (leftEyeBase && rightEyeBase && nosePoint && isVisible(landmarks[0])) {
    const eyeCenterZ = (leftEyeBase.z + rightEyeBase.z) * 0.5;
    const frontSign = Math.sign(nosePoint.z - eyeCenterZ) || 1;
    facePushZ = frontSign * 0.2;
  }

  const leftLens = leftEyeBase.clone();
  const rightLens = rightEyeBase.clone();
  leftLens.y += 0.018;
  rightLens.y += 0.018;
  leftLens.z += facePushZ;
  rightLens.z += facePushZ;

  const eyeAxis = new THREE.Vector3().subVectors(rightLens, leftLens);
  const eyeDistance = Math.max(0.001, eyeAxis.length());
  const angle = Math.atan2(eyeAxis.y, eyeAxis.x);
  eyeAxis.normalize();
  leftLens.addScaledVector(eyeAxis, -0.018);
  rightLens.addScaledVector(eyeAxis, 0.018);

  [leftLens, rightLens].forEach((point, index) => {
    const lens = sunglassLensMeshes[index];
    if (!lens) return;
    lens.position.copy(point);
    lens.rotation.set(0, 0, angle);
    lens.scale.set(0.19, 0.105, 1);
  });

  if (sunglassBridgeMesh) {
    const bridgePoint = new THREE.Vector3().lerpVectors(leftLens, rightLens, 0.5);
    sunglassBridgeMesh.position.copy(bridgePoint);
    sunglassBridgeMesh.rotation.set(0, 0, angle);
    sunglassBridgeMesh.scale.set(Math.max(0.05, eyeDistance * 0.28), 0.012, 1);
  }
}

function hideSunglasses() {
  sunglassLensMeshes.forEach((lens) => lens.position.set(9999, 9999, 9999));
  sunglassBridgeMesh?.position.set(9999, 9999, 9999);
}

function getFrameAt(timeMs: number) {
  if (!props.frames.length) return null;
  let frame = props.frames[0];
  for (const candidate of props.frames) { if (candidate.timestamp_ms > timeMs) break; frame = candidate; }
  return frame;
}

function getDuration() { return Math.max(1, props.frames[props.frames.length - 1]?.timestamp_ms ?? 1); }
function isVisible(point?: PoseReplayLandmark) { return Boolean(point && (point.visibility ?? 1) >= 0.35); }
function writePoint(buffer: Float32Array, offset: number, point: THREE.Vector3) { buffer[offset] = point.x; buffer[offset + 1] = point.y; buffer[offset + 2] = point.z; }
function writeColor(buffer: Float32Array, index: number, color: THREE.Color) { const off = index * 3; buffer[off] = color.r; buffer[off + 1] = color.g; buffer[off + 2] = color.b; }
function hidePoint(buffer: Float32Array, offset: number) { buffer[offset] = 9999; buffer[offset + 1] = 9999; buffer[offset + 2] = 9999; }
function markNeedsUpdate(geometry: THREE.BufferGeometry | null) { const a = geometry?.getAttribute("position") as THREE.BufferAttribute | undefined; if (a) a.needsUpdate = true; }
function setVisible(visible: boolean) { if (skeletonGroup) skeletonGroup.visible = visible; }

function updateDepthParticleColors(bodyBuffer: Float32Array, points: THREE.Vector3[], landmarks: PoseReplayLandmark[]) {
  if (!particleColors) return;
  const particleCount = particleBindings.length + headBindings.length + palmBindings.length + footBindings.length;
  const valid = points.filter(p => p); const avgZ = valid.length > 0 ? valid.reduce((s, p) => s + p.z, 0) / valid.length : 0;
  for (let i = 0; i < particleCount; i++) { const bx = bodyBuffer[i * 3]; if (bx > 9000) continue; const pz = bodyBuffer[i * 3 + 2] || avgZ; const depthFactor = Math.max(0, Math.min(1, (pz - avgZ + 0.8) / 1.6)); const color = PARTICLE_TONES[getParticleTone(i)].clone(); color.lerp(FRONT_DEPTH_TINT, depthFactor); writeColor(particleColors, i, color); }
  const ca = particleGeometry?.getAttribute("color") as THREE.BufferAttribute | undefined; if (ca) ca.needsUpdate = true;
}

function resizeRenderer() {
  const container = containerRef.value;
  if (!container || !renderer || !camera) return;
  const width = Math.max(1, container.clientWidth); const height = Math.max(1, container.clientHeight);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

watch(() => props.frames, () => { playbackMs = 0; lastTick = 0; emit("update:progress", 0); _replayPrevPoints = null; void nextTick(() => updatePose(props.frames[0] ?? null)); });
watch(() => props.progress, (value) => { if (!props.playing) { playbackMs = value * getDuration(); updatePose(getFrameAt(playbackMs)); } });
watch(() => props.backgroundImage, (imageUrl) => { updateSceneBackground(imageUrl || ""); });

onMounted(() => { initScene(); });
onBeforeUnmount(() => {
  window.cancelAnimationFrame(animationId);
  resizeObserver?.disconnect();
  controls?.dispose();
  if (renderer) { renderer.dispose(); const parent = renderer.domElement.parentNode; if (parent) parent.removeChild(renderer.domElement); }
});
</script>

<style scoped>
.pose-particle-viewer { position: absolute; inset: 0; min-height: 360px; }
.pose-particle-viewer :deep(canvas) { width: 100%; height: 100%; display: block; }
.pose-particle-empty { position: absolute; inset: 0; z-index: 4; display: grid; place-items: center; align-content: center; gap: 8px; padding: 24px; color: #cbd5e1; text-align: center; background: linear-gradient(rgba(59,130,246,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(59,130,246,0.04) 1px,transparent 1px),rgba(7,11,20,0.76); background-size: 30px 30px; }
.pose-particle-empty strong { color: #f8fafc; font-size: 18px; }
.pose-particle-empty span { max-width: 300px; color: #94a3b8; line-height: 1.6; }
</style>

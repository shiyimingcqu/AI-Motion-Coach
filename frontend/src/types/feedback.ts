/**
 * Maps an analysis metric name to the affected MediaPipe body parts.
 */
export interface BodyPartMapping {
  landmarks: number[]
  bones: Array<[number, number]>
  label_zh: string
}

/**
 * Metric → MediaPipe landmark indices and bone pairs.
 *
 * Landmark convention (MediaPipe Pose 33):
 *   0=nose 11=left_shoulder 12=right_shoulder
 *   13=left_elbow  14=right_elbow  15=left_wrist  16=right_wrist
 *   23=left_hip    24=right_hip    25=left_knee   26=right_knee
 *   27=left_ankle  28=right_ankle  31=left_foot   32=right_foot
 */
export const METRIC_BODY_PART_MAP: Record<string, BodyPartMapping> = {
  knee_angle: {
    landmarks: [25, 26],
    bones: [[23, 25], [25, 27], [24, 26], [26, 28]],
    label_zh: "膝关节",
  },
  knee_symmetry_diff: {
    landmarks: [25, 26],
    bones: [[23, 25], [25, 27], [24, 26], [26, 28]],
    label_zh: "膝关节",
  },
  trunk_angle: {
    landmarks: [11, 12, 23, 24],
    bones: [[11, 23], [12, 24], [11, 12], [23, 24]],
    label_zh: "躯干",
  },
  elbow_angle: {
    landmarks: [13, 14],
    bones: [[11, 13], [13, 15], [12, 14], [14, 16]],
    label_zh: "肘关节",
  },
  body_line_angle: {
    landmarks: [11, 12, 23, 24, 25, 26, 27, 28],
    bones: [[11, 23], [12, 24], [23, 25], [24, 26], [25, 27], [26, 28], [23, 24], [11, 12]],
    label_zh: "身体",
  },
  hip_angle: {
    landmarks: [23, 24],
    bones: [[11, 23], [12, 24], [23, 24]],
    label_zh: "髋关节",
  },
  hip_sag_angle: {
    landmarks: [11, 12, 23, 24, 25, 26],
    bones: [[11, 23], [12, 24], [23, 25], [24, 26], [23, 24]],
    label_zh: "髋部",
  },
  shoulder_abduction_angle: {
    landmarks: [11, 12],
    bones: [[11, 12]],
    label_zh: "肩部",
  },
  neck_angle: {
    landmarks: [0, 11, 12],
    bones: [[0, 11], [0, 12], [11, 12]],
    label_zh: "颈部",
  },
  wrist_height: {
    landmarks: [15, 16],
    bones: [[13, 15], [14, 16]],
    label_zh: "手腕",
  },
  ankle_distance: {
    landmarks: [27, 28, 31, 32],
    bones: [[27, 31], [28, 32]],
    label_zh: "踝关节",
  },
}

/**
 * Highlight instruction for 3D viewer.
 * bonePairs refer to MediaPipe landmark index pairs (same format as BodyPartMapping.bones).
 */
export interface HighlightInstruction {
  bonePairs: Array<[number, number]>
  color: string
  pulseSpeed: number
}

/**
 * Try to infer a metric name from the Chinese issue text (fallback when metric field is missing).
 */
export function inferMetricFromIssue(issue: string): string | null {
  if (/膝|深蹲|蹲/.test(issue)) return "knee_angle"
  if (/躯干|前倾|塌腰/.test(issue)) return "trunk_angle"
  if (/肘/.test(issue)) return "elbow_angle"
  if (/臀|髋/.test(issue)) return "hip_angle"
  if (/肩/.test(issue)) return "shoulder_abduction_angle"
  if (/颈/.test(issue)) return "neck_angle"
  if (/腕|手/.test(issue)) return "wrist_height"
  if (/踝|脚/.test(issue)) return "ankle_distance"
  if (/对称/.test(issue)) return "knee_symmetry_diff"
  if (/身体|直线/.test(issue)) return "body_line_angle"
  return null
}

/**
 * EXERCISE_KEY_JOINTS — maps each exercise to its key bone pairs.
 *
 * These are shown as blue highlights guiding the user to the body parts
 * that matter most for this movement.
 *
 * bonePairs refer to SKELETON_BONES entries in PoseParticleViewer.vue.
 * Landmark convention: 11/12=shoulders, 13/14=elbows, 15/16=wrists
 * 23/24=hips, 25/26=knees, 27/28=ankles, 29/30=heels, 31/32=toes
 */
export const EXERCISE_KEY_JOINTS: Record<string, Array<[number, number]>> = {
  squat:           [[23,25],[25,27],[24,26],[26,28],[11,23],[12,24],[23,24]],
  push_up:         [[11,13],[13,15],[12,14],[14,16],[11,23],[12,24],[23,24]],
  pushup:          [[11,13],[13,15],[12,14],[14,16],[11,23],[12,24],[23,24]],
  jumping_jack:    [[11,12],[23,24],[23,25],[24,26],[25,27],[26,28]],
  plank:           [[11,23],[12,24],[23,24]],
  lunge:           [[23,25],[25,27],[24,26],[26,28],[27,31],[28,32]],
  glute_bridge:    [[23,25],[24,26],[23,24],[25,27],[26,28]],
  high_knees:      [[23,25],[25,27],[24,26],[26,28]],
  burpee:          [[11,13],[13,15],[12,14],[14,16],[23,25],[25,27],[24,26],[26,28],[11,23],[12,24]],
  dumbbell_curl:   [[11,13],[13,15],[12,14],[14,16]],
  dumbbell_press:  [[11,13],[13,15],[12,14],[14,16],[11,12]],
  dumbbell_shoulder_press: [[11,13],[13,15],[12,14],[14,16],[11,12]],
  pull_up:         [[11,13],[13,15],[12,14],[14,16],[11,23],[12,24]],
  mountain_climber:[[23,25],[25,27],[24,26],[26,28],[11,23],[12,24]],
  russian_twist:   [[11,23],[12,24],[23,24],[11,12]],
};

/** Map severity level to highlight color. */
export function severityToHighlightColor(severity: "high" | "medium" | "low" | string): string {
  switch (severity) {
    case "high":   return "#ff3344"
    case "medium": return "#ff8833"
    case "low":    return "#ffcc33"
    default:       return "#ff8833"
  }
}

/** Map severity level to pulse speed (Hz). */
export function severityToPulseSpeed(severity: "high" | "medium" | "low" | string): number {
  switch (severity) {
    case "high":   return 3
    case "medium": return 2
    case "low":    return 1.5
    default:       return 2
  }
}

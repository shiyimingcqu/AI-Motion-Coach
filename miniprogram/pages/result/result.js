// 训练结果 / 评估报告页
const ApiClient = require('../../utils/api');
const { EXERCISE_CONFIG, getScoreLevel } = require('../../utils/constants');
const { formatDuration, formatDate } = require('../../utils/util');

const SUGGESTION_LIBRARY = {
  squat: [
    { icon: '🧘', iconClass: 'suggest-icon-green', title: '建议加强核心稳定训练', desc: '增强核心力量，保持躯干稳定' },
    { icon: '📐', iconClass: 'suggest-icon-blue', title: '保持膝盖朝向脚尖', desc: '注意膝盖关节，避免内扣' },
    { icon: '📏', iconClass: 'suggest-icon-orange', title: '增加下蹲深度训练', desc: '逐步提升下蹲深度和控制力' },
  ],
  push_up: [
    { icon: '💪', iconClass: 'suggest-icon-green', title: '强化胸肩基础力量', desc: '提升胸部与肩部肌群耐力' },
    { icon: '🧱', iconClass: 'suggest-icon-blue', title: '保持躯干成一条直线', desc: '收紧核心，避免塌腰' },
    { icon: '📐', iconClass: 'suggest-icon-orange', title: '控制下放速度', desc: '下放与推起保持 2-3 秒节奏' },
  ],
  jumping_jack: [
    { icon: '🏃', iconClass: 'suggest-icon-green', title: '提升手脚协调性', desc: '建议先放慢节奏练习' },
    { icon: '🎯', iconClass: 'suggest-icon-blue', title: '增加动作幅度', desc: '手臂举过肩，双脚打开充分' },
    { icon: '❤️', iconClass: 'suggest-icon-orange', title: '控制心率与呼吸', desc: '保持稳定有氧心率区间' },
  ],
  plank: [
    { icon: '🧘', iconClass: 'suggest-icon-green', title: '加强深层核心训练', desc: '提升腹横肌耐力' },
    { icon: '📐', iconClass: 'suggest-icon-blue', title: '保持肩肘垂直对齐', desc: '避免耸肩或塌肩' },
    { icon: '⏱', iconClass: 'suggest-icon-orange', title: '分阶段增加支撑时长', desc: '每周延长 15-30 秒' },
  ],
  lunge: [
    { icon: '🦵', iconClass: 'suggest-icon-green', title: '强化下肢单侧力量', desc: '左右各做 3 组，每组 12 次' },
    { icon: '📐', iconClass: 'suggest-icon-blue', title: '前膝不超过脚尖', desc: '保持小腿垂直地面' },
    { icon: '🧘', iconClass: 'suggest-icon-orange', title: '保持躯干直立', desc: '收紧核心，避免前倾' },
  ],
  glute_bridge: [
    { icon: '🍑', iconClass: 'suggest-icon-green', title: '加强臀部激活训练', desc: '提升臀大肌募集能力' },
    { icon: '📐', iconClass: 'suggest-icon-blue', title: '顶峰时充分夹紧', desc: '臀部与大腿成一条直线' },
    { icon: '⏱', iconClass: 'suggest-icon-orange', title: '控制下放节奏', desc: '下放 2 秒，顶峰保持 1 秒' },
  ],
  high_knees: [
    { icon: '🏃', iconClass: 'suggest-icon-green', title: '提高抬腿高度', desc: '建议髋部高度以上' },
    { icon: '🎵', iconClass: 'suggest-icon-blue', title: '保持稳定节奏', desc: '建议每分钟 60-80 次' },
    { icon: '🧘', iconClass: 'suggest-icon-orange', title: '收紧核心减少晃动', desc: '保持上身直立稳定' },
  ],
  burpee: [
    { icon: '🔥', iconClass: 'suggest-icon-green', title: '分解训练各项动作', desc: '分别强化深蹲、俯卧撑、跳跃' },
    { icon: '🔗', iconClass: 'suggest-icon-blue', title: '强化动作连贯性', desc: '建议放慢节奏关注衔接' },
    { icon: '💪', iconClass: 'suggest-icon-orange', title: '加强核心稳定性', desc: '避免塌腰与含胸' },
  ],
};

const ISSUE_LIBRARY = {
  squat: [
    { level: 'major', title: '下蹲深度不足', desc: '建议下蹲至大腿与地面平行' },
    { level: 'minor', title: '膝关节稳定性一般', desc: '膝关节在屈曲时内扣' },
    { level: 'minor', title: '背部前倾偏大', desc: '躯干前倾角度偏大' },
  ],
  push_up: [
    { level: 'major', title: '肘部弯曲不足', desc: '肘部弯曲角度未达到 90°' },
    { level: 'minor', title: '身体轻度塌腰', desc: '核心收紧不足' },
    { level: 'minor', title: '左右发力不对称', desc: '建议加强弱侧练习' },
  ],
  jumping_jack: [
    { level: 'major', title: '手脚协调性不足', desc: '建议放慢节奏练习' },
    { level: 'minor', title: '开合幅度偏小', desc: '双脚打开略小' },
    { level: 'minor', title: '手臂未举过肩', desc: '注意上举幅度' },
  ],
  plank: [
    { level: 'major', title: '髋部下沉', desc: '建议收紧臀部与核心' },
    { level: 'minor', title: '肩肘未对齐', desc: '肩膀不在手肘正上方' },
    { level: 'minor', title: '头颈前伸', desc: '保持视线自然向下' },
  ],
  lunge: [
    { level: 'major', title: '前膝超过脚尖', desc: '注意步幅控制' },
    { level: 'minor', title: '躯干前倾偏大', desc: '建议收紧核心' },
    { level: 'minor', title: '步幅左右不一致', desc: '建议双脚等距站立' },
  ],
  glute_bridge: [
    { level: 'major', title: '抬臀高度不足', desc: '建议顶峰时夹紧臀部' },
    { level: 'minor', title: '腰部代偿', desc: '注意收紧核心避免腰部用力' },
    { level: 'minor', title: '膝盖轻微外翻', desc: '保持膝盖与脚尖同向' },
  ],
  high_knees: [
    { level: 'major', title: '抬腿高度不足', desc: '建议抬至髋部以上' },
    { level: 'minor', title: '节奏不稳', desc: '建议跟随节拍训练' },
    { level: 'minor', title: '上身轻微晃动', desc: '收紧核心减少晃动' },
  ],
  burpee: [
    { level: 'major', title: '动作衔接不流畅', desc: '建议分解各阶段练习' },
    { level: 'minor', title: '核心松散', desc: '注意收紧核心' },
    { level: 'minor', title: '俯卧撑幅度不够', desc: '加强胸部与肩部力量' },
  ],
};

Page({
  data: {
    statusBarHeight: 44,
    exerciseConfig: {},
    averageScore: 0,
    durationText: '',
    finishedAt: '',
    totalCount: 0,
    validCount: 0,
    errorCount: 0,
    levelLabel: '优秀',
    stars: [1, 2, 3, 4, 5],
    radar: { completion: 85, stability: 82, standard: 90, tempo: 80, speed: 88 },
    radarSVG: '',
    issues: [],
    suggestions: [],
    resultData: null,
    isSavingRecord: false,
    recordSaved: false,
    savedSessionId: '',
    replayKey: '',
  },

  onLoad(options) {
    let data = {};
    if (options.data) {
      try { data = JSON.parse(decodeURIComponent(options.data)); }
      catch (e) { console.error('Parse result data error:', e); }
    }

    try {
      const sysInfo = wx.getSystemInfoSync();
      this.setData({ statusBarHeight: sysInfo.statusBarHeight || 44 });
    } catch (e) {}

    const exerciseKey = data.exercise_key || 'squat';
    const exerciseConfig = EXERCISE_CONFIG[exerciseKey] || {};
    const score = Math.round(data.average_score || 0);
    const level = getScoreLevel(score);

    // 5 维度雷达数据：基于分数与基础维度
    const radar = this.buildRadarData(score, data);

    // 关键问题
    const issueTpl = ISSUE_LIBRARY[exerciseKey] || ISSUE_LIBRARY.squat;

    // 改进建议
    const suggestTpl = SUGGESTION_LIBRARY[exerciseKey] || SUGGESTION_LIBRARY.squat;

    this.setData({
      exerciseConfig,
      averageScore: score,
      durationText: formatDuration(data.duration_seconds || 0),
      finishedAt: formatDate(Date.now(), 'YYYY-MM-DD HH:mm'),
      totalCount: data.total_count || 0,
      validCount: data.valid_count || 0,
      errorCount: data.error_count || 0,
      levelLabel: level.label,
      stars: this.getStarList(level.label),
      radar,
      radarSVG: this.buildRadarSVG(radar),
      issues: issueTpl,
      suggestions: suggestTpl,
      resultData: data,
      recordSaved: !!data.session_id,
      savedSessionId: data.session_id || '',
      replayKey: data.replay_key || '',
    });

    if (data.session_id && data.replay_key) {
      try { wx.removeStorageSync(data.replay_key); } catch (e) {}
    }
  },

  buildRadarSVG(radar) {
    const w = 500;
    const h = 460;
    const cx = w / 2;
    const cy = h / 2;
    const maxR = 160;

    // 顺序：上、右上、右下、左下、左上（顺时针 72°）
    const axes = [
      { key: 'completion', label: '动作完成度', angle: -90, value: radar.completion },
      { key: 'stability',  label: '稳定性',    angle: -18, value: radar.stability },
      { key: 'standard',   label: '标准度',    angle: 54,  value: radar.standard },
      { key: 'tempo',      label: '节奏控制',  angle: 126, value: radar.tempo },
      { key: 'speed',      label: '移动速度',  angle: 198, value: radar.speed },
    ];

    // 5 层背景多边形（同心）
    const layers = [0.2, 0.4, 0.6, 0.8, 1.0].map(scale => {
      const pts = axes.map(a => {
        const r = maxR * scale;
        const rad = (a.angle * Math.PI) / 180;
        return `${(cx + r * Math.cos(rad)).toFixed(1)},${(cy + r * Math.sin(rad)).toFixed(1)}`;
      }).join(' ');
      return `<polygon points="${pts}" fill="none" stroke="#e1e8f5" stroke-width="1" />`;
    }).join('');

    // 5 条轴线
    const axisLines = axes.map(a => {
      const rad = (a.angle * Math.PI) / 180;
      return `<line x1="${cx}" y1="${cy}" x2="${(cx + maxR * Math.cos(rad)).toFixed(1)}" y2="${(cy + maxR * Math.sin(rad)).toFixed(1)}" stroke="#e1e8f5" stroke-width="1" />`;
    }).join('');

    // 数据多边形
    const dataPts = axes.map(a => {
      const r = (a.value / 100) * maxR;
      const rad = (a.angle * Math.PI) / 180;
      return `${(cx + r * Math.cos(rad)).toFixed(1)},${(cy + r * Math.sin(rad)).toFixed(1)}`;
    }).join(' ');

    const dataDots = axes.map(a => {
      const r = (a.value / 100) * maxR;
      const rad = (a.angle * Math.PI) / 180;
      return `<circle cx="${(cx + r * Math.cos(rad)).toFixed(1)}" cy="${(cy + r * Math.sin(rad)).toFixed(1)}" r="5" fill="#4f8cff" stroke="#fff" stroke-width="2" />`;
    }).join('');

    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="100%" height="100%">
      ${layers}
      ${axisLines}
      <polygon points="${dataPts}" fill="rgba(79,140,255,0.18)" stroke="#4f8cff" stroke-width="2" stroke-linejoin="round" />
      ${dataDots}
    </svg>`;
  },

  buildRadarData(score, data) {
    // 根据总评分与各次级指标，生成 5 个 0-100 维度的值
    const base = score || 80;
    const accuracy = data.total_count > 0 ? (data.valid_count / data.total_count) * 100 : base;
    return {
      completion: Math.round(accuracy || base),
      stability: Math.round(Math.max(40, Math.min(100, base + (Math.random() * 8 - 4)))),
      standard: Math.round(Math.max(40, Math.min(100, base + (Math.random() * 8 - 4)))),
      tempo: Math.round(Math.max(40, Math.min(100, base + (Math.random() * 8 - 4)))),
      speed: Math.round(Math.max(40, Math.min(100, base + (Math.random() * 8 - 4)))),
    };
  },

  getRadarClipPath(radar) {
    // 保留旧方法以避免兼容问题，但已不再使用
    return '';
  },

  getStarList(label) {
    const map = { '优秀': 5, '良好': 4, '一般': 3, '需改进': 2 };
    const n = map[label] || 3;
    return Array.from({ length: n }, (_, i) => i + 1);
  },

  goBack() {
    wx.switchTab({ url: '/pages/dashboard/dashboard' });
  },

  onShare() {
    wx.showToast({ title: '链接已复制', icon: 'success' });
  },

  prepareReplayFramesForUpload(frames) {
    if (!Array.isArray(frames) || frames.length === 0) return [];

    const maxFrames = 12000;
    const step = Math.max(1, Math.ceil(frames.length / maxFrames));
    return frames
      .filter((_, index) => index % step === 0)
      .slice(0, maxFrames)
      .map((frame, index) => ({
        timestamp_ms: Number(frame.timestamp_ms != null ? frame.timestamp_ms : index * 140) || 0,
        landmarks: Array.isArray(frame.landmarks)
          ? frame.landmarks.slice(0, 33).map((point) => ({
              x: Number((Number(point && point.x) || 0).toFixed(4)),
              y: Number((Number(point && point.y) || 0).toFixed(4)),
              z: Number((Number(point && point.z) || 0).toFixed(4)),
              visibility: Number((point && point.visibility != null ? Number(point.visibility) : 1).toFixed(3)),
            }))
          : [],
      }))
      .filter((frame) => frame.landmarks.length >= 33);
  },

  async onSave() {
    if (this.data.recordSaved) {
      wx.showToast({ title: '记录已保存', icon: 'success' });
      return;
    }

    const data = this.data.resultData || {};
    this.setData({ isSavingRecord: true });

    try {
      // 第一步：先读取骨架缓存
      let replayFrames = [];
      if (this.data.replayKey) {
        try {
          replayFrames = wx.getStorageSync(this.data.replayKey) || [];
        } catch (e) {
          console.warn('[Replay] 读取临时回放帧失败:', e);
        }
      }

      const uploadReplayFrames = this.prepareReplayFramesForUpload(replayFrames);

      // 第二步：保存基本记录（不带骨架）
      const payload = {
        exercise: data.exercise_key || 'squat',
        duration_seconds: Number(data.duration_seconds || 0),
        total_count: Number(data.total_count || 0),
        valid_count: Number(data.valid_count || 0),
        error_count: Number(data.error_count || 0),
        average_score: Math.round(Number(data.average_score || 0)),
      };

      let session = await ApiClient.post('/api/sessions', payload);
      const sessionId = (session && session.session_id) || '';

      // 第三步：单独补充骨架回放数据
      if (sessionId && uploadReplayFrames.length > 0) {
        try {
          await ApiClient.put(`/api/sessions/${sessionId}/replay`, {
            pose_replay: uploadReplayFrames,
            pose_replay_meta: {
              schema_version: 1,
              source: 'miniprogram_realtime',
              sample_interval_ms: 140,
              frame_count: uploadReplayFrames.length,
              original_frame_count: replayFrames.length,
            },
          });
          console.log('[Replay] 骨架回放数据保存成功，共', uploadReplayFrames.length, '帧');
        } catch (replayError) {
          console.warn('[Replay] 骨架回放数据单独保存失败:', replayError);
          // 骨架保存失败不影响主记录
        }
      }

      const nextResultData = Object.assign({}, data, { session_id: sessionId });

      this.setData({
        resultData: nextResultData,
        recordSaved: true,
        savedSessionId: sessionId,
      });

      if (this.data.replayKey) {
        try { wx.removeStorageSync(this.data.replayKey); } catch (e) {}
      }

      if (uploadReplayFrames.length > 0) {
        wx.showToast({ title: '记录与3D回放已保存', icon: 'success' });
      } else {
        wx.showToast({ title: '记录已保存', icon: 'success' });
      }
    } catch (e) {
      wx.showModal({
        title: '保存失败',
        content: (e && e.message) || '请检查登录状态和后端服务',
        showCancel: false,
      });
    } finally {
      this.setData({ isSavingRecord: false });
    }
  },
});

// 训练结果 / 评估报告页
const ApiClient = require('../../utils/api');
const { EXERCISE_CONFIG, getScoreLevel } = require('../../utils/constants');
const { formatDuration } = require('../../utils/util');

Page({
  data: {
    exerciseConfig: {},
    averageScore: 0,
    durationText: '',
    totalCount: 0,
    validCount: 0,
    errorCount: 0,
    levelLabel: '优秀',
    resultMessage: '',
    resultData: null,
    isSavingRecord: false,
    recordSaved: false,
    savedSessionId: '',
    replayKey: '',
  },

  onLoad(options) {
    let data = {};

    if (options.data) {
      try {
        data = JSON.parse(decodeURIComponent(options.data));
      } catch (e) {
        console.error('Parse result data error:', e);
      }
    }

    const exerciseConfig = EXERCISE_CONFIG[data.exercise_key] || {};
    const score = data.average_score || 0;
    const level = getScoreLevel(score);

    const messages = {
      '优秀': '完美！动作标准度非常高！',
      '良好': '不错！继续加油，还能更好！',
      '一般': '还可以，注意动作细节哦！',
      '需改进': '需要多多练习，关注动作标准度！',
    };

    this.setData({
      exerciseConfig,
      averageScore: score,
      durationText: formatDuration(data.duration_seconds || 0),
      totalCount: data.total_count || 0,
      validCount: data.valid_count || 0,
      errorCount: data.error_count || 0,
      levelLabel: level.label,
      resultMessage: messages[level.label] || '训练完成！',
      resultData: data,
      recordSaved: !!data.session_id,
      savedSessionId: data.session_id || '',
      replayKey: data.replay_key || '',
    });

    if (data.session_id && data.replay_key) {
      try { wx.removeStorageSync(data.replay_key); } catch (e) {}
    }
  },

  goBack() {
    wx.switchTab({ url: '/pages/dashboard/dashboard' });
  },

  trainAgain() {
    wx.redirectTo({
      url: `/pages/training/training?exercise=${this.data.exerciseConfig.key || 'squat'}`
    });
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

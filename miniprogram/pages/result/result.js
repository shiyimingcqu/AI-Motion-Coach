// 训练结果页
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
    resultMessage: '',
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
      resultMessage: messages[level.label] || '训练完成！',
    });
  },

  goBack() {
    wx.switchTab({ url: '/pages/dashboard/dashboard' });
  },

  trainAgain() {
    wx.redirectTo({
      url: `/pages/training/training?exercise=${this.data.exerciseConfig.key || 'squat'}`
    });
  }
});

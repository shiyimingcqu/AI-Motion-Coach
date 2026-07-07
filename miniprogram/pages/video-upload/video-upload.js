const ApiClient = require('../../utils/api');
const AuthManager = require('../../utils/auth');
const { EXERCISE_CONFIG } = require('../../utils/constants');
const { showToast } = require('../../utils/util');

function normalizeTextList(raw) {
  if (!Array.isArray(raw)) return [];
  return raw.map((item) => {
    if (typeof item === 'string') return item.trim();
    if (!item || typeof item !== 'object') return '';
    return String(item.title || item.message || item.desc || item.text || '').trim();
  }).filter(Boolean);
}

function extractPoseFrameCount(frames) {
  if (!Array.isArray(frames)) return 0;
  return frames.filter((item) => {
    if (item.keypoints && typeof item.keypoints === 'object' && !Array.isArray(item.keypoints)) {
      return Object.keys(item.keypoints).length > 0;
    }
    if (Array.isArray(item.keypoints)) {
      return item.keypoints.some((kp) => kp && kp.visibility > 0.3);
    }
    return false;
  }).length;
}

function buildResultFromAnalysis(data, selectedExercise, config, videoDuration) {
  const summary = data.summary || {};
  const sessionId = data.session_id || '';
  const processedFrames = data.processed_frames || 0;
  const frames = Array.isArray(data.frames) ? data.frames : [];
  const poseFrames = extractPoseFrameCount(frames);
  const unified = data.unified_feedback || {};
  const unifiedItems = Array.isArray(unified.items) ? unified.items : [];
  const templateScore = data.template_score || {};

  let issues = normalizeTextList(
    data.issues || unified.errors || unifiedItems.map((item) => item.issue)
  );
  let suggestions = normalizeTextList(
    data.suggestions || unified.feedbacks || templateScore.suggestions || unifiedItems.map((item) => item.suggestion)
  );

  if (!issues.length && Array.isArray(templateScore.errors)) {
    issues = normalizeTextList(templateScore.errors);
  }

  let averageScore = summary.average_score || unified.score || 0;
  if (!averageScore && templateScore.score) {
    averageScore = templateScore.score;
  }
  if (!averageScore && frames.length > 0) {
    const scores = frames
      .map((frame) => Number(frame.score))
      .filter((score) => Number.isFinite(score) && score > 0);
    if (scores.length > 0) {
      averageScore = Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length);
    }
  }

  const totalCount = summary.total_count || unified.total_reps || 0;
  const validCount = summary.valid_count || unified.valid_reps || 0;
  const errorCount = summary.error_count != null
    ? summary.error_count
    : Math.max(0, totalCount - validCount);

  if (!sessionId && !totalCount && processedFrames === 0 && poseFrames === 0) {
    throw new Error('视频中未检测到人体，请换一段人物完整入镜的视频');
  }

  if (totalCount === 0 && issues.length === 0 && (processedFrames > 0 || poseFrames > 0)) {
    issues = ['未识别到完整动作循环，但已检测到人体姿态'];
    suggestions = [
      '请确认所选动作类型与视频内容一致',
      '建议使用全身入镜、光线充足的侧面或斜前方视频',
      '视频中至少包含一次完整动作（如下蹲到底再站起）',
    ];
  }

  const result = {
    exercise_key: selectedExercise,
    exercise_name: config.name,
    duration_seconds: summary.duration_seconds || videoDuration || 0,
    total_count: totalCount,
    valid_count: validCount,
    error_count: errorCount,
    average_score: averageScore,
    session_id: sessionId,
    issues,
    suggestions,
    source: 'video_upload',
    processed_frames: processedFrames,
  };

  if (unifiedItems.length > 0) {
    result.feedback_summary = JSON.stringify({ items: unifiedItems });
  } else if (issues.length > 0 || suggestions.length > 0) {
    result.feedback_summary = JSON.stringify({ issues, suggestions });
  }

  return result;
}

function calcMaxFrames(videoDuration) {
  const duration = Number(videoDuration) || 30;
  return String(Math.min(600, Math.max(180, Math.round(duration * 8))));
}

Page({
  data: {
    exerciseOptions: [],
    exerciseIndex: 0,
    selectedExercise: 'squat',
    exerciseName: '深蹲',
    videoPath: '',
    videoName: '',
    videoDuration: 0,
    analyzing: false,
    statusText: '选择动作并上传训练视频，服务端分析完成后直接进入评估报告',
  },

  onLoad(options) {
    const exerciseOptions = Object.values(EXERCISE_CONFIG).map((item) => ({
      key: item.key,
      name: item.name,
    }));

    let exerciseIndex = 0;
    if (options.exercise) {
      const found = exerciseOptions.findIndex((item) => item.key === options.exercise);
      if (found >= 0) exerciseIndex = found;
    }

    const selected = exerciseOptions[exerciseIndex] || exerciseOptions[0];
    this.setData({
      exerciseOptions,
      exerciseIndex,
      selectedExercise: selected.key,
      exerciseName: selected.name,
    });
  },

  onShow() {
    if (!AuthManager.isLoggedIn()) {
      wx.showModal({
        title: '需要登录',
        content: '上传视频分析需要先登录账号',
        confirmText: '去登录',
        cancelText: '返回',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/login/login' });
          } else {
            wx.navigateBack({ fail: () => wx.switchTab({ url: '/pages/dashboard/dashboard' }) });
          }
        },
      });
    }
  },

  onExerciseChange(e) {
    const exerciseIndex = Number(e.detail.value) || 0;
    const selected = this.data.exerciseOptions[exerciseIndex];
    if (!selected) return;
    this.setData({
      exerciseIndex,
      selectedExercise: selected.key,
      exerciseName: selected.name,
    });
  },

  chooseVideo() {
    if (this.data.analyzing) return;

    wx.chooseVideo({
      sourceType: ['album', 'camera'],
      maxDuration: 60,
      compressed: false,
      success: (res) => {
        const name = (res.tempFilePath || '').split('/').pop() || '已选视频';
        this.setData({
          videoPath: res.tempFilePath,
          videoName: name,
          videoDuration: Math.round(res.duration || 0),
          statusText: '视频已选择，点击开始分析',
        });
      },
      fail: (err) => {
        if (err && err.errMsg && err.errMsg.includes('cancel')) return;
        showToast('选择视频失败');
      },
    });
  },

  clearVideo() {
    if (this.data.analyzing) return;
    this.setData({
      videoPath: '',
      videoName: '',
      videoDuration: 0,
      statusText: '选择动作并上传训练视频，系统将在服务端完成姿态分析',
    });
  },

  startAnalysis() {
    if (this.data.analyzing) return;

    if (!AuthManager.isLoggedIn()) {
      wx.showModal({
        title: '需要登录',
        content: '请先登录后再上传视频分析',
        confirmText: '去登录',
        success: (res) => {
          if (res.confirm) wx.navigateTo({ url: '/pages/login/login' });
        },
      });
      return;
    }

    const { videoPath, selectedExercise, videoDuration } = this.data;
    if (!videoPath) {
      showToast('请先选择视频');
      return;
    }

    const config = EXERCISE_CONFIG[selectedExercise];
    if (!config) {
      showToast('动作类型无效');
      return;
    }

    this.setData({
      analyzing: true,
      statusText: '正在上传并分析，请稍候（约 30–90 秒）…',
    });
    wx.showLoading({ title: '分析中...', mask: true });

    // 走 video-test：只做姿态分析并保存 session，跳过标注视频生成，更快更稳
    ApiClient.upload('/api/realtime/video-test', videoPath, {
      exercise: selectedExercise,
      max_frames: calcMaxFrames(videoDuration),
      persist_session: 'true',
    }).then((res) => {
      wx.hideLoading();
      const resultData = buildResultFromAnalysis(
        res || {},
        selectedExercise,
        config,
        videoDuration
      );

      const resultKey = `training_result_${Date.now()}`;
      try {
        wx.setStorageSync(resultKey, resultData);
      } catch (e) {
        console.warn('[VideoUpload] 缓存结果失败:', e);
      }

      this.setData({ analyzing: false });
      wx.redirectTo({
        url: `/pages/result/result?key=${encodeURIComponent(resultKey)}`,
        fail: () => {
          showToast('跳转结果页失败');
        },
      });
    }).catch((err) => {
      wx.hideLoading();
      let message = String((err && err.message) || err || '分析失败');
      if (message.includes('fail') && message.includes('timeout')) {
        message = '分析超时，请换一段更短的视频或稍后重试';
      } else if (message.includes('request:fail')) {
        message = '无法连接后端，请确认后端已启动且开发者工具已关闭域名校验';
      }
      this.setData({
        analyzing: false,
        statusText: message,
      });
      wx.showModal({
        title: '分析失败',
        content: message,
        showCancel: false,
      });
    });
  },
});

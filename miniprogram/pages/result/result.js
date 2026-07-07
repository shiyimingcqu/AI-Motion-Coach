// 训练结果 / 评估报告页
const ApiClient = require('../../utils/api');
const { EXERCISE_CONFIG, getScoreLevel } = require('../../utils/constants');
const { formatDuration, formatDate } = require('../../utils/util');

const AI_ADVICE_POLL_INTERVAL_MS = 2000;
const AI_ADVICE_POLL_TIMEOUT_MS = 90000;

const SEVERITY_TONE = {
  high: 'critical',
  error: 'critical',
  medium: 'warning',
  warning: 'warning',
  low: 'minor',
  info: 'positive',
};

const POSITIVE_LABEL = '不错';
const POSITIVE_SUGGESTION = '继续保持当前节奏，稳定发挥这一优势';

const ISSUE_ASPECT_MAP = {
  '下蹲深度不稳定': 'depth',
  '下蹲深度整体偏浅': 'depth',
  '下蹲深度整体偏深': 'depth',
  '部分动作深度偏浅': 'depth',
  '部分动作深度偏深': 'depth',
  '底部躯干前倾明显': 'trunk',
  '底部躯干前倾偏大': 'trunk',
  '左右膝关节明显不对称': 'symmetry',
  '左右膝关节略不对称': 'symmetry',
  '下蹲速度偏快': 'tempo',
  '整体节奏略快': 'tempo',
  '下降深度不稳定': 'depth',
  '下降幅度整体偏浅': 'depth',
  '下降幅度不足': 'depth',
  '身体直线控制不足': 'body_line',
  '左右发力明显不均': 'symmetry',
};

const EXERCISE_ASPECTS = {
  squat: {
    depth: '下蹲深度整体可控，完成度不错',
    trunk: '躯干稳定性良好，背部控制到位',
    symmetry: '左右膝盖对称性较好',
    tempo: '下蹲节奏比较均匀',
  },
  push_up: {
    depth: '下降深度控制较稳定，能完成完整动作循环',
    body_line: '身体直线保持较好，核心有参与',
    symmetry: '左右发力较为均衡',
    tempo: '动作节奏整体平稳',
  },
  jumping_jack: {
    spread: '开合步幅基本到位',
    arms: '手臂上举动作较完整',
    sync: '手脚配合有一定协调性',
    symmetry: '左右动作对称性尚可',
  },
  plank: {
    body_line: '身体直线维持能力不错',
    core: '核心参与感较好',
    stability: '支撑稳定性在可控范围内',
  },
};

function briefText(text, maxLen = 28) {
  if (!text) return '';
  const normalized = String(text).replace(/\s+/g, ' ').trim();
  const firstPart = normalized.split(/[。；;！!？?\n]/)[0].trim();
  const candidate = firstPart || normalized;
  if (candidate.length <= maxLen) return candidate;
  return `${candidate.slice(0, maxLen)}…`;
}

function pickAverageScore(...candidates) {
  const values = candidates
    .map((item) => Math.round(Number(item)))
    .filter((item) => Number.isFinite(item));
  const positive = values.find((item) => item > 0);
  if (positive != null) return positive;
  return values.length ? values[0] : 0;
}

Page({
  data: {
    statusBarHeight: 44,
    exerciseConfig: {},
    exerciseName: '',
    averageScore: 0,
    durationText: '',
    finishedAt: '',
    totalCount: 0,
    validCount: 0,
    errorCount: 0,
    validRate: 0,
    levelLabel: '优秀',
    gradeLabel: '',
    evaluationSummary: '',
    stars: [1, 2, 3, 4, 5],
    scorePercent: 0,
    scoreColor: '#3b82f6',
    radar: { completion: 85, stability: 82, standard: 90, tempo: 80, speed: 88 },
    radarSVG: '',
    dimensionList: [],
    issues: [],
    suggestions: [],
    feedbackItems: [],
    displayFeedbackItems: [],
    feedbackStats: { critical: 0, warning: 0, minor: 0, positive: 0 },
    hasRealFeedback: false,
    strengths: [],
    weaknesses: [],
    recommendations: [],
    nextSteps: [],
    showDimensionDetail: false,
    dimensionPreview: [],
    aiAdvice: '',
    aiAdvicePreview: '',
    showAiAdvice: true,
    aiAdvicePending: false,
    aiAdviceFailed: false,
    reportLoading: false,
    feedbackLoading: false,
    feedbackReady: false,
    hasBackendReport: false,
    resultData: null,
    recordSaved: false,
    savedSessionId: '',
    replayKey: '',
    showSharePreview: false,
    sharePosterUrl: '',
    sharePosterLoading: false,
  },

  onLoad(options) {
    let data = {};
    if (options.key) {
      try {
        data = wx.getStorageSync(options.key) || {};
        wx.removeStorageSync(options.key);
      } catch (e) {
        console.error('Read result cache error:', e);
      }
    } else if (options.data) {
      try { data = JSON.parse(decodeURIComponent(options.data)); }
      catch (e) { console.error('Parse result data error:', e); }
    }

    try {
      const sysInfo = wx.getSystemInfoSync();
      this.setData({ statusBarHeight: sysInfo.statusBarHeight || 44 });
    } catch (e) {}

    this._aiAdvicePollTimer = null;
    this._aiAdvicePollStartedAt = 0;
    this._bootstrapStarted = false;
    this._aiAdviceDirectStarted = false;
    this.applyLocalResult(data);
    this.bootstrapReport(data);
  },

  onReady() {
    this.scheduleSharePoster();
  },

  onUnload() {
    this.clearAiAdvicePoll();
  },

  applyLocalResult(data) {
    const exerciseKey = data.exercise_key || 'squat';
    const exerciseConfig = EXERCISE_CONFIG[exerciseKey] || {};
    const exerciseName = exerciseConfig.name || '';
    const score = Math.round(data.average_score || 0);
    const level = getScoreLevel(score);
    const scoreVisual = this.buildScoreVisual(score);
    const totalCount = data.total_count || 0;
    const validCount = data.valid_count || 0;
    const validRate = totalCount > 0 ? Math.round((validCount / totalCount) * 100) : 0;

    const realIssues = data.issues || [];
    const realSuggestions = data.suggestions || [];

    const radar = this.buildRadarData(score, data);

    const dimensionList = this.buildDimensionListFromRadar(radar);
    const prefetchApiItems = data.feedback_summary
      ? this.feedbackSummaryToApiItems(this.parseFeedbackSummary(data.feedback_summary), exerciseKey)
      : [];
    const prefetchDisplayItems = prefetchApiItems.length
      ? this.buildDisplayFeedbackItems(prefetchApiItems, {
        exerciseKey,
        exerciseName,
        time: '--:--',
      })
      : [];

    this.setData({
      exerciseConfig,
      exerciseName: exerciseConfig.name || '',
      averageScore: score,
      durationText: formatDuration(data.duration_seconds || 0),
      finishedAt: formatDate(Date.now(), 'YYYY-MM-DD HH:mm'),
      totalCount,
      validCount,
      errorCount: data.error_count || 0,
      validRate,
      levelLabel: level.label,
      gradeLabel: level.label,
      scorePercent: scoreVisual.scorePercent,
      scoreColor: scoreVisual.scoreColor,
      stars: this.getStarList(level.label),
      radar,
      radarSVG: this.buildRadarSVG(radar),
      dimensionList,
      dimensionPreview: this.buildDimensionPreview(dimensionList),
      resultData: Object.assign({}, data, {
        issues: realIssues,
        suggestions: realSuggestions,
      }),
      savedSessionId: data.session_id || '',
      replayKey: data.replay_key || '',
      displayFeedbackItems: prefetchDisplayItems,
      feedbackStats: this.buildFeedbackStats(prefetchDisplayItems),
      hasRealFeedback: prefetchDisplayItems.length > 0,
      issues: [],
      suggestions: realSuggestions,
      nextSteps: this.buildNextSteps([], [], prefetchDisplayItems),
      hasBackendReport: prefetchDisplayItems.length > 0,
      feedbackReady: prefetchDisplayItems.length > 0,
      feedbackLoading: Boolean(data.session_id) && prefetchDisplayItems.length === 0,
      reportLoading: Boolean(data.session_id),
      aiAdvice: '',
      aiAdvicePreview: '',
      showAiAdvice: true,
      aiAdvicePending: false,
      aiAdviceFailed: false,
      strengths: [],
      weaknesses: [],
      recommendations: [],
      evaluationSummary: '',
      showDimensionDetail: false,
    });

    if (data.feedback_summary && data.session_id) {
      this.loadAiAdviceFromSession({
        session_id: data.session_id,
        feedback_summary: data.feedback_summary,
      });
    }

    if (data.session_id) {
      this.refreshSessionFeedback(data.session_id, null, exerciseKey);
    }
  },

  feedbackSummaryToApiItems(summary, exerciseKey) {
    if (!summary || typeof summary !== 'object') return [];

    const structured = summary.items || [];
    if (structured.length > 0) {
      return structured.map((entry, index) => ({
        id: `summary-${index}`,
        exercise: exerciseKey,
        issue: entry.issue || '',
        suggestion: entry.suggestion || '',
        severity: entry.severity || 'warning',
      }));
    }

    const issues = summary.issues || [];
    const suggestions = summary.suggestions || [];
    if (!issues.length) return [];

    return issues.map((issue, index) => ({
      id: `summary-${index}`,
      exercise: exerciseKey,
      issue: typeof issue === 'string' ? issue : (issue.issue || issue.title || ''),
      suggestion: suggestions[index] || '',
      severity: index === 0 ? 'high' : index === 1 ? 'medium' : 'low',
    }));
  },

  getLocalFeedbackApiItems(exerciseKey, sessionRes) {
    const summaryRaw = (sessionRes && sessionRes.feedback_summary)
      || (this.data.resultData && this.data.resultData.feedback_summary);
    if (!summaryRaw) return [];
    return this.feedbackSummaryToApiItems(this.parseFeedbackSummary(summaryRaw), exerciseKey);
  },

  applyFeedbackFromApiItems(apiItems, options, preserveIfEmpty) {
    const built = this.buildDisplayFeedbackItems(apiItems || [], options);
    const shouldPreserve = preserveIfEmpty !== false;
    const displayFeedbackItems = built.length > 0
      ? built
      : (shouldPreserve ? (this.data.displayFeedbackItems || []) : []);

    this.setData({
      displayFeedbackItems,
      feedbackStats: this.buildFeedbackStats(displayFeedbackItems),
      hasRealFeedback: displayFeedbackItems.length > 0,
      nextSteps: this.buildNextSteps([], [], displayFeedbackItems),
      feedbackReady: true,
      issues: [],
      suggestions: [],
    });
  },

  async refreshSessionFeedback(sessionId, sessionRes, exerciseKeyHint) {
    if (!sessionId) return;

    const exerciseKey = exerciseKeyHint
      || (sessionRes && sessionRes.exercise)
      || (this.data.resultData && this.data.resultData.exercise_key)
      || 'squat';
    const exerciseName = (EXERCISE_CONFIG[exerciseKey] && EXERCISE_CONFIG[exerciseKey].name) || exerciseKey;
    const feedbackTime = sessionRes && sessionRes.created_at
      ? String(sessionRes.created_at).slice(11, 19)
      : '--:--';

    this.setData({ feedbackLoading: true });

    let apiItems = [];
    try {
      const feedbackRes = await ApiClient.get('/api/feedback', {
        session_id: sessionId,
        limit: 50,
      });
      apiItems = (feedbackRes && feedbackRes.items) || [];
    } catch (e) {
      console.warn('[Result] 加载 /api/feedback 失败:', e);
    }

    if (!apiItems.length) {
      apiItems = this.getLocalFeedbackApiItems(exerciseKey, sessionRes);
    }

    this.applyFeedbackFromApiItems(apiItems, {
      exerciseKey,
      exerciseName,
      time: feedbackTime,
    });
    this.setData({
      feedbackLoading: false,
      feedbackReady: true,
      hasBackendReport: true,
    });
  },

  async bootstrapReport(data) {
    if (this._bootstrapStarted) return;
    this._bootstrapStarted = true;

    const hasPrefetch = this.data.displayFeedbackItems && this.data.displayFeedbackItems.length > 0;
    if (!hasPrefetch) {
      this.setData({ reportLoading: true });
    }

    try {
      const resultData = Object.assign({}, data, this.data.resultData || {});
      let sessionId = resultData.session_id || this.data.savedSessionId || '';

      if (!sessionId) {
        sessionId = await this.createSessionFromResult(resultData);
        if (sessionId) {
          resultData.session_id = sessionId;
          this.setData({
            resultData,
            savedSessionId: sessionId,
            recordSaved: true,
          });
        }
      }

      const replayKey = resultData.replay_key || this.data.replayKey;
      if (sessionId && replayKey) {
        await this.uploadReplaySilently(sessionId, replayKey);
      }

      if (sessionId) {
        await this.loadBackendReport(sessionId);
      } else {
        this.applyLocalFallbackReport('未获取到训练记录，将使用本次训练本地数据。');
      }
    } catch (e) {
      console.warn('[Result] 自动同步报告失败:', e);
      this.applyLocalFallbackReport();
    } finally {
      this.setData({ reportLoading: false });
    }
  },

  async createSessionFromResult(data) {
    const session = await ApiClient.post('/api/sessions', {
      exercise: data.exercise_key || 'squat',
      duration_seconds: Number(data.duration_seconds || 0),
      total_count: Number(data.total_count || 0),
      valid_count: Number(data.valid_count || 0),
      error_count: Number(data.error_count || 0),
      average_score: Math.round(Number(data.average_score || 0)),
      issues: data.issues || [],
      suggestions: data.suggestions || [],
    });
    return (session && session.session_id) || '';
  },

  async uploadReplaySilently(sessionId, replayKey) {
    let replayFrames = [];
    try {
      replayFrames = wx.getStorageSync(replayKey) || [];
    } catch (e) {
      return;
    }

    const uploadReplayFrames = this.prepareReplayFramesForUpload(replayFrames);
    if (!uploadReplayFrames.length) return;

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
      try { wx.removeStorageSync(replayKey); } catch (e) {}
      this.setData({ replayKey: '' });
    } catch (e) {
      console.warn('[Replay] 自动上传回放失败:', e);
    }
  },

  async loadBackendReport(sessionId) {
    if (!sessionId) return;

    this.setData({
      reportLoading: true,
      feedbackLoading: !(this.data.displayFeedbackItems && this.data.displayFeedbackItems.length),
      savedSessionId: sessionId,
    });

    try {
      const [sessionRes, reportRes] = await Promise.all([
        ApiClient.get(`/api/sessions/${sessionId}`).catch(() => null),
        ApiClient.get(`/api/reports/${sessionId}`).catch(() => null),
      ]);

      await this.refreshSessionFeedback(sessionId, sessionRes);
      this.applySessionStats(reportRes, sessionRes);

      this.setData({ hasBackendReport: true });

      if (sessionRes) {
        this.loadAiAdviceFromSession(sessionRes);
      } else if (!this.data.aiAdvice) {
        this.fetchAiAdviceDirectly();
      }
      this.scheduleSharePoster();
    } catch (e) {
      console.warn('[Result] 加载后端报告失败:', e);
      if (!this.data.displayFeedbackItems || this.data.displayFeedbackItems.length === 0) {
        this.setData({ feedbackReady: true });
      }
    } finally {
      this.setData({
        reportLoading: false,
        feedbackLoading: false,
      });
    }
  },

  applySessionStats(reportRes, sessionRes) {
    const updates = {};
    const exerciseKey = (sessionRes && sessionRes.exercise)
      || (reportRes && reportRes.exercise)
      || (this.data.resultData && this.data.resultData.exercise_key)
      || 'squat';
    const exerciseName = (EXERCISE_CONFIG[exerciseKey] && EXERCISE_CONFIG[exerciseKey].name) || exerciseKey;
    updates.exerciseName = exerciseName;

    if (reportRes) {
      const evaluation = reportRes.evaluation || {};
      const score = pickAverageScore(
        reportRes.average_score,
        sessionRes && sessionRes.average_score,
        this.data.averageScore,
        this.data.resultData && this.data.resultData.average_score,
      );
      const level = getScoreLevel(score);

      updates.averageScore = score;
      updates.totalCount = reportRes.total_count != null ? reportRes.total_count : this.data.totalCount;
      updates.validCount = reportRes.valid_count != null ? reportRes.valid_count : this.data.validCount;
      updates.errorCount = reportRes.error_count != null ? reportRes.error_count : this.data.errorCount;
      updates.validRate = evaluation.valid_rate != null
        ? Math.round(evaluation.valid_rate)
        : (updates.totalCount > 0 ? Math.round((updates.validCount / updates.totalCount) * 100) : 0);
      updates.levelLabel = level.label;
      updates.gradeLabel = evaluation.grade_label || level.label;
      const scoreVisual = this.buildScoreVisual(score);
      updates.scorePercent = scoreVisual.scorePercent;
      updates.scoreColor = scoreVisual.scoreColor;
      updates.stars = this.getStarList(updates.gradeLabel || level.label);
      updates.evaluationSummary = evaluation.summary || '';

      const dimensionScores = evaluation.dimension_scores || {};
      const dimensionList = Object.keys(dimensionScores).map((label) => ({
        label,
        value: Math.round(Number(dimensionScores[label]) || 0),
      }));

      if (dimensionList.length > 0) {
        updates.dimensionList = dimensionList;
        const radar = this.buildRadarFromDimensions(dimensionList);
        updates.radar = radar;
        updates.radarSVG = this.buildRadarSVG(radar);
        updates.dimensionPreview = this.buildDimensionPreview(dimensionList);
      }
    }

    if (sessionRes && sessionRes.average_score != null) {
      updates.averageScore = pickAverageScore(
        sessionRes.average_score,
        updates.averageScore,
        this.data.averageScore,
        this.data.resultData && this.data.resultData.average_score,
      );
      const level = getScoreLevel(updates.averageScore);
      updates.levelLabel = level.label;
      updates.gradeLabel = updates.gradeLabel || level.label;
      const scoreVisual = this.buildScoreVisual(updates.averageScore);
      updates.scorePercent = scoreVisual.scorePercent;
      updates.scoreColor = scoreVisual.scoreColor;
      updates.stars = this.getStarList(updates.gradeLabel || level.label);
    }

    if (Object.keys(updates).length > 0) {
      this.setData(updates);
    }
  },

  applyBackendReport(reportRes, feedbackRes, sessionRes) {
    this.applySessionStats(reportRes, sessionRes);
    const sessionId = (sessionRes && sessionRes.session_id)
      || this.data.savedSessionId
      || (this.data.resultData && this.data.resultData.session_id)
      || '';
    const apiItems = (feedbackRes && feedbackRes.items) || [];
    if (apiItems.length) {
      const exerciseKey = (sessionRes && sessionRes.exercise)
        || (this.data.resultData && this.data.resultData.exercise_key)
        || 'squat';
      const exerciseName = (EXERCISE_CONFIG[exerciseKey] && EXERCISE_CONFIG[exerciseKey].name) || exerciseKey;
      const feedbackTime = sessionRes && sessionRes.created_at
        ? String(sessionRes.created_at).slice(11, 19)
        : '--:--';
      this.applyFeedbackFromApiItems(apiItems, { exerciseKey, exerciseName, time: feedbackTime });
    } else if (sessionId) {
      this.refreshSessionFeedback(sessionId, sessionRes);
    }
    this.setData({ hasBackendReport: true, feedbackReady: true });
  },

  applyLocalFallbackReport(hint) {
    const data = this.data.resultData || {};
    if (hint) {
      console.warn('[Result]', hint);
    }

    const exerciseKey = data.exercise_key || 'squat';
    const exerciseName = (EXERCISE_CONFIG[exerciseKey] && EXERCISE_CONFIG[exerciseKey].name) || exerciseKey;

    if (data.feedback_summary) {
      const apiItems = this.feedbackSummaryToApiItems(
        this.parseFeedbackSummary(data.feedback_summary),
        exerciseKey,
      );
      if (apiItems.length) {
        this.applyFeedbackFromApiItems(apiItems, {
          exerciseKey,
          exerciseName,
          time: '--:--',
        });
      }
    }

    if (data.feedback_summary && data.session_id) {
      this.loadAiAdviceFromSession({
        session_id: data.session_id,
        feedback_summary: data.feedback_summary,
      });
    } else if (data.session_id) {
      this.refreshSessionFeedback(data.session_id, null, exerciseKey);
    }

    this.setData({
      hasBackendReport: this.data.displayFeedbackItems.length > 0 || Boolean(data.session_id),
      reportLoading: false,
      feedbackLoading: false,
      feedbackReady: true,
      showAiAdvice: true,
      aiAdvicePending: !this.data.aiAdvice,
      aiAdviceFailed: false,
    }, () => {
      if (!this.data.aiAdvice) {
        this.fetchAiAdviceDirectly();
      }
    });
  },

  parseFeedbackSummary(raw) {
    if (!raw) return {};
    if (typeof raw === 'object') return raw;
    try {
      return JSON.parse(raw);
    } catch (e) {
      return {};
    }
  },

  normalizeSummaryItems(summary, exercise) {
    const structured = summary.items || [];
    if (structured.length > 0) {
      return structured.map((entry, index) => ({
        id: `summary-${index}`,
        exercise,
        issue: entry.issue || '',
        suggestion: entry.suggestion || '',
        severity: entry.severity || 'warning',
      }));
    }

    const issues = summary.issues || [];
    const suggestions = summary.suggestions || [];
    if (!issues.length) return [];

    return issues.map((issue, index) => ({
      exercise,
      issue,
      suggestion: suggestions[index] || '',
      severity: index === 0 ? 'high' : index === 1 ? 'medium' : 'low',
    }));
  },

  getSeverityTypeLabel(severity) {
    if (severity === 'high' || severity === 'error') return '严重';
    if (severity === 'medium' || severity === 'warning') return '警告';
    if (severity === 'low') return '轻微';
    if (severity === 'info') return POSITIVE_LABEL;
    return '提示';
  },

  buildFeedbackStats(items) {
    const stats = { critical: 0, warning: 0, minor: 0, positive: 0 };
    (items || []).forEach((item) => {
      if (item.tone && stats[item.tone] != null) {
        stats[item.tone] += 1;
      }
    });
    return stats;
  },

  buildNextSteps(_weaknesses, recommendations, displayFeedbackItems) {
    const issueSet = new Set(
      (displayFeedbackItems || [])
        .map((item) => String(item.problem || '').trim())
        .filter(Boolean),
    );
    const suggestionSet = new Set(
      (displayFeedbackItems || [])
        .map((item) => String(item.suggestion || '').trim())
        .filter(Boolean),
    );

    const steps = [];
    const addStep = (raw) => {
      const normalized = String(raw || '').trim();
      if (!normalized || issueSet.has(normalized) || suggestionSet.has(normalized)) return;
      if (/错误动作次数偏多|有效动作占比仅/.test(normalized)) return;
      issueSet.add(normalized);
      steps.push({ text: normalized, type: 'recommend' });
    };

    (displayFeedbackItems || []).forEach((item) => {
      if (item.kind === 'error' && item.suggestion) {
        addStep(item.suggestion);
      }
    });
    (recommendations || []).forEach(addStep);

    return steps.slice(0, 4);
  },

  buildDimensionPreview(dimensionList) {
    return (dimensionList || []).slice(0, 3);
  },

  buildStrengthMessages(exerciseKey, issues) {
    const aspects = EXERCISE_ASPECTS[exerciseKey] || EXERCISE_ASPECTS.squat;
    const flagged = new Set(
      (issues || []).map((issue) => ISSUE_ASPECT_MAP[issue]).filter(Boolean),
    );
    const messages = Object.entries(aspects)
      .filter(([key]) => !flagged.has(key))
      .map(([, message]) => message);

    if (messages.length === 0) {
      return ['训练态度积极，愿意反复尝试并调整动作'];
    }
    return messages;
  },

  buildDisplayFeedbackItems(items, options = {}) {
    const exerciseKey = options.exerciseKey || 'squat';
    const exerciseName = options.exerciseName || '训练';
    const time = options.time || '--:--';
    const mapped = this.mapFeedbackItems(items);
    const errorItems = mapped.filter((item) => item.issue && item.severity !== 'info');
    const infoItems = mapped.filter((item) => item.severity === 'info' || (!item.issue && item.suggestion));

    const positiveNotes = [];
    infoItems.forEach((item) => {
      const note = briefText(item.suggestion || item.issue || '', 40);
      if (note) positiveNotes.push(note);
    });

    const errorProblems = errorItems.map((item) => item.issue).filter(Boolean);
    this.buildStrengthMessages(exerciseKey, errorProblems).forEach((note) => {
      positiveNotes.push(note);
    });

    const displayItems = [];
    [...new Set(positiveNotes)].slice(0, 5).forEach((note) => {
      displayItems.push({
        kind: 'positive',
        tone: 'positive',
        exercise: exerciseName,
        type: POSITIVE_LABEL,
        problem: note,
        suggestion: POSITIVE_SUGGESTION,
        time,
      });
    });

    errorItems.forEach((item) => {
      const tone = SEVERITY_TONE[item.severity] || 'minor';
      displayItems.push({
        kind: 'error',
        tone,
        exercise: exerciseName,
        type: this.getSeverityTypeLabel(item.severity),
        problem: briefText(item.issue, 40),
        suggestion: briefText(item.suggestion, 48),
        time,
      });
    });

    return displayItems;
  },

  mapFeedbackItems(items) {
    return (items || [])
      .filter((item) => item && (item.issue || item.suggestion))
      .map((item) => {
        const severity = item.severity || 'medium';
        const tone = SEVERITY_TONE[severity] || 'minor';

        return {
          issue: item.issue || '',
          suggestion: item.suggestion || '',
          severity,
          severityLabel: this.getSeverityTypeLabel(severity),
          tone,
          level: tone === 'critical' ? 'major' : tone === 'positive' ? 'positive' : 'minor',
        };
      });
  },

  loadAiAdviceFromSession(session) {
    const sessionId = session && session.session_id;
    const raw = session && session.feedback_summary;
    const summary = raw ? this.parseFeedbackSummary(raw) : {};
    const text = typeof summary.ai_advice === 'string' ? summary.ai_advice.trim() : '';

    if (text) {
      this.applyAiAdviceText(text);
      return;
    }

    if (summary.ai_advice_status === 'failed') {
      this.setData({
        aiAdvice: 'AI 建议生成失败，请稍后刷新重试。',
        aiAdvicePreview: '',
        aiAdvicePending: false,
        aiAdviceFailed: true,
        showAiAdvice: true,
      });
      return;
    }

    if (!sessionId) {
      this.fetchAiAdviceDirectly();
      return;
    }

    this.setData({ aiAdvicePending: true, aiAdviceFailed: false, aiAdvice: '', showAiAdvice: true });
    this.fetchAiAdviceDirectly();
    this.startAiAdvicePoll(sessionId);
  },

  buildAiAdvicePayload() {
    const data = this.data.resultData || {};
    const exercise = data.exercise_key || 'squat';
    const errors = [];
    const feedbacks = [];

    const pushUnique = (arr, value) => {
      const text = String(value || '').trim();
      if (text && !arr.includes(text)) arr.push(text);
    };

    (data.issues || []).forEach((item) => {
      pushUnique(errors, typeof item === 'string' ? item : (item.title || item.issue));
    });
    (data.suggestions || []).forEach((item) => {
      pushUnique(feedbacks, typeof item === 'string' ? item : (item.desc || item.suggestion));
    });

    (this.data.feedbackItems || []).forEach((item) => {
      pushUnique(errors, item.issue);
      pushUnique(feedbacks, item.suggestion);
    });

    if (!errors.length && !feedbacks.length) {
      pushUnique(errors, '本次训练暂无明显问题记录');
    }

    return { exercise, errors, feedbacks };
  },

  async fetchAiAdviceDirectly() {
    if (this._aiAdviceDirectStarted || this.data.aiAdvice) return;
    this._aiAdviceDirectStarted = true;

    const payload = this.buildAiAdvicePayload();
    this.setData({ aiAdvicePending: true, aiAdviceFailed: false, aiAdvice: '', showAiAdvice: true });

    try {
      const res = await ApiClient.post('/api/ai/advice', payload);
      const text = (res && res.text ? String(res.text) : '').trim();
      if (text) {
        this.clearAiAdvicePoll();
        this.applyAiAdviceText(text);
      }
    } catch (e) {
      console.warn('[Result] 直连 AI 建议失败:', e);
    }
  },

  startAiAdvicePoll(sessionId) {
    this.clearAiAdvicePoll();
    this._aiAdvicePollStartedAt = Date.now();

    const pollOnce = async () => {
      if (Date.now() - this._aiAdvicePollStartedAt > AI_ADVICE_POLL_TIMEOUT_MS) {
        this.clearAiAdvicePoll();
        if (!this.data.aiAdvice) {
          this.setData({
            aiAdvicePending: false,
            aiAdviceFailed: true,
            aiAdvice: 'AI 建议生成超时，请稍后刷新重试。',
          });
        }
        return;
      }

      try {
        const session = await ApiClient.get(`/api/sessions/${sessionId}`);
        const raw = session && session.feedback_summary;
        if (!raw) return;

        const summary = this.parseFeedbackSummary(raw);
        const text = typeof summary.ai_advice === 'string' ? summary.ai_advice.trim() : '';

        if (text) {
          this.clearAiAdvicePoll();
          this.applyAiAdviceText(text);
          return;
        }

        if (summary.ai_advice_status === 'failed') {
          this.clearAiAdvicePoll();
          this.setData({
            aiAdvice: 'AI 建议生成失败，请稍后刷新重试。',
            aiAdvicePreview: '',
            aiAdvicePending: false,
            aiAdviceFailed: true,
            showAiAdvice: true,
          });
        }
      } catch (e) {
        const msg = (e && e.message) || '';
        console.warn('[Result] AI 建议轮询失败:', msg);
        if (/401|403|404/.test(msg)) {
          this.clearAiAdvicePoll();
          this.setData({
            aiAdvicePending: false,
            aiAdviceFailed: true,
            aiAdvice: msg.includes('401')
              ? '请先登录后再查看 AI 建议'
              : '无法读取训练记录，请重新登录后重试',
          });
        }
      }
    };

    pollOnce();
    this._aiAdvicePollTimer = setInterval(pollOnce, AI_ADVICE_POLL_INTERVAL_MS);
  },

  clearAiAdvicePoll() {
    if (this._aiAdvicePollTimer) {
      clearInterval(this._aiAdvicePollTimer);
      this._aiAdvicePollTimer = null;
    }
  },

  formatAdviceText(text) {
    return String(text)
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/^#+\s*/gm, '')
      .replace(/^[-*]\s*/gm, '• ')
      .trim();
  },

  buildDimensionListFromRadar(radar) {
    return [
      { label: '动作完成度', value: radar.completion },
      { label: '稳定性', value: radar.stability },
      { label: '标准度', value: radar.standard },
      { label: '节奏控制', value: radar.tempo },
      { label: '移动速度', value: radar.speed },
    ];
  },

  buildRadarFromDimensions(dimensionList) {
    const values = dimensionList.map((item) => item.value);
    const avg = values.length
      ? Math.round(values.reduce((sum, value) => sum + value, 0) / values.length)
      : 80;

    return {
      completion: values[0] != null ? values[0] : avg,
      stability: values[1] != null ? values[1] : avg,
      standard: values[2] != null ? values[2] : avg,
      tempo: values[3] != null ? values[3] : avg,
      speed: values[4] != null ? values[4] : avg,
      axisLabels: dimensionList.map((item) => item.label),
    };
  },

  buildRadarSVG(radar) {
    const w = 500;
    const h = 460;
    const cx = w / 2;
    const cy = h / 2;
    const maxR = 160;

    const labels = radar.axisLabels || ['动作完成度', '稳定性', '标准度', '节奏控制', '移动速度'];
    const values = [radar.completion, radar.stability, radar.standard, radar.tempo, radar.speed];
    const count = labels.length;
    const angleStep = 360 / count;

    const axes = labels.map((label, index) => ({
      label,
      angle: -90 + index * angleStep,
      value: values[index] != null ? values[index] : 0,
    }));

    const layers = [0.2, 0.4, 0.6, 0.8, 1.0].map((scale) => {
      const pts = axes.map((axis) => {
        const r = maxR * scale;
        const rad = (axis.angle * Math.PI) / 180;
        return `${(cx + r * Math.cos(rad)).toFixed(1)},${(cy + r * Math.sin(rad)).toFixed(1)}`;
      }).join(' ');
      return `<polygon points="${pts}" fill="none" stroke="#e1e8f5" stroke-width="1" />`;
    }).join('');

    const axisLines = axes.map((axis) => {
      const rad = (axis.angle * Math.PI) / 180;
      return `<line x1="${cx}" y1="${cy}" x2="${(cx + maxR * Math.cos(rad)).toFixed(1)}" y2="${(cy + maxR * Math.sin(rad)).toFixed(1)}" stroke="#e1e8f5" stroke-width="1" />`;
    }).join('');

    const dataPts = axes.map((axis) => {
      const r = (axis.value / 100) * maxR;
      const rad = (axis.angle * Math.PI) / 180;
      return `${(cx + r * Math.cos(rad)).toFixed(1)},${(cy + r * Math.sin(rad)).toFixed(1)}`;
    }).join(' ');

    const dataDots = axes.map((axis) => {
      const r = (axis.value / 100) * maxR;
      const rad = (axis.angle * Math.PI) / 180;
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
    const base = score || 80;
    const accuracy = data.total_count > 0 ? (data.valid_count / data.total_count) * 100 : base;
    return {
      completion: Math.round(accuracy || base),
      stability: Math.round(Math.max(40, Math.min(100, base))),
      standard: Math.round(Math.max(40, Math.min(100, base))),
      tempo: Math.round(Math.max(40, Math.min(100, base))),
      speed: Math.round(Math.max(40, Math.min(100, base))),
      axisLabels: ['动作完成度', '稳定性', '标准度', '节奏控制', '移动速度'],
    };
  },

  getStarList(label) {
    const map = { '优秀': 5, '良好': 4, '一般': 3, '需改进': 2, '合格': 3 };
    const n = map[label] || 3;
    return Array.from({ length: n }, (_, i) => i + 1);
  },

  goBack() {
    wx.switchTab({ url: '/pages/dashboard/dashboard' });
  },

  buildScoreVisual(score) {
    const level = getScoreLevel(Math.round(Number(score) || 0));
    return {
      scorePercent: Math.min(100, Math.max(0, Math.round(Number(score) || 0))),
      scoreColor: level.color,
    };
  },

  buildAiAdvicePreview(text) {
    const normalized = String(text || '').replace(/\s+/g, ' ').trim();
    if (!normalized) return '';
    if (normalized.length <= 72) return normalized;
    return `${normalized.slice(0, 72)}…`;
  },

  applyAiAdviceText(text) {
    const formatted = this.formatAdviceText(text);
    this.setData({
      aiAdvice: formatted,
      aiAdvicePreview: this.buildAiAdvicePreview(formatted),
      aiAdvicePending: false,
      aiAdviceFailed: false,
      showAiAdvice: false,
    });
  },

  toggleAiAdvice() {
    this.setData({ showAiAdvice: !this.data.showAiAdvice });
  },

  toggleDimensionDetail() {
    this.setData({ showDimensionDetail: !this.data.showDimensionDetail });
  },

  goTrainAgain() {
    const exerciseKey = (this.data.resultData && this.data.resultData.exercise_key)
      || (this.data.exerciseConfig && this.data.exerciseConfig.key)
      || 'squat';
    wx.redirectTo({
      url: `/pages/training/training?exercise=${exerciseKey}`,
    });
  },

  onShareTap() {
    if (this.data.sharePosterLoading) return;

    this.setData({ sharePosterLoading: true });
    wx.showLoading({ title: '生成分享卡片...', mask: true });
    this.generateSharePoster((url) => {
      wx.hideLoading();
      if (url) {
        this.setData({
          showSharePreview: true,
          sharePosterUrl: url,
          sharePosterLoading: false,
        });
      } else {
        this.setData({ sharePosterLoading: false });
        wx.showToast({ title: '卡片生成失败，请重试', icon: 'none' });
      }
    });
  },

  closeSharePreview() {
    this.setData({ showSharePreview: false });
  },

  saveSharePoster() {
    const filePath = this.data.sharePosterUrl || this._shareImagePath;
    if (!filePath) return;

    wx.saveImageToPhotosAlbum({
      filePath,
      success: () => wx.showToast({ title: '已保存到相册', icon: 'success' }),
      fail: () => {
        wx.showModal({
          title: '保存失败',
          content: '请在设置中允许保存到相册后重试',
          showCancel: false,
        });
      },
    });
  },

  onShareAppMessage() {
    const exerciseName = this.data.exerciseName || '训练';
    const score = this.data.averageScore || 0;
    const meta = this.getShareScoreMeta(score);
    const payload = {
      title: `${meta.emoji} ${exerciseName} ${score}分 · ${meta.mood}，一起来运动吧！`,
      path: '/pages/dashboard/dashboard',
    };
    if (this._shareImagePath) {
      payload.imageUrl = this._shareImagePath;
    }
    return payload;
  },

  getShareScoreMeta(score) {
    const value = Math.round(Number(score) || 0);
    if (value >= 90) {
      return { emoji: '🏆', mood: '表现卓越', band: '90-100分', label: '优秀', color: '#22c55e', bg: '#ecfdf3' };
    }
    if (value >= 75) {
      return { emoji: '🔥', mood: '状态火热', band: '75-89分', label: '良好', color: '#3b82f6', bg: '#eff6ff' };
    }
    if (value >= 60) {
      return { emoji: '💪', mood: '继续加油', band: '60-74分', label: '一般', color: '#f59e0b', bg: '#fffbeb' };
    }
    return { emoji: '🎯', mood: '潜力无限', band: '0-59分', label: '需改进', color: '#ef4444', bg: '#fef2f2' };
  },

  scheduleSharePoster() {
    if (this._sharePosterTimer) {
      clearTimeout(this._sharePosterTimer);
    }
    this._sharePosterTimer = setTimeout(() => {
      this.generateSharePoster();
    }, 600);
  },

  generateSharePoster(done) {
    const width = 500;
    const height = 560;
    const score = Math.round(this.data.averageScore || 0);
    const percent = Math.min(100, Math.max(0, this.data.scorePercent || score));
    const meta = this.getShareScoreMeta(score);
    const ringColor = meta.color;
    const exerciseName = this.data.exerciseName || '训练';
    const grade = this.data.gradeLabel || this.data.levelLabel || meta.label;
    const validRate = this.data.validRate != null ? this.data.validRate : 0;
    const totalCount = this.data.totalCount || 0;
    const validCount = this.data.validCount || 0;
    const durationText = this.data.durationText || '0:00';
    const finishedAt = (this.data.finishedAt || '').split(' ')[0] || '';

    const ctx = wx.createCanvasContext('sharePoster', this);

    ctx.setFillStyle(meta.bg);
    ctx.fillRect(0, 0, width, height);

    ctx.setFillStyle(ringColor);
    ctx.fillRect(0, 0, width, 120);

    ctx.setFillStyle('rgba(255,255,255,0.18)');
    ctx.beginPath();
    ctx.arc(width - 40, 20, 70, 0, 2 * Math.PI);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(30, 100, 50, 0, 2 * Math.PI);
    ctx.fill();

    this._fillRoundRect(ctx, 24, 28, width - 48, height - 56, 20, '#ffffff');

    ctx.setFillStyle('#64748b');
    ctx.setFontSize(13);
    ctx.setTextAlign('left');
    ctx.fillText('运动姿态评估', 44, 58);
    if (finishedAt) {
      ctx.setTextAlign('right');
      ctx.fillText(finishedAt, width - 44, 58);
    }

    ctx.setTextAlign('center');
    ctx.setFontSize(46);
    ctx.fillText(meta.emoji, width / 2, 108);

    this._fillRoundRect(ctx, width / 2 - 68, 124, 136, 30, 15, meta.bg);
    ctx.setFillStyle(ringColor);
    ctx.setFontSize(16);
    ctx.fillText(exerciseName, width / 2, 145);

    const cx = width / 2;
    const cy = 228;
    const radius = 52;

    ctx.setLineWidth(10);
    ctx.setStrokeStyle('#eef2f7');
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
    ctx.stroke();

    ctx.setStrokeStyle(ringColor);
    ctx.setLineCap('round');
    ctx.beginPath();
    ctx.arc(cx, cy, radius, -Math.PI / 2, -Math.PI / 2 + (2 * Math.PI * percent) / 100);
    ctx.stroke();

    ctx.setFillStyle('#0f172a');
    ctx.setFontSize(40);
    ctx.fillText(String(score), cx - 6, cy + 12);
    ctx.setFontSize(14);
    ctx.setFillStyle('#94a3b8');
    ctx.fillText('分', cx + 30, cy + 4);

    this._fillRoundRect(ctx, cx - 42, cy + radius + 14, 84, 26, 13, ringColor);
    ctx.setFillStyle('#ffffff');
    ctx.setFontSize(15);
    ctx.fillText(grade, cx, cy + radius + 33);

    ctx.setFillStyle(ringColor);
    ctx.setFontSize(17);
    ctx.fillText(meta.mood, cx, cy + radius + 62);
    ctx.setFillStyle('#64748b');
    ctx.setFontSize(13);
    ctx.fillText(`${meta.band} · ${meta.label}`, cx, cy + radius + 84);

    const stats = [
      { label: '总次数', value: String(totalCount) },
      { label: '有效', value: String(validCount) },
      { label: '正确率', value: `${validRate}%` },
      { label: '时长', value: durationText },
    ];
    const boxW = 98;
    const boxH = 54;
    const gap = 8;
    const startX = (width - boxW * 4 - gap * 3) / 2;
    const boxY = 356;

    stats.forEach((item, index) => {
      const x = startX + index * (boxW + gap);
      this._fillRoundRect(ctx, x, boxY, boxW, boxH, 10, '#f8fafc');
      ctx.setFillStyle('#0f172a');
      ctx.setFontSize(18);
      ctx.setTextAlign('center');
      ctx.fillText(item.value, x + boxW / 2, boxY + 28);
      ctx.setFillStyle('#94a3b8');
      ctx.setFontSize(11);
      ctx.fillText(item.label, x + boxW / 2, boxY + 46);
    });

    ctx.setFillStyle('#cbd5e1');
    ctx.fillRect(44, 428, width - 88, 1);

    ctx.setFillStyle('#475569');
    ctx.setFontSize(14);
    ctx.fillText('扫码进入小程序，一起来挑战！', width / 2, 456);

    ctx.setFillStyle(ringColor);
    ctx.setFontSize(12);
    ctx.fillText('AI 姿态评估 · 科学训练', width / 2, height - 36);

    ctx.draw(false, () => {
      setTimeout(() => {
        wx.canvasToTempFilePath({
          canvasId: 'sharePoster',
          x: 0,
          y: 0,
          width,
          height,
          destWidth: width * 2,
          destHeight: height * 2,
          fileType: 'png',
          success: (res) => {
            this._shareImagePath = res.tempFilePath;
            if (typeof done === 'function') done(res.tempFilePath);
          },
          fail: (err) => {
            console.warn('[Share] 生成分享卡片失败:', err);
            if (typeof done === 'function') done('');
          },
        }, this);
      }, 500);
    });
  },

  _fillRoundRect(ctx, x, y, w, h, r, fillStyle) {
    ctx.setFillStyle(fillStyle);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.arc(x + w - r, y + r, r, -Math.PI / 2, 0);
    ctx.lineTo(x + w, y + h - r);
    ctx.arc(x + w - r, y + h - r, r, 0, Math.PI / 2);
    ctx.lineTo(x + r, y + h);
    ctx.arc(x + r, y + h - r, r, Math.PI / 2, Math.PI);
    ctx.lineTo(x, y + r);
    ctx.arc(x + r, y + r, r, Math.PI, Math.PI * 1.5);
    ctx.closePath();
    ctx.fill();
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
});

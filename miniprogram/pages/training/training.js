// 训练页 - 核心逻辑
// 摄像头帧捕获 → POST pose-detect 获取关键点 → WebSocket 实时评分 → Canvas 骨架绘制
const ApiClient = require('../../utils/api');
const { EXERCISE_CONFIG, getScoreLevel, API_BASE_URL } = require('../../utils/constants');
const AuthManager = require('../../utils/auth');
const { showToast } = require('../../utils/util');

const METRIC_CONFIG = {
  squat: [
    { key: 'knee_angle', label: '膝角', aliases: ['knee_angle'] },
    { key: 'hip_angle', label: '髋角', aliases: ['hip_angle'] },
    { key: 'trunk_angle', label: '躯干倾斜角', aliases: ['trunk_angle'] },
    { key: 'knee_symmetry_diff', label: '左右膝差', aliases: ['knee_symmetry_diff'] },
  ],
  push_up: [
    { key: 'elbow_angle', label: '肘角', aliases: ['elbow_angle'] },
    { key: 'shoulder_angle', label: '肩角', aliases: ['shoulder_angle'] },
    { key: 'body_line_angle', label: '身体直线角', aliases: ['body_line_angle'] },
    { key: 'hip_sag_angle', label: '髋部塌陷角', aliases: ['hip_sag_angle'] },
  ],
  plank: [
    { key: 'body_line_angle', label: '肩髋踝直线角', aliases: ['body_line_angle'] },
    { key: 'hip_angle', label: '髋部角', aliases: ['hip_angle'] },
    { key: 'neck_angle', label: '颈部角', aliases: ['neck_angle'] },
  ],
  jumping_jack: [
    { key: 'shoulder_abduction_angle', label: '肩外展角', aliases: ['shoulder_abduction_angle'] },
    { key: 'leg_spread_angle', label: '双腿夹角', aliases: ['leg_spread_angle'] },
    { key: 'wrist_height', label: '手腕高度', aliases: ['wrist_height'] },
    { key: 'ankle_distance', label: '脚踝距离', aliases: ['ankle_distance'] },
  ],
};

Page({
  data: {
    // 训练状态
    state: 'ready',          // ready | countdown | running | paused | finished
    exerciseKey: 'squat',
    exerciseName: '深蹲',
    countdown: 3,

    // 摄像头
    cameraWidth: 375,
    cameraHeight: 500,
    statusBarHeight: 44,
    cameraPosition: 'front',   // front | back
    cameraPosLabel: '前置',

    // 评分与计数
    currentScore: 0,
    totalCount: 0,
    validCount: 0,
    errorCount: 0,
    calories: 0,
    currentPhase: '',
    issues: [],
    feedback: [],

    // 三项关键角度指标
    metrics: {
      knee_angle: '--',
      hip_angle: '--',
      trunk_angle: '--',
      knee_symmetry_diff: '--',
    },
    metricCards: [
      { key: 'knee_angle', label: '膝角', value: '--', unit: '°' },
      { key: 'hip_angle', label: '髋角', value: '--', unit: '°' },
      { key: 'trunk_angle', label: '躯干倾斜角', value: '--', unit: '°' },
      { key: 'knee_symmetry_diff', label: '左右膝差', value: '--', unit: '°' },
    ],

    // 骨架
    currentKeypoints: null,
    scoreColor: '#4f8cff',
    phaseLabel: '',

    // 底部快速切换动作
    quickActions: [
      { key: 'squat', name: '深蹲', icon: '🦵' },
      { key: 'push_up', name: '俯卧撑', icon: '💪' },
      { key: 'jumping_jack', name: '开合跳', icon: '🤸' },
      { key: 'plank', name: '平板支撑', icon: '🧘' },
    ],

    // 调试信息
    debugFrames: 0,
    debugOkFrames: 0,
    debugErrors: 0,
    debugWsStatus: '未连接',
    debugLastError: '',
    debugFrameSize: '',
    showDebug: false,

    // 内部
    startTime: 0,
    _trainingFinishedCalled: false,
    scoresHistory: [],
    cameraReady: false,
    isDemoMode: false,
    demoVideoSrc: '',
    demoProgress: '',
    _errorCountTotal: 0,
  },

  // WebSocket 相关
  _wsTask: null,
  _wsReady: false,
  _frameTimer: null,
  _lastFrameTime: 0,
  _cameraContext: null,
  _frameListener: null,
  _frameCanvas: null,
  _frameCanvasCtx: null,
  _processingFrame: false,
  _pendingFrame: null,
  _demoTimer: null,
  _pendingScore: 0,
  _lastCommittedScoreCount: 0,
  _lastRealtimeScoreCommitTime: 0,
  _poseDetectResetPending: false,
  _serverMetricConfig: {},
  _poseReplayFrames: [],
  _poseReplayNodes: [],
  _poseReplayStartedAt: 0,
  _lastReplayNodeCount: 0,
  _prevSmoothedLandmarks: null,
  _smoothDt: 0,
  _smoothHistory: [],

  FRAME_INTERVAL: 16,
  FRAME_INTERVALS: {
    jumping_jack: 16,
    squat: 16,
    push_up: 16,
    plank: 16,
    pull_up: 16,
    bench_press: 16,
    barbell_squat: 16,
    dumbbell_fly: 16,
    lat_pulldown: 16,
    dumbbell_shoulder_press: 16,
  },

  onLoad(options) {
    const exerciseKey = options.exercise || 'squat';
    const config = EXERCISE_CONFIG[exerciseKey] || EXERCISE_CONFIG.squat;

    const initialMetrics = this._emptyMetricsForExercise(exerciseKey);
    this.setData({
      exerciseKey,
      exerciseName: config.name,
      metrics: initialMetrics,
      metricCards: this._buildMetricCards(exerciseKey, initialMetrics),
    });

    const sysInfo = wx.getSystemInfoSync();
    this.setData({
      statusBarHeight: sysInfo.statusBarHeight || 44,
      cameraWidth: sysInfo.windowWidth,
      cameraHeight: Math.floor(sysInfo.windowHeight * 0.55),
    });
  },

  onUnload() {
    this.cleanup();
  },

  // ========== Show Confirm (内联，避免依赖 util 异步问题) ==========
  _showConfirm(title, content) {
    return new Promise((resolve) => {
      wx.showModal({
        title: title,
        content: content,
        success: (res) => resolve(!!res.confirm),
        fail: () => resolve(false),
      });
    });
  },

  // ========== 摄像头初始化 ==========
  initCamera() {
    return new Promise((resolve, reject) => {
      try {
        const cameraCtx = wx.createCameraContext('trainingCamera');
        this._cameraContext = cameraCtx;

        const listener = cameraCtx.onCameraFrame((frame) => {
          this.handleCameraFrame(frame);
        });

        listener.start({
          mode: 'jpeg',
        size: this.data.exerciseKey === 'jumping_jack' ? 'small' : 'medium'
      });

        this._frameListener = listener;
        this.setData({ cameraReady: true });
        console.log('[Camera] 帧监听已启动');
        resolve();
      } catch (e) {
        console.error('[Camera] 初始化失败:', e);
        reject(e);
      }
    });
  },

  onCameraError(e) {
    console.error('[Camera] 错误:', e);
    showToast('摄像头启动失败，请检查权限');
    this.setData({ debugLastError: '摄像头错误: ' + JSON.stringify(e.detail || {}) });
  },

  // ========== WebSocket 连接 ==========
  connectWebSocket() {
    const token = AuthManager.getToken();
    if (!token) {
      this.setData({ debugWsStatus: '无Token', debugLastError: '未登录，请重新登录' });
      showToast('请先登录');
      return;
    }

    const wsUrl = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://');

    this.setData({ debugWsStatus: '连接中...' });

    this._wsTask = wx.connectSocket({
      url: `${wsUrl}/api/realtime/pose?exercise_type=${this.data.exerciseKey}&token=${token}`,
      success: () => {
        console.log('[WS] 正在连接...');
      },
      fail: (err) => {
        console.error('[WS] 连接失败:', err);
        this.setData({ debugWsStatus: '连接失败', debugLastError: err.errMsg || 'unknown' });
      }
    });

    this._wsTask.onOpen(() => {
      console.log('[WS] 已连接');
      this._wsReady = true;
      this.setData({ debugWsStatus: '已连接' });
      this.sendWS({ type: 'start', exercise_type: this.data.exerciseKey });
    });

    this._wsTask.onMessage((msg) => {
      try {
        const data = JSON.parse(msg.data);
        this.handleWSMessage(data);
      } catch (e) {
        console.error('[WS] 消息解析失败:', e);
      }
    });

    this._wsTask.onError((err) => {
      console.error('[WS] 错误:', err);
      this.setData({ debugWsStatus: '错误', debugLastError: err.errMsg || 'WS error' });
    });

    this._wsTask.onClose((res) => {
      console.log('[WS] 已关闭, code:', res.code, 'reason:', res.reason);
      this._wsReady = false;
      this.setData({ debugWsStatus: '已关闭(' + (res.code || '?') + ')' });
    });
  },

  sendWS(data) {
    if (this._wsReady && this._wsTask) {
      this._wsTask.send({
        data: JSON.stringify(data),
        fail: (err) => console.error('[WS] 发送失败:', err)
      });
    }
  },

  handleWSMessage(data) {
    switch (data.type) {
      case 'status':
        console.log('[WS] 状态:', data.state);
        if (data.core_metrics && data.exercise_type) {
          this._serverMetricConfig[data.exercise_type] = this._normalizeMetricConfig(data.core_metrics);
          const metrics = this._emptyMetricsForExercise(data.exercise_type);
          this.setData({
            metrics,
            metricCards: this._buildMetricCards(data.exercise_type, metrics),
          });
        }
        break;

      case 'analysis':
        const incomingScore = data.score != null ? Math.round(data.score) : this.data.currentScore;
        const issues = data.errors || [];
        const feedback = data.feedback || [];

        // 累积纠错历史（用于结束汇总去重）
        if (issues.length > 0) {
          if (!this._errorHistory) this._errorHistory = [];
          this._errorHistory.push(...issues);
        }
        if (feedback.length > 0) {
          if (!this._feedbackHistory) this._feedbackHistory = [];
          this._feedbackHistory.push(...feedback);
        }

        const previousTotalCount = this.data.totalCount;
        let totalCount = this.data.totalCount;
        let validCount = this.data.validCount;
        let errorCount = this.data.errorCount;

        const repFinished = !!(
          data.is_rep_finished ||
          data.rep_finished ||
          data.action_completed ||
          data.completed ||
          (data.count != null && data.count > totalCount)
        );

        if (data.count != null) {
          totalCount = data.count;
        }
        if (data.count != null && data.count > previousTotalCount) {
          this._recordReplayNode(data.count, issues, feedback, incomingScore);
        }
        validCount = data.valid_count != null ? data.valid_count : validCount;
        errorCount = data.error_count != null ? data.error_count : Math.max(0, totalCount - validCount);

        const phase = data.phase || data.current_phase || '';
        const phaseLabel = phase ? '当前阶段: ' + phase : '';

        const newMetrics = this._buildMetricsFromAnalysis(data, this.data.metrics);

        // 卡路里估算：基于动作次数，假定每次 5.6 kcal（与设计稿 12 次 68kcal 一致）
        const calories = Math.round(totalCount * 5.6);
        let displayScore = this.data.currentScore;
        let scoreColor = this.data.scoreColor;

        this._pendingScore = incomingScore;
        if (this._shouldCommitScore(repFinished, totalCount, incomingScore) && incomingScore > 0) {
          const level = getScoreLevel(incomingScore);
          displayScore = incomingScore;
          scoreColor = level.color;
          this.data.scoresHistory.push(incomingScore);
        }

        const setDataObj = {
          currentScore: displayScore,
          scoreColor,
          totalCount,
          validCount,
          errorCount,
          calories,
          currentPhase: phase,
          phaseLabel,
          metrics: newMetrics,
          metricCards: this._buildMetricCards(this.data.exerciseKey, newMetrics),
        };
        // 只在有纠错文案时才更新，避免空帧覆盖上一次的建议（"闪一下"问题）
        if (issues.length > 0) {
          setDataObj.issues = issues;
        }
        if (feedback.length > 0) {
          setDataObj.feedback = feedback;
        }
        this.setData(setDataObj);
        break;

      case 'summary':
        console.log('[WS] 训练总结:', data);
        if (this._finishTimer) {
          clearTimeout(this._finishTimer);
          this._finishTimer = null;
        }
        this._finishNavigated = true;
        this.onTrainingFinished(data.session || data);
        break;
    }
  },

  // 切换动作（底部 tab）
  switchExercise(e) {
    const key = e.currentTarget.dataset.key;
    if (!key || key === this.data.exerciseKey) return;
    if (this.data.state === 'running' || this.data.state === 'paused') {
      wx.showModal({
        title: '切换动作',
        content: '切换动作会结束当前训练，确定继续吗？',
        success: (res) => {
          if (res.confirm) this._doFinishThenRedirect(key);
        }
      });
    } else {
      const config = EXERCISE_CONFIG[key] || {};
      const metrics = this._emptyMetricsForExercise(key);
      this.setData({
        exerciseKey: key,
        exerciseName: config.name || '训练',
        metrics,
        metricCards: this._buildMetricCards(key, metrics),
      });
    }
  },

  _doFinishThenRedirect(nextKey) {
    this._doFinish();
    setTimeout(() => {
      wx.redirectTo({ url: `/pages/training/training?exercise=${nextKey}` });
    }, 1500);
  },

  // 暂停/继续（设计稿大按钮）
  togglePause() {
    if (this.data.state === 'running') this.pauseTraining();
    else if (this.data.state === 'paused') this.resumeTraining();
  },

  // ========== 帧处理 ==========
  handleCameraFrame(frame) {
    if (this.data.state !== 'running') return;

    const now = Date.now();
    if (now - this._lastFrameTime < this._getFrameInterval()) return;
    this._lastFrameTime = now;

    if (this._processingFrame) {
      this._pendingFrame = frame;
      return;
    }

    const debugFrames = this.data.debugFrames + 1;
    if (this.data.showDebug || debugFrames % 5 === 0) {
      const frameSize = (frame.width || '?') + 'x' + (frame.height || '?');
      this.setData({ debugFrames, debugFrameSize: frameSize });
    } else {
      this.data.debugFrames = debugFrames;
    }

    this.processFrame(frame);
  },

  async processFrame(frame) {
    const startedAt = Date.now();
    try {
      let debugErrors = this.data.debugErrors + 1;
      // frame.data 是 ArrayBuffer (JPEG)
      if (this._processingFrame) return;
      this._processingFrame = true;

      const base64 = await this._cameraFrameToJpegBase64(frame);
      if (!base64) {
        throw new Error('camera frame encode failed');
      }

      const payload = {
        exercise_type: this.data.exerciseKey,
        frames: [{ image: base64 }]
      };
      if (this._poseDetectResetPending) {
        payload.reset_state = true;
        this._poseDetectResetPending = false;
      }

      const result = await ApiClient.post('/api/realtime/pose-detect', payload);
      const totalMs = Date.now() - startedAt;
      const backendMs = result && result.process_ms != null ? Math.round(result.process_ms) : null;

      if (result && result.frames && result.frames.length > 0) {
        const frameData = result.frames[0];

          // 更新骨架关键点
          if (frameData.keypoints && frameData.keypoints.length > 0) {
            let replayFrame = null;
            const hasVisible = frameData.keypoints.some(kp => kp && kp.visibility > 0.5);
            if (hasVisible) {
              const debugOkFrames = this.data.debugOkFrames + 1;
              this.setData({ debugOkFrames });
              replayFrame = this._captureReplayFrame(frameData.keypoints);

              // 同时通过 setData 和组件方法更新
              const newMetrics = this._buildMetricsFromKeypoints(frameData.keypoints, frameData.features, this.data.metrics);
              this.setData({
                currentKeypoints: frameData.keypoints,
                metrics: newMetrics,
                metricCards: this._buildMetricCards(this.data.exerciseKey, newMetrics),
                debugLastError: backendMs == null ? `延迟 ${totalMs}ms` : `延迟 ${totalMs}ms / 后端 ${backendMs}ms`,
              });
              const skeletonComp = this.selectComponent('#skeleton');
              if (skeletonComp) {
                try {
                  skeletonComp.updateKeypoints(frameData.keypoints);
                } catch (e) {
                  console.warn('[Frame] 骨架绘制失败:', e);
                }
              }
            }

            if (this.data.exerciseKey === 'jumping_jack' && frameData.analysis) {
              this.handleWSMessage({ type: 'analysis', ...frameData.analysis });
            } else if (this._wsReady) {
              const namedKeypoints = this._convertToNamedKeypoints(frameData.keypoints);
              if (Object.keys(namedKeypoints).length > 0) {
                this.sendWS({
                  type: 'frame',
                  keypoints: namedKeypoints,
                  timestamp_ms: replayFrame ? replayFrame.timestamp_ms : undefined,
                  replay_keypoints: replayFrame ? replayFrame.landmarks : undefined
                });
              }
            }
          } else if (frameData.error) {
          // 后端返回了错误信息
          debugErrors = this.data.debugErrors + 1;
          this.setData({ debugErrors, debugLastError: frameData.error });
          this._showErrorToast(frameData.error.substring(0, 20));
        } else {
          // 没有关键点也没有错误 — 可能是没检测到人体
          // 静默，避免刷屏
        }
      } else {
        // API 返回空
        const debugErrors = this.data.debugErrors + 1;
        this.setData({ debugErrors, debugLastError: 'API返回空帧' });
        this._showErrorToast('后端未检测到人体');
      }
    } catch (err) {
      const debugErrors = this.data.debugErrors + 1;
      const errMsg = (err && err.message) || String(err);
      this.setData({ debugErrors, debugLastError: errMsg.substring(0, 50) });
      const isNetworkOrHttpError =
        errMsg.indexOf('网络请求失败') >= 0 ||
        errMsg.indexOf('request:fail') >= 0 ||
        errMsg.indexOf('HTTP') >= 0 ||
        errMsg.indexOf('statusCode') >= 0;
      this._showErrorToast(isNetworkOrHttpError ? '请求后端失败' : errMsg.substring(0, 20));
      console.error('[Frame] 错误:', err);
    } finally {
      this._processingFrame = false;
      if (this._pendingFrame && this.data.state === 'running') {
        const nextFrame = this._pendingFrame;
        this._pendingFrame = null;
        setTimeout(() => this.processFrame(nextFrame), 0);
      }
    }
  },

  _initFrameCanvas() {
    if (this._frameCanvas && this._frameCanvasCtx) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      wx.createSelectorQuery()
        .select('#frameCanvas')
        .fields({ node: true, size: true })
        .exec((res) => {
          const canvas = res && res[0] && res[0].node;
          if (!canvas) {
            reject(new Error('frame canvas not found'));
            return;
          }

          this._frameCanvas = canvas;
          this._frameCanvasCtx = canvas.getContext('2d');
          resolve();
        });
    });
  },

  async _cameraFrameToJpegBase64(frame) {
    await this._initFrameCanvas();

    const canvas = this._frameCanvas;
    const ctx = this._frameCanvasCtx;
    const width = frame.width;
    const height = frame.height;

    if (!canvas || !ctx || !width || !height || !frame.data) {
      return '';
    }

    canvas.width = width;
    canvas.height = height;

    const pixels = new Uint8ClampedArray(frame.data);
    let imageData;
    if (typeof ImageData !== 'undefined') {
      imageData = new ImageData(pixels, width, height);
    } else if (ctx.createImageData) {
      imageData = ctx.createImageData(width, height);
      imageData.data.set(pixels);
    } else {
      throw new Error('ImageData not supported');
    }
    ctx.putImageData(imageData, 0, 0);

    const maxSide = this.data.exerciseKey === 'jumping_jack' ? 192 : 320;
    const scale = Math.min(1, maxSide / Math.max(width, height));
    const destWidth = Math.max(1, Math.round(width * scale));
    const destHeight = Math.max(1, Math.round(height * scale));
    const quality = this.data.exerciseKey === 'jumping_jack' ? 0.35 : 0.60;

    const tempPath = await new Promise((resolve, reject) => {
      wx.canvasToTempFilePath({
        canvas,
        x: 0,
        y: 0,
        width,
        height,
        destWidth,
        destHeight,
        fileType: 'jpg',
        quality,
        success: (res) => resolve(res.tempFilePath),
        fail: reject,
      }, this);
    });

    return new Promise((resolve, reject) => {
      wx.getFileSystemManager().readFile({
        filePath: tempPath,
        encoding: 'base64',
        success: (res) => resolve(res.data),
        fail: reject,
      });
    });
  },

  _showErrorToast(msg) {
    // 只在前 3 次显示 toast，避免刷屏
    if (this.data._errorCountTotal < 3) {
      this.data._errorCountTotal++;
      showToast(msg);
    }
  },

  // 将 33 点数组转为命名关键点字典
  _convertToNamedKeypoints(keypointsArray) {
    const names = [
      'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
      'right_eye_inner', 'right_eye', 'right_eye_outer',
      'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
      'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
      'left_wrist', 'right_wrist', 'left_pinky', 'right_pinky',
      'left_index', 'right_index', 'left_thumb', 'right_thumb',
      'left_hip', 'right_hip', 'left_knee', 'right_knee',
      'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
      'left_foot_index', 'right_foot_index',
    ];

    const result = {};
    for (let i = 0; i < Math.min(names.length, keypointsArray.length); i++) {
      const kp = keypointsArray[i];
      if (kp && kp.visibility > 0.3) {
        result[names[i]] = {
          x: kp.x,
          y: kp.y,
          visibility: kp.visibility
        };
      }
    }
    return result;
  },

  _captureReplayFrame(keypointsArray) {
    const raw = this._normalizeReplayKeypoints(keypointsArray);
    if (raw.length < 33) return null;

    const now = Date.now();
    const startedAt = this._poseReplayStartedAt || this.data.startTime || now;
    const frame = {
      timestamp_ms: Math.max(0, now - startedAt),
      landmarks: raw,
    };

    this._poseReplayFrames.push(frame);
    if (this._poseReplayFrames.length > 36000) {
      this._poseReplayFrames = this._poseReplayFrames.slice(-36000);
    }

    return frame;
  },

  _recordReplayNode(repIndex, issues, feedback, score) {
    const frameIndex = Math.max(0, this._poseReplayFrames.length - 1);
    const frame = this._poseReplayFrames[frameIndex] || null;
    if (!repIndex || repIndex <= this._lastReplayNodeCount || !frame) return;

    this._lastReplayNodeCount = repIndex;
    this._poseReplayNodes.push({
      rep_index: repIndex,
      frame_index: frameIndex,
      timestamp_ms: Number(frame.timestamp_ms || 0),
      score: Number(score || 0),
      issues: (issues || []).map((issue, index) => ({
        issue,
        suggestion: feedback && feedback[index] ? feedback[index] : '',
        severity: 'warning',
        metric: '',
        value: 0,
      })),
    });
  },

  _normalizeReplayKeypoints(keypointsArray) {
    if (!Array.isArray(keypointsArray)) return [];
    return keypointsArray.slice(0, 33).map((kp) => ({
      x: Number(kp && kp.x) || 0,
      y: Number(kp && kp.y) || 0,
      z: Number(kp && kp.z) || 0,
      visibility: kp && kp.visibility != null ? (Number(kp.visibility) || 0) : 1,
    }));
  },

  _namedKeypointsToArray(namedKeypoints) {
    const names = [
      'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
      'right_eye_inner', 'right_eye', 'right_eye_outer',
      'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
      'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
      'left_wrist', 'right_wrist', 'left_pinky', 'right_pinky',
      'left_index', 'right_index', 'left_thumb', 'right_thumb',
      'left_hip', 'right_hip', 'left_knee', 'right_knee',
      'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
      'left_foot_index', 'right_foot_index',
    ];

    return names.map((name) => {
      const kp = namedKeypoints && namedKeypoints[name];
      return kp ? {
        x: kp.x,
        y: kp.y,
        z: kp.z || 0,
        visibility: kp.visibility == null ? 1 : kp.visibility,
      } : { x: 0, y: 0, z: 0, visibility: 0 };
    });
  },

  _getFrameInterval() {
    return this.FRAME_INTERVALS[this.data.exerciseKey] || this.FRAME_INTERVAL;
  },

  _buildMetricsFromAnalysis(data, fallback) {
    return this._buildMetricsFromSources(data, fallback);
  },

  _buildMetricsFromKeypoints(keypoints, features, fallback) {
    const calculated = this._calculateAnglesFromKeypoints(keypoints);
    return this._buildMetricsFromSources({ metrics: features, features: calculated }, fallback);
  },

  _getMetricConfig(exerciseKey) {
    const key = exerciseKey || this.data.exerciseKey;
    return this._serverMetricConfig[key] || METRIC_CONFIG[key] || METRIC_CONFIG.squat;
  },

  _normalizeMetricConfig(coreMetrics) {
    return (coreMetrics || [])
      .filter((item) => item && item.feature_key)
      .map((item) => ({
        key: item.feature_key,
        label: item.label || item.feature_key,
        aliases: [item.feature_key],
      }));
  },

  _emptyMetricsForExercise(exerciseKey) {
    const metrics = {};
    this._getMetricConfig(exerciseKey).forEach((item) => {
      metrics[item.key] = '--';
    });
    return metrics;
  },

  _buildMetricCards(exerciseKey, metrics) {
    const current = metrics || this._emptyMetricsForExercise(exerciseKey);
    return this._getMetricConfig(exerciseKey).map((item) => ({
      key: item.key,
      label: item.label,
      value: this._formatMetricValue(current[item.key]),
      unit: this._metricUnit(item.key),
    }));
  },

  _formatMetricValue(value) {
    if (value == null || value === '--') return '--';
    if (typeof value !== 'number' || !isFinite(value)) return value;
    return Math.abs(value) < 1 ? value.toFixed(3) : String(Math.round(value));
  },

  _metricUnit(key) {
    if (key === 'wrist_height' || key === 'ankle_distance') return '';
    return '°';
  },

  _shouldCommitScore(repFinished, totalCount, incomingScore) {
    if (this.data.exerciseKey === 'plank') {
      if (!incomingScore || incomingScore <= 0) return false;
      const now = Date.now();
      if (!this._lastRealtimeScoreCommitTime || now - this._lastRealtimeScoreCommitTime >= 3000) {
        this._lastRealtimeScoreCommitTime = now;
        return true;
      }
      return false;
    }

    if (this.data.exerciseKey === 'jumping_jack') {
      if (!incomingScore || incomingScore <= 0) return false;
      const now = Date.now();
      if (repFinished || !this._lastRealtimeScoreCommitTime || now - this._lastRealtimeScoreCommitTime >= 300) {
        this._lastRealtimeScoreCommitTime = now;
        if (repFinished && totalCount != null && totalCount > this._lastCommittedScoreCount) {
          this._lastCommittedScoreCount = totalCount;
        }
        return true;
      }
      return false;
    }

    if (!repFinished) return false;
    if (totalCount == null) return true;
    if (totalCount <= this._lastCommittedScoreCount) return false;
    this._lastCommittedScoreCount = totalCount;
    return true;
  },

  _buildMetricsFromSources(data, fallback) {
    const current = fallback || this._emptyMetricsForExercise(this.data.exerciseKey);
    const next = {};
    this._getMetricConfig(this.data.exerciseKey).forEach((item) => {
      next[item.key] = this._pickMetric(data, item.aliases || [item.key], current[item.key]);
    });
    return next;
  },

  _pickMetric(data, keys, fallback) {
    const sources = [
      data,
      data && data.metrics,
      data && data.features,
      data && data.detail,
      data && data.detail_scores,
    ];

    for (let i = 0; i < sources.length; i++) {
      const source = sources[i];
      if (!source) continue;
      for (let j = 0; j < keys.length; j++) {
        const value = source[keys[j]];
        if (typeof value === 'number' && isFinite(value)) {
          return Math.round(value);
        }
      }
    }

    return fallback == null ? '--' : fallback;
  },

  _calculateAnglesFromKeypoints(keypoints) {
    if (!keypoints || !keypoints.length) return {};

    const leftKnee = this._angleAt(keypoints, 23, 25, 27);
    const rightKnee = this._angleAt(keypoints, 24, 26, 28);
    const leftHip = this._angleAt(keypoints, 11, 23, 25);
    const rightHip = this._angleAt(keypoints, 12, 24, 26);
    const leftElbow = this._angleAt(keypoints, 11, 13, 15);
    const rightElbow = this._angleAt(keypoints, 12, 14, 16);
    const leftShoulder = this._angleAt(keypoints, 23, 11, 13);
    const rightShoulder = this._angleAt(keypoints, 24, 12, 14);
    const leftShoulderAbduction = this._angleAt(keypoints, 23, 11, 15);
    const rightShoulderAbduction = this._angleAt(keypoints, 24, 12, 16);
    const ankleDistance = this._distance(keypoints[27], keypoints[28]);
    const wristHeight = this._averageMetric(
      this._verticalOffset(keypoints[11], keypoints[15]),
      this._verticalOffset(keypoints[12], keypoints[16])
    );
    const side = this._bestVisibleSide(keypoints);
    const sideOffset = side === 'left' ? 0 : 1;
    const bodyLineRaw = this._angleAt(keypoints, 11 + sideOffset, 23 + sideOffset, 27 + sideOffset);
    const hipSagRaw = this._angleAt(keypoints, 11 + sideOffset, 23 + sideOffset, 25 + sideOffset);
    const neckAngle = this._angleAt(keypoints, 7 + sideOffset, 11 + sideOffset, 23 + sideOffset);
    const legSpreadAngle = this._legSpreadAngle(keypoints);
    const trunkAngle = this._torsoIncline(keypoints);
    const bodyLineAngle = bodyLineRaw == null ? null : Math.abs(180 - bodyLineRaw);
    const hipSag = hipSagRaw == null ? null : Math.abs(180 - hipSagRaw);
    const hipAngle = this.data.exerciseKey === 'plank'
      ? hipSag
      : this._averageMetric(leftHip, rightHip);

    return {
      knee_angle: this._averageMetric(leftKnee, rightKnee),
      hip_angle: hipAngle,
      trunk_angle: trunkAngle,
      torso_angle: trunkAngle,
      knee_symmetry_diff: leftKnee == null || rightKnee == null ? null : Math.abs(leftKnee - rightKnee),
      elbow_angle: this._averageMetric(leftElbow, rightElbow),
      shoulder_angle: this._averageMetric(leftShoulder, rightShoulder),
      avg_arm_angle: this._averageMetric(leftElbow, rightElbow),
      shoulder_abduction_angle: this._averageMetric(leftShoulderAbduction, rightShoulderAbduction),
      leg_spread_angle: legSpreadAngle,
      wrist_height: wristHeight,
      ankle_distance: ankleDistance,
      body_line_angle: bodyLineAngle,
      hip_sag: hipSag,
      hip_sag_angle: hipSag,
      neck_angle: neckAngle,
    };
  },

  _angleAt(keypoints, aIndex, bIndex, cIndex) {
    const a = keypoints[aIndex];
    const b = keypoints[bIndex];
    const c = keypoints[cIndex];
    if (!this._isVisible(a) || !this._isVisible(b) || !this._isVisible(c)) return null;

    const abx = a.x - b.x;
    const aby = a.y - b.y;
    const cbx = c.x - b.x;
    const cby = c.y - b.y;
    const dot = abx * cbx + aby * cby;
    const abLen = Math.sqrt(abx * abx + aby * aby);
    const cbLen = Math.sqrt(cbx * cbx + cby * cby);
    if (!abLen || !cbLen) return null;

    const cosine = Math.max(-1, Math.min(1, dot / (abLen * cbLen)));
    return Math.acos(cosine) * 180 / Math.PI;
  },

  _torsoIncline(keypoints) {
    const leftShoulder = keypoints[11];
    const rightShoulder = keypoints[12];
    const leftHip = keypoints[23];
    const rightHip = keypoints[24];
    if (!this._isVisible(leftShoulder) || !this._isVisible(rightShoulder) ||
        !this._isVisible(leftHip) || !this._isVisible(rightHip)) {
      return null;
    }

    const shoulder = {
      x: (leftShoulder.x + rightShoulder.x) / 2,
      y: (leftShoulder.y + rightShoulder.y) / 2,
    };
    const hip = {
      x: (leftHip.x + rightHip.x) / 2,
      y: (leftHip.y + rightHip.y) / 2,
    };
    const dx = shoulder.x - hip.x;
    const dy = shoulder.y - hip.y;
    if (!dx && !dy) return null;
    return Math.abs(Math.atan2(dx, dy)) * 180 / Math.PI;
  },

  _averageMetric(a, b) {
    const values = [a, b].filter((value) => typeof value === 'number' && isFinite(value));
    if (!values.length) return null;
    return values.reduce((sum, value) => sum + value, 0) / values.length;
  },

  _legSpreadAngle(keypoints) {
    const leftAnkle = keypoints[27];
    const rightAnkle = keypoints[28];
    const leftHip = keypoints[23];
    const rightHip = keypoints[24];
    if (!this._isVisible(leftAnkle) || !this._isVisible(rightAnkle) ||
        !this._isVisible(leftHip) || !this._isVisible(rightHip)) {
      return null;
    }

    const hipCenter = {
      x: (leftHip.x + rightHip.x) / 2,
      y: (leftHip.y + rightHip.y) / 2,
      visibility: 1,
    };
    return this._angleFromPoints(leftAnkle, hipCenter, rightAnkle);
  },

  _bestVisibleSide(keypoints) {
    const leftScore = this._visibilitySum(keypoints, [7, 11, 13, 15, 23, 25, 27]);
    const rightScore = this._visibilitySum(keypoints, [8, 12, 14, 16, 24, 26, 28]);
    return leftScore >= rightScore ? 'left' : 'right';
  },

  _visibilitySum(keypoints, indexes) {
    return indexes.reduce((sum, index) => {
      const point = keypoints[index];
      return sum + (point && point.visibility != null ? point.visibility : 0);
    }, 0);
  },

  _isVisible(point) {
    return !!point && (point.visibility == null || point.visibility > 0.5);
  },

  _distance(a, b) {
    if (!this._isVisible(a) || !this._isVisible(b)) return null;
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    return Math.sqrt(dx * dx + dy * dy);
  },

  _verticalOffset(origin, point) {
    if (!this._isVisible(origin) || !this._isVisible(point)) return null;
    return origin.y - point.y;
  },

  _angleFromPoints(a, b, c) {
    const abx = a.x - b.x;
    const aby = a.y - b.y;
    const cbx = c.x - b.x;
    const cby = c.y - b.y;
    const dot = abx * cbx + aby * cby;
    const abLen = Math.sqrt(abx * abx + aby * aby);
    const cbLen = Math.sqrt(cbx * cbx + cby * cby);
    if (!abLen || !cbLen) return null;

    const cosine = Math.max(-1, Math.min(1, dot / (abLen * cbLen)));
    return Math.acos(cosine) * 180 / Math.PI;
  },

  // ========== 训练控制 ==========
  async startTraining() {
    if (this.data.state !== 'ready') return;
    this._trainingFinishedCalled = false;
    this.setData({ debugFrames: 0, debugOkFrames: 0, debugErrors: 0, _errorCountTotal: 0 });

    // 初始化摄像头
    if (!this.data.cameraReady) {
      try {
        await this.initCamera();
      } catch (e) {
        showToast('摄像头初始化失败');
        this.setData({ debugLastError: 'initCamera 失败' });
        return;
      }
    }

    // 连接 WebSocket
    this.connectWebSocket();

    // 倒计时
    this.setData({ state: 'countdown', countdown: 3 });

    let count = 3;
    const timer = setInterval(() => {
      count--;
      if (count <= 0) {
        clearInterval(timer);
        const startedAt = Date.now();
        const metrics = this._emptyMetricsForExercise(this.data.exerciseKey);
        this._poseReplayFrames = [];
        this._poseReplayNodes = [];
        this._poseReplayStartedAt = startedAt;
        this._lastReplayNodeCount = 0;
        this.setData({
          state: 'running',
          startTime: startedAt,
          countdown: 0,
          currentScore: 0,
          totalCount: 0,
          validCount: 0,
          errorCount: 0,
          issues: [],
          feedback: [],
          metrics,
          metricCards: this._buildMetricCards(this.data.exerciseKey, metrics),
          scoresHistory: [],
        });
        this._pendingScore = 0;
        this._lastCommittedScoreCount = 0;
        this._lastRealtimeScoreCommitTime = 0;
        this._poseDetectResetPending = true;
        this._errorHistory = [];
        this._feedbackHistory = [];
      } else {
        this.setData({ countdown: count });
      }
    }, 1000);
  },

  pauseTraining() {
    if (this.data.state !== 'running') return;
    this.setData({ state: 'paused' });
    this.sendWS({ type: 'pause' });
  },

  resumeTraining() {
    if (this.data.state !== 'paused') return;
    this.setData({ state: 'running' });
    this.sendWS({ type: 'resume' });
  },

  finishTraining() {
    if (this.data.state === 'finished') return;
    wx.showModal({
      title: '结束训练',
      content: '确定要结束当前训练吗？',
      success: (res) => {
        if (res.confirm) {
          this._doFinish();
        }
      }
    });
  },

  _doFinish() {
    this.setData({ state: 'finished' });
    this._finishNavigated = false;
    this.sendWS({ type: 'finish' });

    if (this._finishTimer) {
      clearTimeout(this._finishTimer);
    }

    // 不等 AI 生成，只等后端保存 session 并返回 summary
    this._finishTimer = setTimeout(() => {
      if (this.data.state === 'finished' && !this._finishNavigated) {
        this._finishNavigated = true;
        this.onTrainingFinished(null);
      }
    }, 5000);
  },

  // ========== 调试功能 ==========

  // 拍照测试：拍一张照片发送到后端检测
  startDemoMode() {
    if (this.data.state !== 'ready') return;

    wx.chooseVideo({
      sourceType: ['album', 'camera'],
      maxDuration: 60,
      compressed: true,
      success: (res) => {
        this._stopDemoPlayback();
        this.cleanup();
        const metrics = this._emptyMetricsForExercise(this.data.exerciseKey);

        this.setData({
          isDemoMode: true,
          demoVideoSrc: res.tempFilePath,
          state: 'ready',
          currentScore: 0,
          totalCount: 0,
          validCount: 0,
          errorCount: 0,
          currentPhase: '',
          phaseLabel: '',
          issues: [],
          feedback: [],
          currentKeypoints: null,
          debugFrames: 0,
          debugOkFrames: 0,
          debugErrors: 0,
          debugWsStatus: '演示分析中',
          debugLastError: '',
          demoProgress: '',
          metrics,
          metricCards: this._buildMetricCards(this.data.exerciseKey, metrics),
        });

        wx.showLoading({ title: '分析视频中...' });
        ApiClient.upload('/api/realtime/video-test', res.tempFilePath, {
          exercise: this.data.exerciseKey,
          max_frames: 180,
        }).then((data) => {
          wx.hideLoading();
          const frames = (data.frames || []).filter((item) => item.keypoints && Object.keys(item.keypoints).length > 0);
          if (!frames.length) {
            this.setData({
              state: 'ready',
              debugWsStatus: '演示失败',
              debugLastError: '视频中未检测到人体',
            });
            wx.showModal({ title: '未检测到人体', content: '请换一段人物完整入镜的视频', showCancel: false });
            return;
          }

          this._playDemoFrames(frames, data.summary || {});
        }).catch((err) => {
          wx.hideLoading();
          this.setData({
            state: 'ready',
            debugWsStatus: '演示失败',
            debugLastError: String((err && err.message) || err),
          });
          wx.showModal({ title: '演示分析失败', content: String((err && err.message) || err), showCancel: false });
        });
      }
    });
  },

  _playDemoFrames(frames, summary) {
    this._stopDemoPlayback();

    const total = frames.length;
    let index = 0;
    const metrics = this._emptyMetricsForExercise(this.data.exerciseKey);
    this.setData({
      state: 'running',
      startTime: Date.now(),
      debugWsStatus: '演示播放中',
      debugFrames: 0,
      debugOkFrames: 0,
      debugErrors: 0,
      scoresHistory: [],
      metrics,
      metricCards: this._buildMetricCards(this.data.exerciseKey, metrics),
    });
    this._pendingScore = 0;
    this._lastCommittedScoreCount = 0;
    this._lastRealtimeScoreCommitTime = 0;

    const videoCtx = wx.createVideoContext('demoVideo', this);
    try {
      videoCtx.seek(0);
      videoCtx.play();
    } catch (e) {}

    const tick = () => {
      if (index >= total) {
        const finalScore = summary.average_score || this.data.currentScore;
        const level = getScoreLevel(finalScore || 0);
        this._stopDemoPlayback();
        try { videoCtx.pause(); } catch (e) {}
        this.setData({
          state: 'finished',
          currentScore: Math.round(finalScore || 0),
          scoreColor: level.color,
          totalCount: summary.total_count || this.data.totalCount,
          validCount: summary.valid_count || this.data.validCount,
          errorCount: summary.error_count || this.data.errorCount,
          debugWsStatus: '演示完成',
          demoProgress: `${total}/${total}`,
        });
        return;
      }

      this._applyDemoFrame(frames[index], index, total);
      index += 1;
    };

    tick();
    this._demoTimer = setInterval(tick, 250);
  },

  _applyDemoFrame(frame, index, total) {
    const keypoints = this._namedKeypointsToArray(frame.keypoints || {});
    const visible = keypoints.filter((kp) => kp && kp.visibility > 0.5).length;
    const incomingScore = frame.score != null ? Math.round(frame.score) : this.data.currentScore;
    const phase = frame.stage || frame.phase || '';
    const issues = frame.errors || frame.issues || [];
    const totalCount = frame.count != null ? frame.count : this.data.totalCount;
    const validCount = frame.valid_count != null ? frame.valid_count : this.data.validCount;
    const errorCount = Math.max(0, totalCount - validCount);
    const repFinished = !!(
      frame.is_rep_finished ||
      frame.rep_finished ||
      frame.action_completed ||
      frame.completed ||
      (frame.count != null && frame.count > this.data.totalCount)
    );
    let displayScore = this.data.currentScore;
    let scoreColor = this.data.scoreColor;

    this._pendingScore = incomingScore;
    if (this._shouldCommitScore(repFinished, totalCount, incomingScore) && incomingScore > 0) {
      const level = getScoreLevel(incomingScore || 0);
      displayScore = incomingScore;
      scoreColor = level.color;
      this.data.scoresHistory.push(incomingScore);
    }
    const newMetrics = this._buildMetricsFromKeypoints(keypoints, frame.features || frame.metrics, this.data.metrics);

    this.setData({
      currentKeypoints: keypoints,
      currentScore: displayScore,
      scoreColor,
      totalCount,
      validCount,
      errorCount,
      metrics: newMetrics,
      metricCards: this._buildMetricCards(this.data.exerciseKey, newMetrics),
      currentPhase: phase,
      phaseLabel: phase ? '当前阶段: ' + phase : '',
      issues,
      feedback: Array.isArray(frame.feedback) ? frame.feedback : [],
      debugFrames: index + 1,
      debugOkFrames: visible > 0 ? this.data.debugOkFrames + 1 : this.data.debugOkFrames,
      debugFrameSize: `demo ${index + 1}/${total}`,
      demoProgress: `${index + 1}/${total}`,
    });

    const skeletonComp = this.selectComponent('#skeleton');
    if (skeletonComp) {
      skeletonComp.updateKeypoints(keypoints);
    }
  },

  _stopDemoPlayback() {
    if (this._demoTimer) {
      clearInterval(this._demoTimer);
      this._demoTimer = null;
    }
    try {
      wx.createVideoContext('demoVideo', this).pause();
    } catch (e) {}
  },

  debugPhoto() {
    const that = this;
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sizeType: ['compressed'],
      success(res) {
        const tempPath = res.tempFiles[0].tempFilePath;
        wx.getFileSystemManager().readFile({
          filePath: tempPath,
          encoding: 'base64',
          success: async (fileRes) => {
            const base64 = fileRes.data;
            try {
              wx.showToast({ title: '检测中...', icon: 'none' });
              const result = await ApiClient.post('/api/realtime/pose-detect', {
                exercise_type: that.data.exerciseKey,
                frames: [{ image: base64 }]
              });
              const frameData = (result.frames && result.frames[0]) || {};
              if (frameData.keypoints && frameData.keypoints.length > 0) {
                const visible = frameData.keypoints.filter(kp => kp && kp.visibility > 0.5).length;
                that.setData({ currentKeypoints: frameData.keypoints });
                const skeletonComp = that.selectComponent('#skeleton');
                if (skeletonComp) skeletonComp.updateKeypoints(frameData.keypoints);
                wx.showModal({
                  title: '检测成功',
                  content: `检测到 ${visible}/33 个可见关键点`,
                  showCancel: false,
                  complete: () => {
                    // 关闭弹窗后清除骨架
                    that.setData({ currentKeypoints: null });
                    const sc = that.selectComponent('#skeleton');
                    if (sc) sc.clear();
                  }
                });
              } else if (frameData.error) {
                wx.showModal({ title: '检测失败', content: frameData.error, showCancel: false });
              } else {
                wx.showModal({ title: '未检测到人体', content: '请确保照片中有人', showCancel: false });
              }
            } catch (err) {
              wx.showModal({ title: '请求失败', content: String(err.message || err), showCancel: false });
            }
          },
          fail: (err) => {
            wx.showModal({ title: '读文件失败', content: String(err.errMsg), showCancel: false });
          }
        });
      }
    });
  },

  // 视频测试：提取视频首帧检测
  debugVideo() {
    const that = this;
    wx.chooseVideo({
      sourceType: ['album', 'camera'],
      maxDuration: 10,
      compressed: true,
      success(res) {
        wx.showLoading({ title: '处理中...' });
        ApiClient.upload('/api/realtime/video-test', res.tempFilePath, {
          exercise: that.data.exerciseKey,
          max_frames: 240,
        }).then((data) => {
          wx.hideLoading();
          const frames = data.frames || [];
          const hit = frames.find((item) => item.keypoints && Object.keys(item.keypoints).length > 0);
          const processed = data.processed_frames || frames.length || 0;
          const valid = data.valid_keypoint_frames || frames.filter((item) => item.keypoints && Object.keys(item.keypoints).length > 0).length;

          if (hit) {
            const keypoints = that._namedKeypointsToArray(hit.keypoints);
            const visible = keypoints.filter((kp) => kp && kp.visibility > 0.5).length;
            that.setData({ currentKeypoints: keypoints });
            const sc = that.selectComponent('#skeleton');
            if (sc) sc.updateKeypoints(keypoints);
            wx.showModal({
              title: '检测成功',
              content: '已处理 ' + processed + ' 帧，有效 ' + valid + ' 帧，当前显示 ' + visible + '/33 个关键点',
              showCancel: false,
              complete: () => {
                that.setData({ currentKeypoints: null });
                const sc2 = that.selectComponent('#skeleton');
                if (sc2) sc2.clear();
              }
            });
          } else {
            wx.showModal({
              title: '未检测到人体',
              content: '后端已处理 ' + processed + ' 帧，有效 0 帧。请确认后端已重启，并选择人物完整入镜的视频。',
              showCancel: false
            });
          }
        }).catch((e) => {
          wx.hideLoading();
          wx.showModal({ title: '失败', content: String(e.message || e), showCancel: false });
        });
        return;
        // 视频缩略图就是 tempThumbPath
        const thumbPath = res.thumbTempFilePath || res.tempFilePath;
        wx.getFileSystemManager().readFile({
          filePath: thumbPath,
          encoding: 'base64',
          success: async (fileRes) => {
            wx.hideLoading();
            wx.showToast({ title: '检测中...', icon: 'none' });
            try {
              const result = await ApiClient.post('/api/realtime/pose-detect', {
                exercise_type: that.data.exerciseKey,
                frames: [{ image: fileRes.data }]
              });
              const frameData = (result.frames && result.frames[0]) || {};
              if (frameData.keypoints && frameData.keypoints.length > 0) {
                const visible = frameData.keypoints.filter(kp => kp && kp.visibility > 0.5).length;
                that.setData({ currentKeypoints: frameData.keypoints });
                const sc = that.selectComponent('#skeleton');
                if (sc) sc.updateKeypoints(frameData.keypoints);
                wx.showModal({
                  title: '检测成功',
                  content: `${visible}/33 个关键点`,
                  showCancel: false,
                  complete: () => {
                    that.setData({ currentKeypoints: null });
                    const sc2 = that.selectComponent('#skeleton');
                    if (sc2) sc2.clear();
                  }
                });
              } else if (frameData.error) {
                wx.showModal({ title: '失败', content: frameData.error, showCancel: false });
              } else {
                wx.showModal({ title: '未检测到', content: '帧中未发现人体', showCancel: false });
              }
            } catch (e) {
              wx.showModal({ title: '失败', content: String(e.message || e), showCancel: false });
            }
          },
          fail: () => {
            wx.hideLoading();
            // readFile 对视频文件可能失败，退到上传方式
            wx.uploadFile({
              url: API_BASE_URL + '/api/videos/upload',
              filePath: res.tempFilePath,
              name: 'file',
              formData: { exercise: that.data.exerciseKey },
              header: { 'Authorization': 'Bearer ' + AuthManager.getToken() },
              success(uploadRes) {
                wx.hideLoading();
                try {
                  const data = JSON.parse(uploadRes.data);
                  wx.showModal({ title: '上传成功', content: data.file_uri || 'ok', showCancel: false });
                } catch (e) {
                  wx.showModal({ title: '结果', content: '状态: ' + uploadRes.statusCode, showCancel: false });
                }
              },
              fail() {
                wx.hideLoading();
                wx.showModal({ title: '失败', content: '视频处理暂不可用', showCancel: false });
              }
            });
          }
        });
      }
    });
  },

  // 强制退出（不保存数据）
  forceExit() {
    wx.showModal({
      title: '强制退出',
      content: '将直接退出训练，不保存数据。确定吗？',
      success: (res) => {
        if (res.confirm) {
          this.cleanup();
          wx.navigateBack();
        }
      }
    });
  },

  onTrainingFinished(session) {
    // Guard against double invocation — WS summary + _doFinish timeout
    if (this._trainingFinishedCalled) return;
    this._trainingFinishedCalled = true;

    const duration = Math.round((Date.now() - (this.data.startTime || Date.now())) / 1000);
    const avgScore = this.data.scoresHistory.length > 0
      ? Math.round(this.data.scoresHistory.reduce((a, b) => a + b, 0) / this.data.scoresHistory.length)
      : this.data.currentScore;

    // 纠错建议去重汇总（从逐次 score_rep 累积而来）
    const allErrors = [...new Set((this._errorHistory || []).filter(Boolean))];
    const allFeedbacks = [...new Set((this._feedbackHistory || []).filter(Boolean))];

    const resultData = {
      exercise_key: this.data.exerciseKey,
      exercise_name: this.data.exerciseName,
      duration_seconds: (session && session.duration_seconds) || duration,
      total_count: (session && session.total_count) || this.data.totalCount,
      valid_count: (session && session.valid_count) || this.data.validCount,
      error_count: (session && session.error_count) || this.data.errorCount,
      average_score: (session && session.average_score) || avgScore,
      session_id: (session && session.session_id) || '',
      feedback_summary: (session && session.feedback_summary) || '',
      issues: allErrors,
      suggestions: allFeedbacks,
    };

    if (this._poseReplayFrames && this._poseReplayFrames.length > 0) {
      const replayKey = `pose_replay_${Date.now()}`;
      try {
        wx.setStorageSync(replayKey, this._poseReplayFrames);
        resultData.replay_key = replayKey;
        resultData.has_replay = true;
        resultData.replay_nodes = this._poseReplayNodes || [];
      } catch (e) {
        console.warn('[Replay] 临时保存回放帧失败:', e);
      }
    }

    const resultKey = `training_result_${Date.now()}`;
    try {
      wx.setStorageSync(resultKey, resultData);
    } catch (e) {
      console.warn('[Result] 缓存训练结果失败:', e);
    }

    this.cleanup();

    const navigateUrl = resultKey
      ? `/pages/result/result?key=${encodeURIComponent(resultKey)}`
      : `/pages/result/result?data=${encodeURIComponent(JSON.stringify(resultData))}`;

    wx.redirectTo({
      url: navigateUrl,
      fail: () => {
        wx.navigateBack();
      }
    });
  },

  handleBack() {
    if (this.data.state === 'running' || this.data.state === 'paused') {
      wx.showModal({
        title: '退出训练',
        content: '退出后当前训练数据将丢失，确定退出吗？',
        success: (res) => {
          if (res.confirm) {
            this.cleanup();
            wx.navigateBack();
          }
        }
      });
    } else {
      this.cleanup();
      wx.navigateBack();
    }
  },

  toggleDebug() {
    this.setData({ showDebug: !this.data.showDebug });
  },

  // 切换摄像头
  toggleCamera() {
    if (this.data.state !== 'ready') return;
    const newPos = this.data.cameraPosition === 'front' ? 'back' : 'front';
    this.setData({ cameraPosition: newPos, cameraPosLabel: newPos === 'front' ? '前置' : '后置', cameraReady: false });
    this._cameraContext = null;
    this._frameListener = null;
  },

  // 切换到后置并立即开始训练
  switchAndStart() {
    if (this.data.state !== 'ready') return;
    if (this.data.cameraPosition !== 'back') {
      this.setData({ cameraPosition: 'back', cameraPosLabel: '后置', cameraReady: false });
      this._cameraContext = null;
      this._frameListener = null;
    }
    // 延迟让摄像头切换生效
    setTimeout(() => {
      this.startTraining();
    }, 500);
  },

  cleanup() {
    this._stopDemoPlayback();
    if (this._wsTask) {
      try { this._wsTask.close(); } catch (e) {}
      this._wsTask = null;
      this._wsReady = false;
    }
    if (this._frameListener) {
      try { this._frameListener.stop(); } catch (e) {}
      this._frameListener = null;
    }
    this._cameraContext = null;
    this._processingFrame = false;
    this._pendingFrame = null;
    this.setData({
      isDemoMode: false,
      demoVideoSrc: '',
      demoProgress: '',
    });
  }
});

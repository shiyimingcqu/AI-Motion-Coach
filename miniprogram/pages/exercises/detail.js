// 动作详情页
const { EXERCISE_CONFIG } = require('../../utils/constants');

const EXERCISE_IMAGES = {
  squat: '/assets/fitness/exercise-squat.png',
  push_up: '/assets/fitness/exercise-pushup.png',
  jumping_jack: '/assets/fitness/exercise-jumping-jack.png',
  plank: '/assets/fitness/exercise-plank.png',
  lunge: '/assets/fitness/exercise-squat.png',
  burpee: '/assets/fitness/exercise-pushup.png',
  high_knees: '/assets/fitness/exercise-jumping-jack.png',
};

Page({
  data: {
    exercise: {},
    exerciseStats: null
  },

  onLoad(options) {
    const key = options.key || 'squat';
    const config = EXERCISE_CONFIG[key] || EXERCISE_CONFIG.squat;

    this.setData({
      exercise: {
        key: config.key,
        name: config.name,
        category: config.category,
        level: config.level,
        duration: '约10分钟',
        description: this.getDescription(config.key),
        accentColor: config.accentColor,
        icon: config.icon,
        image: EXERCISE_IMAGES[config.key] || '',
        modes: ['摄像头实时检测', '视频上传分析'],
        errors: this.getErrors(config.key),
        phases: config.phases || [],
      }
    });

    // 设置导航栏标题
    wx.setNavigationBarTitle({ title: config.name });
  },

  getDescription(key) {
    const descriptions = {
      squat: '深蹲是下肢力量训练的基础动作，主要锻炼股四头肌、臀大肌和核心肌群。通过评估下蹲深度、膝关节角度和躯干姿态来判断动作标准度。',
      push_up: '俯卧撑是经典的上肢力量训练动作，主要锻炼胸大肌、三角肌前束和肱三头肌。系统会监测肘部弯曲角度、身体直线度和肩部稳定性。',
      jumping_jack: '开合跳是高效的心肺训练动作，适合热身和燃脂。系统评估手脚协调性、开合幅度和动作节奏。',
      plank: '平板支撑是核心稳定性训练的王牌动作，锻炼腹横肌、腹直肌和竖脊肌。系统监测髋部高度、肩肘对齐度和身体直线度。',
      lunge: '弓步蹲是下肢力量与平衡训练动作，锻炼臀大肌、股四头肌和核心。系统评估膝关节角度、身体直立度和步幅对称性。',
      glute_bridge: '臀桥是臀部激活和核心训练的基础动作，适合初学者。系统监测髋部抬起高度、膝盖角度和身体直线度。',
      high_knees: '高抬腿是提高心率、增强下肢爆发力的心肺训练。系统评估抬膝高度、节奏稳定性和身体直立度。',
      burpee: '波比跳是全身高强度间歇训练动作，结合深蹲、俯卧撑和跳跃。系统评估动作连贯性、核心稳定性和各阶段标准度。',
    };
    return descriptions[key] || '系统将通过姿态检测技术实时评估你的动作标准度，给出评分和改进建议。';
  },

  getErrors(key) {
    const errorMap = {
      squat: ['下蹲深度不足', '膝盖内扣', '躯干前倾过大', '左右不平衡'],
      push_up: ['身体塌腰', '肘部弯曲不足', '左右不对称', '头部姿态不当'],
      jumping_jack: ['手臂未举过肩', '双脚打开不足', '手脚不同步', '节奏不稳定'],
      plank: ['髋部下沉', '肩膀不在手肘正上方', '头颈姿态异常'],
      lunge: ['膝盖超过脚尖', '身体前倾', '步幅不一致'],
      glute_bridge: ['抬臀高度不足', '腰部代偿', '膝盖外翻'],
      high_knees: ['膝盖抬起高度不足', '节奏不稳', '身体晃动'],
      burpee: ['动作不连贯', '核心松散', '俯卧撑不标准'],
    };
    return errorMap[key] || [];
  },

  startTraining() {
    const key = this.data.exercise.key;
    wx.navigateTo({ url: `/pages/training/training?exercise=${key}` });
  }
});

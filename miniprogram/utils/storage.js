// 本地存储封装
const STORAGE_PREFIX = 'pose_eval_';

class Storage {
  static set(key, value) {
    try {
      wx.setStorageSync(STORAGE_PREFIX + key, value);
    } catch (e) {
      console.error('Storage set error:', e);
    }
  }

  static get(key, defaultValue = null) {
    try {
      const value = wx.getStorageSync(STORAGE_PREFIX + key);
      return value !== '' ? value : defaultValue;
    } catch (e) {
      console.error('Storage get error:', e);
      return defaultValue;
    }
  }

  static remove(key) {
    try {
      wx.removeStorageSync(STORAGE_PREFIX + key);
    } catch (e) {
      console.error('Storage remove error:', e);
    }
  }

  static clear() {
    try {
      wx.clearStorageSync();
    } catch (e) {
      console.error('Storage clear error:', e);
    }
  }

  // 特定 key 常量
  static KEYS = {
    TOKEN: 'token',
    TOKEN_EXPIRE: 'token_expire',
    USER_INFO: 'user_info'
  };
}

module.exports = Storage;

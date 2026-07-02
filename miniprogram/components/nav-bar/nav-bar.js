// 自定义导航栏
Component({
  properties: {
    title: {
      type: String,
      value: ''
    },
    showBack: {
      type: Boolean,
      value: false
    }
  },

  data: {
    statusBarHeight: 44
  },

  lifetimes: {
    attached() {
      const sysInfo = wx.getSystemInfoSync();
      this.setData({
        statusBarHeight: sysInfo.statusBarHeight || 44
      });
    }
  },

  methods: {
    handleBack() {
      wx.navigateBack();
    }
  }
});

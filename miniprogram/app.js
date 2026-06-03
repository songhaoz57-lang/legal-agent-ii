// ii 法律助手 - 微信小程序
App({
  globalData: {
    // 后端 API 地址，部署后改为实际域名
    apiBase: "https://legal-agent-ii.onrender.com",
    userInfo: null
  },

  onLaunch() {
    // 检查更新
    if (wx.getUpdateManager) {
      const um = wx.getUpdateManager()
      um.onUpdateReady(() => {
        wx.showModal({ title: "更新提示", content: "新版本已就绪，是否重启应用？", success: r => r.confirm && um.applyUpdate() })
      })
    }
  },

  // 封装请求
  request(path, method = "GET", data = null) {
    const url = this.globalData.apiBase + path
    return new Promise((resolve, reject) => {
      wx.request({
        url, method, data,
        header: { "Content-Type": method === "POST" ? "application/json" : "application/json" },
        success: res => {
          if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data)
          else reject(res.data)
        },
        fail: err => reject(err)
      })
    })
  },

  // 上传文件
  uploadFile(path, filePath, fileName = "file") {
    const url = this.globalData.apiBase + path
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url, filePath, name: fileName,
        success: res => {
          try { resolve(JSON.parse(res.data)) }
          catch { reject(res) }
        },
        fail: err => reject(err)
      })
    })
  }
})

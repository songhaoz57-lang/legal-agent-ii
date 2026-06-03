const app = getApp()

Page({
  data: {
    fileName: "",
    reviewing: false,
    result: null
  },

  // 选择文件
  chooseFile() {
    wx.chooseMessageFile({
      count: 1,
      type: "file",
      extension: ["docx", "doc", "txt", "pdf"],
      success: res => {
        const file = res.tempFiles[0]
        this.setData({ fileName: file.name, result: null })
        this.reviewContract(file.path)
      },
      fail: err => {
        if (err.errMsg.indexOf("cancel") === -1) {
          wx.showToast({ title: "选择文件失败", icon: "none" })
        }
      }
    })
  },

  // 审查合同
  async reviewContract(filePath) {
    this.setData({ reviewing: true })
    try {
      const result = await app.uploadFile("/api/review", filePath)
      this.setData({ result, reviewing: false })
    } catch (e) {
      this.setData({ reviewing: false, fileName: "" })
      wx.showToast({ title: "审查失败，请重试", icon: "none" })
    }
  }
})

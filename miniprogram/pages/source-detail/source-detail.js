const app = getApp()

Page({
  data: {
    path: "",
    title: "",
    content: "",
    htmlContent: "",
    loading: true,
    error: ""
  },

  onLoad(options) {
    const path = decodeURIComponent(options.path || "")
    const title = decodeURIComponent(options.title || "法律条文")
    this.setData({ path, title })
    wx.setNavigationBarTitle({ title })
    this.loadContent(path)
  },

  async loadContent(path) {
    try {
      const data = await app.request("/api/source/" + encodeURIComponent(path))
      const raw = data.content || data.text || ""
      // 简单 Markdown 转 HTML
      const html = raw
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/^### (.+)$/gm, '<h3 style="font-size:32rpx;font-weight:600;margin:24rpx 0 12rpx">$1</h3>')
        .replace(/^## (.+)$/gm, '<h2 style="font-size:34rpx;font-weight:700;margin:28rpx 0 14rpx">$1</h2>')
        .replace(/^# (.+)$/gm, '<h1 style="font-size:36rpx;font-weight:700;margin:32rpx 0 16rpx">$1</h1>')
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.+?)\*/g, "<em>$1</em>")
        .replace(/^- (.+)$/gm, '<li style="margin-left:32rpx;list-style:disc">$1</li>')
        .replace(/\n/g, "<br/>")
      this.setData({ htmlContent: html, loading: false })
    } catch (e) {
      this.setData({ loading: false, error: "加载内容失败" })
    }
  }
})

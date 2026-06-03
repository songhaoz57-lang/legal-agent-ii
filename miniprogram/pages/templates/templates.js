const app = getApp()

Page({
  data: {
    templates: [],
    loading: true
  },

  onLoad() { this.loadTemplates() },
  onShow() {
    if (this.data.templates.length === 0) this.loadTemplates()
  },

  async loadTemplates() {
    this.setData({ loading: true })
    try {
      const data = await app.request("/api/templates")
      const templates = (data.templates || []).map((t, i) => ({
        ...t,
        id: t.id || t.name || i,
        icon: this.getIcon(t.name || "")
      }))
      this.setData({ templates, loading: false })
    } catch (e) {
      this.setData({ loading: false })
      wx.showToast({ title: "加载失败", icon: "none" })
    }
  },

  getIcon(name) {
    if (name.includes("劳动") || name.includes("劳动")) return "👷"
    if (name.includes("保密") || name.includes("NDA")) return "🔒"
    if (name.includes("服务") || name.includes("服务")) return "🤝"
    if (name.includes("买卖") || name.includes("销售")) return "💰"
    return "📄"
  },

  selectTemplate(e) {
    const { id, name } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/generate/generate?id=${id}&name=${encodeURIComponent(name)}`
    })
  }
})

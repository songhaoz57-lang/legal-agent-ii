const app = getApp()

Page({
  data: {
    sources: [],
    filteredSources: [],
    keyword: "",
    activeCat: "",
    categories: []
  },

  onLoad() { this.loadSources() },
  onShow() {
    if (this.data.sources.length === 0) this.loadSources()
  },

  async loadSources() {
    try {
      const data = await app.request("/api/sources")
      const sources = (data.sources || []).map(s => ({
        ...s,
        title: s.title || s.path || "未知文件",
        category: s.category || this.guessCategory(s.path || "")
      }))
      const cats = [...new Set(sources.map(s => s.category).filter(Boolean))]
      this.setData({ sources, filteredSources: sources, categories: cats })
    } catch (e) {
      wx.showToast({ title: "加载失败", icon: "none" })
    }
  },

  guessCategory(path) {
    if (!path) return "法律法规"
    if (path.includes("合同") || path.includes("contract")) return "合同法"
    if (path.includes("劳动") || path.includes("labor")) return "劳动法"
    if (path.includes("公司") || path.includes("company")) return "公司法"
    if (path.includes("知识产权") || path.includes("ip")) return "知识产权"
    if (path.includes("刑法") || path.includes("criminal")) return "刑法"
    if (path.includes("民法典") || path.includes("civil")) return "民法典"
    return "法律法规"
  },

  onSearch(e) {
    const kw = e.detail.value.trim().toLowerCase()
    this.setData({ keyword: kw })
    this.applyFilter(kw, this.data.activeCat)
  },

  filterCat(e) {
    const cat = e.currentTarget.dataset.cat
    this.setData({ activeCat: cat })
    this.applyFilter(this.data.keyword, cat)
  },

  applyFilter(kw, cat) {
    let list = this.data.sources
    if (kw) list = list.filter(s => s.title.toLowerCase().includes(kw))
    if (cat) list = list.filter(s => s.category === cat)
    this.setData({ filteredSources: list })
  },

  openDetail(e) {
    const { path, title } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/source-detail/source-detail?path=${encodeURIComponent(path)}&title=${encodeURIComponent(title)}`
    })
  }
})

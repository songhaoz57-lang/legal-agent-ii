const app = getApp()

Page({
  data: {
    messages: [],
    inputText: "",
    loading: false,
    scrollTo: ""
  },

  onInput(e) {
    this.setData({ inputText: e.detail.value })
  },

  quickAsk(e) {
    const q = e.currentTarget.dataset.q
    this.setData({ inputText: q })
    this.sendMsg()
  },

  async sendMsg() {
    const text = this.data.inputText.trim()
    if (!text || this.data.loading) return

    const msgs = [...this.data.messages, { id: Date.now(), role: "user", content: text }]
    this.setData({ messages: msgs, inputText: "", loading: true, scrollTo: "msg-bottom" })

    try {
      const result = await app.request("/api/ask", "POST", { question: text })
      const reply = result.answer || result.response || "抱歉，暂时无法回答该问题。"
      this.setData({
        messages: [...this.data.messages, { id: Date.now() + 1, role: "ai", content: reply }],
        loading: false,
        scrollTo: "msg-bottom"
      })
    } catch (e) {
      this.setData({
        messages: [...this.data.messages, { id: Date.now() + 1, role: "ai", content: "请求失败，请检查网络后重试。" }],
        loading: false, scrollTo: "msg-bottom"
      })
    }
  }
})

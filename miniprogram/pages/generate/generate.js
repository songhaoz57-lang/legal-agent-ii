const app = getApp()

// 各模板所需字段
const TEMPLATE_FIELDS = {
  "劳动合同": [
    { key: "employer", label: "用人单位名称" },
    { key: "employee", label: "员工姓名" },
    { key: "position", label: "岗位名称" },
    { key: "salary", label: "月薪（元）" },
    { key: "start_date", label: "合同起始日期" },
    { key: "duration", label: "合同期限（年）" }
  ],
  "保密协议": [
    { key: "company", label: "公司名称" },
    { key: "employee", label: "员工姓名" },
    { key: "confidential_info", label: "保密内容描述" },
    { key: "duration", label: "保密期限（年）" }
  ],
  "服务合同": [
    { key: "client", label: "委托方名称" },
    { key: "provider", label: "服务方名称" },
    { key: "service_desc", label: "服务内容" },
    { key: "amount", label: "合同金额（元）" },
    { key: "start_date", label: "服务起始日期" }
  ],
  "买卖合同": [
    { key: "buyer", label: "买方名称" },
    { key: "seller", label: "卖方名称" },
    { key: "goods", label: "商品名称及规格" },
    { key: "quantity", label: "数量" },
    { key: "price", label: "单价（元）" },
    { key: "delivery_date", label: "交货日期" }
  ]
}

Page({
  data: {
    templateId: "",
    templateName: "",
    fields: [],
    generating: false,
    resultContent: ""
  },

  onLoad(options) {
    const id = options.id || ""
    const name = decodeURIComponent(options.name || "合同")
    wx.setNavigationBarTitle({ title: "生成" + name })

    const fieldDefs = TEMPLATE_FIELDS[name] || [
      { key: "party_a", label: "甲方" },
      { key: "party_b", label: "乙方" },
      { key: "content", label: "合同主要内容" }
    ]
    const fields = fieldDefs.map(f => ({ ...f, value: "" }))

    this.setData({ templateId: id, templateName: name, fields })
  },

  onFieldChange(e) {
    const key = e.currentTarget.dataset.key
    const value = e.detail.value
    const fields = this.data.fields.map(f => f.key === key ? { ...f, value } : f)
    this.setData({ fields })
  },

  async generate() {
    const fields = this.data.fields
    const empty = fields.find(f => !f.value.trim())
    if (empty) {
      wx.showToast({ title: "请填写" + empty.label, icon: "none" })
      return
    }

    this.setData({ generating: true, resultContent: "" })

    const params = {}
    fields.forEach(f => { params[f.key] = f.value.trim() })

    try {
      const data = await app.request("/api/contract/generate", "POST", {
        template: this.data.templateName,
        fields: params
      })
      this.setData({
        generating: false,
        resultContent: data.content || data.contract || "生成失败"
      })
    } catch (e) {
      this.setData({ generating: false })
      wx.showToast({ title: "生成失败，请重试", icon: "none" })
    }
  },

  copyContent() {
    wx.setClipboardData({
      data: this.data.resultContent,
      success: () => wx.showToast({ title: "已复制到剪贴板" })
    })
  }
})

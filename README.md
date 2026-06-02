# Legal Agent

一个面向法律咨询初筛、资料检索和文书分析的 Agent 项目骨架。它默认不替代律师意见，而是帮助用户整理事实、识别风险、检索本地法律资料，并生成带引用和待核验清单的答复。

## 功能

- 法律问题初筛：识别司法辖区、当事人角色、关键事实、时间线和缺失信息。
- 本地资料检索：从 `data/legal_sources` 读取 Markdown / TXT 资料，并把来源片段交给模型引用。
- 风险护栏：遇到紧急、诉讼时效、刑事、移民、税务、证券、家庭暴力等高风险事项时提示尽快联系持证律师或相关机构。
- 可审计输出：答复包含适用范围、依据摘要、引用来源、下一步问题和人工复核提示。

## 快速开始

```powershell
cd work/legal-agent
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
```

编辑 `.env`，填入 `OPENAI_API_KEY`。

运行：

```powershell
legal-agent ask "房东扣押押金，我应该如何准备沟通材料？" --jurisdiction "California, United States"
```

也可以直接用模块方式运行：

```powershell
python -m legal_agent.cli ask "合同里违约金过高怎么办？" --jurisdiction "China"
```

## 添加法律资料

把法律条文、公司合规模板、办案指引或 FAQ 放到：

```text
data/legal_sources/
```

支持 `.md` 和 `.txt` 文件。建议每个文件开头写清楚：

```markdown
# 标题
Jurisdiction: California, United States
Source URL: https://example.com/source
Last reviewed: 2026-06-02
```

## 输出边界

本项目生成的是法律信息辅助和工作草稿，不是法律意见。所有结论都应由持证律师或合规负责人结合最新法律、事实证据和适用司法辖区复核。

## 项目结构

```text
legal-agent/
  data/legal_sources/      本地法律资料
  src/legal_agent/         Agent、工具、配置和 CLI
  tests/                   不调用 OpenAI API 的单元测试
```

## 测试

```powershell
pytest
```


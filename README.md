# 招标合同审核 Skill + 轻量级 Python AI Agent

本仓库提供招标文件、合同与中标结果公示审核规则，并附带可独立运行的 Python CLI Agent。审核保留原有双路径：原始 PDF/DOCX 用于本地隐私、空白字段扫描；提取文本用于关键字段提取、合同内部错误检查及跨文件条款比较。

## 功能

- 独立运行：不依赖 Codex、豆包或其他工作目录；可以从任意目录调用 Python 程序。
- 双 API 自动分工：文本 API 负责条款分析与跨文件比对；多模态 API 仅在 PDF 页面文本提取很少时尝试识别扫描页。
- 本地隐私初筛：手机号、身份证号、QQ 号及疑似银行账号等候选信息在本地扫描；发给远程 AI 的文本会先尝试脱敏。
- 字段与证据复用：提取结果保存为 JSON，内部错误和跨文件比对复用字段结果。
- 断点续跑：通过 --resume 复用输入文件未变化时的分析结果。
- 输出：总报告 report.md、结构化结果 fields_and_findings.json、每份原始文件的初筛报告 scans/。

## 安装

建议使用 Python 3.10 或更新版本。

```bash
python -m venv .venv
# Windows
.venv/Scripts/activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

## 配置 API

复制 .env.example 为 .env，分别配置文本和多模态 API。两者都使用 OpenAI SDK 的 Chat Completions 兼容格式；可以使用官方 OpenAI 地址，也可以填写支持兼容接口的服务地址和模型名称。

```dotenv
TEXT_API_KEY=你的文本API密钥
TEXT_BASE_URL=https://api.openai.com/v1
TEXT_MODEL=你的文本模型名称

MULTIMODAL_API_KEY=你的多模态API密钥
MULTIMODAL_BASE_URL=https://api.openai.com/v1
MULTIMODAL_MODEL=支持图像输入的模型名称
```

密钥只放在本机 .env，不要提交到 Git。即使两个 API 来自同一家服务，也分别配置；如果暂时没有多模态模型，程序会在视觉提取失败时提示并继续处理可提取文本。

## 运行

审核单个文件：

```bash
python scripts/contract_agent.py "D:\\合同材料\\合同.pdf" --out "D:\\审核结果"
```

审核一个目录内所有 PDF/DOCX/TXT：

```bash
python scripts/contract_agent.py "D:\\合同材料" --out "D:\\审核结果"
```

断点续跑：

```bash
python scripts/contract_agent.py "D:\\合同材料" --out "D:\\审核结果" --resume
```

跳过本地隐私与空白初筛：

```bash
python scripts/contract_agent.py "D:\\合同材料" --no-scan
```

## 输出文件

- report.md：关键字段、合同内部错误、跨文件比对、隐私与空白初筛，以及最后一章“合同未填写及缺失信息清单”。
- fields_and_findings.json：结构化字段、证据、内部问题和跨文件比较结果。
- scans/：每份原始材料的本地隐私/空白初筛报告。
- .agent_state.json：断点续跑缓存；可能包含合同分析内容，请妥善保管，不要公开或提交。

## 现有规则

- SKILL.md：审核工作流、字段提取、内部逻辑检查和判定规则
- scripts/privacy_scan.py：原始 PDF/DOCX/TXT 隐私信息与空白字段初筛、带来源位置的 TXT 导出
- references/field-checklist.md：审核字段清单与风险分级
- references/report-template.md：审核报告模板

## 限制

- 扫描版 PDF 的视觉识别仅处理文本层较少的页面，最多识别前 30 页（可通过 VISION_MAX_PAGES 调整）；未配置多模态 API 时，扫描页可能无法识别。
- DOCX 使用段落/表格位置，不编造 PDF 页码。旧版 DOC 需先转为 DOCX 或 PDF。
- 程序不自动联网检索中标公示；需将公示材料一并放入输入目录。
- AI 输出不是法律意见。请人工复核金额、期限、付款、担保、违约责任、争议解决、主体冲突及所有高风险结论。
- 本地脱敏是常见模式的启发式处理，不能保证识别所有个人信息；提交远程 API 前仍应遵守组织的数据处理要求。

# 招标合同审核 Skill + 轻量级 Python AI Agent

本仓库提供招标文件、合同与中标结果公示审核规则，并附带可独立运行的 Python CLI Agent。审核保留原有双路径：原始 PDF/DOCX 用于本地隐私、空白字段扫描；提取文本用于关键字段提取、合同内部错误检查及跨文件条款比较。

## 功能

- 独立运行：不依赖 Codex、豆包或其他工作目录；可以从任意目录调用 Python 程序。
- 本地 Python 文本提取：使用 PyMuPDF 提取 PDF 文本、使用 python-docx 提取 DOCX 段落和表格；招标文件的合同条款章节由 Python 规则定位并单独导出，不调用 AI。
- 隐私初筛：文本层中的手机号、身份证号、QQ 号及疑似银行账号由本地 Python 规则识别；PDF 中含嵌入图片或文本层不足的页面可用多模态模型 OCR 后再扫描。多模态识别会将页面图像发送到配置的 API，可能仍有漏检。
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

复制 .env.example 为 .env，配置用于字段提取、合同内部检查和跨文件比对的文本 API。文档转文本和招标合同条款章节定位均在本地由 Python 完成，不调用 AI。

```dotenv
TEXT_API_KEY=你的文本API密钥
TEXT_BASE_URL=https://api.openai.com/v1
TEXT_MODEL=你的文本模型名称

# 图片 OCR / 隐私扫描（可选；未配置则只扫描文本层）
MULTIMODAL_API_KEY=你的多模态API密钥
MULTIMODAL_BASE_URL=https://api.openai.com/v1
MULTIMODAL_MODEL=支持图像输入的模型名称
VISION_MAX_PAGES=30
```

密钥只放在本机 .env，不要提交到 Git。

## 运行：招标文件、合同与公示三方比对

默认在当前工作目录下读取 `招标文件.pdf` 和 `合同.pdf`，并且必须提供公示 HTML URL 或本地 HTML 文件：

```bash
python scripts/contract_agent.py --notice "https://example.com/public-notice.html"
```

默认输出到当前目录的 `./output`。可指定本地文件路径或可直接下载的 HTTP(S) URL：

```bash
python scripts/contract_agent.py --tender "D:/项目/招标文件.pdf" --contract "D:/项目/合同.pdf" --notice "https://example.com/public-notice.html" --out "D:/审核结果"
```

如果招标文件和合同已在当前目录且文件名符合默认值，只需提供公示参数：

```bash
python scripts/contract_agent.py --notice "D:/项目/中标结果公示.html"
```

参数说明：
- `--tender`：本地 PDF/DOCX/TXT，或可直接下载的 HTTP(S) 文件 URL；默认 `./招标文件.pdf`。
- `--contract`：本地 PDF/DOCX/TXT，或可直接下载的 HTTP(S) 文件 URL；默认 `./合同.pdf`。
- `--notice`：必填。可访问的 HTML 公示网页 URL，或本地 HTML/HTM/TXT 文件。
- `--out`：输出目录，默认 `./output`。

断点续跑和跳过本地初筛：

```bash
python scripts/contract_agent.py --notice "https://example.com/public-notice.html" --resume
python scripts/contract_agent.py --notice "https://example.com/public-notice.html" --no-scan
```

公示网页通过普通 HTTP 请求提取可见文本；如果网页需要登录、触发反爬或依赖 JavaScript 动态渲染，程序可能无法完整读取。程序不会绕过访问控制。远程下载文件会暂存到输出目录下的 `.inputs/`。
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

- 招标合同条款定位和 PDF/DOCX/TXT 文本层提取使用本地 Python。对于含图片或文本层不足的 PDF 页面，若配置多模态 API，程序会对最多 `VISION_MAX_PAGES` 页进行图像 OCR，并将识别文本纳入隐私规则扫描；未配置时会提示图片隐私可能漏检。页面图像会发送给多模态服务商；如不能外传，应关闭该 API 并使用本地 OCR。
- DOCX 使用段落/表格位置，不编造 PDF 页码。旧版 DOC 需先转为 DOCX 或 PDF。
- 程序会读取 `--notice` 指定的公示 HTML 网页或本地 HTML/HTM/TXT 文件；需要登录、反爬或 JavaScript 渲染的页面可能无法读取。
- AI 输出不是法律意见。请人工复核金额、期限、付款、担保、违约责任、争议解决、主体冲突及所有高风险结论。
- 本地脱敏是常见模式的启发式处理，不能保证识别所有个人信息；提交远程 API 前仍应遵守组织的数据处理要求。

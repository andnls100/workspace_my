# workspace_my — 招标合同审核 Skill

本仓库提供招标文件、合同与中标结果公示审核技能。审核采用双路径：原始 PDF/DOCX 用于隐私、空白字段及版式扫描；转换后的 TXT 用于关键字段提取、合同内部错误检查及跨文件条款比较。

## 主要文件
- `SKILL.md`：审核工作流、字段提取、合同内部逻辑检查和判定规则
- `scripts/privacy_scan.py`：原始 PDF/DOCX 隐私信息、空白字段和可选 PDF 版式线初筛；支持导出带来源位置的 TXT
- `references/field-checklist.md`：审核字段清单与风险分级
- `references/report-template.md`：审核报告模板
- `tests/test_privacy_scan.py`：基础回归测试
- `MANIFEST.json`：版本和文件清单

## 安装依赖
```bash
pip install pypdf python-docx
```
可选 PDF 版式检测：`pip install pdfplumber`

## 建议流程
1. 在原始文件上运行隐私及空白初筛，保留 PDF/DOCX 格式证据。
2. 导出 TXT，供 AI 提取关键字段、检查合同内部错误和进行跨文件比较。
3. 复用字段与证据生成报告，只对冲突、提取失败和高风险项目追加复核。

## 示例
```bash
# 原始 DOCX：隐私及空白初筛
python scripts/privacy_scan.py "合同.docx" --mode all --out "合同初筛报告.md"

# 原始 PDF：隐私、空白及 PDF 版式横线初筛
python scripts/privacy_scan.py "合同.pdf" --mode all --layout --out "合同初筛报告.md"

# 导出带页码/位置标记的 TXT，供条款分析复用
python scripts/privacy_scan.py "招标文件.pdf" --export-text "招标文件.txt"
python scripts/privacy_scan.py "合同.docx" --export-text "合同.txt"

# 可选：招标文件字段级空白交叉提示
python scripts/privacy_scan.py "合同.docx" --mode blanks --tender "招标文件.pdf" --out "合同未填写及缺失信息清单.md"
```

PDF 导出会保留页码标记；DOCX 通常无法仅靠文档对象可靠还原实际分页，因此导出段落/表格位置，不能将这些位置冒充页码。扫描版 PDF 需要 OCR；旧版 DOC 需先转换为 DOCX 或 PDF。自动检测仅用于初筛，必须人工复核。

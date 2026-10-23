# workspace_my — 招标合同审核 Skill

本仓库提供招标文件、合同与中标结果公示一致性审核技能，包含合同隐私信息和未填写字段初筛。

## 主要文件
- `SKILL.md`：审核工作流和判定规则
- `scripts/privacy_scan.py`：隐私信息、空白字段和可选 PDF 版式线初筛
- `references/field-checklist.md`：审核字段清单与风险分级
- `references/report-template.md`：审核报告模板
- `tests/test_privacy_scan.py`：基础回归测试
- `MANIFEST.json`：版本和文件清单

## 安装依赖
```bash
pip install pypdf python-docx
```
可选 PDF 版式检测：`pip install pdfplumber`

## 示例
```bash
python scripts/privacy_scan.py "合同.docx" --mode blanks --out "合同未填写及缺失信息清单.md"
python scripts/privacy_scan.py "合同.pdf" --mode all --layout --out "合同初筛报告.md"
python scripts/privacy_scan.py "合同.docx" --mode blanks --tender "招标文件.pdf" --out "合同未填写及缺失信息清单.md"
```

自动检测仅用于初筛，所有空白和隐私候选项均须人工复核；扫描版 PDF 需要 OCR，旧版 DOC 需转换为 DOCX/PDF。
# DeepSeek 教师模型合同审查蒸馏流水线

本目录使用远程 DeepSeek API 生成候选训练数据，不下载教师模型权重。流水线会提取项目文档、调用教师模型、执行机械校验、生成质量报告，再构建 SFT 数据；**不会自动启动训练**。

## 安全注意

- 发送给远程 API 前，必须确认有权处理这些材料并完成脱敏。本项目的规则脱敏仅是初筛，不保证移除所有个人信息或商业秘密。
- 不要提交 `.env`、合同原文、API key、生成数据或人工标准答案。
- AI 输出是候选标注。金额、日期、证据和法律风险必须核验；程序通过不代表法律结论正确。

## 安装与配置

在仓库根目录执行：

```bash
pip install -r requirements.txt
```

将根目录 `.env.example` 复制为本地 `.env`，填写可用的 DeepSeek API 配置：

```dotenv
DEEPSEEK_API_KEY=你的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=你账号实际可用的模型名
DISTILL_INPUT_DIR=distill/data/input
DISTILL_OUTPUT_DIR=distill/data
```

先运行 `python -m distill.scripts.check_teacher_api` 验证模型列表和一次最小调用。

## 输入样本怎么放

每个独立项目建一个目录，尽可能放入招标文件、合同和中标公示：

```text
distill/data/input/
├── 项目001/
│   ├── 招标文件.pdf
│   ├── 合同.docx
│   └── 中标公示.pdf
├── 项目002/
│   ├── 招标文件.docx
│   ├── 合同.pdf
│   └── 中标公示.html
└── 项目003/
    ├── 招标文件.pdf
    ├── 合同.docx
    └── 中标公示.txt
```

支持 PDF、DOCX、TXT、HTML/HTM。扫描版 PDF 需先 OCR；文档内容应尽量可复制。项目目录名作为项目 ID，避免重复。不要把真实合同样本推送到 Git。

## 运行方式

### 完整流水线

先用一个项目验证配置与输出：

```bash
python -m distill.scripts.run_pipeline --limit 1 --skip-build
```

确认 API 输出、证据和质量报告后，再去掉限制或设置较大的 `--limit`：

```bash
python -m distill.scripts.run_pipeline
```

只有在已积累足够多的独立项目、且希望生成训练/验证文件时才运行完整构建步骤。

`--limit N` 只限制本次教师 API 调用数量；`--skip-api-check` 可跳过 API 连通性检查；`--skip-build` 只执行数据准备、生成、校验和报告，不拆分训练集，适合少量样本试跑。任务和生成结果按 task ID 断点续跑。

### 分步运行

```bash
python -m distill.scripts.prepare_data
python -m distill.scripts.generate_teacher_data --limit 1
python -m distill.scripts.validate_dataset
python -m distill.scripts.evaluate_dataset
python -m distill.scripts.build_dataset
```

## 输出文件

| 文件 | 内容 |
|---|---|
| `tasks.jsonl` | 从项目文档整理出的教师任务 |
| `generated.jsonl` | DeepSeek 返回的候选答案、输入和调用用量 |
| `validated.jsonl` | 通过基本结构及证据原文校验的候选样本 |
| `rejected.jsonl` | 未通过基本校验、需要修复或人工复核的样本 |
| `evaluation_report.json` | 样本数量、字段状态、风险等级、结构问题和证据原文匹配统计 |
| `train.jsonl`, `eval.jsonl` | 后续训练准备使用的 SFT 数据 |

## 自动分析能做什么、不能做什么

`evaluate_dataset.py` 自动汇总生成样本的结构问题、字段状态、风险等级，以及证据引文是否能在对应来源文本中找到。它还支持可选的人工标准答案对照。

**没有人工标准答案时，程序无法得出真实字段准确率、风险漏报率或误报率。** 引文原文匹配也不能证明该引文足以支持 AI 的结论。不要把机械校验通过率当作模型准确率。

### 可选：与人工标准答案对比

建立单独的 `gold.jsonl`，每行一个项目，格式示例：

```json
{"project_id":"项目001","answer":{"fields":[{"name":"合同金额","value":"100万元","status":"已提取"}],"findings":[{"category":"付款风险","severity":"高"}]}}
```

标准答案应由人工核验，且该项目应与模型训练集隔离。执行：

```bash
python -m distill.scripts.evaluate_dataset --input distill/data/generated.jsonl --gold distill/data/gold.jsonl --output distill/data/evaluation_report.json
```

报告会比较字段的 `name/value/status` 完全匹配率，并按 `category/severity` 统计风险项 precision、recall、F1。它们是有限的结构化指标，不等同于全面法律准确率。标准答案不要提交到 Git。

## 样本量与训练

先用 1–5 个已脱敏项目检查流程，再积累更多独立项目。可将 100 个经过人工核验的项目作为第一轮微调实验起点；是否足够取决于任务覆盖和验证结果，不是准确率保证。同一项目的切片不能当作独立项目，训练/验证/最终测试集应按项目划分。

训练前检查 `evaluation_report.json`，人工抽检通过与拒绝样本，确认没有伪造证据、金额或日期。项目数量太少时，`build_dataset` 可能无法形成有效的训练/验证拆分。

## 训练

学生模型与教师模型分开选择。完成数据审核后，再按目标硬件安装并配置 [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) 进行 LoRA/SFT。本目录目前不自动下载学生模型、不启动训练，也不自动修正低质量答案。

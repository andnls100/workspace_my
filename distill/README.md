# DeepSeek 教师模型合同审查蒸馏流水线

本目录将远程 DeepSeek API 作为教师模型，不下载教师权重；学生模型独立训练。流水线先生成、验证数据，再交给 LLaMA-Factory 训练。

## 安全注意
- 发送给远程 API 前必须取得数据授权，并确认已脱敏；本项目的规则脱敏只是初筛，不保证移除所有商业秘密或个人信息。
- 不要把 `.env`、合同原文、API key 或生成数据提交到 Git。
- 模型输出仅是候选标签；金额/日期/证据等必须核验，法律判断必须人工复核。

## 安装
```bash
pip install -r requirements.txt
```
仓库根目录已有 `openai`、`python-dotenv` 等依赖，无需单独安装 Distillery。训练时另行安装 [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory)。

将根目录 `.env.example` 中的设置复制到本地 `.env` 并配置：
```dotenv
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
# 以官方账户当前可用模型列表为准；不要仅凭模型别名推断实际路由
DEEPSEEK_MODEL=deepseek-v4-pro
DISTILL_INPUT_DIR=distill/data/input
DISTILL_OUTPUT_DIR=distill/data
```

## 输入格式
把每个项目的已提取文本放在 `distill/data/input/<项目ID>/`，支持 PDF、DOCX、TXT、HTML/HTM。脚本尽可能保留页码（PDF）和来源文件名。建议每个项目包含招标文件、合同和中标公示。原始材料目录默认不提交 Git。

## 运行
```bash
python -m distill.scripts.check_teacher_api
python -m distill.scripts.prepare_data
python -m distill.scripts.generate_teacher_data
python -m distill.scripts.validate_dataset
python -m distill.scripts.build_dataset
# 一键执行上述步骤（先检查 API；失败即停止）
python -m distill.scripts.run_pipeline --limit 3
```
可通过 `--limit N` 限制 API 样本数。生成任务和结果采用 JSONL，已完成任务可断点续跑。

先用 `--limit 1` 做小规模连通性试跑，确认输出后再增加数量。流水线不会自动启动模型训练；必须先人工抽检训练样本。

输出：
- `distill/data/tasks.jsonl`: 教师任务
- `distill/data/generated.jsonl`: 教师候选答案
- `distill/data/validated.jsonl`: 通过基本程序校验的候选样本
- `distill/data/rejected.jsonl`: 拒绝/需复核样本
- `distill/data/train.jsonl`, `eval.jsonl`: LLaMA-Factory 可转换使用的数据

## 训练
先阅读 LLaMA-Factory 当前版本文档，下载适合目标硬件的学生模型，并单独配置训练。这里不自动启动训练，避免未经检查的数据直接用于微调。完成后用独立项目集评估字段准确率、证据命中率和高风险漏检率。

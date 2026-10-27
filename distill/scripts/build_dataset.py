"""Build conservative chat-style JSONL from validated candidate answers."""
from __future__ import annotations
import argparse, hashlib
from pathlib import Path
from .common import DATA, read_jsonl, write_jsonl

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default=str(DATA/"validated.jsonl"))
    ap.add_argument("--eval-ratio",type=float,default=0.15)
    args=ap.parse_args()
    if not 0.05 <= args.eval_ratio <= 0.4:
        ap.error("--eval-ratio 必须在 0.05 到 0.4 之间")
    rows=read_jsonl(Path(args.input))
    train=[]; ev=[]
    for row in rows:
        if row.get("validation_status") not in {"candidate_pass","validated"}:
            continue
        # 以项目 ID 稳定划分，避免同一项目泄漏到训练集和测试集。
        project=str(row.get("project_id") or row.get("task_id") or "")
        bucket=int(hashlib.sha256(project.encode()).hexdigest()[:8],16)/0xffffffff
        record={"messages":[
            {"role":"system","content":"你是招标合同审核助手。只引用可见证据；不确定时明确标记，公示未披露不得推断一致。"},
            {"role":"user","content":"请按合同审查规范输出字段、证据与跨文件差异。项目材料见输入任务。"},
            {"role":"assistant","content":__import__("json").dumps(row["answer"],ensure_ascii=False)}
        ]}
        (ev if bucket < args.eval_ratio else train).append(record)
    write_jsonl(DATA/"train.jsonl",train)
    write_jsonl(DATA/"eval.jsonl",ev)
    print(f"训练样本 {len(train)}，验证样本 {len(ev)}。注意：训练输入目前是通用任务指令；正式训练前应把原始材料输入与答案配对，不能只训练答案。")
    return 0 if train and ev else 1

if __name__ == "__main__":
    raise SystemExit(main())

"""Build chat-style JSONL from validated input/answer pairs."""
from __future__ import annotations
import argparse, hashlib, json
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
        payload=row.get("input")
        answer=row.get("answer")
        if not isinstance(payload,dict) or not payload.get("documents") or not isinstance(answer,dict):
            print(f"[跳过] {row.get('task_id')}: 缺少原始输入或答案")
            continue
        project=str(row.get("project_id") or row.get("task_id") or "")
        bucket=int(hashlib.sha256(project.encode()).hexdigest()[:8],16)/0xffffffff
        # 训练输入必须包含真实任务材料；不能只训练答案格式。
        user_content=json.dumps(payload,ensure_ascii=False)
        record={"messages":[
            {"role":"system","content":"你是招标合同审核助手。只引用可见证据；不确定时明确标记，公示未披露不得推断一致。"},
            {"role":"user","content":user_content},
            {"role":"assistant","content":json.dumps(answer,ensure_ascii=False)}
        ]}
        (ev if bucket < args.eval_ratio else train).append(record)
    write_jsonl(DATA/"train.jsonl",train)
    write_jsonl(DATA/"eval.jsonl",ev)
    print(f"训练样本 {len(train)}，验证样本 {len(ev)}。")
    if len(train)<2 or len(ev)<1:
        print("样本/项目数不足以可靠划分训练与验证集；请补充多个独立项目，避免同一项目泄漏。")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

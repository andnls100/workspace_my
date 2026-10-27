"""Conservative mechanical validation; this is not a legal correctness proof."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from .common import DATA, read_jsonl, write_jsonl

REQUIRED_TOP={"fields","findings","limitations"}
def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default=str(DATA/"generated.jsonl"))
    ap.add_argument("--valid",default=str(DATA/"validated.jsonl"))
    ap.add_argument("--rejected",default=str(DATA/"rejected.jsonl"))
    args=ap.parse_args()
    good=[]; bad=[]
    for row in read_jsonl(Path(args.input)):
        issues=[]
        answer=row.get("answer")
        if not isinstance(answer,dict): issues.append("answer_not_object")
        else:
            missing=REQUIRED_TOP-set(answer)
            if missing: issues.append("missing_top_keys:"+",".join(sorted(missing)))
            if not isinstance(answer.get("fields",[]),list): issues.append("fields_not_list")
            if not isinstance(answer.get("findings",[]),list): issues.append("findings_not_list")
            # 检查证据引用是否出现在同一任务输入材料中（精确短引；不保证语义正确）。
            task_id=row.get("task_id")
            # generated record 不含原始材料；此处做格式/引文存在性初筛，进一步核对需保留 source_text_index。
            for group in ("fields","findings"):
                for item in answer.get(group,[]) if isinstance(answer.get(group,[]),list) else []:
                    if not isinstance(item,dict):
                        issues.append(f"{group}_item_not_object"); continue
                    ev=item.get("evidence",[])
                    if not isinstance(ev,list): issues.append(f"{group}_evidence_not_list"); continue
                    for e in ev:
                        if not isinstance(e,dict) or not e.get("source") or not e.get("quote"):
                            issues.append(f"{group}_evidence_missing_source_or_quote")
                        elif len(str(e.get("quote","")).strip())<4:
                            issues.append(f"{group}_quote_too_short")
                    if group=="fields" and not item.get("status"):
                        issues.append("field_missing_status")
        row["validation_issues"]=sorted(set(issues))
        row["validation_status"]="candidate_pass" if not issues else "rejected"
        (good if not issues else bad).append(row)
    write_jsonl(Path(args.valid),good)
    write_jsonl(Path(args.rejected),bad)
    print(f"结构初筛通过 {len(good)}，拒绝 {len(bad)}。注意：此脚本不验证引文是否真实出现在原文中，也不证明法律结论正确；需另做原文比对和人工抽检。")
    return 0 if good else 1

if __name__ == "__main__":
    raise SystemExit(main())

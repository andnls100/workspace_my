"""Conservative mechanical validation; this is not a legal correctness proof."""
from __future__ import annotations
import argparse
from pathlib import Path
from .common import DATA, read_jsonl, write_jsonl

REQUIRED_TOP={"fields","findings","limitations"}

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default=str(DATA/"generated.jsonl"))
    ap.add_argument("--valid",default=str(DATA/"validated.jsonl"))
    ap.add_argument("--rejected",default=str(DATA/"rejected.jsonl"))
    ap.add_argument("--require-evidence-in-source",action="store_true",default=True)
    args=ap.parse_args()
    good=[]; bad=[]
    for row in read_jsonl(Path(args.input)):
        issues=[]
        answer=row.get("answer")
        if not isinstance(answer,dict):
            issues.append("answer_not_object")
        else:
            missing=REQUIRED_TOP-set(answer)
            if missing: issues.append("missing_top_keys:"+",".join(sorted(missing)))
            for group in ("fields","findings"):
                items=answer.get(group,[])
                if not isinstance(items,list):
                    issues.append(f"{group}_not_list"); continue
                for item in items:
                    if not isinstance(item,dict):
                        issues.append(f"{group}_item_not_object"); continue
                    if group=="fields" and not item.get("status"):
                        issues.append("field_missing_status")
                    evidence=item.get("evidence",[])
                    if not isinstance(evidence,list):
                        issues.append(f"{group}_evidence_not_list"); continue
                    for ev in evidence:
                        if not isinstance(ev,dict) or not ev.get("source") or not ev.get("quote"):
                            issues.append(f"{group}_evidence_missing_source_or_quote"); continue
                        quote=str(ev.get("quote","")).strip()
                        if len(quote)<4: issues.append(f"{group}_quote_too_short")
                        if args.require_evidence_in_source:
                            source_docs=(row.get("input") or {}).get("documents",[])
                            candidates=[d for d in source_docs if str(d.get("source",""))==str(ev.get("source",""))]
                            # Same source can occur in multiple chunks/pages; any exact substring match is accepted.
                            if not any(quote in str(d.get("text","")) for d in candidates):
                                issues.append("evidence_quote_not_found:"+str(ev.get("source")))
        row["validation_issues"]=sorted(set(issues))
        row["validation_status"]="candidate_pass" if not issues else "rejected"
        (good if not issues else bad).append(row)
    write_jsonl(Path(args.valid),good)
    write_jsonl(Path(args.rejected),bad)
    print(f"结构与精确引文初筛通过 {len(good)}，拒绝 {len(bad)}。")
    print("注意：精确引文匹配不能证明语义判断或法律结论正确；仍需抽检，并核对金额、日期、单位和高风险问题。")
    return 0 if good else 1

if __name__ == "__main__":
    raise SystemExit(main())

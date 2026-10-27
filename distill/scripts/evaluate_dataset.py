"""Produce an auditable quality report for generated contract-review samples.

Mechanical screening is not a proof of legal correctness. For accuracy metrics,
pass a manually reviewed gold JSONL via --gold.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .common import DATA, read_jsonl


def norm(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().casefold().split())


def field_map(answer: Any) -> dict[str, tuple[str, str]]:
    if not isinstance(answer, dict) or not isinstance(answer.get("fields"), list):
        return {}
    return {
        norm(item["name"]): (norm(item.get("value")), norm(item.get("status")))
        for item in answer["fields"]
        if isinstance(item, dict) and item.get("name")
    }


def finding_keys(answer: Any) -> set[tuple[str, str]]:
    if not isinstance(answer, dict) or not isinstance(answer.get("findings"), list):
        return set()
    return {
        (norm(item.get("category")), norm(item.get("severity")))
        for item in answer["findings"]
        if isinstance(item, dict) and item.get("category")
    }


def score_gold(rows: list[dict[str, Any]], gold_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gold_by_project = {str(r["project_id"]): r for r in gold_rows if r.get("project_id") is not None}
    compared, field_total, field_correct = 0, 0, 0
    tp = fp = fn = 0
    missing_gold = []
    for row in rows:
        pid = str(row.get("project_id"))
        gold = gold_by_project.get(pid)
        if gold is None:
            missing_gold.append(pid)
            continue
        compared += 1
        predicted_fields = field_map(row.get("answer"))
        expected_fields = field_map(gold.get("answer", gold))
        for name, expected in expected_fields.items():
            field_total += 1
            field_correct += predicted_fields.get(name) == expected
        predicted_findings = finding_keys(row.get("answer"))
        expected_findings = finding_keys(gold.get("answer", gold))
        tp += len(predicted_findings & expected_findings)
        fp += len(predicted_findings - expected_findings)
        fn += len(expected_findings - predicted_findings)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else (0.0 if precision == 0 or recall == 0 else None)
    return {
        "gold_projects_compared": compared,
        "projects_without_gold": sorted(set(missing_gold)),
        "field_exact_match_accuracy": field_correct / field_total if field_total else None,
        "field_items_scored": field_total,
        "finding_category_severity_precision": precision,
        "finding_category_severity_recall": recall,
        "finding_category_severity_f1": f1,
        "finding_counts": {"true_positive": tp, "false_positive": fp, "false_negative": fn},
        "gold_note": "字段按 name 比较 value/status 完全一致；风险按 category/severity 比较。不是全面法律准确率。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="评估合同审查教师输出并生成 JSON 报告")
    parser.add_argument("--input", default=str(DATA / "generated.jsonl"))
    parser.add_argument("--gold", help="可选：人工核验标准答案 JSONL，每行包含 project_id 和 answer")
    parser.add_argument("--output", default=str(DATA / "evaluation_report.json"))
    args = parser.parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"找不到输入文件：{input_path}")
        return 2
    rows = read_jsonl(input_path)
    statuses = Counter(str(r.get("validation_status", "unknown")) for r in rows)
    field_statuses, finding_severities, schema_issues = Counter(), Counter(), Counter()
    quote_checks = {"with_evidence": 0, "exact_quote_found": 0, "quote_missing_or_not_found": 0}
    projects = set()
    for row in rows:
        if row.get("project_id") is not None:
            projects.add(str(row["project_id"]))
        answer = row.get("answer")
        if not isinstance(answer, dict):
            schema_issues["answer_not_object"] += 1
            continue
        for key in ("fields", "findings", "limitations"):
            if key not in answer:
                schema_issues[f"missing_{key}"] += 1
        documents = (row.get("input") or {}).get("documents", [])
        if not isinstance(documents, list):
            documents = []
        fields = answer.get("fields", [])
        if isinstance(fields, list):
            for field in fields:
                if not isinstance(field, dict):
                    schema_issues["field_not_object"] += 1
                    continue
                field_statuses[str(field.get("status", "missing"))] += 1
                evidence = field.get("evidence", [])
                if not isinstance(evidence, list):
                    schema_issues["field_evidence_not_list"] += 1
                    continue
                for ev in evidence:
                    if not isinstance(ev, dict) or not ev.get("quote"):
                        quote_checks["quote_missing_or_not_found"] += 1
                        continue
                    quote_checks["with_evidence"] += 1
                    src, quote = str(ev.get("source", "")), str(ev["quote"]).strip()
                    found = any(
                        isinstance(doc, dict) and str(doc.get("source", "")) == src and quote in str(doc.get("text", ""))
                        for doc in documents
                    )
                    quote_checks["exact_quote_found" if found else "quote_missing_or_not_found"] += 1
        else:
            schema_issues["fields_not_list"] += 1
        findings = answer.get("findings", [])
        if isinstance(findings, list):
            for finding in findings:
                if isinstance(finding, dict):
                    finding_severities[str(finding.get("severity", "missing"))] += 1
                else:
                    schema_issues["finding_not_object"] += 1
        else:
            schema_issues["findings_not_list"] += 1
    report: dict[str, Any] = {
        "input_file": str(input_path),
        "sample_count": len(rows),
        "unique_project_count": len(projects),
        "validation_status_counts": dict(statuses),
        "field_status_counts": dict(field_statuses),
        "finding_severity_counts": dict(finding_severities),
        "schema_issue_counts": dict(schema_issues),
        "evidence_quote_checks": {
            **quote_checks,
            "exact_match_rate": quote_checks["exact_quote_found"] / quote_checks["with_evidence"] if quote_checks["with_evidence"] else None,
            "note": "按来源名和原文子串匹配；匹配成功不代表证据足以支持结论。",
        },
        "limitations": [
            "没有人工标准答案时，无法计算真实字段准确率、风险漏报率或误报率。",
            "本报告是数据质量筛查，不构成法律意见或模型能力认证。",
            "评估集应按独立项目与训练集隔离，避免数据泄漏。",
        ],
    }
    if args.gold:
        report["gold_comparison"] = score_gold(rows, read_jsonl(Path(args.gold)))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"评估报告：{output}")
    print(f"样本 {len(rows)}，独立项目 {len(projects)}，字段状态分布 {dict(field_statuses)}")
    print("机械引文匹配不等于结论正确；没有人工标准答案时，不应把统计当作模型准确率。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

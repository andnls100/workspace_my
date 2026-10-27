"""Run the data-preparation, teacher-generation, validation and reporting pipeline."""
from __future__ import annotations
import argparse, subprocess, sys
from .common import ROOT

STEPS = [
    ("prepare_data", ["-m", "distill.scripts.prepare_data"]),
    ("generate_teacher_data", ["-m", "distill.scripts.generate_teacher_data"]),
    ("validate_dataset", ["-m", "distill.scripts.validate_dataset"]),
    ("evaluate_dataset", ["-m", "distill.scripts.evaluate_dataset"]),
    ("build_dataset", ["-m", "distill.scripts.build_dataset"]),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare, generate, validate, report and build contract-review distillation data.")
    ap.add_argument("--limit", type=int, default=0, help="本次最多请求多少个教师任务")
    ap.add_argument("--skip-api-check", action="store_true", help="跳过 API 连通性检查")
    args = ap.parse_args()
    if args.limit < 0:
        ap.error("--limit 必须大于或等于 0")
    if not args.skip_api_check:
        cmd = [sys.executable, "-m", "distill.scripts.check_teacher_api"]
        result = subprocess.run(cmd, cwd=ROOT)
        if result.returncode:
            return result.returncode
    for name, module_args in STEPS:
        cmd = [sys.executable, *module_args]
        if name == "generate_teacher_data" and args.limit > 0:
            cmd.extend(["--limit", str(args.limit)])
        print("\n>>> " + " ".join(cmd), flush=True)
        result = subprocess.run(cmd, cwd=ROOT)
        if result.returncode:
            print(f"[停止] {name} 退出码 {result.returncode}；修复问题后可重跑，已生成样本会断点续跑。", file=sys.stderr)
            return result.returncode
    print("流水线完成。请查看 distill/data/evaluation_report.json，并人工抽检样本；报告不证明法律结论正确。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3

import importlib
import json
from pathlib import Path
import sys


TARGETS = {
    # Level 1
    "level1_01_request_validation": "study.level1.examples.01_request_validation",
    "level1_02_response_handling": "study.level1.examples.02_response_handling",
    "level1_03_unified_response": "study.level1.examples.03_unified_response",
    "level1_04_error_handling": "study.level1.examples.04_error_handling",
    "level1_05_restful_api": "study.level1.examples.05_restful_api",
    # Level 2
    "level2_01_di_basics": "study.level2.examples.01_di_basics",
    "level2_02_class_vs_function_deps": "study.level2.examples.02_class_vs_function_deps",
    "level2_03_dependency_lifecycle": "study.level2.examples.03_dependency_lifecycle",
    "level2_04_service_layer": "study.level2.examples.04_service_layer",
    "level2_05_best_practices": "study.level2.examples.05_best_practices",
    # Level 3
    "level3_01_database_basics": "study.level3.examples.01_database_basics",
    "level3_02_sqlalchemy_basics": "study.level3.examples.02_sqlalchemy_basics",
    "level3_03_repository_pattern": "study.level3.examples.03_repository_pattern",
    "level3_04_transactions": "study.level3.examples.04_transactions",
    "level3_05_migrations": "study.level3.examples.05_migrations",
    # Level 4
    "level4_01_redis_cache": "study.level4.examples.01_redis_cache",
    "level4_02_message_queue": "study.level4.examples.02_message_queue",
    "level4_03_external_api": "study.level4.examples.03_external_api",
    "level4_04_monitoring": "study.level4.examples.04_monitoring",
    "level4_05_resilience": "study.level4.examples.05_resilience",
    # Level 5
    "level5_main": "study.level5.examples.main",
}


def main() -> None:
    # 允许从任意目录执行脚本
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    out_dir = Path("study/testing/apifox/openapi")
    out_dir.mkdir(parents=True, exist_ok=True)

    exported = []
    failed = []

    for name, module_path in TARGETS.items():
        try:
            module = importlib.import_module(module_path)
            app = getattr(module, "app")
            schema = app.openapi()

            out_path = out_dir / f"{name}.openapi.json"
            out_path.write_text(
                json.dumps(schema, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            exported.append((name, str(out_path)))
        except Exception as exc:  # pragma: no cover - helper script
            failed.append((name, module_path, str(exc)))

    print(f"Exported: {len(exported)}")
    for name, path in exported:
        print(f"  OK   {name} -> {path}")

    print(f"Failed: {len(failed)}")
    for name, module_path, err in failed:
        print(f"  FAIL {name} ({module_path}) -> {err}")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

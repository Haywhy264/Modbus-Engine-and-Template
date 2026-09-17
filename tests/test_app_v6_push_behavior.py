from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "template" / "app_V6.py"
SPEC = importlib.util.spec_from_file_location("app_v6_under_test", MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(module)
merge_csv_payloads = module.merge_csv_payloads


def test_merge_csv_payloads_keeps_all_pulled_files():
    current = {
        "Plant_Tag.csv": "Index,Name\n1,A\n",
        "Plant_Node.csv": "Index,Name\n1,B\n",
    }
    pulled = {
        "Plant_Tag.csv": "Index,Name\n1,override\n",
        "Plant_Node.csv": "Index,Name\n1,B\n",
        "Extra_Custom.csv": "Name,Value\nfoo,bar\n",
    }

    merged = merge_csv_payloads(current, pulled)

    assert merged["Plant_Tag.csv"] == "Index,Name\n1,override\n"
    assert merged["Extra_Custom.csv"] == "Name,Value\nfoo,bar\n"
    assert set(merged) == {"Plant_Tag.csv", "Plant_Node.csv", "Extra_Custom.csv"}

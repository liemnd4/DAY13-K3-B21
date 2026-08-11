from __future__ import annotations

import json
from pathlib import Path

from app import logging_config


def test_structlog_scrubs_top_level_and_nested_pii_before_jsonl_persistence(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    logging_config.configure_logging()

    logging_config.get_logger().info(
        "security_test",
        service="api",
        correlation_id="req-security",
        custom_email="abc@gmail.com",
        payload={
            "nested": {
                "phone": "0901234567",
                "cards": ["4111111111111111"],
            }
        },
    )

    raw = log_path.read_text(encoding="utf-8")
    record = json.loads(raw)

    assert "abc@gmail.com" not in raw
    assert "0901234567" not in raw
    assert "4111111111111111" not in raw
    assert record["custom_email"] == "[REDACTED_EMAIL]"
    assert record["payload"]["nested"]["phone"] == "[REDACTED_PHONE_VN]"
    assert record["payload"]["nested"]["cards"] == ["[REDACTED_CREDIT_CARD]"]

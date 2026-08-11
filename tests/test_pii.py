from app.pii import scrub_text, scrub_value


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_all_configured_identity_and_payment_patterns() -> None:
    assert scrub_text("CCCD 001203012345") == "CCCD [REDACTED_CCCD]"
    assert scrub_text("Card 4111111111111111") == "Card [REDACTED_CREDIT_CARD]"
    assert scrub_text("Passport B1234567") == "Passport [REDACTED_PASSPORT]"


def test_scrub_value_recurses_without_changing_structure_or_non_strings() -> None:
    value = {
        "user@example.com": "user@example.com",
        "nested": {
            "phone": "0901234567",
            "items": [
                "001203012345",
                {"card": "4111111111111111"},
            ],
        },
        "tuple_data": ("B1234567", 123, True),
    }

    assert scrub_value(value) == {
        "user@example.com": "[REDACTED_EMAIL]",
        "nested": {
            "phone": "[REDACTED_PHONE_VN]",
            "items": [
                "[REDACTED_CCCD]",
                {"card": "[REDACTED_CREDIT_CARD]"},
            ],
        },
        "tuple_data": ("[REDACTED_PASSPORT]", 123, True),
    }

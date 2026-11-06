from app.security.redaction import redact


def test_redaction_removes_common_secrets():
    text = 'Authorization: Bearer abc.def password=hunter2 "totp_secret":"ABC123" cookie=session'
    cleaned = redact(text)
    for secret in ("abc.def", "hunter2", "ABC123", "session"):
        assert secret not in cleaned


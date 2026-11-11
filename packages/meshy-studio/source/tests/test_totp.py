from app.security.totp import totp_now


def test_totp_rfc6238_vector():
    assert totp_now("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ", at=59, digits=8) == "94287082"


def test_totp_accepts_spaces_lowercase():
    assert totp_now("gezd gnbv gy3t qojq gezd gnbv gy3t qojq", at=59, digits=8) == "94287082"

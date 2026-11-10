from app.mail.purelymail import ImapMailbox


class Conn:
    def login(self, *a): pass
    def select(self, *a, **k): pass
    def search(self, *a): return "OK", [b"1 2"]
    def logout(self): pass
    def fetch(self, uid, spec):
        if uid == b"1":
            return "OK", [b")"]  # no body: used to crash with 'int' has no attribute 'decode'
        raw = b"From: Meshy <noreply@meshy.ai>\r\nSubject: 123456 is your Meshy verification code\r\n\r\nhi"
        return "OK", [(b"2 (RFC822 {10}", raw), b")"]


def test_fetch_without_body_is_skipped():
    messages = ImapMailbox("a@b.c", "x", imap_factory=lambda h, p: Conn()).recent()
    assert [m.subject for m in messages] == ["123456 is your Meshy verification code"]

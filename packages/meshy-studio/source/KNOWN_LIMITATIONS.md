# Known limitations

- **Not production-ready.** It meets the engineering criteria listed in TEST_REPORT.md, but the restructured engine has not been run live
  against Meshy, concurrency > 1 has never run with real browsers, and Purelymail IMAP has never run against a real mailbox.
- **Meshy integration is browser automation of the Meshy web app**, not an official API. Meshy may change its UI, tours and popups at any
  time (the code uses `data-testid` where possible and saves a screenshot to `output/diagnostics/` on failure) and its terms may not allow
  automated use of the web app; this was not verified. An official-API engine needs a paid API key and was not built.
- **Free credit is not renewable by this app.** It never creates Meshy accounts (that would circumvent the one-free-account
  limit). When no account has the 30 credits a model needs, jobs are Paused until an account recovers or you choose another one.
- **Accounts bought from a reseller** can be blocked by their domain's 2-Step Verification policy on a new browser profile ("Couldn't sign you
  in"). The app marks them "Needs verification" and skips them; it does not try to bypass it. A TOTP secret in the account line helps (only
  tested with a fake page). Browser sessions cannot be moved between PCs (Chrome encrypts cookies per Windows user).
- **Emergency Stop and Cancel are local.** A Meshy task that was already submitted keeps running on Meshy's servers and may still spend
  credits; there is no safe remote cancel. Such a job is never re-submitted automatically, and Retry is blocked until server reconciliation exists.
- **Purelymail:** IMAP (`imap.purelymail.com:993`) and management API defaults match Purelymail's published documentation/OpenAPI.
  Creation, duplicate prevention, timeout reconciliation and credential safety have automated coverage, but live API creation still needs
  the owner's API token and has not yet been executed. Mailbox clean-up is not implemented.
- **Credentials:** stored in Windows Credential Manager (protected by the Windows user, not a separate DPAPI file). `accounts.txt` in a team
  package contains plaintext passwords until the first start imports it (the renamed `accounts.imported.txt` still contains them: delete it).
- **Concurrency** is limited to 3 and each parallel job needs its own account; parallel Chrome windows are heavy.
- **FBX needs Blender** (installed, or a ~340 MB portable copy is downloaded on first use; that download is untested). FBX has no
  metallic-roughness slot (the PNG is still saved).
- **The one-file exe** takes 5-30 s to start the first time (unpacking ~98 MB; antivirus scans make it slower) and needs Windows 10/11 x64.
  Drag & drop from Explorer was tested only in-process, not with a real OLE drag.
- Legacy one-off scripts live in `tools/legacy/` and are not maintained.

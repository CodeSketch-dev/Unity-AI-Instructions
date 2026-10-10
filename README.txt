HUONG DAN DONG BO UNITY AI INSTRUCTIONS
======================================

Repository chinh:
https://github.com/CodeSketch-dev/Unity-AI-Instructions.git

Muc dich:
- AGENTS.md trong repository la nguon chuan duy nhat.
- Codex su dung: %USERPROFILE%\.codex\AGENTS.md
- Claude su dung: %USERPROFILE%\.claude\CLAUDE.md
- sync.ps1 se sao luu file cu neu noi dung thay doi, sau do dong bo ban moi.

QUY TAC QUAN TRONG
------------------

1. Chi sua AGENTS.md trong repository Unity-AI-Instructions.
2. Khong sua truc tiep ban trong .codex hoac .claude, vi lan sync tiep theo se ghi de.
3. Khong dua token, API key, keystore, password hoac credential vao repository.
4. Sau khi sync, mo chat/session moi de Codex va Claude nap lai instructions.
5. Chay tung lenh PowerShell rieng biet va nhan Enter sau moi lenh.


PHAN A - MAY CHINH: LAY BAN MOI NHAT VA DONG BO
================================================

Dung khi AGENTS.md tren GitHub da thay doi va may nay can cap nhat.

1. Mo PowerShell.

2. Di den repository:

   Set-Location "C:\Unity\GitProject\Unity-AI-Instructions"

3. Chay script. Script tu dong git pull --ff-only truoc khi dong bo:

   powershell -NoProfile -ExecutionPolicy Bypass -File ".\sync.ps1"

4. Mo chat/session Codex va Claude moi.


PHAN B - MAY CHINH: SUA AGENTS.MD VA PUSH LEN GITHUB
====================================================

Dung khi muon thay doi house style hoac them instruction moi.

1. Mo PowerShell va di den repository:

   Set-Location "C:\Unity\GitProject\Unity-AI-Instructions"

2. Lay ban moi nhat truoc khi sua:

   git pull --ff-only

3. Mo file de sua:

   notepad ".\AGENTS.md"

4. Sau khi luu, xem thay doi:

   git diff -- AGENTS.md

5. Kiem tra loi whitespace:

   git diff --check

6. Dong bo ban vua sua vao Codex va Claude ma khong pull lai:

   powershell -NoProfile -ExecutionPolicy Bypass -File ".\sync.ps1" -SkipPull

7. Stage file:

   git add -- AGENTS.md

8. Kiem tra noi dung da stage:

   git diff --cached --stat
   git diff --cached --check

9. Tao commit. Thay noi dung message cho phu hop:

   git commit -m "Update shared agent instructions"

10. Push len GitHub:

   git push

11. Mo chat/session Codex va Claude moi.


PHAN C - MAY KHAC DA CLONE REPOSITORY
=====================================

1. Mo PowerShell.

2. Di den noi repository da duoc clone. Vi du:

   Set-Location "C:\Unity\GitProject\Unity-AI-Instructions"

3. Pull va dong bo bang mot lenh:

   powershell -NoProfile -ExecutionPolicy Bypass -File ".\sync.ps1"

4. Mo chat/session Codex va Claude moi.


PHAN D - MAY MOI CHUA CLONE REPOSITORY
======================================

1. Dam bao Git da duoc cai va da dang nhap GitHub de doc private repository.

2. Tao folder chua repository neu can:

   New-Item -ItemType Directory -Path "C:\Unity\GitProject" -Force

3. Di den folder:

   Set-Location "C:\Unity\GitProject"

4. Clone repository:

   git clone "https://github.com/CodeSketch-dev/Unity-AI-Instructions.git"

5. Di vao repository:

   Set-Location ".\Unity-AI-Instructions"

6. Chay script dong bo:

   powershell -NoProfile -ExecutionPolicy Bypass -File ".\sync.ps1"

7. Mo chat/session Codex va Claude moi.

Luu y: Repository co the nam o duong dan khac. sync.ps1 dung vi tri cua chinh no
lam repository root, nen khong bat buoc phai clone vao C:\Unity\GitProject.


PHAN E - KIEM TRA CAC FILE DA DONG BO GIONG NHAU
================================================

Chay trong PowerShell:

   Get-FileHash `
       ".\AGENTS.md", `
       "$env:USERPROFILE\.codex\AGENTS.md", `
       "$env:USERPROFILE\.claude\CLAUDE.md"

Ba gia tri Hash phai giong nhau.

Kiem tra trang thai Git:

   git status --short

Neu khong co output thi working tree dang sach.


PHAN F - XU LY MOT SO LOI THUONG GAP
====================================

1. Loi "running scripts is disabled on this system"

Khong can thay doi Execution Policy toan he thong. Chay:

   powershell -NoProfile -ExecutionPolicy Bypass -File ".\sync.ps1"

2. Loi git pull do co thay doi local chua commit

Kiem tra:

   git status --short
   git diff

Khong reset hoac xoa thay doi. Hay commit thay doi hop le, hoac sao luu va xu ly
xung dot truoc khi pull.

3. Script bao da backup file Claude hoac Codex

Day la hanh vi binh thuong. Backup nam cung folder voi file dich va co dang:

   AGENTS.md.backup-yyyyMMdd-HHmmss
   CLAUDE.md.backup-yyyyMMdd-HHmmss

4. Muon phuc hoi backup

Vi du cho Claude:

   Copy-Item `
       -LiteralPath "$env:USERPROFILE\.claude\CLAUDE.md.backup-yyyyMMdd-HHmmss" `
       -Destination "$env:USERPROFILE\.claude\CLAUDE.md" `
       -Force

Thay yyyyMMdd-HHmmss bang timestamp that cua file backup.


QUY TRINH NGAN GON HANG NGAY
============================

Chi pull va dong bo:

   Set-Location "C:\Unity\GitProject\Unity-AI-Instructions"
   powershell -NoProfile -ExecutionPolicy Bypass -File ".\sync.ps1"

Sua va push:

   Set-Location "C:\Unity\GitProject\Unity-AI-Instructions"
   git pull --ff-only
   notepad ".\AGENTS.md"
   git diff --check
   powershell -NoProfile -ExecutionPolicy Bypass -File ".\sync.ps1" -SkipPull
   git add -- AGENTS.md
   git diff --cached --check
   git commit -m "Update shared agent instructions"
   git push


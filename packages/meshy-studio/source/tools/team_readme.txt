Meshy AI Studio - team build

Requirements: Windows 10/11 and an internet connection. No Python or pip needed: all libraries are inside
MeshyAIStudio.exe. Google Chrome is used if installed; otherwise the app downloads a browser itself.

1. Put this folder anywhere and run MeshyAIStudio.exe. The first start is slow: the exe unpacks itself, then
   downloads the model decoder (and a browser if Chrome is missing). The status line shows progress.
2. The accounts in accounts.txt are imported automatically on the first start (passwords go to the Windows
   credential store of THIS machine; the file is then renamed accounts.imported.txt - delete it afterwards).
3. Drop an image into the window: it is queued and processed automatically (login, generate, texture,
   remesh 10K, download). Finished GLB files are in the Export folder.
4. Claude Code / Codex: register the MCP server, see packages\meshy-studio\README.md in the
   Unity-AI-Instructions repo (skill meshy-model-gen).

accounts.txt / accounts.imported.txt contain passwords: do not share them outside the team.

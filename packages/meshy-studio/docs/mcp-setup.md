# Meshy MCP setup

Register once (run from anywhere):

```
claude mcp add meshy -- python D:\GitProject\Meshy\tools\meshy_mcp_server.py
codex mcp add meshy -- python D:\GitProject\Meshy\tools\meshy_mcp_server.py
```

Tools: `generate_model(image_path, note?)`, `job_status(job_id)`, `list_jobs`, `list_accounts`, `import_accounts(file_path)`, `list_exports`.
`generate_model` queues the job and starts `python -m app.runner` if no runner/app is active (the app window also acts as the runner; only one may hold `data/runner.lock`).

Account file lines: `email|password` or `email|password|recovery_email|totp_secret`. Secrets go to the Windows credential store, never to MCP output.

## Result flow
`generate_model` -> `job_status(job_id)` until `status` is `Completed`; `result_path` is the textured ~10K-triangle GLB in `Export/`
(verified: 9,365-9,536 triangles, 3 textures). Account failures rotate automatically; quota-limited accounts rest 24 h.

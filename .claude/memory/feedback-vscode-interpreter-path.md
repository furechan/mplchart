---
name: feedback-vscode-interpreter-path
description: fix the VS Code "interpreter path could not be resolved" warning via a workspace defaultInterpreterPath override
metadata:
  type: feedback
---

# VS Code interpreter path warning

If the Python extension shows "Default interpreter path '.venv/bin/python' could not be resolved" but `.venv/bin/python` exists, the warning often comes from a global relative default interpreter path.

Set a workspace override in `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
}
```

This stabilizes resolution for the current repo and avoids cross-workspace ambiguity.

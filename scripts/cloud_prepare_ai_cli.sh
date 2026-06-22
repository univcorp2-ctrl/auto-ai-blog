#!/usr/bin/env bash
set -euo pipefail

echo "== Cloud AI CLI preparation =="

echo "Python: $(python --version)"
echo "Node: $(node --version 2>/dev/null || echo 'node not installed')"

if [[ -n "${CLOUD_AI_CLI_INSTALL_COMMANDS:-}" ]]; then
  echo "Running CLOUD_AI_CLI_INSTALL_COMMANDS..."
  bash -lc "${CLOUD_AI_CLI_INSTALL_COMMANDS}"
else
  echo "CLOUD_AI_CLI_INSTALL_COMMANDS is empty. Skipping automatic CLI installation."
fi

found_any="false"
for cli in claude gemini codex; do
  if command -v "$cli" >/dev/null 2>&1; then
    echo "FOUND: $cli => $(command -v "$cli")"
    found_any="true"
  else
    echo "MISSING: $cli"
  fi
done

if [[ "$found_any" != "true" ]]; then
  echo "No AI CLI was found. Cloud generation will skip because draft generation cannot run."
  echo "Set CLOUD_AI_CLI_INSTALL_COMMANDS and the required CLI authentication secrets for your cloud runner."
fi

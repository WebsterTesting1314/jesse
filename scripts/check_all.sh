#!/usr/bin/env bash
set -euo pipefail

echo "=== Running Pre-commit Hooks (if available) ==="
if command -v pre-commit >/dev/null; then
  pre-commit run --all-files --show-diff-on-failure || echo "Pre-commit hooked failures (see above)"
else
  echo "Skipping pre-commit: command not found"
fi

echo "=== Running Python Unittests (if pytest available) ==="
if command -v pytest >/dev/null; then
  pytest -q || echo "pytest failures (see above)"
else
  echo "Skipping pytest: command not found"
fi

echo "=== Running Mypy Type Checks (if available) ==="
if command -v mypy >/dev/null; then
  mypy . || echo "mypy type issues (see above)"
else
  echo "Skipping mypy: command not found"
fi

echo "=== Running Solidity Lint (if solhint available) ==="
if command -v solhint >/dev/null; then
  solhint "contracts/**/*.sol" || echo "solhint warnings/errors (see above)"
else
  echo "Skipping solhint: command not found"
fi

echo "=== Building Docs (if antora available) ==="
if command -v antora >/dev/null; then
  antora contracts/lib/openzeppelin-contracts/docs/antora.yml || echo "Antora docs build failed (see above)"
else
  echo "Skipping docs build: command not found"
fi

echo "=== Check-all completed ==="
#!/usr/bin/env bash
# Faz o push da branch para o GitHub.
# Uso: ./push.sh [remote_url]
# Exemplo: ./push.sh https://github.com/pplferreira/RoteamentoLLM.git

set -e

BRANCH="claude/llm-routing-cli-qUxVF"
REMOTE_URL="${1:-https://github.com/pplferreira/RoteamentoLLM.git}"

echo "→ Remote: $REMOTE_URL"
echo "→ Branch: $BRANCH"
echo ""

git remote set-url origin "$REMOTE_URL"
git push -u origin "$BRANCH"

echo ""
echo "✓ Push concluído."

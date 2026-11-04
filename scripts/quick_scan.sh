#!/usr/bin/env bash
# security-audit 快速扫描脚本 —— 只读静态分析，绝不执行目标项目的任何代码
# 用法: quick_scan.sh <目标目录>
set -u

TARGET="${1:?用法: quick_scan.sh <目标目录>}"
[ -d "$TARGET" ] || { echo "错误: $TARGET 不是目录"; exit 1; }

# 排除依赖目录与版本库，只看项目自身代码
EXCLUDE_DIRS=(.git node_modules venv .venv env site-packages vendor dist build __pycache__ .tox target)
GREP_EXCLUDE=()
PRUNE=( '(' )
for d in "${EXCLUDE_DIRS[@]}"; do
  GREP_EXCLUDE+=(--exclude-dir="$d")
  PRUNE+=(-name "$d" -o)
done
unset 'PRUNE[-1]'
PRUNE+=( ')' -prune -o )

ffind() { find "$TARGET" "${PRUNE[@]}" "$@"; }
fgrep() { grep -r "${GREP_EXCLUDE[@]}" "$@"; }

section() { printf '\n===== %s =====\n' "$1"; }

section "1. 依赖清单与锁文件"
ffind -maxdepth 3 -type f \( \
  -name 'package.json' -o -name 'package-lock.json' -o -name 'yarn.lock' -o -name 'pnpm-lock.yaml' -o \
  -name 'requirements*.txt' -o -name 'setup.py' -o -name 'pyproject.toml' -o -name 'Pipfile*' -o -name 'poetry.lock' -o \
  -name 'go.mod' -o -name 'Cargo.toml' -o -name 'Cargo.lock' -o -name 'Gemfile*' -o -name 'pom.xml' -o -name 'composer.json' \
  \) -print 2>/dev/null

section "2. 安装/构建钩子"
fgrep -InE '"(pre|post)?install"\s*:' "$TARGET" --include='package.json' 2>/dev/null | head -20
fgrep -InE 'cmdclass|setup_requires' "$TARGET" --include='setup.py' --include='pyproject.toml' 2>/dev/null | head -20
fgrep -InE '(curl|wget)[^|"]*\|\s*(sudo\s+)?(bash|sh|python)' "$TARGET" \
  --include='Makefile' --include='Dockerfile*' --include='*.sh' --include='*.yml' --include='*.yaml' 2>/dev/null | head -20

section "3. CI 配置"
ffind -maxdepth 4 \( -path '*/.github/workflows/*' -o -name '.gitlab-ci.yml' -o -name '.circleci' \) -print 2>/dev/null | head -20

section "4. AI 攻击面文件"
ffind -maxdepth 4 \( \
  -iname 'AGENTS.md' -o -iname 'CLAUDE.md' -o -iname '.cursorrules' -o -iname '.windsurfrules' -o \
  -path '*/.cursor/*' -o -path '*/.continue/*' -o -name 'copilot-instructions.md' -o \
  -iname '*mcp*.json' -o -name '*.ipynb' -o -iname '*.pkl' -o -iname '*.ckpt' \
  \) -print 2>/dev/null | head -40
echo '--- 注入关键词 ---'
fgrep -InEi 'ignore (all )?(previous|prior) instructions|disregard.{0,20}instructions|as an ai (assistant|model)|new system prompt' \
  "$TARGET" --include='*.md' --include='*.txt' --include='*.py' --include='*.js' --include='*.ts' 2>/dev/null | head -20
echo '--- 零宽字符 ---'
fgrep -IlP '[\x{200B}-\x{200D}\x{FEFF}]' "$TARGET" 2>/dev/null | head -20

section "5. 无源码二进制"
ffind -type f \( -name '*.so' -o -name '*.dll' -o -name '*.exe' -o -name '*.bin' -o -name '*.dylib' \) -print 2>/dev/null | head -30

section "6. 混淆与可疑执行"
fgrep -InE '(base64|b64decode|fromhex|zlib\.decompress).{0,80}(exec|eval|system|popen|subprocess)' \
  "$TARGET" --include='*.py' --include='*.js' --include='*.ts' 2>/dev/null | head -20
fgrep -InE '\b(exec|eval)\s*\(' "$TARGET" --include='*.py' --include='*.js' --include='*.ts' 2>/dev/null | head -20
echo '--- 超长行(>800字符) ---'
fgrep -IlE '.{800,}' "$TARGET" --include='*.py' --include='*.js' --include='*.ts' 2>/dev/null | head -10

section "7. 敏感路径访问"
fgrep -InE '\.ssh|\.aws/|\.env["'"'"']|cookies|Login Data|\.metamask|wallet\.dat' \
  "$TARGET" --include='*.py' --include='*.js' --include='*.ts' 2>/dev/null | head -20

section "8. 硬编码 IP（排除内网/文档段）"
fgrep -InoE '([0-9]{1,3}\.){3}[0-9]{1,3}' "$TARGET" \
  --include='*.py' --include='*.js' --include='*.ts' --include='*.go' --include='*.json' 2>/dev/null \
  | grep -vE '(127\.|0\.0\.0\.0|255\.|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)' | head -20

section "9. 疑似硬编码密钥"
fgrep -InE 'AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|xox[bap]-[A-Za-z0-9-]+' \
  "$TARGET" 2>/dev/null | head -20

section "10. 可用扫描工具检测"
for t in osv-scanner trivy pip-audit gitleaks trufflehog semgrep bandit guarddog; do
  if command -v "$t" >/dev/null 2>&1; then echo "[可用] $t"; else echo "[缺失] $t"; fi
done

printf '\n快速扫描完成。命中项均需人工核实，grep 命中 ≠ 恶意。\n'

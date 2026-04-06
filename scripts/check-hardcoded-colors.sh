#!/bin/bash
# Phase 14: Hardcoded hex color audit script
# Scans frontend/src and frontend/index.html for ALL hex color values
# After excluding whitelisted files, any remaining matches are FAIL
set -e
cd "$(dirname "$0")/.."

echo "Scanning for hardcoded hex colors..."

# Whitelisted files (allowed to contain hex colors)
WHITELIST_FILES=(
  "theme/index.ts"            # buildTheme seed colors
  "theme/semanticColors.ts"   # static fallback constants
  "theme/chartColors.ts"      # dark-mode approximate constants
  "theme/useCardStatusColors.ts" # card status color definitions
  "theme/ThemeModeProvider.tsx"  # dark-mode body bg #1F1F1F (matches index.html FOUC)
  "MainLayout.module.css"     # Sider logo #fff (D-16)
)

# Build grep exclude pattern
EXCLUDE_PATTERN=$(printf "|%s" "${WHITELIST_FILES[@]}")
EXCLUDE_PATTERN="${EXCLUDE_PATTERN:1}"  # strip leading |

# Scan .tsx/.ts/.jsx/.js files for hex colors in quotes
VIOLATIONS_TSX=$(grep -rEn "'#[0-9a-fA-F]{3,8}'|\"#[0-9a-fA-F]{3,8}\"" \
  frontend/src/ \
  --include="*.tsx" --include="*.ts" --include="*.jsx" --include="*.js" \
  --exclude-dir=node_modules --exclude-dir=dist 2>/dev/null \
  | grep -vE "($EXCLUDE_PATTERN)" || true)

# Scan index.html for hex colors (exclude FOUC script #1F1F1F)
VIOLATIONS_HTML=$(grep -En "'#[0-9a-fA-F]{3,8}'|\"#[0-9a-fA-F]{3,8}\"" \
  frontend/index.html 2>/dev/null \
  | grep -vE "#1F1F1F" || true)

# Scan CSS module files (exclude whitelisted)
VIOLATIONS_CSS=$(grep -rEn "#[0-9a-fA-F]{3,8}" \
  frontend/src/ \
  --include="*.css" --include="*.module.css" \
  --exclude-dir=node_modules --exclude-dir=dist 2>/dev/null \
  | grep -vE "($EXCLUDE_PATTERN)" || true)

ALL_VIOLATIONS=""
[ -n "$VIOLATIONS_TSX" ] && ALL_VIOLATIONS="$ALL_VIOLATIONS\n--- TSX/TS ---\n$VIOLATIONS_TSX"
[ -n "$VIOLATIONS_HTML" ] && ALL_VIOLATIONS="$ALL_VIOLATIONS\n--- HTML ---\n$VIOLATIONS_HTML"
[ -n "$VIOLATIONS_CSS" ] && ALL_VIOLATIONS="$ALL_VIOLATIONS\n--- CSS ---\n$VIOLATIONS_CSS"

if [ -n "$ALL_VIOLATIONS" ]; then
  echo "FAIL: Hardcoded hex colors found outside whitelist:"
  echo -e "$ALL_VIOLATIONS"
  exit 1
fi

echo "PASS: No hardcoded hex colors outside whitelist."

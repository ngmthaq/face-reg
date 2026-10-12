#!/usr/bin/env bash
# scan-secrets.sh — Scans a file or git diff for hardcoded secrets.
#
# Usage:
#   Scan specific files:     ./scan-secrets.sh [file ...]
#   Scan staged changes:     git diff --cached | ./scan-secrets.sh --diff
#   Scan unstaged changes:   git diff | ./scan-secrets.sh --diff
#   Scan last commit:        git show | ./scan-secrets.sh --diff

set -euo pipefail

FOUND=0

# ── Patterns: "NAME|severity|regex" ──────────────────────────────────────────
PATTERNS=(
  # Cloud provider credentials
  "AWS_ACCESS_KEY|critical|AKIA[0-9A-Z]{16}"
  "AWS_SECRET_KEY|critical|aws_secret_access_key[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9/+=]{40}"
  "GCP_SERVICE_ACCOUNT|critical|\"type\"[[:space:]]*:[[:space:]]*\"service_account\""
  "GCP_API_KEY|high|AIza[0-9A-Za-z_-]{35}"
  "AZURE_CLIENT_SECRET|critical|azure[-_]?client[-_]?secret[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9_~.-]{34,}"

  # GitHub tokens
  "GITHUB_PAT|critical|ghp_[0-9A-Za-z]{36}"
  "GITHUB_OAUTH|critical|gho_[0-9A-Za-z]{36}"
  "GITHUB_APP_TOKEN|critical|ghs_[0-9A-Za-z]{36}"
  "GITHUB_REFRESH_TOKEN|critical|ghr_[0-9A-Za-z]{36}"
  "GITHUB_FINE_GRAINED_PAT|critical|github_pat_[0-9A-Za-z_]{82}"

  # Private keys
  "PRIVATE_KEY|critical|-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"
  "PGP_PRIVATE_BLOCK|critical|-----BEGIN PGP PRIVATE KEY BLOCK-----"

  # Generic secrets
  "GENERIC_SECRET|high|(secret|token|password|passwd|pwd|api[-_]?key|apikey|access[-_]?key|auth[-_]?token|client[-_]?secret)[[:space:]]*[:=][[:space:]]*['\"][A-Za-z0-9_/+=~.-]{8,}['\"]"
  "CONNECTION_STRING|high|(mongodb(\+srv)?|postgres(ql)?|mysql|redis|amqp|mssql)://[^[:space:]'\"]{10,}"
  "BEARER_TOKEN|medium|[Bb]earer[[:space:]]+[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}"

  # Messaging and SaaS
  "SLACK_TOKEN|high|xox[baprs]-[0-9]{10,}-[0-9A-Za-z-]+"
  "SLACK_WEBHOOK|high|https://hooks\.slack\.com/services/T[0-9A-Z]{8,}/B[0-9A-Z]{8,}/[0-9A-Za-z]{24}"
  "DISCORD_TOKEN|high|[MN][A-Za-z0-9]{23,}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}"
  "TWILIO_API_KEY|high|SK[0-9a-fA-F]{32}"
  "SENDGRID_API_KEY|high|SG\.[0-9A-Za-z_-]{22}\.[0-9A-Za-z_-]{43}"
  "STRIPE_SECRET_KEY|critical|sk_live_[0-9A-Za-z]{24,}"
  "STRIPE_RESTRICTED_KEY|high|rk_live_[0-9A-Za-z]{24,}"

  # npm tokens
  "NPM_TOKEN|high|npm_[0-9A-Za-z]{36}"

  # JWT
  "JWT_TOKEN|medium|eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"

  # Internal IPs with ports
  "INTERNAL_IP_PORT|medium|(^|[^.0-9])(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}):[0-9]{2,5}([^0-9]|$)"
)

# ── Helpers ───────────────────────────────────────────────────────────────────
severity_color() {
  case "$1" in
    critical) printf '\033[0;31m' ;;  # red
    high)     printf '\033[0;33m' ;;  # yellow
    medium)   printf '\033[0;36m' ;;  # cyan
    *)        printf '\033[0m'    ;;
  esac
}
RESET='\033[0m'

report() {
  local name="$1" severity="$2" location="$3" match="$4"
  local color
  color=$(severity_color "$severity")
  printf "${color}[%s]${RESET} %s\n  Location : %s\n  Match    : %s\n  Fix      : Remove hardcoded value; use env vars or a secrets manager.\n\n" \
    "$(echo "$severity" | tr '[:lower:]' '[:upper:]')" "$name" "$location" "$match"
  FOUND=$((FOUND + 1))
}

# ── Scan a single line ────────────────────────────────────────────────────────
scan_line() {
  local line="$1" location="$2"
  for entry in "${PATTERNS[@]}"; do
    IFS='|' read -r name severity regex <<< "$entry"
    if echo "$line" | grep -qE "$regex" 2>/dev/null; then
      local match
      match=$(echo "$line" | grep -oE "$regex" | head -1)
      report "$name" "$severity" "$location" "$match"
    fi
  done
}

# ── Scan mode: files ──────────────────────────────────────────────────────────
scan_files() {
  for file in "$@"; do
    [[ -f "$file" ]] || { echo "Skipping (not a file): $file"; continue; }
    local lineno=0
    while IFS= read -r line; do
      lineno=$((lineno + 1))
      scan_line "$line" "$file:$lineno"
    done < "$file"
  done
}

# ── Scan mode: git diff (stdin) ───────────────────────────────────────────────
scan_diff() {
  local current_file="<unknown>" lineno=0
  while IFS= read -r line; do
    # Track current file from diff headers: +++ b/path/to/file
    if [[ "$line" =~ ^\+\+\+\ b/(.+)$ ]]; then
      current_file="${BASH_REMATCH[1]}"
      lineno=0
      continue
    fi
    # Track line numbers from hunk headers: @@ -a,b +c,d @@
    if [[ "$line" =~ ^@@\ [^+]*\+([0-9]+) ]]; then
      lineno=$(( BASH_REMATCH[1] - 1 ))
      continue
    fi
    # Only scan added lines
    if [[ "$line" =~ ^\+ && ! "$line" =~ ^\+\+\+ ]]; then
      lineno=$((lineno + 1))
      scan_line "${line:1}" "$current_file:$lineno"
    elif [[ ! "$line" =~ ^- ]]; then
      lineno=$((lineno + 1))
    fi
  done
}

# ── Entry point ───────────────────────────────────────────────────────────────
main() {
  if [[ "${1:-}" == "--diff" ]]; then
    echo "Scanning diff (stdin) for secrets..."
    scan_diff
  elif [[ $# -gt 0 ]]; then
    echo "Scanning files for secrets: $*"
    scan_files "$@"
  else
    echo "Usage:"
    echo "  Scan files:          $0 [file ...]"
    echo "  Scan staged diff:    git diff --cached | $0 --diff"
    echo "  Scan unstaged diff:  git diff | $0 --diff"
    echo "  Scan last commit:    git show | $0 --diff"
    exit 1
  fi

  if [[ $FOUND -eq 0 ]]; then
    echo "✓ No secrets detected."
    exit 0
  else
    echo "✖ $FOUND potential secret(s) found. Review and remediate before merging."
    exit 1
  fi
}

main "$@"
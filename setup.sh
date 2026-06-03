#!/bin/bash
# CC-Status 一键配置脚本
# 用法: bash setup.sh

set -e

CLAUDE_DIR="$HOME/.claude"
SCRIPTS_DIR="$CLAUDE_DIR/scripts"
STATUS_DIR="$CLAUDE_DIR/status"
SETTINGS="$CLAUDE_DIR/settings.json"

echo "=== CC-Status 配置 ==="

# 1. 创建目录
mkdir -p "$SCRIPTS_DIR" "$STATUS_DIR"

# 2. 写入状态脚本
cat > "$SCRIPTS_DIR/set-status.sh" << 'EOF'
#!/bin/bash
STATE_FILE="$HOME/.claude/status/${CLAUDE_CODE_SESSION_ID:0:8}.state"
NEW_STATE="$1"
if [ "$NEW_STATE" = "yellow" ] && [ -f "$STATE_FILE" ]; then
  if grep -q '"state":"red"' "$STATE_FILE" 2>/dev/null; then
    exit 0
  fi
fi
mkdir -p "$HOME/.claude/status"
printf '{"state":"%s","name":"%s"}' "$NEW_STATE" "$(basename "$PWD")" > "$STATE_FILE"
EOF
chmod +x "$SCRIPTS_DIR/set-status.sh"
echo "[OK] 状态脚本: $SCRIPTS_DIR/set-status.sh"

# 3. 写入 hooks 到 settings.json
if [ ! -f "$SETTINGS" ]; then
  echo '{"hooks":{}}' > "$SETTINGS"
fi

python3 - << 'PYEOF'
import json, os

settings_path = os.path.expanduser("~/.claude/settings.json")
with open(settings_path, "r", encoding="utf-8") as f:
    data = json.load(f)

hook_cmd = 'bash "$HOME/.claude/scripts/set-status.sh"'

hooks = {
    "PreToolUse": [{"matcher": "", "hooks": [{"type": "command", "command": f"{hook_cmd} yellow"}]}],
    "Stop": [{"matcher": "", "hooks": [{"type": "command", "command": f"{hook_cmd} green"}]}],
    "StopFailure": [{"matcher": "", "hooks": [{"type": "command", "command": f"{hook_cmd} green"}]}],
    "Notification": [{"matcher": "", "hooks": [{"type": "command", "command": f"{hook_cmd} red"}]}],
    "PermissionRequest": [{"matcher": "", "hooks": [{"type": "command", "command": f"{hook_cmd} red"}]}],
    "UserPromptSubmit": [{"matcher": "", "hooks": [{"type": "command", "command": f"{hook_cmd} yellow"}]}],
}

data["hooks"] = hooks

with open(settings_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("[OK] Hooks 已写入:", settings_path)
PYEOF

echo ""
echo "=== 配置完成 ==="
echo "1. 重启 Claude Code"
echo "2. 运行 CC-Status.exe"
echo ""

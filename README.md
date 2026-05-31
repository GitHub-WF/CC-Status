# CC-Status v1.0.0

Claude Code 桌面状态显示器，实时显示多个会话的工作状态。

## 功能

- 红 / 黄 / 绿三色状态指示
- 多会话同时显示，自动识别会话名
- 双击名称可重命名
- 拖拽排序
- 窗口置顶
- 60 秒无活动自动清除

## 安装

### Windows

直接运行 `win/CC-Status.exe`。

### Mac

```bash
cd mac
bash build.sh
./CC-Status
```

Mac 需要先安装 Python3：`brew install python3`

## 使用

1. 启动 CC-Status，悬浮窗出现在屏幕右下角
2. 打开 Claude Code 会话，面板自动显示对应状态
3. 左键拖拽面板标题栏移动位置
4. 左键拖拽色块上下排列顺序
5. 双击名称可重命名
6. 右键菜单：置顶 / 清除全部 / 关闭
7. 每个色块右侧 × 按钮关闭单个会话

## 状态说明

| 颜色 | 含义 |
|------|------|
| 红色 | 需要确认（权限请求 / 通知） |
| 黄色 | 思考中（工具调用 / 处理中） |
| 绿色 | 空闲（等待输入） |

## 依赖

Claude Code 需要配置以下 hooks（写入 `~/.claude/settings.json`）：

```json
{
  "hooks": {
    "PreToolUse": [{ "matcher": "", "hooks": [{ "type": "command", "command": "mkdir -p \"$HOME/.claude/status\" && echo '{\"state\":\"yellow\"}' > \"$HOME/.claude/status/${CLAUDE_CODE_SESSION_ID:0:8}.state\"" }] }],
    "Stop": [{ "matcher": "", "hooks": [{ "type": "command", "command": "mkdir -p \"$HOME/.claude/status\" && echo '{\"state\":\"green\"}' > \"$HOME/.claude/status/${CLAUDE_CODE_SESSION_ID:0:8}.state\"" }] }],
    "Notification": [{ "matcher": "", "hooks": [{ "type": "command", "command": "mkdir -p \"$HOME/.claude/status\" && echo '{\"state\":\"red\"}' > \"$HOME/.claude/status/${CLAUDE_CODE_SESSION_ID:0:8}.state\"" }] }],
    "UserPromptSubmit": [{ "matcher": "", "hooks": [{ "type": "command", "command": "mkdir -p \"$HOME/.claude/status\" && echo '{\"state\":\"yellow\"}' > \"$HOME/.claude/status/${CLAUDE_CODE_SESSION_ID:0:8}.state\"" }] }]
  }
}
```

## 文件说明

```
CC-Status/
├── win/
│   └── CC-Status.exe        # Windows 可执行文件
├── mac/
│   ├── claude_status.py     # Python 源码
│   └── build.sh             # Mac 构建脚本
└── README.md
```

## 数据目录

- `~/.claude/status/*.state` — 会话状态文件
- `~/.claude/status/names.json` — 自定义会话名

## License

MIT

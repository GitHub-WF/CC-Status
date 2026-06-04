# CC-Status v1.1.0

Claude Code 桌面状态显示器，实时显示多个会话的工作状态。

## 功能

- 红 / 黄 / 绿三色状态指示，实时同步 Claude Code 状态
- 多会话同时显示，自动识别会话名
- 系统托盘图标，彩色圆点显示会话状态
- × 最小化到托盘，托盘右键退出
- 双击名称可重命名
- 拖拽排序
- 窗口置顶
- 每个会话独立关闭按钮

## 安装

### Windows

1. 运行一键配置脚本（只需一次）：

```bash
bash setup.sh
```

2. 重启 VSCode

3. 运行 `win/CC-Status.exe`

### Mac

```bash
bash setup.sh
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
6. 每个色块右侧 × 按钮移除单个会话
7. 标题栏 ─ 或 × 最小化到系统托盘
8. 托盘图标右键：显示面板 / 退出
9. 面板右键菜单：置顶 / 清除全部 / 退出

## 状态说明

| 颜色 | 含义 |
|------|------|
| 红色 | 需要确认（权限请求 / 通知） |
| 黄色 | 思考中（工具调用 / 处理中） |
| 绿色 | 空闲（等待输入） |

## 文件说明

```
CC-Status/
├── win/
│   └── CC-Status.exe          # Windows 可执行文件
├── mac/
│   ├── claude_status.py       # Python 源码
│   └── build.sh               # Mac 构建脚本
├── setup.sh                   # 一键配置 hooks 脚本
└── README.md
```

## 数据目录

- `~/.claude/status/*.state` — 会话状态文件
- `~/.claude/status/names.json` — 自定义会话名
- `~/.claude/scripts/set-status.sh` — 状态切换脚本

## License

MIT

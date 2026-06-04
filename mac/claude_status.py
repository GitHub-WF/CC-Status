"""
CC-Status v1.1.0 - Claude Code 状态显示器
系统托盘 + 悬浮面板，×最小化到托盘，右键退出
"""
import os
import sys
import json
import time
import glob
import threading
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pystray

STATUS_DIR = os.path.join(Path.home(), ".claude", "status")
PROJECTS_DIR = os.path.join(Path.home(), ".claude", "projects")
NAMES_FILE = os.path.join(STATUS_DIR, "names.json")

BG = "#202020"
CARD_BG = "#2d2d2d"
CARD_HOVER = "#383838"
HEADER_BG = "#1e1e1e"
BORDER = "#404040"
TEXT_PRI = "#ffffff"
TEXT_SEC = "#c8c8c8"
TEXT_MUTED = "#8a8a8a"
ACCENT = "#60cdff"

STATUS_INFO = {
    "red":    ("需要确认", "#f25c54"),
    "yellow": ("思考中...", "#f9a825"),
    "green":  ("空闲",     "#4caf50"),
}

_title_cache = {}
_title_cache_time = 0
_custom_names = {}


def load_custom_names():
    global _custom_names
    try:
        if os.path.exists(NAMES_FILE):
            with open(NAMES_FILE, "r", encoding="utf-8") as f:
                _custom_names = json.load(f)
    except:
        _custom_names = {}


def save_custom_names():
    try:
        os.makedirs(os.path.dirname(NAMES_FILE), exist_ok=True)
        with open(NAMES_FILE, "w", encoding="utf-8") as f:
            json.dump(_custom_names, f, ensure_ascii=False, indent=2)
    except:
        pass


def scan_titles():
    global _title_cache, _title_cache_time
    now = time.time()
    if now - _title_cache_time < 10:
        return _title_cache
    titles = {}
    for proj_dir in glob.glob(os.path.join(PROJECTS_DIR, "*")):
        if not os.path.isdir(proj_dir):
            continue
        for jsonl in glob.glob(os.path.join(proj_dir, "*.jsonl")):
            sid_full = os.path.basename(jsonl).replace(".jsonl", "")
            prefix = sid_full[:8]
            try:
                with open(jsonl, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            if data.get("type") == "ai-title" and data.get("aiTitle"):
                                titles[prefix] = data["aiTitle"]
                                break
                        except json.JSONDecodeError:
                            continue
            except:
                pass
    _title_cache = titles
    _title_cache_time = now
    return titles


def read_sessions():
    sessions = []
    titles = scan_titles()
    load_custom_names()
    for fp in glob.glob(os.path.join(STATUS_DIR, "*.state")):
        try:
            sid = os.path.basename(fp).replace(".state", "")
            mtime = os.path.getmtime(fp)
            with open(fp, "r", encoding="utf-8") as f:
                raw = f.read().strip()
            try:
                data = json.loads(raw)
                state = data.get("state", "green").lower()
            except:
                state = raw.lower()
            info = STATUS_INFO.get(state, STATUS_INFO["green"])
            name = _custom_names.get(sid, titles.get(sid, sid))
            sessions.append({"id": sid, "name": name, "mtime": mtime,
                             "text": info[0], "color": info[1], "state": state})
        except:
            pass
    sessions.sort(key=lambda s: s["mtime"], reverse=True)
    return sessions


def create_tray_icon(sessions):
    """Create a 32x32 icon with spaced colored dots"""
    S = 32
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([0, 0, S - 1, S - 1], radius=6,
                           fill="#2d2d2d", outline="#555555", width=1)

    if not sessions:
        draw.ellipse([9, 9, 23, 23], fill="#4caf50")
        return img

    n = min(len(sessions), 4)
    colors = [s["color"] for s in sessions[:n]]

    if n == 1:
        draw.ellipse([8, 8, 24, 24], fill=colors[0])
    elif n == 2:
        draw.ellipse([3, 9, 15, 21], fill=colors[0])
        draw.ellipse([17, 9, 29, 21], fill=colors[1])
    elif n == 3:
        draw.ellipse([3, 3, 13, 13], fill=colors[0])
        draw.ellipse([19, 3, 29, 13], fill=colors[1])
        draw.ellipse([11, 19, 21, 29], fill=colors[2])
    else:
        draw.ellipse([3, 3, 13, 13], fill=colors[0])
        draw.ellipse([19, 3, 29, 13], fill=colors[1])
        draw.ellipse([3, 19, 13, 29], fill=colors[2])
        draw.ellipse([19, 19, 29, 29], fill=colors[3])

    return img


class SessionCard:
    def __init__(self, parent, session, panel):
        self.panel = panel
        self.sid = session["id"]
        self.color = session["color"]

        self.frame = tk.Frame(parent, bg=CARD_BG, cursor="arrow")
        self.frame.pack(fill="x", padx=10, pady=(0, 4))

        self.inner = tk.Frame(self.frame, bg=CARD_BG)
        self.inner.pack(fill="x", padx=10, pady=7)

        self.dot_cv = tk.Canvas(self.inner, width=12, height=12,
                                bg=CARD_BG, highlightthickness=0)
        self.dot_cv.pack(side="left", padx=(0, 8))
        self.dot_id = self.dot_cv.create_oval(1, 1, 11, 11, fill=session["color"], outline="")

        self.name_lbl = tk.Label(self.inner, text=session["name"][:22],
                                 fg=TEXT_PRI, bg=CARD_BG,
                                 font=("Segoe UI Variable", 10))
        self.name_lbl.pack(side="left")

        self.state_lbl = tk.Label(self.inner, text=session["text"],
                                  fg=TEXT_MUTED, bg=CARD_BG,
                                  font=("Segoe UI Variable", 9))
        self.state_lbl.pack(side="right", padx=(4, 0))

        self.close_lbl = tk.Label(self.inner, text="✕", fg=TEXT_MUTED, bg=CARD_BG,
                                  font=("Segoe UI Variable", 8), cursor="hand2")
        self.close_lbl.pack(side="right", padx=(0, 8))
        self.close_lbl.bind("<Enter>", lambda e: self.close_lbl.config(fg=TEXT_SEC))
        self.close_lbl.bind("<Leave>", lambda e: self.close_lbl.config(fg=TEXT_MUTED))
        self.close_lbl.bind("<Button-1>", lambda e, s=self.sid: panel._remove_session(s))

        for w in (self.frame, self.inner, self.name_lbl, self.dot_cv, self.state_lbl):
            w.bind("<Enter>", self._enter)
            w.bind("<Leave>", self._leave)

    def _enter(self, e):
        for w in (self.frame, self.inner, self.name_lbl, self.dot_cv, self.state_lbl, self.close_lbl):
            w.config(bg=CARD_HOVER)

    def _leave(self, e):
        for w in (self.frame, self.inner, self.name_lbl, self.dot_cv, self.state_lbl, self.close_lbl):
            w.config(bg=CARD_BG)

    def update(self, session):
        self.color = session["color"]
        self.dot_cv.itemconfig(self.dot_id, fill=session["color"])
        self.name_lbl.config(text=session["name"][:22])
        self.state_lbl.config(text=session["text"])

    def destroy(self):
        self.frame.destroy()


class StatusPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CC-Status")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)
        self.root.configure(bg="black")

        self.always_on_top = True
        self.cards = {}
        self.order = []
        self._drag_id = None
        self._win_drag = {"x": 0, "y": 0}
        self._editing = None
        self._visible = True
        self._tray_icon = None

        # Outer
        self.outer = tk.Frame(self.root, bg=BG,
                              highlightthickness=1, highlightbackground=BORDER)
        self.outer.pack(fill="both", expand=True)

        # Header
        self.header = tk.Frame(self.outer, bg=HEADER_BG, cursor="fleur")
        self.header.pack(fill="x")

        hdr = tk.Frame(self.header, bg=HEADER_BG)
        hdr.pack(fill="x", padx=12, pady=6)

        tk.Label(hdr, text="CC-Status", fg=TEXT_SEC, bg=HEADER_BG,
                 font=("Segoe UI Variable", 9)).pack(side="left")

        # Close button (minimize to tray) - rightmost
        self.close_lbl = tk.Label(hdr, text="  ✕  ", fg=TEXT_MUTED, bg=HEADER_BG,
                                  font=("Segoe UI Variable", 9), cursor="hand2")
        self.close_lbl.pack(side="right", padx=(0, 2))
        self.close_lbl.bind("<Enter>", lambda e: self.close_lbl.config(fg=TEXT_PRI, bg="#c42b1c"))
        self.close_lbl.bind("<Leave>", lambda e: self.close_lbl.config(fg=TEXT_MUTED, bg=HEADER_BG))
        self.close_lbl.bind("<Button-1>", lambda e: self._minimize_to_tray())

        # Minimize to tray button - left of close
        self.min_lbl = tk.Label(hdr, text="  ─  ", fg=TEXT_MUTED, bg=HEADER_BG,
                                font=("Segoe UI Variable", 9), cursor="hand2")
        self.min_lbl.pack(side="right", padx=(0, 2))
        self.min_lbl.bind("<Enter>", lambda e: self.min_lbl.config(fg=TEXT_PRI, bg="#3a3a3c"))
        self.min_lbl.bind("<Leave>", lambda e: self.min_lbl.config(fg=TEXT_MUTED, bg=HEADER_BG))
        self.min_lbl.bind("<Button-1>", lambda e: self._minimize_to_tray())

        self.header.bind("<Button-1>", self._win_start)
        self.header.bind("<B1-Motion>", self._win_move)
        hdr.bind("<Button-1>", self._win_start)
        hdr.bind("<B1-Motion>", self._win_move)

        # List
        self.list_frame = tk.Frame(self.outer, bg=BG)
        self.list_frame.pack(fill="both", expand=True, pady=(6, 0))
        tk.Frame(self.outer, bg=BG, height=6).pack(fill="x")

        # Context menu
        self.menu = tk.Menu(self.root, tearoff=0,
                           bg=CARD_BG, fg=TEXT_PRI,
                           activebackground=ACCENT, activeforeground="#000000",
                           font=("Segoe UI Variable", 9), relief="flat", bd=1)
        self.menu.add_command(label="  置顶", command=self._toggle_topmost)
        self.menu.add_command(label="  清除全部", command=self._clear_all)
        self.menu.add_separator()
        self.menu.add_command(label="  退出", command=self._quit)
        self.outer.bind("<Button-3>", self._show_menu)
        self.list_frame.bind("<Button-3>", self._show_menu)

        # Position
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"280x60+{sw - 300}+{sh - 120}")

        # Start tray in background
        self._start_tray()

        # Start polling
        self._poll()

    def _start_tray(self):
        def run_tray():
            img = create_tray_icon([])
            menu = pystray.Menu(
                pystray.MenuItem("显示面板", lambda: self.root.after(0, self._show_from_tray), default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出 CC-Status", lambda: self.root.after(0, self._quit))
            )
            self._tray_icon = pystray.Icon("CC-Status", img, "CC-Status", menu)
            self._tray_icon.run()

        t = threading.Thread(target=run_tray, daemon=True)
        t.start()

    def _update_tray_icon(self, sessions):
        if self._tray_icon:
            try:
                self._tray_icon.icon = create_tray_icon(sessions)
            except:
                pass

    def _minimize_to_tray(self):
        self.root.withdraw()
        self._visible = False

    def _show_from_tray(self):
        self.root.deiconify()
        self.root.lift()
        self._visible = True

    def _win_start(self, e):
        self._win_drag = {"x": e.x_root, "y": e.y_root}

    def _win_move(self, e):
        dx = e.x_root - self._win_drag["x"]
        dy = e.y_root - self._win_drag["y"]
        self.root.geometry(f"+{self.root.winfo_x()+dx}+{self.root.winfo_y()+dy}")
        self._win_drag = {"x": e.x_root, "y": e.y_root}

    def _row_press(self, sid, e):
        self._drag_id = sid
        self.root.bind("<B1-Motion>", self._row_motion)
        self.root.bind("<ButtonRelease-1>", self._row_release)

    def _row_motion(self, e):
        if not self._drag_id or self._drag_id not in self.cards:
            return
        cur_idx = self.order.index(self._drag_id)
        for i, sid in enumerate(self.order):
            if sid == self._drag_id or sid not in self.cards:
                continue
            ry = self.cards[sid].frame.winfo_rooty() + self.cards[sid].frame.winfo_height() // 2
            if e.y_root < ry and i < cur_idx:
                self.order.pop(cur_idx)
                self.order.insert(i, self._drag_id)
                self._repack()
                break
            elif e.y_root > ry and i > cur_idx:
                self.order.pop(cur_idx)
                self.order.insert(i, self._drag_id)
                self._repack()
                break

    def _row_release(self, e):
        self._drag_id = None
        self.root.unbind("<B1-Motion>")
        self.root.unbind("<ButtonRelease-1>")

    def _remove_session(self, sid):
        fp = os.path.join(STATUS_DIR, f"{sid}.state")
        try:
            os.remove(fp)
        except:
            pass
        if sid in self.cards:
            self.cards[sid].destroy()
            del self.cards[sid]
        if sid in self.order:
            self.order.remove(sid)
        self._repack()

    def _clear_all(self):
        for sid in list(self.order):
            self._remove_session(sid)

    def _start_rename(self, sid):
        if self._editing:
            return
        self._editing = sid
        if sid not in self.cards:
            return
        card = self.cards[sid]
        name_lbl = card.name_lbl

        entry = tk.Entry(card.inner, bg=CARD_HOVER, fg=TEXT_PRI,
                         font=("Segoe UI Variable", 10),
                         insertbackground=TEXT_PRI, bd=0, highlightthickness=1,
                         highlightbackground=ACCENT)
        entry.insert(0, name_lbl.cget("text"))
        entry.select_range(0, "end")
        entry.focus_set()

        name_lbl.pack_forget()
        entry.pack(side="left", padx=(0, 4), fill="x", expand=True)

        def finish(event=None):
            new_name = entry.get().strip()
            if new_name:
                _custom_names[sid] = new_name
                save_custom_names()
                name_lbl.config(text=new_name[:22])
            entry.destroy()
            name_lbl.pack(side="left")
            self._editing = None

        entry.bind("<Return>", finish)
        entry.bind("<FocusOut>", finish)
        entry.bind("<Escape>", lambda e: (entry.destroy(),
                                           name_lbl.pack(side="left"),
                                           setattr(self, "_editing", None)))

    def _make_card(self, session):
        card = SessionCard(self.list_frame, session, self)
        sid = session["id"]
        for w in (card.frame, card.inner, card.name_lbl, card.dot_cv, card.state_lbl):
            w.bind("<Button-1>", lambda e, s=sid: self._row_press(s, e))
            w.bind("<Double-Button-1>", lambda e, s=sid: self._start_rename(s))
        return card

    def _poll(self):
        self.root.after(1000, self._poll)
        if self._drag_id or self._editing:
            return
        sessions = read_sessions()
        # Reorder to match panel order
        session_map = {s["id"]: s for s in sessions}
        ordered = [session_map[sid] for sid in self.order if sid in session_map]
        self._update_tray_icon(ordered)
        for s in sessions:
            sid = s["id"]
            if sid in self.cards:
                self.cards[sid].update(s)
            else:
                self.cards[sid] = self._make_card(s)
                self.order.append(sid)
        self._repack()

    def _repack(self):
        for sid in self.order:
            if sid in self.cards:
                self.cards[sid].frame.pack_forget()
        for sid in self.order:
            if sid in self.cards:
                self.cards[sid].frame.pack(fill="x", padx=10, pady=(0, 4))
        n = len(self.order)
        h = max(60, n * 42 + 36)
        self.root.geometry(f"280x{h}")

    def _show_menu(self, e):
        self.menu.tk_popup(e.x_root, e.y_root)

    def _toggle_topmost(self):
        self.always_on_top = not self.always_on_top
        self.root.attributes("-topmost", self.always_on_top)

    def _quit(self):
        if self._tray_icon:
            self._tray_icon.stop()
        self.root.destroy()
        sys.exit(0)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    StatusPanel().run()

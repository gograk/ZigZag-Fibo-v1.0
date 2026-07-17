#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZIGZAG_FIBO BY GOGRAK — Android APK UI (Kivy)
Semua logika sinyal ada di bot_core.py (tidak diubah).
"""

import threading
from datetime import datetime, timezone

# ── Kivy config SEBELUM import kivy lainnya ──────────────
from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '800')
Config.set('kivy', 'window_icon', '')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line

Window.clearcolor = (0.05, 0.05, 0.08, 1)

import bot_core as bot

APP_TITLE = "ZIGZAG_FIBO BY GOGRAK"

# ── Notification ─────────────────────────────────────────
def _send_android_notif(title, body):
    try:
        from plyer import notification
        notification.notify(
            title=title, message=body,
            app_name=APP_TITLE, timeout=5,
        )
    except Exception:
        pass

bot.notify_callback = _send_android_notif

# ════════════════════════════════════════════════════════
#  STATUS TRACKING (WIN / LOSS / OPEN / PENDING)
# ════════════════════════════════════════════════════════
_sig_status = {}   # key -> "WIN"|"LOSS"|"OPEN"|"PENDING"

def _sig_key(sig):
    return f"{sig['ts']}|{sig['tf']}|{sig['type']}|{sig['entry']:.3f}"

def _refresh_statuses():
    with bot.S.lock:
        trades  = dict(bot.S.active_trades)
        signals = list(bot.S.signals_today)
        price   = bot.S.price

    for sig in signals:
        key = _sig_key(sig)
        if key in _sig_status and _sig_status[key] in ("WIN", "LOSS"):
            continue  # already settled
        # try matching to a trade
        matched = None
        for tid, t in trades.items():
            if (t.get('ts') == sig['ts'] and t['tf'] == sig['tf']
                    and t['type'] == sig['type']
                    and abs(t['entry'] - sig['entry']) < 0.01):
                matched = t
                break
        if matched:
            if matched.get('be_done'):
                _sig_status[key] = "WIN"
            elif price > 0:
                if sig['type'] == 'sell' and price >= sig['sl']:
                    _sig_status[key] = "LOSS"
                elif sig['type'] == 'buy' and price <= sig['sl']:
                    _sig_status[key] = "LOSS"
                else:
                    _sig_status.setdefault(key, "OPEN")
        else:
            _sig_status.setdefault(key, "PENDING")

# ════════════════════════════════════════════════════════
#  WIDGET HELPERS
# ════════════════════════════════════════════════════════
def lbl(text, size=13, bold=False, color=(1, 1, 1, 1),
        halign='left', valign='middle', **kw):
    l = Label(text=text, font_size=size, bold=bold, color=color,
               halign=halign, valign=valign,
               size_hint_y=None, markup=True, **kw)
    l.bind(texture_size=l.setter('size'))
    return l

def _add_bg(widget, color, radius=0):
    with widget.canvas.before:
        Color(*color)
        if radius:
            widget._bg = RoundedRectangle(pos=widget.pos,
                                           size=widget.size, radius=[radius])
        else:
            widget._bg = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda w, v: setattr(w._bg, 'pos', v),
                size=lambda w, v: setattr(w._bg, 'size', v))

def h_sep(height=1, color=(0.15, 0.17, 0.22, 1)):
    w = Widget(size_hint_y=None, height=height)
    _add_bg(w, color)
    return w

def section_title(text):
    box = BoxLayout(size_hint_y=None, height=28, padding=[0, 4])
    box.add_widget(lbl(f"[color=777777]{text}[/color]",
                       size=11, halign='center'))
    return box

def pill_btn(text, active=False, on_press=None, width=60):
    color_text = (0.05, 0.05, 0.08, 1) if active else (0.7, 0.7, 0.7, 1)
    bg = (1, 0.75, 0, 1) if active else (0.18, 0.20, 0.26, 1)
    btn = Button(
        text=text, font_size=12, size_hint=(None, None),
        width=width, height=30,
        background_color=(0, 0, 0, 0),
        background_normal='', color=color_text,
    )
    _add_bg(btn, bg, radius=14)
    if on_press:
        btn.bind(on_press=on_press)
    return btn

# ════════════════════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════════════════════
def make_header(right_text="XAUUSD : ZigZag+Fibo"):
    h = BoxLayout(size_hint_y=None, height=46, padding=[14, 8])
    _add_bg(h, (0.06, 0.08, 0.12, 1))
    h.add_widget(lbl(
        f"[b][color=ffd700]◆ {APP_TITLE} ◆[/color][/b]",
        size=13, halign='left'))
    h.add_widget(lbl(
        f"[color=666666]{right_text}[/color]",
        size=10, halign='right'))
    return h

# ════════════════════════════════════════════════════════
#  BOTTOM NAV BAR
# ════════════════════════════════════════════════════════
class BottomNav(BoxLayout):
    def __init__(self, on_switch, **kw):
        super().__init__(orientation='horizontal',
                         size_hint_y=None, height=62, **kw)
        _add_bg(self, (0.07, 0.08, 0.12, 1))
        self._on_switch = on_switch
        self._btns = {}
        items = [
            ('dashboard', '⊞', 'Dashboard'),
            ('sinyal',    '▊', 'Sinyal'),
            ('fibo',      '∿', 'Fibo'),
        ]
        for key, icon, label_text in items:
            box = BoxLayout(orientation='vertical', padding=[0, 6])
            icon_l = lbl(icon, size=22, halign='center')
            text_l = lbl(label_text, size=9, halign='center',
                         color=(0.45, 0.45, 0.45, 1))
            box.add_widget(icon_l)
            box.add_widget(text_l)
            btn = Button(background_color=(0, 0, 0, 0),
                         background_normal='')
            btn.add_widget(box)
            btn.bind(on_press=lambda b, k=key: self._tap(k))
            self._btns[key] = (btn, icon_l, text_l)
            self.add_widget(btn)
        self._set_active('dashboard')

    def _tap(self, key):
        self._set_active(key)
        self._on_switch(key)

    def set_active(self, key):
        self._set_active(key)

    def _set_active(self, key):
        for k, (btn, icon_l, text_l) in self._btns.items():
            gold = (1, 0.78, 0, 1)
            dim  = (0.38, 0.38, 0.38, 1)
            icon_l.color = gold if k == key else dim
            text_l.color = gold if k == key else dim

# ════════════════════════════════════════════════════════
#  TAB: DASHBOARD
# ════════════════════════════════════════════════════════
class DashTab(ScrollView):
    def __init__(self, **kw):
        super().__init__(size_hint=(1, 1), **kw)
        root = BoxLayout(orientation='vertical', padding=[14, 10],
                         spacing=10, size_hint_y=None)
        root.bind(minimum_height=root.setter('height'))

        # ── Price Card ─────────────────────────────────
        price_box = BoxLayout(orientation='vertical', spacing=4,
                               size_hint_y=None, height=130, padding=[0, 10])
        _add_bg(price_box, (0.09, 0.11, 0.16, 1), radius=10)

        self.ws_lbl = lbl("HARGA LIVE", size=12,
                           color=(0.3, 0.85, 0.85, 1), halign='center')
        self.sym_lbl = lbl("XAUUSD", size=13,
                            color=(0.65, 0.65, 0.65, 1), halign='center')
        self.price_lbl = lbl("—", size=34, bold=True,
                              color=(1, 1, 1, 1), halign='center')
        self.chg_lbl = lbl("", size=14, halign='center')

        price_box.add_widget(self.ws_lbl)
        price_box.add_widget(self.sym_lbl)
        price_box.add_widget(self.price_lbl)
        price_box.add_widget(self.chg_lbl)
        root.add_widget(price_box)

        # ── RSI Section ────────────────────────────────
        root.add_widget(section_title("RSI-14 per Timeframe"))
        rsi_box = BoxLayout(size_hint_y=None, height=56,
                             padding=[6, 4], spacing=2)
        _add_bg(rsi_box, (0.09, 0.11, 0.16, 1), radius=10)

        self.rsi_cells = {}
        for tf in bot.TIMEFRAMES:
            col = BoxLayout(orientation='vertical', spacing=2)
            name_l = lbl(bot.TF_LABEL[tf], size=11,
                          color=(0.6, 0.6, 0.6, 1), halign='center')
            val_l  = lbl("—", size=15, bold=True,
                          halign='center', color=(1, 1, 1, 1))
            col.add_widget(name_l)
            col.add_widget(val_l)
            self.rsi_cells[tf] = val_l
            rsi_box.add_widget(col)
        root.add_widget(rsi_box)

        # ── Stats Section ──────────────────────────────
        root.add_widget(section_title("Statistik Sosial"))
        stats_box = BoxLayout(orientation='vertical', spacing=0,
                               size_hint_y=None, padding=[12, 8])
        stats_box.bind(minimum_height=stats_box.setter('height'))
        _add_bg(stats_box, (0.09, 0.11, 0.16, 1), radius=10)

        self.stat_rows = {}
        stat_items = [
            ("total",  "Total Sinyal"),
            ("win",    "Win (%)"),
            ("loss",   "Loss (%)"),
            ("pnl",    "P&L Harian"),
            ("dd",     "Max Drawdown"),
            ("uptime", "Uptime"),
        ]
        for key, label_text in stat_items:
            row = BoxLayout(size_hint_y=None, height=28)
            row.add_widget(lbl(f"[color=888888]{label_text}[/color]",
                               size=12, halign='left'))
            val_l = lbl("—", size=12, halign='right',
                         color=(1, 1, 1, 1))
            row.add_widget(val_l)
            self.stat_rows[key] = val_l
            stats_box.add_widget(row)
        root.add_widget(stats_box)

        # ── Log Section ────────────────────────────────
        root.add_widget(section_title("Log"))
        log_box = BoxLayout(orientation='vertical', size_hint_y=None,
                             padding=[10, 8], spacing=2)
        log_box.bind(minimum_height=log_box.setter('height'))
        _add_bg(log_box, (0.09, 0.11, 0.16, 1), radius=10)
        self.log_lbl = lbl("", size=11, color=(0.65, 0.70, 0.65, 1),
                             halign='left')
        log_box.add_widget(self.log_lbl)
        root.add_widget(log_box)

        self.add_widget(root)

    def refresh(self, *_):
        with bot.S.lock:
            price   = bot.S.price
            prev    = bot.S.prev_price
            rsi_d   = dict(bot.S.rsi)
            ws_ok   = bot.S.ws_connected
            total   = bot.S.total_signals
            wins    = bot.S.wins
            dpnl    = bot.S.daily_pnl
            dd      = bot.S.max_dd
            start   = bot.S.start_time
            signals = list(bot.S.signals_today)

        uptime = str(datetime.now(timezone.utc) - start).split('.')[0]

        # WS status
        if ws_ok:
            self.ws_lbl.text = "[color=00cccc]● HARGA LIVE[/color]"
        else:
            self.ws_lbl.text = "[color=ff8800]● KONEKSI ULANG...[/color]"

        # Price
        chg  = price - prev if prev else 0
        sign = "+" if chg >= 0 else ""
        col  = "00dd77" if chg >= 0 else "ff4444"
        self.price_lbl.text = f"{price:,.3f}" if price else "—"
        self.chg_lbl.text   = (f"[color=#{col}]{sign}{chg:.3f}[/color]"
                                if price else "")

        # RSI
        for tf in bot.TIMEFRAMES:
            val = rsi_d.get(tf, 0.0)
            if   val >= 70: c = "ff4444"
            elif val <= 30: c = "44ccff"
            else:           c = "ffffff"
            self.rsi_cells[tf].text = (
                f"[color=#{c}]{val:.0f}[/color]" if val else "—")

        # Stats
        losses = sum(1 for s in signals
                     if _sig_status.get(_sig_key(s)) == "LOSS")
        win_pct  = f"{round(wins/total*100)}%" if total else "—"
        loss_pct = f"{round(losses/total*100)}%" if total else "—"
        pnl_col  = "00dd77" if dpnl >= 0 else "ff4444"
        pnl_sign = "+" if dpnl >= 0 else ""

        self.stat_rows["total"].text  = f"{total}"
        self.stat_rows["win"].text    = (
            f"[color=00dd77]{wins} ({win_pct})[/color]")
        self.stat_rows["loss"].text   = (
            f"[color=ff4444]{losses} ({loss_pct})[/color]")
        self.stat_rows["pnl"].text    = (
            f"[color=#{pnl_col}]{pnl_sign}{dpnl:.2f}[/color]")
        self.stat_rows["dd"].text     = f"{dd:.2f}"
        self.stat_rows["uptime"].text = uptime

        # Log
        entries = list(bot._log_buf)[-6:]
        lines = []
        for e in entries:
            if "WS_DIAG" in e or "cert" in e or "CONNECT" in e:
                lines.append(f"[color=ff5555]{e}[/color]")
            else:
                lines.append(e)
        self.log_lbl.text = "\n".join(lines)


# ════════════════════════════════════════════════════════
#  TAB: SINYAL
# ════════════════════════════════════════════════════════
STATUS_COLORS = {
    "WIN":     ("00aa44", "WIN"),
    "LOSS":    ("cc2222", "LOSS"),
    "OPEN":    ("cc7700", "OPEN"),
    "PENDING": ("333344", "PENDING"),
}

class SinyalTab(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical',
                         padding=[0, 0], spacing=0, **kw)

        # ── Filter row ─────────────────────────────────
        filter_row = BoxLayout(size_hint_y=None, height=46,
                                padding=[10, 8], spacing=8)
        _add_bg(filter_row, (0.07, 0.09, 0.13, 1))

        self._active_filter = "ALL"
        self._filter_btns   = {}
        for f in ("ALL", "OPEN", "WIN", "LOSS", "PENDING"):
            btn = pill_btn(f, active=(f == "ALL"), width=62)
            btn.bind(on_press=lambda b, flt=f: self._set_filter(flt))
            self._filter_btns[f] = btn
            filter_row.add_widget(btn)
        self.add_widget(filter_row)

        # ── Count label ────────────────────────────────
        self.count_lbl = lbl("0 sinyal ditemukan",
                              size=11, color=(0.55, 0.55, 0.55, 1),
                              halign='left')
        count_row = BoxLayout(size_hint_y=None, height=28, padding=[14, 4])
        count_row.add_widget(self.count_lbl)
        self.add_widget(count_row)

        # ── Signal list ────────────────────────────────
        sv = ScrollView(size_hint=(1, 1))
        self.sig_box = BoxLayout(orientation='vertical', spacing=6,
                                  size_hint_y=None, padding=[10, 4])
        self.sig_box.bind(minimum_height=self.sig_box.setter('height'))
        sv.add_widget(self.sig_box)
        self.add_widget(sv)

    def _set_filter(self, flt):
        self._active_filter = flt
        for f, btn in self._filter_btns.items():
            gold = (1, 0.78, 0, 1)
            dim  = (0.18, 0.20, 0.26, 1)
            with btn.canvas.before:
                btn.canvas.before.clear()
            _add_bg(btn, gold if f == flt else dim, radius=14)
            btn.color = ((0.05, 0.05, 0.08, 1) if f == flt
                         else (0.7, 0.7, 0.7, 1))
        self.refresh()

    def refresh(self, *_):
        with bot.S.lock:
            sigs = list(bot.S.signals_today)
        _refresh_statuses()

        flt = self._active_filter
        if flt == "ALL":
            filtered = list(reversed(sigs[-30:]))
        else:
            filtered = [s for s in reversed(sigs[-30:])
                        if _sig_status.get(_sig_key(s), "PENDING") == flt]

        self.count_lbl.text = (
            f"[color=aaaaaa]{len(filtered)} sinyal ditemukan[/color]")
        self.sig_box.clear_widgets()

        if not filtered:
            self.sig_box.add_widget(
                lbl("[color=555555]Belum ada sinyal.[/color]",
                    size=13, halign='center'))
            return

        for sig in filtered:
            self.sig_box.add_widget(self._make_card(sig))

    def _make_card(self, sig):
        is_buy   = sig["type"] == "buy"
        status   = _sig_status.get(_sig_key(sig), "PENDING")
        st_color, st_text = STATUS_COLORS.get(status, ("333344", status))
        side_col = (0.05, 0.65, 0.25, 1) if is_buy else (0.75, 0.12, 0.12, 1)
        side_hex  = "00cc44" if is_buy else "cc2222"
        label_txt = "BUY" if is_buy else "SELL"

        # extract HH:MM from ts "DD/MM/YYYY HH:MM:SS"
        try:
            time_str = sig["ts"].split(" ")[1][:5]
        except Exception:
            time_str = sig.get("ts", "")

        pnl = sig.get("pnl", 0.0)
        pnl_col  = "00dd77" if pnl >= 0 else "ff4444"
        pnl_sign = "+" if pnl >= 0 else ""

        outer = BoxLayout(orientation='horizontal',
                           size_hint_y=None, height=96, spacing=0)

        # left colour strip
        strip = Widget(size_hint_x=None, width=4)
        _add_bg(strip, side_col, radius=0)
        outer.add_widget(strip)

        # card body
        body = BoxLayout(orientation='vertical', padding=[10, 8],
                          spacing=4, size_hint_x=1)
        _add_bg(body, (0.10, 0.12, 0.17, 1), radius=0)

        # row 1: badge + tf + time | status
        row1 = BoxLayout(size_hint_y=None, height=26)

        badge = BoxLayout(size_hint=(None, None), width=40, height=22)
        _add_bg(badge, side_col, radius=4)
        badge.add_widget(lbl(f"[b]{label_txt}[/b]", size=11,
                              color=(1, 1, 1, 1), halign='center'))
        row1.add_widget(badge)
        row1.add_widget(Widget(size_hint_x=None, width=6))
        row1.add_widget(lbl(
            f"[color=888888]{sig['tf']}  {time_str}[/color]",
            size=11, halign='left'))

        status_badge = BoxLayout(size_hint=(None, None), width=60, height=22)
        _add_bg(status_badge, tuple(int(st_color[i:i+2], 16)/255
                                    for i in (0, 2, 4)) + (1,), radius=4)
        status_badge.add_widget(
            lbl(f"[b]{st_text}[/b]", size=10,
                color=(1, 1, 1, 1), halign='center'))
        row1.add_widget(status_badge)

        body.add_widget(row1)

        # row 2: column headers
        hdr = BoxLayout(size_hint_y=None, height=18)
        for t in ("Entry", "TP", "SL", "PnL"):
            hdr.add_widget(lbl(f"[color=666666]{t}[/color]",
                               size=10, halign='left'))
        body.add_widget(hdr)

        # row 3: values
        vals = BoxLayout(size_hint_y=None, height=24)
        vals.add_widget(lbl(f"[b]{sig['entry']:.3f}[/b]",
                             size=13, halign='left'))
        vals.add_widget(lbl(f"[color=00cc55][b]{sig['tp1']:.3f}[/b][/color]",
                             size=13, halign='left'))
        vals.add_widget(lbl(f"[color=ff4444][b]{sig['sl']:.3f}[/b][/color]",
                             size=13, halign='left'))
        vals.add_widget(lbl(
            f"[color=#{pnl_col}]{pnl_sign}{pnl:.1f}[/color]",
            size=13, halign='left'))
        body.add_widget(vals)

        outer.add_widget(body)
        return outer


# ════════════════════════════════════════════════════════
#  TAB: FIBO
# ════════════════════════════════════════════════════════
FIBO_ROWS = [
    (2.414,  "[SL.Sell2]", "ff2222"),   # SL Sell 2 — teratas
    (2.236,  "[1.Sel2] A", "ff4444"),
    (2.000,  "[1.Sel2] B", "ff4444"),
    (1.786,  "[SL.Sell1]", "ff2222"),   # SL Sell 1
    (1.618,  "[1.Sel1] A", "ff6666"),
    (1.500,  "[1.Sel1] B", "ff6666"),
    (1.000,  "[ ] HIGH",   "dddddd"),
    (0.500,  "[ ] MID",    "dddddd"),
    (0.000,  "[ ] LOW",    "dddddd"),
    (-0.500, "[1.Buy1] A", "44dd88"),
    (-0.618, "[1.Buy1] B", "44dd88"),
    (-1.000, "[1.Buy2] A", "33cc77"),
    (-1.236, "[1.Buy2] B", "33cc77"),
    (-0.786, "[SL.Buy1]",  "88ffaa"),
    (-1.414, "[SL.Buy2]",  "88ffaa"),
]

class FiboTab(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical',
                         padding=[0, 0], spacing=0, **kw)

        # ── TF filter row ──────────────────────────────
        filter_row = BoxLayout(size_hint_y=None, height=46,
                                padding=[10, 8], spacing=6)
        _add_bg(filter_row, (0.07, 0.09, 0.13, 1))

        self._active_tf     = "ALL"
        self._filter_btns   = {}
        for f in ("ALL", "5M", "15M", "30M", "1H", "4H"):
            btn = pill_btn(f, active=(f == "ALL"), width=50)
            btn.bind(on_press=lambda b, flt=f: self._set_filter(flt))
            self._filter_btns[f] = btn
            filter_row.add_widget(btn)
        self.add_widget(filter_row)

        # ── Fibo list ──────────────────────────────────
        sv = ScrollView(size_hint=(1, 1))
        self.fibo_box = BoxLayout(orientation='vertical', spacing=8,
                                   size_hint_y=None, padding=[10, 6])
        self.fibo_box.bind(minimum_height=self.fibo_box.setter('height'))
        sv.add_widget(self.fibo_box)
        self.add_widget(sv)

    def _set_filter(self, flt):
        self._active_tf = flt
        for f, btn in self._filter_btns.items():
            gold = (1, 0.78, 0, 1)
            dim  = (0.18, 0.20, 0.26, 1)
            with btn.canvas.before:
                btn.canvas.before.clear()
            _add_bg(btn, gold if f == flt else dim, radius=14)
            btn.color = ((0.05, 0.05, 0.08, 1) if f == flt
                         else (0.7, 0.7, 0.7, 1))
        self.refresh()

    def refresh(self, *_):
        with bot.S.lock:
            snap  = {tf: dict(d) for tf, d in bot.S.fibo.items() if d}
            price = bot.S.price
            rsi_d = dict(bot.S.rsi)

        show_tfs = bot.TIMEFRAMES
        if self._active_tf != "ALL":
            label_map = {v: k for k, v in bot.TF_LABEL.items()}
            raw = label_map.get(self._active_tf)
            show_tfs = [raw] if raw else []

        self.fibo_box.clear_widgets()
        for tf in show_tfs:
            d = snap.get(tf)
            if not d:
                continue
            self.fibo_box.add_widget(
                self._make_card(tf, d, price, rsi_d.get(tf, 0)))

    def _make_card(self, tf, d, price, rsi_val):
        lv    = d["levels"]
        hi, lo = d["high"], d["low"]
        label = bot.TF_LABEL[tf]

        # trend arrow: if high_time > low_time → bearish ▼, else ▲
        try:
            ht = d.get("high_time", "")
            lt = d.get("low_time",  "")
            arrow = "▼" if ht > lt else "▲"
            arrow_col = "ff5555" if arrow == "▼" else "44dd88"
        except Exception:
            arrow, arrow_col = "▲", "44dd88"

        card = BoxLayout(orientation='vertical', spacing=0,
                          size_hint_y=None, padding=[10, 8])
        card.bind(minimum_height=card.setter('height'))
        _add_bg(card, (0.09, 0.11, 0.16, 1), radius=8)

        # ── Card header ────────────────────────────────
        hdr = BoxLayout(size_hint_y=None, height=32, spacing=6)

        # ZZ badge
        badge = BoxLayout(size_hint=(None, None), width=70, height=24)
        _add_bg(badge, (0.14, 0.16, 0.22, 1), radius=4)
        badge.add_widget(lbl(
            f"[b][color={arrow_col}]ZZ {label} {arrow}[/color][/b]",
            size=11, halign='center'))
        hdr.add_widget(badge)

        # H/L and RSI right-aligned
        hdr.add_widget(lbl(
            f"[color=ff8888]H:{hi:.3f}[/color]  "
            f"[color=88dd88]L:{lo:.3f}[/color]",
            size=10, halign='right'))
        hdr.add_widget(lbl(
            f"[color=888888]RSI {rsi_val:.0f}[/color]",
            size=10, halign='right', size_hint_x=None, width=50))
        card.add_widget(hdr)
        card.add_widget(h_sep(color=(0.14, 0.16, 0.22, 1)))

        # ── Level rows ─────────────────────────────────
        for level, name, col_hex in FIBO_ROWS:
            val  = lv.get(level, None)
            if val is None:
                continue
            near = price > 0 and abs(price - val) < 2.0
            marker = "  ◀" if near else ""
            row = BoxLayout(size_hint_y=None, height=22)
            row.add_widget(lbl(
                f"[color=#{col_hex}]{name}[/color]",
                size=11, halign='left'))
            row.add_widget(lbl(
                f"[color=#{col_hex}][b]{val:.3f}[/b][/color]"
                f"[color=ffff44]{marker}[/color]",
                size=11, halign='right'))
            card.add_widget(row)

        return card


# ════════════════════════════════════════════════════════
#  ROOT WIDGET
# ════════════════════════════════════════════════════════
class RootWidget(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', **kw)

        self._current_tab = 'dashboard'

        # ── Tab headers (per-tab) ──────────────────────
        self._headers = {
            'dashboard': make_header("XAUUSD : ZigZag+Fibo"),
            'sinyal':    make_header("Sinyal Trading"),
            'fibo':      make_header("XAUUSD · ZigZag+Fibo"),
        }
        self._header_host = BoxLayout(size_hint_y=None, height=46)
        self.add_widget(self._header_host)

        # ── Content area ──────────────────────────────
        self.content = BoxLayout()
        self.add_widget(self.content)

        # ── Bottom nav ─────────────────────────────────
        self.nav = BottomNav(on_switch=self._switch)
        self.add_widget(self.nav)

        # ── Tab views ─────────────────────────────────
        self.dash_tab   = DashTab()
        self.sinyal_tab = SinyalTab()
        self.fibo_tab   = FiboTab()

        self._switch('dashboard')

        # ── Callbacks & timers ─────────────────────────
        bot.ui_update_callback = self._schedule_refresh
        Clock.schedule_interval(self._refresh_all, 1)

    def _switch(self, tab):
        self._current_tab = tab
        self.content.clear_widgets()
        self._header_host.clear_widgets()
        self._header_host.add_widget(self._headers[tab])
        views = {
            'dashboard': self.dash_tab,
            'sinyal':    self.sinyal_tab,
            'fibo':      self.fibo_tab,
        }
        self.content.add_widget(views[tab])
        self.nav.set_active(tab)

    def _schedule_refresh(self):
        Clock.schedule_once(self._refresh_all, 0)

    def _refresh_all(self, *_):
        _refresh_statuses()
        self.dash_tab.refresh()
        self.sinyal_tab.refresh()
        self.fibo_tab.refresh()


# ════════════════════════════════════════════════════════
#  APP
# ════════════════════════════════════════════════════════
class ZigzagFiboApp(App):
    def build(self):
        self.title = APP_TITLE
        root = RootWidget()
        threading.Thread(target=bot.start_bot,
                         daemon=True, name="bot_start").start()
        return root


if __name__ == "__main__":
    ZigzagFiboApp().run()

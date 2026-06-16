"""Berevent Spell Codex - standalone desktop app for players.

A self-contained window with: an SRD spell library (search + filters), a spell
detail view, the glyph, and its binary necklace; plus a Generator tab to build a
glyph from arbitrary attributes. Pure Python standard library (Tkinter) so it
bundles into a single portable .exe with no runtime dependencies.

SRD spell data: 5e SRD (OGL). Glyph engine: SpellWriting (MIT).
"""
import json
import tkinter as tk
from tkinter import font as tkfont

import glyph_core as gc

# Dungeon Stone palette (matches the tracker)
BG = "#1a1a1e"; SURFACE = "#26262d"; SURF_HI = "#2e2e38"; BORDER = "#3a3a45"
TEXT = "#e8e4d9"; MUTED = "#8a8a99"; GOLD = "#c9973a"; RED = "#9b2c2c"; BLUE = "#4a6a8a"

SCHOOL_COLOR = {
    "Abjuration": BLUE, "Conjuration": "#7a6a9a", "Divination": "#5a8a8a",
    "Enchantment": "#a86a8a", "Evocation": RED, "Illusion": "#8a7aaa",
    "Necromancy": "#5a9a6a", "Transmutation": GOLD,
}


def level_label(n):
    return "Cantrip" if n == 0 else f"Level {n}"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Berevent Spell Codex")
        self.configure(bg=BG)
        self.geometry("1040x700")
        self.minsize(860, 560)

        self.f_disp = tkfont.Font(family="Georgia", size=15, weight="bold")
        self.f_h = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.f_body = tkfont.Font(family="Segoe UI", size=10)
        self.f_mono = tkfont.Font(family="Consolas", size=9)
        self.f_small = tkfont.Font(family="Segoe UI", size=8)

        with open(gc.resource_path("data", "spells.json"), encoding="utf-8") as fh:
            self.spells = json.load(fh)
        self.spells.sort(key=lambda s: s["name"])

        self._build_tabs()

    # -- tab chrome -----------------------------------------------------------
    def _build_tabs(self):
        bar = tk.Frame(self, bg=SURFACE)
        bar.pack(fill="x", side="top")
        self.pages = {}
        self._tabbtns = {}
        for key, label in (("library", "Spell Library"), ("generator", "Necklace Generator")):
            b = tk.Button(bar, text=label, font=self.f_h, bd=0, padx=18, pady=10,
                          bg=SURFACE, fg=MUTED, activebackground=SURF_HI,
                          activeforeground=GOLD, cursor="hand2",
                          command=lambda k=key: self.show(k))
            b.pack(side="left")
            self._tabbtns[key] = b

        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True)
        self.pages["library"] = LibraryPage(container, self)
        self.pages["generator"] = GeneratorPage(container, self)
        for p in self.pages.values():
            p.place(relwidth=1, relheight=1)
        self.show("library")

    def show(self, key):
        self.pages[key].tkraise()
        for k, b in self._tabbtns.items():
            b.configure(fg=GOLD if k == key else MUTED,
                        bg=SURF_HI if k == key else SURFACE)


# --- shared drawing ---------------------------------------------------------
def draw_glyph(canvas, attrs):
    canvas.delete("all")
    w = canvas.winfo_width() or 300
    h = canvas.winfo_height() or 300
    cx, cy = w / 2, h / 2
    r = min(w, h) * 0.42
    pts = gc.vertices(cx, cy, r)

    for a, b in gc.chords(attrs):
        x1, y1 = pts[a]; x2, y2 = pts[b]
        canvas.create_line(x1, y1, x2, y2, fill=GOLD, width=2)

    for i, (x, y) in enumerate(pts):
        rad = 5
        if i == 0:  # vertex-0 marker, solid, at 12 o'clock
            canvas.create_oval(x - rad, y - rad, x + rad, y + rad, fill=TEXT, outline=TEXT)
        else:
            canvas.create_oval(x - rad, y - rad, x + rad, y + rad, outline=MUTED, width=1)

    if attrs.get("concentration"):
        canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=TEXT, outline=TEXT)
    if attrs.get("ritual"):
        canvas.create_oval(cx - 9, cy - 9, cx + 9, cy + 9, outline=TEXT, width=2)


def draw_pips(canvas, attrs):
    canvas.delete("all")
    rows = gc.decode(attrs)
    w = canvas.winfo_width() or 360
    label_w = 86
    pip_area = max(160, w - label_w - 10)
    gap = 3
    pip_w = (pip_area - gap * (gc.N_POL - 1)) / gc.N_POL
    row_h = 22
    for ri, row in enumerate(rows):
        y = ri * row_h + 4
        canvas.create_text(6, y + 6, anchor="w", fill=MUTED, font=("Segoe UI", 8),
                           text=row["attribute"].upper())
        x = label_w
        for ch in row["bits"]:
            on = ch == "1"
            canvas.create_rectangle(
                x, y, x + pip_w, y + 11,
                fill=GOLD if on else "", outline=GOLD if on else BORDER)
            x += pip_w + gap
    canvas.configure(height=len(rows) * row_h + 8)


# --- Library page -----------------------------------------------------------
class LibraryPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        left = tk.Frame(self, bg=BG, width=300)
        left.pack(side="left", fill="y", padx=(14, 8), pady=14)
        left.pack_propagate(False)

        self.q = tk.StringVar()
        ent = tk.Entry(left, textvariable=self.q, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                       relief="flat", font=app.f_body)
        ent.pack(fill="x", ipady=5)
        _placeholder(ent, self.q, "Search name or text…")

        levels = ["All levels"] + [level_label(n) for n in range(10)]
        schools = ["All schools"] + sorted({s["school"] for s in app.spells})
        classes = ["All classes"] + sorted({c for s in app.spells for c in s["classes"]})
        self.v_level = _menu(left, app, levels)
        self.v_school = _menu(left, app, schools)
        self.v_class = _menu(left, app, classes)

        # add traces only after every filter var exists, so the placeholder
        # setting self.q above can't fire refilter() prematurely
        self.q.trace_add("write", lambda *a: self.refilter())
        for v in (self.v_level, self.v_school, self.v_class):
            v.trace_add("write", lambda *a: self.refilter())

        self.count = tk.Label(left, text="", bg=BG, fg=MUTED, font=app.f_small, anchor="w")
        self.count.pack(fill="x", pady=(8, 2))

        lb_wrap = tk.Frame(left, bg=BORDER)
        lb_wrap.pack(fill="both", expand=True)
        sb = tk.Scrollbar(lb_wrap)
        sb.pack(side="right", fill="y")
        self.lb = tk.Listbox(lb_wrap, bg=SURFACE, fg=TEXT, selectbackground=GOLD,
                             selectforeground=BG, relief="flat", highlightthickness=0,
                             font=app.f_body, activestyle="none", yscrollcommand=sb.set)
        self.lb.pack(side="left", fill="both", expand=True)
        sb.config(command=self.lb.yview)
        self.lb.bind("<<ListboxSelect>>", self.on_select)

        # right detail
        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(8, 14), pady=14)

        self.name = tk.Label(right, text="Select a spell", bg=BG, fg=GOLD,
                             font=app.f_disp, anchor="w")
        self.name.pack(fill="x")
        self.meta = tk.Label(right, text="", bg=BG, fg=MUTED, font=app.f_small, anchor="w",
                             justify="left")
        self.meta.pack(fill="x", pady=(2, 8))

        body_wrap = tk.Frame(right, bg=BORDER)
        body_wrap.pack(fill="both", expand=True)
        self.desc = tk.Text(body_wrap, bg=SURFACE, fg=TEXT, relief="flat", wrap="word",
                            font=app.f_body, padx=12, pady=10, height=8,
                            highlightthickness=0)
        self.desc.pack(fill="both", expand=True)
        self.desc.configure(state="disabled")

        gl = tk.Frame(right, bg=BG)
        gl.pack(fill="x", pady=(10, 0))
        self.glyph = tk.Canvas(gl, bg=SURFACE, width=240, height=240, highlightthickness=1,
                               highlightbackground=BORDER)
        self.glyph.pack(side="left")
        self.pips = tk.Canvas(gl, bg=BG, highlightthickness=0)
        self.pips.pack(side="left", fill="x", expand=True, padx=(12, 0))

        self.current = None
        self.glyph.bind("<Configure>", lambda e: self._redraw())
        self.pips.bind("<Configure>", lambda e: self._redraw())
        self.refilter()

    def filtered(self):
        term = self.q.get().strip().lower()
        if term == "search name or text…":
            term = ""
        lv = self.v_level.get(); sc = self.v_school.get(); cl = self.v_class.get()
        out = []
        for s in self.app.spells:
            if lv != "All levels" and level_label(s["level"]) != lv:
                continue
            if sc != "All schools" and s["school"] != sc:
                continue
            if cl != "All classes" and cl not in s["classes"]:
                continue
            if term and term not in (s["name"] + " " + " ".join(s["desc"])).lower():
                continue
            out.append(s)
        return out

    def refilter(self):
        self.shown = self.filtered()
        self.lb.delete(0, "end")
        for s in self.shown:
            self.lb.insert("end", f"  {s['name']}")
        self.count.config(text=f"{len(self.shown)} spells")

    def on_select(self, _evt):
        sel = self.lb.curselection()
        if not sel:
            return
        self.current = self.shown[sel[0]]
        s = self.current
        self.name.config(text=s["name"])
        comp = ", ".join(s["components"]) + (" *" if s.get("material") else "")
        flags = ""
        if s.get("concentration"):
            flags += " · Concentration"
        if s.get("ritual"):
            flags += " · Ritual"
        self.meta.config(
            text=f"{level_label(s['level'])} {s['school']}{flags}\n"
                 f"Cast {s['casting_time']}   ·   Range {s['range']}   ·   "
                 f"{comp}   ·   {s['duration']}")
        self.desc.configure(state="normal")
        self.desc.delete("1.0", "end")
        self.desc.insert("end", "\n".join(s["desc"]))
        if s.get("higher_level"):
            self.desc.insert("end", "\n\nAt Higher Levels. " + " ".join(s["higher_level"]))
        if s.get("material"):
            self.desc.insert("end", "\n\n* " + s["material"])
        self.desc.insert("end", "\n\nClasses: " + ", ".join(s["classes"]))
        self.desc.configure(state="disabled")
        self._redraw()

    def _redraw(self):
        if not self.current:
            return
        attrs = gc.srd_to_attrs(self.current)
        draw_glyph(self.glyph, attrs)
        draw_pips(self.pips, attrs)


# --- Generator page ---------------------------------------------------------
class GeneratorPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        left = tk.Frame(self, bg=BG, width=320)
        left.pack(side="left", fill="y", padx=14, pady=14)
        left.pack_propagate(False)

        tk.Label(left, text="Forge a glyph", bg=BG, fg=GOLD, font=app.f_disp,
                 anchor="w").pack(fill="x", pady=(0, 10))

        self.vars = {}
        for attr, label in (("level", "Level"), ("school", "School"),
                            ("damagetype", "Damage"), ("aoe", "Area"),
                            ("range", "Range"), ("duration", "Duration")):
            tk.Label(left, text=label.upper(), bg=BG, fg=MUTED, font=app.f_small,
                     anchor="w").pack(fill="x", pady=(6, 1))
            opts = gc.options_display(attr)
            var = tk.StringVar(value=opts[min(1, len(opts) - 1)])
            var.trace_add("write", lambda *a: self._redraw())
            _styled_menu(left, var, opts, app)
            self.vars[attr] = var

        self.v_conc = tk.BooleanVar(value=False)
        self.v_rit = tk.BooleanVar(value=False)
        cf = tk.Frame(left, bg=BG)
        cf.pack(fill="x", pady=(12, 0))
        for txt, var in (("Concentration", self.v_conc), ("Ritual", self.v_rit)):
            cb = tk.Checkbutton(cf, text=txt, variable=var, bg=BG, fg=TEXT,
                                selectcolor=SURFACE, activebackground=BG,
                                activeforeground=GOLD, font=app.f_body,
                                command=self._redraw, bd=0, highlightthickness=0)
            cb.pack(side="left", padx=(0, 14))

        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(8, 14), pady=14)
        self.glyph = tk.Canvas(right, bg=SURFACE, highlightthickness=1,
                               highlightbackground=BORDER)
        self.glyph.pack(fill="both", expand=True)
        self.pips = tk.Canvas(right, bg=BG, highlightthickness=0)
        self.pips.pack(fill="x", pady=(10, 0))
        self.glyph.bind("<Configure>", lambda e: self._redraw())
        self.pips.bind("<Configure>", lambda e: self._redraw())

    def attrs(self):
        a = {k: v.get() for k, v in self.vars.items()}
        a["concentration"] = self.v_conc.get()
        a["ritual"] = self.v_rit.get()
        return a

    def _redraw(self):
        a = self.attrs()
        draw_glyph(self.glyph, a)
        draw_pips(self.pips, a)


# --- small helpers ----------------------------------------------------------
def _menu(parent, app, options):
    var = tk.StringVar(value=options[0])
    _styled_menu(parent, var, options, app)
    return var


def _styled_menu(parent, var, options, app):
    mb = tk.OptionMenu(parent, var, *options)
    mb.configure(bg=SURFACE, fg=TEXT, activebackground=SURF_HI, activeforeground=GOLD,
                 relief="flat", highlightthickness=0, font=app.f_body, anchor="w",
                 bd=0, cursor="hand2")
    mb["menu"].configure(bg=SURFACE, fg=TEXT, activebackground=GOLD, activeforeground=BG,
                         font=app.f_body)
    mb.pack(fill="x")
    return mb


def _placeholder(entry, var, text):
    def on_focus_in(_):
        if var.get() == text:
            var.set("")
            entry.config(fg=TEXT)

    def on_focus_out(_):
        if not var.get():
            var.set(text)
            entry.config(fg=MUTED)

    var.set(text)
    entry.config(fg=MUTED)
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)


if __name__ == "__main__":
    App().mainloop()

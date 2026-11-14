#!/usr/bin/env python3
"""
Génère show/Show-Rock-XL.streamDeckProfile (Stream Deck XL, 32 touches) à partir de Show-Rock.qxw.

Chaque touche utilise le plugin « QLC+ Show » (streamdeck-plugin/) : elle appuie directement sur le bouton
du Virtual Console par l'accès web de QLC+ (ID du widget). Seul TAP reste un raccourci clavier
(QLC+ n'expose pas le tap tempo par le web).
Les touches et les couleurs sont lues dans le .qxw : relancer après generate_show.py.

    python3 tools/make_streamdeck.py
"""
import io
import json
import os
import uuid
import zipfile
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
QXW = os.path.join(HERE, "..", "show", "Show-Rock.qxw")
OUT = os.path.join(HERE, "..", "show", "Show-Rock-XL.streamDeckProfile")
MODEL = "20GAT9901"            # Stream Deck XL
COLS, ROWS = 8, 4
NS = {"q": "http://www.qlcplus.org/Workspace"}
PLUGIN = "ca.lequeb.qlcplus"

# ------------------------------------------------------------ lecture du show
keys = {}                      # raccourci -> (caption une ligne, bg int|None)
tree = ET.parse(QXW)
for b in tree.getroot().iter("{%s}Button" % NS["q"]):
    k = b.find("q:Key", NS)
    if k is None or not k.text:
        continue
    bg = b.find("q:Appearance/q:BackgroundColor", NS)
    col = int(bg.text) & 0xFFFFFF if bg is not None and bg.text != "Default" else None
    keys[k.text] = (b.get("Caption").replace("\n", " "), col, b.get("ID"))
tap_key = None
for sd in tree.getroot().iter("{%s}SpeedDial" % NS["q"]):
    k = sd.find("q:Key", NS)
    if k is not None:
        tap_key = k.text


HOLD = {f"Alt+Shift+{c}" for c in "KLMNOPQRST"}     # strobes / bumps / flashs : allumés tant que tenus


def btn(key, title=None):
    caption, col, wid = keys[key]
    return ("qlc", title or caption, (wid, "hold" if key in HOLD else ""), col)


TAP = ("hotkey", "TAP\ntempo", tap_key, 0x00A060)

# ------------------------------------------------------------ codes clavier
QT_F1 = 0x01000030


def hotkey_settings(seq):
    parts = seq.split("+")
    key, mods = parts[-1], set(parts[:-1])
    if len(key) == 1 and key.isalpha():
        vk = qt = ord(key.upper())
    elif key.startswith("F") and key[1:].isdigit():
        n = int(key[1:])
        vk, qt = 111 + n, QT_F1 + n - 1
    elif len(key) == 1 and key.isdigit():
        vk = qt = ord(key)
    else:
        raise ValueError(seq)
    alt, ctrl, shift = "Alt" in mods, "Ctrl" in mods, "Shift" in mods
    return {"Coalesce": True, "Hotkeys": [{
        "KeyCmd": False, "KeyCtrl": ctrl, "KeyOption": alt, "KeyShift": shift,
        "KeyModifiers": (1 if alt else 0) | (2 if ctrl else 0) | (4 if shift else 0),
        "NativeCode": vk, "QTKeyCode": qt, "VKeyCode": vk}]}


# ------------------------------------------------------------ images
def icon(col, folder=False, on=False):
    col = 0x333333 if col is None else col
    rgb = ((col >> 16) & 255, (col >> 8) & 255, col & 255)
    im = Image.new("RGB", (288, 288), (0, 0, 0))
    d = ImageDraw.Draw(im)
    if on:                                       # touche active : cadre blanc épais
        d.rounded_rectangle((0, 0, 287, 287), radius=52, fill=(255, 255, 255))
        d.rounded_rectangle((22, 22, 265, 265), radius=38, fill=rgb)
    else:
        rgb = tuple(int(c * 0.55) for c in rgb)  # touche au repos : un peu plus sombre
        d.rounded_rectangle((10, 10, 278, 278), radius=46, fill=rgb)
    if folder:                                   # petit onglet de dossier
        d.rounded_rectangle((40, 30, 140, 70), radius=14, fill=tuple(min(255, c + 60) for c in rgb))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def text_color(col):
    if col is None:
        return "#ffffff"
    r, g, b = (col >> 16) & 255, (col >> 8) & 255, col & 255
    return "#000000" if (r * 299 + g * 587 + b * 114) / 1000 > 150 else "#ffffff"


def b32(u):
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTVW"
    bits = "".join(f"{x:08b}" for x in uuid.UUID(u).bytes)
    bits += "0" * (-len(bits) % 5)
    return "".join(alphabet[int(bits[i:i + 5], 2)] for i in range(0, len(bits), 5)) + "Z"


# ------------------------------------------------------------ titres (jamais coupés)
SHORT = {"FEU D'ARTIFICE": "ARTIFICE", "COUCHER SOLEIL": "COUCHER\nSOLEIL", "PRÉ-REFRAIN": "PRÉ-\nREFRAIN",
         "GROS REFRAIN": "GROS\nREFRAIN", "SOLO GUITARE": "SOLO\nGUITARE", "SPOT CHANTEUR": "SPOT\nCHANTEUR",
         "SOLO BATTERIE": "SOLO\nBATTERIE", "Alterné ambre/bleu": "Alterné\nambre\nbleu",
         "Remplir centre": "Remplir\ncentre", "Chase couleurs": "Chase\ncouleurs", "Rotation rapide": "Rotation\nrapide",
         "Rotation gobo": "Rotation\ngobo", "Balayage lent": "Balayage\nlent", "Magenta / Cyan": "Magenta\nCyan",
         "Blanc chaud": "Blanc\nchaud", "Blanc froid": "Blanc\nfroid", "Rouge sang": "Rouge\nsang",
         "Bords bleus": "Bords\nbleus", "Bords rouges": "Bords\nrouges", "V inversé": "V\ninversé",
         "Arc-en-ciel": "Arc-en-\nciel", "Plasma lent": "Plasma\nlent", "Fondu lent": "Fondu\nlent",
         "Vague rouge": "Vague\nrouge", "Vague bleue": "Vague\nbleue", "Vague tilt": "Vague\ntilt",
         "Pair / Impair": "Pair\nImpair", "Un par un": "Un par\nun", "Chase gobos": "Chase\ngobos",
         "BLEU GLACE": "BLEU\nGLACE", "ROUGE & UV": "ROUGE\n& UV", "SOLO BASSE": "SOLO\nBASSE",
         "ROCK BLANC": "ROCK\nBLANC", "OUVERTURE": "OUVER-\nTURE",
         "ACOUSTIQUE": "ACOUS-\nTIQUE", "APOTHÉOSE": "APOTHÉ-\nOSE"}
MAXC = 8


def wrap(t):
    t = SHORT.get(t.replace("\n", " "), t)
    out = []
    for line in t.split("\n"):
        words, cur = line.split(" "), ""
        for w in words:
            if cur and len(cur) + 1 + len(w) > MAXC:
                out.append(cur); cur = w
            else:
                cur = (cur + " " + w).strip()
        out.append(cur)
    return "\n".join(out)


# ------------------------------------------------------------ pages (◀ ▶ en bas à droite)
pages = []                      # [(uuid, name, {(c, r): item})]
SLOTS = [(c, r) for r in range(ROWS) for c in range(COLS) if (c, r) not in ((6, 3), (7, 3))]


def page(name, items):
    assert len(items) <= len(SLOTS), (name, len(items))
    grid = {slot: it for slot, it in zip(SLOTS, items) if it is not None}
    grid[(6, 3)] = ("prev",)
    grid[(7, 3)] = ("next",)
    pages.append((str(uuid.uuid4()), name, grid))


def look_row(mod):
    return [btn(f"{mod}F{i}") for i in range(1, 11)]


def keyed(prefix, letters):
    return [btn(f"{prefix}{c}") for c in letters]


auto = btn("F11", "▶ AUTO")
fondu, blackout = btn("N", "FONDU\nNOIR"), btn("X", "BLACK-\nOUT")
onoff = keyed("Alt+Shift+", "KLMNOPQRST")       # strobes, bumps, flashs (tant que tenus)
quick_pos = [btn("Shift+D", "→ CHAN-\nTEUR"), btn("Shift+C", "→ BAND"), btn("Shift+B", "→ PUBLIC")]

foh70, foh40 = btn("Alt+7", "FOH\n70 %"), btn("Alt+4", "FOH\n40 %")
sliders = {sl.get("Caption"): sl.get("ID") for sl in tree.getroot().iter(f"{{{NS['q']}}}Slider")}
FOH_COL = 0xF2D8A0


def level(cap, step):
    """touche « Niveau » du plugin sur le fader/bouton rotatif `cap` (step % par appui, 0 = affichage)"""
    sign = " +" if step > 0 else " −" if step < 0 else ""
    return ("level", f"{cap}{sign}\n0 %", (sliders[cap], step, cap), FOH_COL)


def level_row(cap):
    return [level(cap, -10), level(cap, 0), level(cap, 10)]
lekos = [btn(f"Ctrl+{i}", f"LEKO {i}") for i in (1, 2, 3)]

page("1 SHOW", look_row("") + [auto, TAP] + onoff + quick_pos + [foh70, foh40, None] + [fondu, blackout])
page("2 LOOKS", look_row("Shift+") + look_row("Ctrl+") + [auto, TAP, foh70] + lekos + [fondu, blackout])
page("3 PAR", keyed("Alt+", "ABCDEFGHIJKLMNOPQRST") + keyed("Alt+Shift+", "ABCDEFGHIJ"))
page("4 TÊTES", keyed("Ctrl+Shift+", "ABCDEFGHIJ") + keyed("Ctrl+Shift+", "KLMNOPQR")
     + keyed("Ctrl+Shift+", "TUVWY") + [None, None, None, TAP, None, fondu, blackout])
page("5 POSITIONS", keyed("Shift+", "ABCDEFGHIJK") + [None] * 5 + keyed("Shift+", "LMNOPQ")
     + [None, None, TAP, None, fondu, blackout])

page("6 FOH", [foh70, foh40, None] + lekos + [None, None]
     + level_row("FOH") + [None] + level_row("L1") + [None]
     + level_row("L2") + [None] + level_row("L3") + [None]
     + [None, None, None, None, fondu, blackout])

# ------------------------------------------------------------ écriture
prof_uuid = str(uuid.uuid4()).upper()
root = f"{prof_uuid}.sdProfile"
zf = zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED)
ids = [p[0] for p in pages]
zf.writestr(f"{root}/manifest.json", json.dumps({
    "AppIdentifier": "*",
    "Device": {"Model": MODEL, "UUID": ""},
    "Name": "Show Rock (QLC+)",
    "Pages": {"Current": ids[0], "Default": ids[0], "Pages": ids},
    "Version": "2.0"}, ensure_ascii=False, indent=1))

for pid, name, grid in pages:
    pdir = f"{root}/Profiles/{b32(pid)}"
    actions = {}
    for (c, r), it in sorted(grid.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        aid = str(uuid.uuid4())
        if it[0] in ("prev", "next"):
            title = "◀\n" + "PAGE" if it[0] == "prev" else "PAGE\n▶"
            img = f"Images/k{c}{r}.png"
            zf.writestr(f"{pdir}/{img}", icon(0x202020, folder=False))
            actions[f"{c},{r}"] = {
                "ActionID": aid, "LinkedTitle": True,
                "Name": "Previous Page" if it[0] == "prev" else "Next Page", "Settings": {}, "State": 0,
                "States": [{"Image": img, "Title": title, "ShowTitle": True, "TitleAlignment": "middle",
                            "TitleColor": "#ffffff", "FontSize": 10, "FontStyle": "Bold", "FontFamily": "",
                            "FontUnderline": False, "OutlineThickness": 2}],
                "UUID": "com.elgato.streamdeck.page." + ("previous" if it[0] == "prev" else "next")}
            continue
        kind, title, target, col = it

        def st(img_name, on):
            zf.writestr(f"{pdir}/{img_name}", icon(col, on=on))
            dim = None if col is None else (int(((col >> 16) & 255) * .55) << 16 | int(((col >> 8) & 255) * .55) << 8
                                            | int((col & 255) * .55))
            return {"Image": img_name, "Title": wrap(title), "ShowTitle": True, "TitleAlignment": "middle",
                    "TitleColor": text_color(col if on else dim), "FontSize": 9, "FontStyle": "Bold",
                    "FontFamily": "", "FontUnderline": False, "OutlineThickness": 2}
        if kind == "level":
            wid, step, cap = target
            actions[f"{c},{r}"] = {"ActionID": aid, "LinkedTitle": False, "Name": "Niveau QLC+ (fader)",
                                   "Plugin": {"Name": "QLC+ Show", "UUID": PLUGIN, "Version": "1.1.0.0"},
                                   "Settings": {"widgetId": wid, "step": str(step), "label": cap}, "State": 0,
                                   "States": [st(f"Images/k{c}{r}.png", step == 0)],
                                   "UUID": PLUGIN + ".level"}
        elif kind == "hotkey":
            actions[f"{c},{r}"] = {"ActionID": aid, "LinkedTitle": True, "Name": "Hotkey",
                                   "Settings": hotkey_settings(target), "State": 0,
                                   "States": [st(f"Images/k{c}{r}.png", True)],
                                   "UUID": "com.elgato.streamdeck.system.hotkey"}
        else:
            wid, mode = target
            actions[f"{c},{r}"] = {"ActionID": aid, "LinkedTitle": True, "Name": "Bouton QLC+",
                                   "Plugin": {"Name": "QLC+ Show", "UUID": PLUGIN, "Version": "1.1.0.0"},
                                   "Settings": {"widgetId": wid, "mode": mode}, "State": 0,
                                   "States": [st(f"Images/k{c}{r}.png", False), st(f"Images/k{c}{r}on.png", True)],
                                   "UUID": PLUGIN + ".button"}
    zf.writestr(f"{pdir}/manifest.json", json.dumps(
        {"Controllers": [{"Actions": actions, "Type": "Keypad"}], "Icon": "", "Name": name},
        ensure_ascii=False, indent=1))
zf.close()

print(f"OK -> {os.path.abspath(OUT)}")
for pid, name, grid in pages:
    print(f"  {name:12s} {len(grid):2d} touches")

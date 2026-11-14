#!/usr/bin/env python3
"""
Génère show/Show-Rock-XL.streamDeckProfile (Stream Deck XL, 32 touches) à partir de Show-Rock.qxw.

Chaque touche envoie le raccourci clavier du bouton QLC+ correspondant (action Système → Raccourci).
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

# ------------------------------------------------------------ lecture du show
keys = {}                      # raccourci -> (caption une ligne, bg int|None)
tree = ET.parse(QXW)
for b in tree.getroot().iter("{%s}Button" % NS["q"]):
    k = b.find("q:Key", NS)
    if k is None or not k.text:
        continue
    bg = b.find("q:Appearance/q:BackgroundColor", NS)
    col = int(bg.text) & 0xFFFFFF if bg is not None and bg.text != "Default" else None
    keys[k.text] = (b.get("Caption").replace("\n", " "), col)
tap_key = None
for sd in tree.getroot().iter("{%s}SpeedDial" % NS["q"]):
    k = sd.find("q:Key", NS)
    if k is not None:
        tap_key = k.text


def btn(key, title=None):
    caption, col = keys[key]
    return ("hotkey", title or caption, key, col)


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
def icon(col, folder=False):
    col = 0x333333 if col is None else col
    rgb = ((col >> 16) & 255, (col >> 8) & 255, col & 255)
    im = Image.new("RGB", (288, 288), (0, 0, 0))
    d = ImageDraw.Draw(im)
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


# ------------------------------------------------------------ pages
pages = {}                      # page uuid -> (name, {(c, r): item})


def page(name, items, back=False):
    pid = str(uuid.uuid4())
    slots = [(c, r) for r in range(ROWS) for c in range(COLS)]
    if back:
        slots = slots[1:]
    grid = {(0, 0): ("back",)} if back else {}
    for slot, it in zip(slots, items):
        if it is not None:
            grid[slot] = it
    assert len([i for i in items if i is not None]) <= len(slots), name
    pages[pid] = (name, grid)
    return pid


def folder(title, pid, col=0x444444):
    return ("folder", title, pid, col)


def look_row(mod):
    return [btn(f"{mod}F{i}") for i in range(1, 11)]


def keyed(prefix, letters):
    return [btn(f"{prefix}{c}") for c in letters]


auto = btn("F11", "▶ AUTO")

p_looks2 = page("Looks 2", look_row("Shift+") + [None] * 10 + [auto, TAP], back=True)
p_looks3 = page("Looks 3", look_row("Ctrl+") + [None] * 10 + [auto, TAP], back=True)
p_par = page("PAR", keyed("Alt+", "ABCDEFGHIJKLMNOPQRST") + keyed("Alt+Shift+", "ABCDEFGHIJ"), back=True)
p_heads = page("Têtes", keyed("Ctrl+Shift+", "ABCDEFGHIJ") + keyed("Ctrl+Shift+", "KLMNOPQR")
               + keyed("Ctrl+Shift+", "TUVWY"), back=True)
p_pos = page("Positions", keyed("Shift+", "ABCDEFGHIJK") + [None] * 5 + keyed("Shift+", "LMNOPQ")
             + [None, None, TAP], back=True)

main_items = (
    look_row("")[:8]
    + look_row("")[8:10] + [auto, TAP,
                            folder("LOOKS 2 ▸", p_looks2, 0x5A2A5A), folder("LOOKS 3 ▸", p_looks3, 0x5A2A5A),
                            folder("PAR ▸", p_par, 0x2F5A9A), folder("TÊTES ▸", p_heads, 0x9A3A2A)]
    + [btn("Alt+Shift+K", "STROBE\nPAR"), btn("Alt+Shift+L", "BLINDER"),
       btn("Alt+Shift+M", "STROBE\nTÊTES"), btn("Alt+Shift+N", "STROBE\nFOU"),
       btn("G", "BUMP\nGAUCHE"), btn("H", "BUMP\nDROITE"),
       btn("J", "FLASH\nROUGE"), btn("K", "FLASH\nBLEU")]
    + [btn("L", "FLASH\nUV"), btn("M", "FLASH\nTÊTES"),
       folder("POSITIONS ▸", p_pos, 0x204060),
       btn("Shift+D", "→ Chanteur"), btn("Shift+C", "→ Band"), btn("Shift+B", "→ Public"),
       btn("N", "FONDU\nAU NOIR"), btn("X", "BLACKOUT")]
)
p_main = page("Show Rock", main_items)

# ------------------------------------------------------------ écriture
prof_uuid = str(uuid.uuid4()).upper()
root = f"{prof_uuid}.sdProfile"
zf = zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED)
zf.writestr(f"{root}/manifest.json", json.dumps({
    "AppIdentifier": "*",
    "Device": {"Model": MODEL, "UUID": ""},
    "Name": "Show Rock (QLC+)",
    "Pages": {"Current": p_main, "Default": p_main, "Pages": [p_main]},
    "Version": "2.0"}, ensure_ascii=False, indent=1))

for pid, (name, grid) in pages.items():
    pdir = f"{root}/Profiles/{b32(pid)}"
    actions = {}
    for n, ((c, r), it) in enumerate(sorted(grid.items(), key=lambda kv: (kv[0][1], kv[0][0]))):
        aid = str(uuid.uuid4())
        if it[0] == "back":
            actions[f"{c},{r}"] = {"ActionID": aid, "LinkedTitle": True, "Name": "Parent Folder",
                                   "Settings": {}, "State": 0, "States": [{}],
                                   "UUID": "com.elgato.streamdeck.profile.backtoparent"}
            continue
        kind, title, target, col = it
        img = f"Images/k{c}{r}.png"
        zf.writestr(f"{pdir}/{img}", icon(col, folder=(kind == "folder")))
        state = {"Image": img, "Title": title, "ShowTitle": True, "TitleAlignment": "middle",
                 "TitleColor": text_color(col), "FontSize": 11, "FontStyle": "Bold",
                 "FontFamily": "", "FontUnderline": False, "OutlineThickness": 2}
        if kind == "folder":
            actions[f"{c},{r}"] = {"ActionID": aid, "LinkedTitle": True, "Name": "Create Folder",
                                   "Settings": {"ProfileUUID": target}, "State": 0, "States": [state],
                                   "UUID": "com.elgato.streamdeck.profile.openchild"}
        else:
            actions[f"{c},{r}"] = {"ActionID": aid, "LinkedTitle": True, "Name": "Hotkey",
                                   "Settings": hotkey_settings(target), "State": 0, "States": [state],
                                   "UUID": "com.elgato.streamdeck.system.hotkey"}
    zf.writestr(f"{pdir}/manifest.json", json.dumps(
        {"Controllers": [{"Actions": actions, "Type": "Keypad"}], "Icon": "", "Name": name},
        ensure_ascii=False, indent=1))
zf.close()

print(f"OK -> {os.path.abspath(OUT)}")
for pid, (name, grid) in pages.items():
    print(f"  {name:10s} {len(grid):2d} touches")

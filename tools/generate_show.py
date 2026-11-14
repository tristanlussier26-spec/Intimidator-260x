#!/usr/bin/env python3
"""
Génère le workspace QLC+ « Show Rock » (show/Show-Rock.qxw).

Patch (Universe 1, adresses DMX 1-based) :
  - Têtes 1-4 : Chauvet Intimidator Spot 260X, mode 14 Channel -> 1, 15, 29, 43
  - PAR 1-12 (gauche -> droite) : Blizzard Lighting Hotbox EXA, 11 Channel Mode -> 66, 77, ... 187

Relancer :  python3 tools/generate_show.py
Pour changer une adresse ou ajouter un fixture, modifie les constantes plus bas.
"""
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

OUT = os.path.join(os.path.dirname(__file__), "..", "show", "Show-Rock.qxw")

# ---------------------------------------------------------------- Patch
HEAD_MODEL = ("Chauvet", "Intimidator Spot 260X", "14 Channel", 14)
HEAD_ADDR = [1, 15, 29, 43]
PAR_MODEL = ("Blizzard Lighting", "Hotbox EXA", "11 Channel Mode", 11)
PAR_FIRST, PAR_COUNT = 66, 12

# Canaux (index 0-based dans le mode)
H_PAN, H_PANF, H_TILT, H_TILTF, H_SPEED, H_COLOR, H_GOBO, H_GROT, H_PRISM, H_FOCUS, \
    H_DIM, H_STROBE, H_FUNC, H_MACRO = range(14)
P_DIM, P_R, P_G, P_B, P_A, P_W, P_UV, P_STROBE, P_PROG, P_SPEED, P_32B = range(11)

H_SHUTTER_OPEN = 255   # 216-255 = On (0-3 = fermé !)

fixtures = []          # (id, name, model, addr0)
for i, a in enumerate(HEAD_ADDR):
    fixtures.append((len(fixtures), f"Tête {i + 1}", HEAD_MODEL, a - 1))
HEADS = [f[0] for f in fixtures]
for i in range(PAR_COUNT):
    fixtures.append((len(fixtures), f"PAR {i + 1}", PAR_MODEL, PAR_FIRST - 1 + i * PAR_MODEL[3]))
PARS = [f[0] for f in fixtures if f[2] is PAR_MODEL]

# ---------------------------------------------------------------- Helpers
ws = ET.Element("Workspace", {"xmlns": "http://www.qlcplus.org/Workspace",
                              "CurrentWindow": "VirtualConsole"})
cr = ET.SubElement(ws, "Creator")
ET.SubElement(cr, "Name").text = "Q Light Controller Plus"
ET.SubElement(cr, "Version").text = "4.12.7"
ET.SubElement(cr, "Author").text = "LeQueb"
engine = ET.SubElement(ws, "Engine")

iomap = ET.SubElement(engine, "InputOutputMap")
uni = ET.SubElement(iomap, "Universe", {"Name": "Universe 1", "ID": "0"})
ET.SubElement(uni, "Output", {"Plugin": "DMX USB", "Line": "0"})

for fid, name, (man, model, mode, nch), addr in fixtures:
    fx = ET.SubElement(engine, "Fixture")
    for tag, val in (("Manufacturer", man), ("Model", model), ("Mode", mode), ("ID", fid),
                     ("Name", name), ("Universe", 0), ("Address", addr), ("Channels", nch)):
        ET.SubElement(fx, tag).text = str(val)


def group(gid, name, members):
    g = ET.SubElement(engine, "FixtureGroup", {"ID": str(gid)})
    ET.SubElement(g, "Name").text = name
    ET.SubElement(g, "Size", {"X": str(len(members)), "Y": "1"})
    for x, fid in enumerate(members):
        ET.SubElement(g, "Head", {"X": str(x), "Y": "0", "Fixture": str(fid)}).text = "0"


G_PAR, G_HEADS = 0, 1
group(G_PAR, "PAR (gauche → droite)", PARS)
group(G_HEADS, "Têtes", HEADS)

_fid = [0]


def new_func(ftype, name, path):
    f = ET.SubElement(engine, "Function", {"ID": str(_fid[0]), "Type": ftype, "Name": name,
                                           "Path": path})
    _fid[0] += 1
    return f, _fid[0] - 1


def scene(name, path, values, fade_in=0):
    """values: {fixture_id: {channel: value}}"""
    f, fid = new_func("Scene", name, path)
    ET.SubElement(f, "Speed", {"FadeIn": str(fade_in), "FadeOut": "0", "Duration": "0"})
    for fx in sorted(values):
        chans = values[fx]
        txt = ",".join(f"{c},{v}" for c, v in sorted(chans.items()))
        ET.SubElement(f, "FixtureVal", {"ID": str(fx)}).text = txt
    return fid


def chaser(name, path, steps, hold=500):
    f, fid = new_func("Chaser", name, path)
    ET.SubElement(f, "Speed", {"FadeIn": "0", "FadeOut": "0", "Duration": str(hold)})
    ET.SubElement(f, "Direction").text = "Forward"
    ET.SubElement(f, "RunOrder").text = "Loop"
    ET.SubElement(f, "SpeedModes", {"FadeIn": "Default", "FadeOut": "Default", "Duration": "Common"})
    for n, sid in enumerate(steps):
        ET.SubElement(f, "Step", {"Number": str(n), "FadeIn": "0", "Hold": "0",
                                  "FadeOut": "0"}).text = str(sid)
    return fid


def matrix(name, script, color1, color2=None, props=None, duration=500, fade=0):
    f, fid = new_func("RGBMatrix", name, "PAR/Effets")
    ET.SubElement(f, "Speed", {"FadeIn": str(fade), "FadeOut": str(fade), "Duration": str(duration)})
    ET.SubElement(f, "Direction").text = "Forward"
    ET.SubElement(f, "RunOrder").text = "Loop"
    ET.SubElement(f, "Algorithm", {"Type": "Script"}).text = script
    ET.SubElement(f, "MonoColor").text = str(0xFF000000 | color1)
    if color2 is not None:
        ET.SubElement(f, "EndColor").text = str(0xFF000000 | color2)
    ET.SubElement(f, "ControlMode").text = "RGB"
    ET.SubElement(f, "FixtureGroup").text = str(G_PAR)
    for k, v in (props or {}).items():
        ET.SubElement(f, "Property", {"Name": k, "Value": v})
    return fid


def efx(name, algo, width, height, duration=4000, xfreq=2, yfreq=3):
    f, fid = new_func("EFX", name, "Têtes/Mouvements")
    for n, h in enumerate(HEADS):
        fx = ET.SubElement(f, "Fixture")
        ET.SubElement(fx, "ID").text = str(h)
        ET.SubElement(fx, "Head").text = "0"
        ET.SubElement(fx, "Mode").text = "0"
        ET.SubElement(fx, "Direction").text = "Forward"
        ET.SubElement(fx, "StartOffset").text = str(n * 90)   # décalage en éventail
    ET.SubElement(f, "PropagationMode").text = "Parallel"
    ET.SubElement(f, "Speed", {"FadeIn": "0", "FadeOut": "0", "Duration": str(duration)})
    ET.SubElement(f, "Direction").text = "Forward"
    ET.SubElement(f, "RunOrder").text = "Loop"
    ET.SubElement(f, "Algorithm").text = algo
    ET.SubElement(f, "Width").text = str(width)
    ET.SubElement(f, "Height").text = str(height)
    ET.SubElement(f, "Rotation").text = "0"
    ET.SubElement(f, "StartOffset").text = "0"
    ET.SubElement(f, "IsRelative").text = "1"      # bouge autour de la position active
    for axis, freq, phase in (("X", xfreq, 90), ("Y", yfreq, 0)):
        a = ET.SubElement(f, "Axis", {"Name": axis})
        ET.SubElement(a, "Offset").text = "127"
        ET.SubElement(a, "Frequency").text = str(freq)
        ET.SubElement(a, "Phase").text = str(phase)
    return fid


# ---------------------------------------------------------------- PAR : couleurs
PAR_COLORS = [  # nom, (R, G, B, A, W, UV), couleur du bouton
    ("Rouge", (255, 0, 0, 0, 0, 0), 0xD01010),
    ("Bleu", (0, 0, 255, 0, 0, 0), 0x1030E0),
    ("Vert", (0, 255, 0, 0, 0, 0), 0x10B030),
    ("Ambre", (0, 0, 0, 255, 0, 0), 0xFF9A10),
    ("Blanc", (0, 0, 0, 0, 255, 0), 0xF0F0F0),
    ("Blanc chaud", (0, 0, 0, 160, 255, 0), 0xFFD9A0),
    ("Magenta", (255, 0, 200, 0, 0, 0), 0xE020C0),
    ("Cyan", (0, 255, 255, 0, 0, 0), 0x20E0E0),
    ("Or", (255, 90, 0, 200, 0, 0), 0xFFB000),
    ("Mauve", (120, 0, 255, 0, 0, 160), 0x8030E0),
    ("UV", (0, 0, 0, 0, 0, 255), 0x5010A0),
]
par_color_ids = {}
for name, rgbawu, _ in PAR_COLORS:
    vals = {p: dict(zip((P_R, P_G, P_B, P_A, P_W, P_UV), rgbawu)) for p in PARS}
    par_color_ids[name] = scene(f"PAR {name}", "PAR/Couleurs", vals)

# Split pair / impair
def split(c1, c2):
    a = dict(zip((P_R, P_G, P_B, P_A, P_W, P_UV), c1))
    b = dict(zip((P_R, P_G, P_B, P_A, P_W, P_UV), c2))
    return {p: (a if i % 2 == 0 else b) for i, p in enumerate(PARS)}

par_color_ids["Rouge / Bleu"] = scene("PAR Rouge / Bleu", "PAR/Couleurs",
                                      split((255, 0, 0, 0, 0, 0), (0, 0, 255, 0, 0, 0)))

# Strobe / blinder (flash)
strobe_par = scene("PAR Strobe blanc", "PAR/Flash",
                   {p: {P_DIM: 255, P_R: 255, P_G: 255, P_B: 255, P_W: 255, P_STROBE: 230} for p in PARS})
blinder = scene("PAR Blinder", "PAR/Flash",
                {p: {P_DIM: 255, P_R: 255, P_G: 255, P_B: 255, P_A: 255, P_W: 255} for p in PARS})

# Effets PAR
chase_cols = chaser("PAR Chase couleurs", "PAR/Effets",
                    [par_color_ids[c] for c in ("Rouge", "Bleu", "Ambre", "Magenta")])
fx_wave = matrix("PAR Vague rouge", "Waves", 0xFF0000, props={"taillength": "60", "tailfade": "Yes"})
fx_one = matrix("PAR Un par un", "One By One", 0x0040FF)
fx_evenodd = matrix("PAR Pair/Impair", "Even/Odd", 0xFF0000, 0x0000FF)
fx_rainbow = matrix("PAR Arc-en-ciel", "Gradient", 0xFF0000, props={"presetIndex": "Rainbow"},
                    duration=80)
fx_center = matrix("PAR Remplir centre", "Fill Unfill From Center", 0xFFA000)
fx_random = matrix("PAR Aléatoire", "Random Single", 0xFFFFFF, duration=120)

# ---------------------------------------------------------------- Têtes
HEAD_COLORS = [("Blanc", 3, 0xF0F0F0), ("Rouge", 10, 0xD01010), ("Orange", 17, 0xFF7A10),
               ("Jaune", 24, 0xF0E010), ("Vert", 31, 0x10B030), ("Bleu", 38, 0x1030E0),
               ("CTO", 45, 0xFFC080), ("Cyan", 52, 0x20E0E0), ("Magenta", 59, 0xE020C0),
               ("Arc-en-ciel", 200, 0x909090)]
head_color_ids = {}
for name, val, _ in HEAD_COLORS:
    head_color_ids[name] = scene(f"Têtes {name}", "Têtes/Couleurs",
                                 {h: {H_COLOR: val, H_STROBE: H_SHUTTER_OPEN, H_FUNC: 0, H_MACRO: 0}
                                  for h in HEADS})

GOBOS = [("Ouvert", 3)] + [(f"Gobo {i}", 3 + 8 * i) for i in range(1, 8)]
gobo_ids = {}
for name, val in GOBOS:
    gobo_ids[name] = scene(f"Têtes {name}", "Têtes/Gobos",
                           {h: {H_GOBO: val, H_GROT: 0, H_STROBE: H_SHUTTER_OPEN} for h in HEADS})
gobo_rot = scene("Têtes Rotation gobo", "Têtes/FX", {h: {H_GROT: 40} for h in HEADS})
prism = scene("Têtes Prisme", "Têtes/FX", {h: {H_PRISM: 128} for h in HEADS})
strobe_heads = scene("Têtes Strobe", "Têtes/FX",
                     {h: {H_DIM: 255, H_COLOR: 3, H_STROBE: 60} for h in HEADS})

# Positions : (pan, tilt) par tête, de gauche à droite. Points de départ à ajuster sur place.
POSITIONS = [
    ("Centre", [(128, 128)] * 4),
    ("Public", [(128, 70)] * 4),
    ("Band", [(128, 185)] * 4),
    ("Chanteur", [(140, 175), (134, 180), (122, 180), (116, 175)]),
    ("Croisé", [(150, 160), (140, 160), (116, 160), (106, 160)]),
    ("Éventail", [(100, 90), (118, 90), (138, 90), (156, 90)]),
    ("Plafond", [(128, 30)] * 4),
]
pos_ids = {}
for name, pts in POSITIONS:
    pos_ids[name] = scene(f"Position {name}", "Têtes/Positions",
                          {h: {H_PAN: p, H_PANF: 0, H_TILT: t, H_TILTF: 0, H_SPEED: 0}
                           for h, (p, t) in zip(HEADS, pts)}, fade_in=0)

efx_ids = {
    "Cercle": efx("Têtes Cercle", "Circle", 40, 40),
    "Huit": efx("Têtes Huit", "Eight", 50, 40),
    "Balayage": efx("Têtes Balayage", "Line", 80, 10, xfreq=1, yfreq=1),
    "Diamant": efx("Têtes Diamant", "Diamond", 40, 40),
    "Ballyhoo": efx("Têtes Ballyhoo", "Lissajous", 70, 50, duration=6000),
}

# ---------------------------------------------------------------- Virtual Console
vc = ET.SubElement(ws, "VirtualConsole")
_wid = [0]


def wid():
    _wid[0] += 1
    return str(_wid[0])


def appearance(parent, bg=None, fg=None, style="None"):
    a = ET.SubElement(parent, "Appearance")
    ET.SubElement(a, "FrameStyle").text = style
    ET.SubElement(a, "ForegroundColor").text = str(0xFF000000 | fg) if fg is not None else "Default"
    ET.SubElement(a, "BackgroundColor").text = str(0xFF000000 | bg) if bg is not None else "Default"
    ET.SubElement(a, "BackgroundImage").text = "None"
    ET.SubElement(a, "Font").text = "Default"


def winstate(parent, x, y, w, h):
    ET.SubElement(parent, "WindowState", {"Visible": "False", "X": str(x), "Y": str(y),
                                          "Width": str(w), "Height": str(h)})


def frame(parent, caption, x, y, w, h, solo=False, bg=None):
    f = ET.SubElement(parent, "SoloFrame" if solo else "Frame", {"Caption": caption, "ID": wid()})
    appearance(f, bg=bg, style="Sunken")
    winstate(f, x, y, w, h)
    for tag, val in (("AllowChildren", "True"), ("AllowResize", "True"), ("ShowHeader", "True"),
                     ("ShowEnableButton", "False")):
        ET.SubElement(f, tag).text = val
    if solo:
        ET.SubElement(f, "Mixing").text = "False"
    ET.SubElement(f, "Collapsed").text = "False"
    ET.SubElement(f, "Disabled").text = "False"
    return f


def text_color_for(bg):
    r, g, b = (bg >> 16) & 255, (bg >> 8) & 255, bg & 255
    return 0x000000 if (r * 299 + g * 587 + b * 114) / 1000 > 140 else 0xFFFFFF


def button(parent, caption, fid, x, y, w=105, h=80, action="Toggle", bg=None, key=None):
    b = ET.SubElement(parent, "Button", {"Caption": caption, "ID": wid(), "Icon": ""})
    winstate(b, x, y, w, h)
    appearance(b, bg=bg, fg=text_color_for(bg) if bg is not None else None)
    ET.SubElement(b, "Function", {"ID": str(fid)})
    ET.SubElement(b, "Action").text = action
    if key:
        ET.SubElement(b, "Key").text = key
    ET.SubElement(b, "Intensity", {"Adjust": "False"}).text = "100"
    return b


def grid(parent, items, cols, w=105, h=80, gap=8, top=35, left=10, action="Toggle"):
    for i, (cap, fid, bg) in enumerate(items):
        r, c = divmod(i, cols)
        button(parent, cap, fid, left + c * (w + gap), top + r * (h + gap), w, h, action, bg)


def level_slider(parent, caption, channels, x, y, w=90, h=260, value=255):
    s = ET.SubElement(parent, "Slider", {"Caption": caption, "ID": wid(), "WidgetStyle": "Slider",
                                         "InvertedAppearance": "false"})
    winstate(s, x, y, w, h)
    appearance(s)
    ET.SubElement(s, "SliderMode", {"ValueDisplayStyle": "Percentage",
                                    "ClickAndGoType": "None", "Monitor": "false"}).text = "Level"
    lv = ET.SubElement(s, "Level", {"LowLimit": "0", "HighLimit": "255", "Value": str(value)})
    for fx, ch in channels:
        ET.SubElement(lv, "Channel", {"Fixture": str(fx)}).text = str(ch)
    pb = ET.SubElement(s, "Playback")
    ET.SubElement(pb, "Function").text = "4294967295"


root = ET.SubElement(vc, "Frame", {"Caption": ""})
appearance(root, bg=0x1A1A1A)

# --- PAR (couleurs + effets dans le même solo frame = un seul look à la fois)
f = frame(root, "PAR — COULEURS & EFFETS", 10, 10, 670, 320, solo=True)
items = [(n, par_color_ids[n], bg) for n, _, bg in PAR_COLORS] + \
        [("Rouge / Bleu", par_color_ids["Rouge / Bleu"], 0x902090)]
fx_items = [("Chase couleurs", chase_cols, 0x404040), ("Vague", fx_wave, 0x404040),
            ("Un par un", fx_one, 0x404040), ("Pair / Impair", fx_evenodd, 0x404040),
            ("Arc-en-ciel", fx_rainbow, 0x404040), ("Remplir centre", fx_center, 0x404040)]
grid(f, items + fx_items, cols=6, w=100)

# --- Masters + tempo
f = frame(root, "MASTERS", 10, 340, 670, 310)
level_slider(f, "PAR", [(p, P_DIM) for p in PARS], 15, 35)
level_slider(f, "Têtes", [(h, H_DIM) for h in HEADS], 115, 35)
sd = ET.SubElement(f, "SpeedDial", {"Caption": "TEMPO (tap)", "ID": wid()})
winstate(sd, 230, 35, 220, 260)
appearance(sd)
ET.SubElement(sd, "AbsoluteValue", {"Minimum": "0", "Maximum": "10000"})
ET.SubElement(sd, "Time").text = "500"
for fid_ in (chase_cols, fx_wave, fx_one, fx_evenodd, fx_center, fx_random):
    ET.SubElement(sd, "Function", {"FadeIn": "0", "FadeOut": "0", "Duration": "6"}).text = str(fid_)
for fid_ in efx_ids.values():  # 1 tour d'EFX = 8 temps
    ET.SubElement(sd, "Function", {"FadeIn": "0", "FadeOut": "0", "Duration": "9"}).text = str(fid_)
button(f, "PAR Aléatoire", fx_random, 465, 35, 210, 80, bg=0x404040)
button(f, "Strobe PAR\n(maintenir)", strobe_par, 465, 125, 100, 80, action="Flash", bg=0xFFFFFF, key="S")
button(f, "Blinder\n(maintenir)", blinder, 575, 125, 100, 80, action="Flash", bg=0xFFE070, key="B")
button(f, "Strobe têtes\n(maintenir)", strobe_heads, 465, 215, 100, 80, action="Flash", bg=0xC0C0C0, key="D")

# --- Urgence
f = frame(root, "GÉNÉRAL", 10, 660, 670, 140)
button(f, "BLACKOUT", 4294967295, 10, 35, 220, 95, action="Blackout", bg=0x000000, key="X")
b = button(f, "TOUT ARRÊTER", 4294967295, 240, 35, 220, 95, action="StopAll", bg=0x802020)
b.find("Action").set("FadeOut", "0")

# --- Têtes : couleurs / gobos / fx
f = frame(root, "TÊTES — COULEUR", 690, 10, 560, 220, solo=True)
grid(f, [(n, head_color_ids[n], bg) for n, _, bg in HEAD_COLORS], cols=5, w=100)
f = frame(root, "TÊTES — GOBO", 690, 240, 560, 220, solo=True)
grid(f, [(n, gobo_ids[n], 0x303050) for n, _ in GOBOS], cols=5, w=100)
f = frame(root, "TÊTES — FX", 690, 470, 560, 130)
grid(f, [("Rotation gobo", gobo_rot, 0x305030), ("Prisme", prism, 0x305030)], cols=5, w=100)

# --- Positions / XY pad / mouvements
f = frame(root, "TÊTES — POSITION", 1260, 10, 560, 220, solo=True)
grid(f, [(n, pos_ids[n], 0x204060) for n, _ in POSITIONS], cols=5, w=100)

xy = ET.SubElement(root, "XYPad", {"Caption": "POSITION LIVE (4 têtes)", "ID": wid(),
                                   "InvertedAppearance": "0"})
winstate(xy, 1260, 240, 280, 360)
appearance(xy)
for h in HEADS:
    fx = ET.SubElement(xy, "Fixture", {"ID": str(h), "Head": "0"})
    ET.SubElement(fx, "Axis", {"ID": "X", "LowLimit": "0", "HighLimit": "1", "Reverse": "False"})
    ET.SubElement(fx, "Axis", {"ID": "Y", "LowLimit": "0", "HighLimit": "1", "Reverse": "False"})
ET.SubElement(xy, "Pan", {"Position": "127"})
ET.SubElement(xy, "Tilt", {"Position": "127"})

f = frame(root, "TÊTES — MOUVEMENT", 1550, 240, 270, 360, solo=True)
grid(f, [(n, i, 0x603060) for n, i in efx_ids.items()], cols=2, w=120, h=70)

props = ET.SubElement(vc, "Properties")
ET.SubElement(props, "Size", {"Width": "1920", "Height": "1080"})
ET.SubElement(props, "GrandMaster", {"ChannelMode": "Intensity", "ValueMode": "Reduce",
                                     "SliderMode": "Normal"})

# ---------------------------------------------------------------- Écriture
os.makedirs(os.path.dirname(OUT), exist_ok=True)
xml = minidom.parseString(ET.tostring(ws, encoding="unicode")).toprettyxml(indent=" ")
xml = xml.replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE Workspace>', 1)
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(xml)
print(f"OK -> {os.path.abspath(OUT)}  ({_fid[0]} fonctions, {_wid[0]} widgets)")

#!/usr/bin/env python3
"""
Génère le workspace QLC+ « Show Rock » (show/Show-Rock.qxw).

Patch (Universe 1, adresses DMX 1-based) :
  - Têtes 1-4 : Chauvet Intimidator Spot 260X, mode 14 Channel -> 1, 15, 29, 43
  - PAR 1-4 (gauche -> droite) : Blizzard Lighting Hotbox EXA, 11 Channel Mode -> 66, 77, 88, 99

Relancer :  python3 tools/generate_show.py
Pour changer une adresse ou ajouter un fixture, modifie les constantes plus bas.
"""
import os
import xml.etree.ElementTree as ET

OUT = os.path.join(os.path.dirname(__file__), "..", "show", "Show-Rock.qxw")

# ---------------------------------------------------------------- Patch
HEAD_MODEL = ("Chauvet", "Intimidator Spot 260X", "14 Channel", 14)
HEAD_ADDR = [1, 15, 29, 43]
PAR_MODEL = ("Blizzard Lighting", "Hotbox EXA", "11 Channel Mode", 11)
PAR_FIRST, PAR_COUNT = 66, 4
# PAR ajoutés, en mode « couleurs seulement » (fixtures Generic inclus dans QLC+, rien à installer)
MOS_MODEL = ("MOSFiATA", "PAR 36 RGB", "7 Channel", 7)   # MOSFiATA 36 LED RGB : dimmer R G B strobe mode vitesse
MOS_DIM, MOS_STROBE, MOS_MODE, MOS_SPEED = 0, 4, 5, 6
UK_MODEL = ("UKing", "ZQ01061 RGBW Par", "8 Channel", 8)   # U`King 18x10W RGBW, mode 8 canaux (A001)
UK_DIM, UK_STROBE, UK_FUNC, UK_SPEED = 0, 5, 6, 7
# D'après le plan de la salle (x : 0 = gauche de la scène, 1 = droite, vu du public)
MOS = [  # nom, adresse, x, rôle
    ("M1 contre", 160, 0.10, "back"), ("M2 contre", 167, 0.30, "back"),
    ("M3 contre", 174, 0.61, "back"), ("M4 contre", 181, 0.80, "back"),
    ("M5 face G", 188, 0.00, "front"), ("M6 face D", 195, 1.00, "front"),
    ("M7 public", 202, -0.05, "crowd"), ("M8 public", 209, -0.04, "crowd"),
]
UK = [("U1 face", 134, 0.33, "front"), ("U2 face", 142, 0.63, "front")]
POS_HOTBOX = [0.2, 0.4, 0.6, 0.8]
# FOH : 3 lekos sur un dimmer Chauvet DMX-4 (canaux 1-3). Hors du show : aucun look ni effet,
# seulement leurs faders, plafonnés à 70 %.
FOH_ADDR, FOH_LEKOS = 150, 3
FOH_MAX = round(255 * 0.70)            # 178 = 70 %

# Canaux (index 0-based dans le mode)
H_PAN, H_PANF, H_TILT, H_TILTF, H_SPEED, H_COLOR, H_GOBO, H_GROT, H_PRISM, H_FOCUS, \
    H_DIM, H_STROBE, H_FUNC, H_MACRO = range(14)
P_DIM, P_R, P_G, P_B, P_A, P_W, P_UV, P_STROBE, P_PROG, P_SPEED, P_32B = range(11)

H_SHUTTER_OPEN = 255   # 216-255 = On (0-3 = fermé !)

fixtures = []          # (id, name, model, addr0)
for i, a in enumerate(HEAD_ADDR):
    fixtures.append((len(fixtures), f"Tête {i + 1}", HEAD_MODEL, a - 1))
HEADS = [f[0] for f in fixtures]
XPOS = {}
for i in range(PAR_COUNT):
    XPOS[len(fixtures)] = POS_HOTBOX[i]
    fixtures.append((len(fixtures), f"PAR {i + 1}", PAR_MODEL, PAR_FIRST - 1 + i * PAR_MODEL[3]))
HOTBOX = [f[0] for f in fixtures if f[2] is PAR_MODEL]
ROLE = {}
for model, lst in ((MOS_MODEL, MOS), (UK_MODEL, UK)):
    for name, a, x, role in lst:
        XPOS[len(fixtures)], ROLE[len(fixtures)] = x, role
        fixtures.append((len(fixtures), name, model, a - 1))
FOH = len(fixtures)
fixtures.append((FOH, "Lekos FOH (DMX-4)", ("Generic", "Generic", "4 Channel", 4), FOH_ADDR - 1))
RGB_PARS = {f[0]: (7 if f[2] is MOS_MODEL else 8) for f in fixtures if f[2] in (MOS_MODEL, UK_MODEL)}
MOSS = [f for f, n in RGB_PARS.items() if n == 7]
UKS = [f for f, n in RGB_PARS.items() if n == 8]
PARS = sorted(XPOS, key=lambda f: XPOS[f])          # tous les PAR, de gauche à droite
CROWD = [p for p in PARS if ROLE.get(p) == "crowd"]  # éclairent le public : seulement dans les flashs
BACK = [p for p in PARS if ROLE.get(p) == "back"]
STAGE = [p for p in PARS if p not in CROWD]          # couleurs, effets, vagues
LEFT = [p for p in PARS if XPOS[p] < 0.5]
RIGHT = [p for p in PARS if XPOS[p] >= 0.5]

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

# Canaux forcés en HTP : ils retombent à 0 dès que plus aucune fonction ne les demande
# (en LTP, QLC+ garde la dernière valeur → prisme / rotation / strobe coincés, testé).
FORCED_HTP = {
    HEAD_MODEL: [H_GROT, H_PRISM, H_FUNC, H_MACRO],
    PAR_MODEL: [P_STROBE, P_PROG, P_SPEED, P_32B],
    MOS_MODEL: [MOS_STROBE, MOS_MODE, MOS_SPEED],
    UK_MODEL: [UK_STROBE, UK_FUNC, UK_SPEED],
}
for fid, name, model_t, addr in fixtures:
    man, model, mode, nch = model_t
    fx = ET.SubElement(engine, "Fixture")
    for tag, val in (("Manufacturer", man), ("Model", model), ("Mode", mode), ("ID", fid),
                     ("Name", name), ("Universe", 0), ("Address", addr), ("Channels", nch)):
        ET.SubElement(fx, tag).text = str(val)
    if model_t in FORCED_HTP:
        ET.SubElement(fx, "ForcedHTP").text = ",".join(map(str, FORCED_HTP[model_t]))


def group(gid, name, members):
    g = ET.SubElement(engine, "FixtureGroup", {"ID": str(gid)})
    ET.SubElement(g, "Name").text = name
    ET.SubElement(g, "Size", {"X": str(len(members)), "Y": "1"})
    for x, fid in enumerate(members):
        ET.SubElement(g, "Head", {"X": str(x), "Y": "0", "Fixture": str(fid)}).text = "0"


G_PAR, G_HEADS = 0, 1
group(G_PAR, "PAR scène (gauche → droite)", STAGE)
group(G_HEADS, "Têtes", HEADS)

_fid = [0]


def new_func(ftype, name, path):
    f = ET.SubElement(engine, "Function", {"ID": str(_fid[0]), "Type": ftype, "Name": name,
                                           "Path": path})
    _fid[0] += 1
    return f, _fid[0] - 1


def rgbify(chans, nch):
    """Convertit des valeurs Hotbox (R G B Ambre Blanc UV) pour un PAR RGB (3) ou RGBW (4)."""
    keys = (P_R, P_G, P_B, P_A, P_W, P_UV)
    if not any(k in chans for k in keys):
        return {}
    r, g, b, a, w, uv = (chans.get(k, 0) for k in keys)
    if nch == 8:     # U`King 8 canaux : dimmer, R, G, B, W (+ strobe/fonction gérés par BASE)
        out = [255, r + a + uv * .3, g + a * .45, b + uv * .6, w]
    else:            # MOSFiATA 7 canaux : dimmer, R, G, B (le blanc est fait avec R+G+B)
        out = [255, r + a + w * .9 + uv * .3, g + a * .45 + w * .8, b + w * .7 + uv * .6]
    return {i: min(255, int(round(v))) for i, v in enumerate(out)}


def scene(name, path, values, fade_in=0, fade_out=0):
    """values: {fixture_id: {channel: value}} (valeurs Hotbox, converties pour les PAR RGB/RGBW)"""
    f, fid = new_func("Scene", name, path)
    ET.SubElement(f, "Speed", {"FadeIn": str(fade_in), "FadeOut": str(fade_out), "Duration": "0"})
    for fx in sorted(values):
        chans = values[fx]
        if "raw" in chans:                          # canaux bruts, sans conversion
            chans = chans["raw"]
        elif fx in RGB_PARS:
            chans = rgbify(chans, RGB_PARS[fx])
            if not chans:
                continue
        txt = ",".join(f"{c},{v}" for c, v in sorted(chans.items()))
        ET.SubElement(f, "FixtureVal", {"ID": str(fx)}).text = txt
    return fid


def chaser(name, path, steps, hold=500, fade=0, fade_out=None):
    f, fid = new_func("Chaser", name, path)
    ET.SubElement(f, "Speed", {"FadeIn": str(fade), "FadeOut": str(fade if fade_out is None else fade_out),
                               "Duration": str(hold)})
    ET.SubElement(f, "Direction").text = "Forward"
    ET.SubElement(f, "RunOrder").text = "Loop"
    ET.SubElement(f, "SpeedModes", {"FadeIn": "Common", "FadeOut": "Common", "Duration": "Common"})
    for n, sid in enumerate(steps):
        ET.SubElement(f, "Step", {"Number": str(n), "FadeIn": "0", "Hold": "0",
                                  "FadeOut": "0"}).text = str(sid)
    return fid


KICK_HOLD, KICK_FADE = 120, 350        # ms : durée du coup, puis fondu de sortie


def kick(name, scene_id, hold=None, fade_out=None):
    """Coup bref : joue la scène une seule fois puis s'éteint en fondu (pour le Stream Deck)."""
    hold = KICK_HOLD if hold is None else hold
    fade_out = KICK_FADE if fade_out is None else fade_out
    f, fid = new_func("Chaser", name, "Kicks")
    ET.SubElement(f, "Speed", {"FadeIn": "0", "FadeOut": str(fade_out), "Duration": str(hold)})
    ET.SubElement(f, "Direction").text = "Forward"
    ET.SubElement(f, "RunOrder").text = "SingleShot"
    ET.SubElement(f, "SpeedModes", {"FadeIn": "Common", "FadeOut": "Common", "Duration": "Common"})
    ET.SubElement(f, "Step", {"Number": "0", "FadeIn": "0", "Hold": "0", "FadeOut": "0"}).text = str(scene_id)
    return fid


def full(pars, chans):
    return {p: dict(chans) for p in pars}


def collection(name, path, members):
    f, fid = new_func("Collection", name, path)
    for n, sid in enumerate(members):
        ET.SubElement(f, "Step", {"Number": str(n)}).text = str(sid)
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


def efx(name, algo, width, height, head, center, start_offset=0, duration=8000, xfreq=2, yfreq=3, path="Têtes/Mouvements"):
    """EFX ABSOLU pour une seule tête, centré sur center=(pan, tilt).
    (Le mode relatif de QLC+ ne bouge pas en 4.12 : testé.)"""
    f, fid = new_func("EFX", name, path)
    fx = ET.SubElement(f, "Fixture")
    ET.SubElement(fx, "ID").text = str(head)
    ET.SubElement(fx, "Head").text = "0"
    ET.SubElement(fx, "Mode").text = "0"
    ET.SubElement(fx, "Direction").text = "Forward"
    ET.SubElement(fx, "StartOffset").text = str(start_offset)
    ET.SubElement(f, "PropagationMode").text = "Parallel"
    ET.SubElement(f, "Speed", {"FadeIn": "800", "FadeOut": "0", "Duration": str(duration)})
    ET.SubElement(f, "Direction").text = "Forward"
    ET.SubElement(f, "RunOrder").text = "Loop"
    ET.SubElement(f, "Algorithm").text = algo
    ET.SubElement(f, "Width").text = str(width)
    ET.SubElement(f, "Height").text = str(height)
    ET.SubElement(f, "Rotation").text = "0"
    ET.SubElement(f, "StartOffset").text = "0"
    ET.SubElement(f, "IsRelative").text = "0"
    for axis, freq, phase, off in (("X", xfreq, 90, center[0]), ("Y", yfreq, 0, center[1])):
        a = ET.SubElement(f, "Axis", {"Name": axis})
        ET.SubElement(a, "Offset").text = str(off)
        ET.SubElement(a, "Frequency").text = str(freq)
        ET.SubElement(a, "Phase").text = str(phase)
    return fid


# ================================================================ BASE (anti-bug)
# Canaux « LTP » (strobe, prisme, rotation...) gardent leur dernière valeur quand un flash
# ou un bouton s'arrête. BASE tourne en permanence (démarrage auto + dans chaque look) et
# fournit la valeur de repli : strobe PAR fermé, prisme off, rotation off, shutter têtes fermé.
base = scene("BASE (toujours active)", "Système",
             {**{p: {P_STROBE: 0, P_PROG: 0, P_SPEED: 0, P_32B: 0} for p in HOTBOX},
              **{h: {H_STROBE: 0, H_PRISM: 0, H_GROT: 0, H_FUNC: 0, H_MACRO: 0} for h in HEADS},
              **{u: {"raw": {UK_STROBE: 0, UK_FUNC: 0, UK_SPEED: 0}} for u in UKS},
              **{m: {"raw": {MOS_STROBE: 0, MOS_MODE: 0, MOS_SPEED: 0}} for m in MOSS}})
engine.set("Autostart", str(base))

# ================================================================ PAR
COLOR_FADE = 400       # ms : fondu entre deux couleurs PAR
CH6 = (P_R, P_G, P_B, P_A, P_W, P_UV)

PAR_COLORS = [  # nom, (R, G, B, A, W, UV), couleur du bouton
    ("Rouge", (255, 0, 0, 0, 0, 0), 0xD01010),
    ("Rouge sang", (255, 0, 0, 60, 0, 0), 0x8A0A0A),
    ("Orange", (255, 40, 0, 255, 0, 0), 0xFF6A00),
    ("Ambre", (0, 0, 0, 255, 0, 0), 0xFF9A10),
    ("Or", (255, 90, 0, 200, 0, 0), 0xFFB800),
    ("Blanc chaud", (0, 0, 0, 160, 255, 0), 0xFFDDB0),
    ("Blanc froid", (0, 40, 120, 0, 255, 0), 0xE0F0FF),
    ("Cyan", (0, 255, 255, 0, 0, 0), 0x20E0E0),
    ("Bleu", (0, 0, 255, 0, 0, 0), 0x1030E0),
    ("Bleu nuit", (0, 0, 255, 0, 0, 200), 0x101870),
    ("Mauve", (120, 0, 255, 0, 0, 160), 0x7A30E0),
    ("Magenta", (255, 0, 200, 0, 0, 0), 0xE020C0),
    ("Vert", (0, 255, 0, 0, 0, 0), 0x10B030),
    ("UV", (0, 0, 0, 0, 0, 255), 0x400A90),
]
PC = {n: c for n, c, _ in PAR_COLORS}
par_color_ids = {}
for name, c, _ in PAR_COLORS:
    par_color_ids[name] = scene(f"PAR {name}", "PAR/Couleurs",
                                {p: {**dict(zip(CH6, c)), P_STROBE: 0} for p in STAGE}, COLOR_FADE, COLOR_FADE)


def split(name, c1, c2):
    a, b = dict(zip(CH6, PC[c1])), dict(zip(CH6, PC[c2]))
    return scene(f"PAR {name}", "PAR/Couleurs",
                 {p: (a if i % 2 == 0 else b) for i, p in enumerate(STAGE)}, COLOR_FADE, COLOR_FADE)


EDGE = max(1, len(STAGE) // 4)


def sides(name, c_out, c_in):
    """extérieur / centre : PAR des bords vs ceux du milieu"""
    a, b = dict(zip(CH6, PC[c_out])), dict(zip(CH6, PC[c_in]))
    return scene(f"PAR {name}", "PAR/Couleurs",
                 {p: (a if i < EDGE or i >= len(STAGE) - EDGE else b) for i, p in enumerate(STAGE)}, COLOR_FADE, COLOR_FADE)


SPLITS = [
    ("Rouge / Ambre", split("Rouge / Ambre", "Rouge", "Ambre"), 0xC04010),
    ("Bleu / Ambre", split("Bleu / Ambre", "Bleu", "Ambre"), 0x606090),
    ("Rouge / Bleu", split("Rouge / Bleu", "Rouge", "Bleu"), 0x902070),
    ("Magenta / Cyan", split("Magenta / Cyan", "Magenta", "Cyan"), 0x9070C0),
    ("Bords bleus", sides("Bords bleus", "Bleu nuit", "Ambre"), 0x506080),
    ("Bords rouges", sides("Bords rouges", "Rouge", "Blanc chaud"), 0xC07070),
]

red_uv = split("Rouge / UV", "Rouge", "UV")

# Effets PAR (RGB Matrix, synchronisés au tap tempo)
FX = {
    "Vague rouge": matrix("PAR Vague rouge", "Waves", 0xFF0000,
                          props={"taillength": "70", "tailfade": "Yes", "direction": "Right"}),
    "Vague bleue": matrix("PAR Vague bleue", "Waves", 0x0030FF,
                          props={"taillength": "70", "tailfade": "Yes", "direction": "Out"}),
    "Pair / Impair": matrix("PAR Pair/Impair rouge-blanc", "Even/Odd", 0xFF0000, 0xFFC890),
    "Alterné ambre/bleu": matrix("PAR Alterné ambre/bleu", "Alternate", 0xFF8000, 0x0020FF),
    "Un par un": matrix("PAR Un par un", "One By One", 0xFFFFFF),
    "Remplir centre": matrix("PAR Remplir centre", "Fill Unfill From Center", 0xFF5000),
    "Arc-en-ciel": matrix("PAR Arc-en-ciel", "Gradient", 0xFF0000,
                          props={"presetIndex": "Rainbow"}, duration=60),
    "Plasma lent": matrix("PAR Plasma lent", "Plasma (Colors)", 0xFF0000, duration=120,
                          props={"presetIndex": "Rainbow"}),
}
FX["Chase couleurs"] = chaser("PAR Chase couleurs", "PAR/Effets",
                              [par_color_ids[c] for c in ("Rouge", "Bleu", "Ambre", "Magenta")],
                              fade=150)
FX["Fondu lent"] = chaser("PAR Fondu lent", "PAR/Effets",
                          [par_color_ids[c] for c in ("Rouge", "Ambre", "Mauve", "Bleu nuit", "Cyan", "Magenta")],
                          hold=3000, fade=2000)
# effets qui suivent le tempo (1 pas = 1 temps)
TEMPO_FX = [FX[k] for k in ("Vague rouge", "Vague bleue", "Pair / Impair", "Alterné ambre/bleu",
                            "Un par un", "Remplir centre", "Chase couleurs")]

# Flash
_strobe_hb = scene("PAR Strobe blanc (Hotbox)", "PAR/Flash",
                   {p: {P_DIM: 255, P_R: 255, P_G: 255, P_B: 255, P_W: 255, P_STROBE: 235} for p in HOTBOX}, 0, 60)
# les PAR RGB n'ont pas de canal strobe : on clignote blanc / noir
_rgb_on = scene("PAR RGB blanc", "PAR/Flash", full(RGB_PARS, {P_R: 255, P_G: 255, P_B: 255, P_W: 255}))
_rgb_off = scene("PAR RGB noir", "PAR/Flash", full(RGB_PARS, {P_R: 0, P_G: 0, P_B: 0, P_W: 0}))
strobe_par = collection("PAR Strobe blanc", "PAR/Flash",
                        [_strobe_hb, chaser("PAR RGB strobe", "PAR/Flash", [_rgb_on, _rgb_off], hold=45)])
blinder = scene("PAR Blinder", "PAR/Flash",
                {p: {P_DIM: 255, P_R: 255, P_G: 255, P_B: 255, P_A: 255, P_W: 255} for p in PARS})
WHITE = {P_DIM: 255, P_R: 255, P_G: 255, P_B: 255, P_A: 255, P_W: 255}
bump_left = scene("PAR Bump gauche", "PAR/Flash", full(LEFT, WHITE))
bump_right = scene("PAR Bump droite", "PAR/Flash", full(RIGHT, WHITE))
flash_red = scene("PAR Flash rouge", "PAR/Flash", full(PARS, {P_DIM: 255, P_R: 255}))
flash_blue = scene("PAR Flash bleu", "PAR/Flash", full(PARS, {P_DIM: 255, P_B: 255, P_UV: 120}))
flash_uv = scene("PAR Flash UV", "PAR/Flash", full(PARS, {P_DIM: 255, P_UV: 255}))
strobe_rand = matrix("PAR Strobe aléatoire", "Random Single", 0xFFFFFF, duration=40)

# ================================================================ FOH (lekos, hors du show)
FOH_FADE = 1500
foh_70 = scene("FOH lekos 70 %", "FOH", {FOH: {c: FOH_MAX for c in range(FOH_LEKOS)}}, FOH_FADE, FOH_FADE)
foh_40 = scene("FOH lekos 40 %", "FOH", {FOH: {c: round(255 * .40) for c in range(FOH_LEKOS)}}, FOH_FADE, FOH_FADE)
foh_l = [scene(f"FOH leko {i + 1} 70 %", "FOH", {FOH: {i: FOH_MAX}}, FOH_FADE, FOH_FADE) for i in range(FOH_LEKOS)]
assert all(v <= FOH_MAX for v in (FOH_MAX, round(255 * .40)))

# ================================================================ Têtes
HEAD_COLORS = [("Blanc", 3, 0xF0F0F0), ("Rouge", 10, 0xD01010), ("Orange", 17, 0xFF7A10),
               ("Jaune", 24, 0xF0E010), ("Vert", 31, 0x10B030), ("Bleu", 38, 0x1030E0),
               ("CTO", 45, 0xFFC080), ("Cyan", 52, 0x20E0E0), ("Magenta", 59, 0xE020C0),
               ("Arc-en-ciel", 205, 0x707070)]
# Court fondu de sortie sur tout ce qui touche des canaux « LTP » (couleur, gobo, prisme, rotation,
# shutter/strobe) : à l'arrêt, ils retombent à 0 au lieu de rester coincés — même si BASE a été
# arrêtée par FONDU AU NOIR. (Testé dans QLC+ : sans fondu de sortie, la valeur reste.)
LTP_OFF = 60
head_color = {}
HEAD_COLOR_VAL = {n: v for n, v, _ in HEAD_COLORS}
for name, val, _ in HEAD_COLORS:
    head_color[name] = scene(f"Têtes {name}", "Têtes/Couleurs",
                             {h: {H_DIM: 255, H_COLOR: val, H_STROBE: H_SHUTTER_OPEN} for h in HEADS},
                             0, LTP_OFF)

GOBOS = [("Ouvert", 3)] + [(f"Gobo {i}", 3 + 8 * i) for i in range(1, 8)]
gobo = {}
for name, val in GOBOS:
    gobo[name] = scene(f"Têtes {name}", "Têtes/Gobos",
                       {h: {H_GOBO: val, H_FOCUS: 128, H_STROBE: H_SHUTTER_OPEN} for h in HEADS}, 0, LTP_OFF)
gobo_rot = scene("Têtes Rotation gobo", "Têtes/FX", {h: {H_GROT: 40} for h in HEADS}, 0, LTP_OFF)
gobo_rot_fast = scene("Têtes Rotation rapide", "Têtes/FX", {h: {H_GROT: 100} for h in HEADS}, 0, LTP_OFF)
# pas des chases : seulement la roue (+ shutter ouvert), pour ne PAS effacer prisme / rotation du look
_chase_col = [scene(f"Têtes chase {c}", "Têtes/FX/Chase",
                    {h: {H_DIM: 255, H_COLOR: HEAD_COLOR_VAL[c], H_STROBE: H_SHUTTER_OPEN} for h in HEADS})
              for c in ("Rouge", "Bleu", "Vert", "Magenta", "Jaune", "Cyan")]
_chase_gobo = [scene(f"Têtes chase Gobo {i}", "Têtes/FX/Chase",
                     {h: {H_GOBO: 3 + 8 * i, H_FOCUS: 128, H_STROBE: H_SHUTTER_OPEN} for h in HEADS})
               for i in range(1, 8)]
head_chase_col = chaser("Têtes Chase couleurs", "Têtes/FX", _chase_col, fade_out=LTP_OFF)
head_chase_gobo = chaser("Têtes Chase gobos", "Têtes/FX", _chase_gobo, fade_out=LTP_OFF)
TEMPO_FX += [head_chase_col, head_chase_gobo]
flash_heads = scene("Têtes Flash blanc", "Têtes/FX",
                    {h: {H_DIM: 255, H_COLOR: 3, H_GOBO: 3, H_STROBE: H_SHUTTER_OPEN} for h in HEADS}, 0, LTP_OFF)
prism = scene("Têtes Prisme", "Têtes/FX", {h: {H_PRISM: 128} for h in HEADS}, 0, LTP_OFF)
strobe_heads = scene("Têtes Strobe", "Têtes/FX",
                     {h: {H_DIM: 255, H_COLOR: 3, H_STROBE: 60} for h in HEADS}, 0, LTP_OFF)

# Positions calculées à partir du plan de la salle (vu du plafond, 1 carré = 2 pi).
# Coordonnées en pixels de la capture du plan : x vers la droite (côté guitare), y vers le fond de la salle.
PX_PER_FT = 27.25                     # 1 carré = 54,5 px = 2 pi
H_LIGHTS = 11.0                       # hauteur des têtes (pi) — à confirmer
H_STAGE = 2.0                         # hauteur de la scène (pi) — à confirmer
PAN_SIGN = -1                         # inversé : confirmé dans la salle (Band visait le fond)
PAN_DEG, TILT_DEG = 540.0, 234.0      # plages de la 260X
HEAD_PX = [(588, 1262), (584, 1418), (583, 1595), (578, 1742)]   # Tête 1 (près de la scène) → Tête 4
SPOT = {  # cibles (x px, y px, hauteur pi)
    "chanteur": (600, 1000, H_STAGE + 5), "batterie": (600, 783, H_STAGE + 3.5),
    "basse": (382, 865, H_STAGE + 4.5), "guitare": (818, 865, H_STAGE + 4.5),
    "centre": (561, 900, H_STAGE + 4),
}


def aim(head, target, pan_offset=0.0):
    """(pan, tilt) DMX pour viser target depuis head.
    Calibration observée : pan 128 + tilt < 128 => faisceau vers +x (mur côté guitare)."""
    import math
    hx, hy = head
    tx, ty, tz = target
    dx, dy = (tx - hx) / PX_PER_FT, (ty - hy) / PX_PER_FT
    dz = H_LIGHTS - tz
    theta = math.degrees(math.atan2(math.hypot(dx, dy), dz))          # angle depuis la verticale
    phi = math.degrees(math.atan2(dy, dx))                            # direction au sol
    best = None
    for off, tsign in ((0, -1), (180, 1), (-180, 1)):                 # deux façons d'y arriver
        for wrap in (-360, 0, 360):
            pan = 128 + PAN_SIGN * (phi - off + wrap + pan_offset) * 255 / PAN_DEG
            tilt = 128 + tsign * theta * 255 / TILT_DEG
            if 0 <= pan <= 255 and 0 <= tilt <= 255:
                # même « branche » pour toutes les têtes (tilt < 128) : pas de demi-tour entre positions
                cand = (abs(pan - 128) + (60 if tsign > 0 else 0), round(pan), round(tilt))
                best = min(best, cand) if best else cand
    return (best[1], best[2]) if best else (128, 128)


# Têtes dont le pan tourne à l'envers (montage ou réglage « pan reverse » dans le menu de la tête).
# Mettre True pour une tête dont le pan tourne à l'envers.
PAN_INVERT = [False, False, False, False]
# Tête montée tournée d'un demi-tour (sa base regarde dans l'autre sens) : +180° de pan.
# Tête 1 : éclairait derrière la scène au lieu de la scène (constaté dans la salle).
PAN_TURN = [180, 0, 0, 0]


def aim_all(targets):
    out = []
    for i, (h, t) in enumerate(zip(HEAD_PX, targets)):
        pan, tilt = aim(h, t, PAN_TURN[i])
        out.append((255 - pan if PAN_INVERT[i] else pan, tilt))
    return out


POS_FADE = 1200
S_ = SPOT
POSITIONS = [
    ("Centre", aim_all([S_["centre"]] * 4)),
    ("Public", aim_all([(300, 1350, 4), (850, 1350, 4), (300, 1650, 4), (850, 1650, 4)])),
    ("Band", aim_all([S_["basse"], S_["batterie"], S_["chanteur"], S_["guitare"]])),
    ("Chanteur", aim_all([S_["chanteur"]] * 4)),
    ("Croisé", aim_all([S_["guitare"], S_["basse"], S_["guitare"], S_["basse"]])),
    ("Éventail", aim_all([(200, 720, 8), (430, 720, 8), (690, 720, 8), (920, 720, 8)])),
    ("V inversé", aim_all([(180, 1050, H_STAGE), (560, 730, 7), (560, 730, 7), (940, 1050, H_STAGE)])),
    ("Batterie", aim_all([S_["batterie"]] * 4)),
    ("Guitare", aim_all([S_["guitare"]] * 4)),
    ("Basse", aim_all([S_["basse"]] * 4)),
    ("Plafond", aim_all([(250, 700, H_LIGHTS - 1), (450, 700, H_LIGHTS - 1),
                         (670, 700, H_LIGHTS - 1), (870, 700, H_LIGHTS - 1)])),
]
for _n, _pts in POSITIONS:
    print(f"  {_n:10s}", _pts)
pos = {}
for name, pts in POSITIONS:
    pos[name] = scene(f"Position {name}", "Têtes/Positions",
                      {h: {H_PAN: p, H_PANF: 0, H_TILT: t, H_TILTF: 0, H_SPEED: 0}
                       for h, (p, t) in zip(HEADS, pts)}, POS_FADE)

MOVE_SPECS = {   # algo, largeur, hauteur, options, décalage de phase par tête
    "Cercle": ("Circle", 22, 30, {}, (0, 90, 180, 270)),
    "Huit": ("Eight", 28, 30, {}, (0, 90, 180, 270)),
    "Balayage lent": ("Line", 32, 6, {"duration": 12000, "xfreq": 1, "yfreq": 1}, (0, 0, 180, 180)),
    "Vague tilt": ("Line", 4, 40, {"duration": 6000, "xfreq": 1, "yfreq": 1}, (0, 90, 180, 270)),
    "Diamant": ("Diamond", 22, 30, {}, (0, 90, 180, 270)),
    "Ballyhoo": ("Lissajous", 40, 45, {"duration": 10000}, (0, 90, 180, 270)),
}
POS_PTS = dict(POSITIONS)
_moves = {}


def move(mname, pname):
    """Mouvement mname autour de la position pname : une collection d'EFX absolus (1 par tête)."""
    if (mname, pname) not in _moves:
        algo, w, h, opt, offs = MOVE_SPECS[mname]
        ids = [efx(f"Têtes {mname} @ {pname} (T{i + 1})", algo, w, h, hd, POS_PTS[pname][i], offs[i],
                   path=f"Têtes/Mouvements/{pname}", **opt)
               for i, hd in enumerate(HEADS)]
        _moves[(mname, pname)] = collection(f"Têtes {mname} @ {pname}", "Têtes/Mouvements", ids)
    return _moves[(mname, pname)]


# boutons manuels : autour de la position « Centre »
MOVES = {n: move(n, "Centre") for n in MOVE_SPECS}

# ================================================================ Looks (tout le rig)
LOOKS = [  # nom, couleur bouton, [fonctions]
    ("INTRO", 0x101870, [par_color_ids["Bleu nuit"], head_color["Bleu"], gobo["Gobo 2"], gobo_rot,
                         pos["Public"], move("Balayage lent", "Public")]),
    ("COUPLET", 0xFF9A10, [par_color_ids["Ambre"], head_color["CTO"], gobo["Ouvert"], pos["Band"]]),
    ("PRÉ-REFRAIN", 0x9070C0, [FX["Alterné ambre/bleu"], head_color["Magenta"], gobo["Gobo 3"],
                               pos["Éventail"], move("Vague tilt", "Éventail")]),
    ("REFRAIN", 0xD01010, [par_color_ids["Rouge"], head_color["Blanc"], gobo["Gobo 1"],
                           pos["Croisé"], move("Huit", "Croisé")]),
    ("GROS REFRAIN", 0xFF2020, [FX["Pair / Impair"], head_color["Blanc"], gobo["Ouvert"], prism,
                                pos["Éventail"], move("Ballyhoo", "Éventail")]),
    ("BALLADE", 0x7A30E0, [FX["Plasma lent"], head_color["Magenta"], gobo["Gobo 5"], gobo_rot,
                           pos["Chanteur"]]),
    ("SOLO GUITARE", 0xFFB800, [par_color_ids["Rouge sang"], head_color["Blanc"], gobo["Ouvert"],
                                pos["Centre"]]),
    ("ÉNERGIE", 0xFF4000, [FX["Vague rouge"], head_color["Rouge"], gobo["Gobo 4"], gobo_rot_fast,
                           pos["V inversé"], move("Cercle", "V inversé")]),
    ("PSYCHÉ", 0x20C0A0, [FX["Arc-en-ciel"], head_color["Arc-en-ciel"], gobo["Gobo 6"], gobo_rot,
                          prism, pos["Plafond"], move("Ballyhoo", "Plafond")]),
    ("FINAL", 0xFFF0D0, [par_color_ids["Blanc chaud"], head_color["Blanc"], gobo["Ouvert"],
                         pos["Public"]]),
]
SPLIT_IDS = {n: i for n, i, _ in SPLITS}
LOOKS2 = [
    ("OUVERTURE", 0xE0F0FF, [par_color_ids["Blanc froid"], head_color["Blanc"], gobo["Ouvert"],
                             pos["Public"], move("Balayage lent", "Public")]),
    ("FEU", 0xFF5000, [FX["Remplir centre"], head_color["Orange"], gobo["Gobo 4"], gobo_rot,
                       pos["Band"], move("Vague tilt", "Band")]),
    ("OCÉAN", 0x0080C0, [FX["Vague bleue"], head_color["Cyan"], gobo["Gobo 2"], gobo_rot,
                         pos["Public"], move("Balayage lent", "Public")]),
    ("DISCO", 0xE020C0, [FX["Chase couleurs"], head_chase_col, gobo["Gobo 7"], prism,
                         pos["Plafond"], move("Cercle", "Plafond")]),
    ("SOMBRE", 0x400A90, [par_color_ids["UV"], head_color["Bleu"], gobo["Gobo 5"], prism,
                          pos["Band"], move("Balayage lent", "Band")]),
    ("ROCK BLANC", 0xC8D8F0, [par_color_ids["Blanc froid"], head_color["Blanc"], gobo["Gobo 1"],
                              pos["Croisé"], move("Huit", "Croisé")]),
    ("ACOUSTIQUE", 0xFFDDB0, [SPLIT_IDS["Bords bleus"], head_color["CTO"], gobo["Ouvert"],
                              pos["Chanteur"]]),
    ("MONTÉE", 0xFFB800, [FX["Un par un"], head_color["Jaune"], gobo["Gobo 3"], gobo_rot_fast,
                          pos["Éventail"], move("Vague tilt", "Éventail")]),
    ("CHAOS", 0xB01010, [FX["Pair / Impair"], head_chase_col, head_chase_gobo, prism,
                         pos["V inversé"], move("Ballyhoo", "V inversé")]),
    ("APOTHÉOSE", 0xFFF0D0, [FX["Arc-en-ciel"], head_color["Blanc"], gobo["Ouvert"], prism,
                             pos["Éventail"], move("Ballyhoo", "Éventail")]),
]
LOOKS3 = [
    ("SPOT CHANTEUR", 0xF0F0F0, [par_color_ids["Bleu nuit"], head_color["Blanc"], gobo["Ouvert"], pos["Chanteur"]]),
    ("SOLO BATTERIE", 0xB01010, [FX["Pair / Impair"], head_color["Rouge"], gobo["Gobo 1"], gobo_rot_fast,
                                 pos["Batterie"], move("Cercle", "Batterie")]),
    ("SOLO BASSE", 0x7A30E0, [par_color_ids["Mauve"], head_color["Magenta"], gobo["Gobo 3"], gobo_rot,
                              pos["Basse"]]),
    ("COUCHER SOLEIL", 0xFF6A00, [par_color_ids["Orange"], head_color["Orange"], gobo["Gobo 5"], gobo_rot,
                                  pos["Éventail"], move("Balayage lent", "Éventail")]),
    ("NÉON", 0x20E0E0, [SPLIT_IDS["Magenta / Cyan"], head_color["Cyan"], gobo["Gobo 7"], prism,
                        pos["Plafond"], move("Cercle", "Plafond")]),
    ("TEMPÊTE", 0xA0A0FF, [strobe_rand, head_color["Blanc"], gobo["Gobo 6"], gobo_rot_fast,
                           pos["Croisé"], move("Huit", "Croisé")]),
    ("ROUGE & UV", 0x900060, [red_uv, head_color["Rouge"], gobo["Gobo 2"], gobo_rot, pos["Public"],
                              move("Vague tilt", "Public")]),
    ("BLEU GLACE", 0x80D0FF, [par_color_ids["Cyan"], head_color["Bleu"], gobo["Gobo 2"], pos["V inversé"],
                              move("Balayage lent", "V inversé")]),
    ("FEU D'ARTIFICE", 0xFF20A0, [FX["Arc-en-ciel"], head_chase_col, head_chase_gobo, prism,
                                  pos["Plafond"], move("Ballyhoo", "Plafond")]),
    ("ENTRACTE", 0x203060, [par_color_ids["Bleu nuit"], head_color["Bleu"], gobo["Gobo 5"], gobo_rot,
                            pos["Plafond"], move("Balayage lent", "Plafond")]),
]
look_ids = [(n, bg, collection(f"LOOK {n}", "Looks", [base] + m)) for n, bg, m in LOOKS]
look2_ids = [(n, bg, collection(f"LOOK {n}", "Looks", [base] + m)) for n, bg, m in LOOKS2]
look3_ids = [(n, bg, collection(f"LOOK {n}", "Looks", [base] + m)) for n, bg, m in LOOKS3]
_all_looks = dict((n, i) for n, _, i in look_ids + look2_ids + look3_ids)
auto_mode = chaser("AUTO — enchaîne les looks", "Looks",
                   [_all_looks[n] for n in ("COUPLET", "PRÉ-REFRAIN", "REFRAIN", "GROS REFRAIN", "FEU",
                                            "OCÉAN", "ÉNERGIE", "DISCO", "ROCK BLANC", "MONTÉE",
                                            "CHAOS", "PSYCHÉ", "SOLO BATTERIE", "NÉON", "TEMPÊTE",
                                            "ROUGE & UV", "FEU D'ARTIFICE")], hold=8000)

# ================================================================ Virtual Console
vc = ET.SubElement(ws, "VirtualConsole")
_wid = [0]


def wid():
    _wid[0] += 1
    return str(_wid[0])


def appearance(parent, bg=None, fg=None, style="None", font=None):
    a = ET.SubElement(parent, "Appearance")
    ET.SubElement(a, "FrameStyle").text = style
    ET.SubElement(a, "ForegroundColor").text = str(0xFF000000 | fg) if fg is not None else "Default"
    ET.SubElement(a, "BackgroundColor").text = str(0xFF000000 | bg) if bg is not None else "Default"
    ET.SubElement(a, "BackgroundImage").text = "None"
    ET.SubElement(a, "Font").text = font or "Default"


def winstate(parent, x, y, w, h):
    ET.SubElement(parent, "WindowState", {"Visible": "False", "X": str(x), "Y": str(y),
                                          "Width": str(w), "Height": str(h)})


def frame(parent, caption, x, y, w, h, solo=False, bg=0x202020, pages=1):
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
    if pages > 1:
        ET.SubElement(f, "Multipage", {"PagesNum": str(pages), "CurrentPage": "0"})
        ET.SubElement(f, "PagesLoop").text = "True"
    return f


def text_color_for(bg):
    r, g, b = (bg >> 16) & 255, (bg >> 8) & 255, bg & 255
    return 0x000000 if (r * 299 + g * 587 + b * 114) / 1000 > 140 else 0xFFFFFF


BOLD = "Sans Serif,11,-1,5,75,0,0,0,0,0"
BIG = "Sans Serif,13,-1,5,75,0,0,0,0,0"


def button(parent, caption, fid, x, y, w=100, h=64, action="Toggle", bg=None, key=None, font=None,
           page=0):
    b = ET.SubElement(parent, "Button", {"Caption": caption, "ID": wid(), "Icon": ""})
    if page:
        b.set("Page", str(page))
    winstate(b, x, y, w, h)
    appearance(b, bg=bg, fg=text_color_for(bg) if bg is not None else None, font=font)
    ET.SubElement(b, "Function", {"ID": str(fid)})
    ET.SubElement(b, "Action").text = action
    if key:
        ET.SubElement(b, "Key").text = key
    ET.SubElement(b, "Intensity", {"Adjust": "False"}).text = "100"
    return b


def grid(parent, items, cols, w=100, h=64, gap=8, top=35, left=10, action="Toggle", font=None, page=0,
         keys=None):
    for i, (cap, fid, bg) in enumerate(items):
        r, c = divmod(i, cols)
        button(parent, cap, fid, left + c * (w + gap), top + r * (h + gap), w, h, action, bg,
               key=keys[i] if keys else None, font=font, page=page)


def level_slider(parent, caption, channels, x, y, w=90, h=250, value=255, high=255, style="Slider"):
    s = ET.SubElement(parent, "Slider", {"Caption": caption, "ID": wid(), "WidgetStyle": style,
                                         "InvertedAppearance": "false"})
    winstate(s, x, y, w, h)
    appearance(s, font=BOLD)
    ET.SubElement(s, "SliderMode", {"ValueDisplayStyle": "Percentage",
                                    "ClickAndGoType": "None", "Monitor": "false"}).text = "Level"
    lv = ET.SubElement(s, "Level", {"LowLimit": "0", "HighLimit": str(high), "Value": str(value)})
    for fx, ch in channels:
        ET.SubElement(lv, "Channel", {"Fixture": str(fx)}).text = str(ch)
    pb = ET.SubElement(s, "Playback")
    ET.SubElement(pb, "Function").text = "4294967295"


NO_FUNC = 4294967295


def L(mod, letters):
    return [f"{mod}{c}" for c in letters]
root = ET.SubElement(vc, "Frame", {"Caption": ""})
appearance(root, bg=0x121212)

# --- Rangée 1 : LOOKS
f = frame(root, "LOOKS DU SHOW — un bouton = tout le rig   (Stream Deck : F1-F10 · Shift+F1-F10 · Ctrl+F1-F10 · AUTO F11)",
          10, 10, 1840, 238, solo=True, bg=0x2A1010)
for row, (ids, mod) in enumerate(((look_ids, ""), (look2_ids, "Shift+"), (look3_ids, "Ctrl+"))):
    for c, (n, bg, fid) in enumerate(ids):
        button(f, n, fid, 10 + c * 166, 35 + row * 66, 158, 58, bg=bg, key=f"{mod}F{c + 1}", font=BIG)
button(f, "▶ AUTO", auto_mode, 10 + 10 * 166, 35, 158, 190, bg=0x00A060, key="F11", font=BIG)

# --- PAR
f = frame(root, "PAR — COULEURS", 10, 258, 670, 255, solo=True)
items = [(n, par_color_ids[n], bg) for n, _, bg in PAR_COLORS] + list(SPLITS)
grid(f, items, cols=7, w=86, h=64, keys=L("Alt+", "ABCDEFGHIJKLMNOPQRST"))
f = frame(root, "PAR — EFFETS (suivent le tempo)", 10, 523, 670, 175, solo=True)
grid(f, [(n, fid, 0x3A3A3A) for n, fid in FX.items()], cols=5, w=122, h=60, keys=L("Alt+Shift+", "ABCDEFGHIJ"))

# --- Masters / tempo / flash
f = frame(root, "MASTERS & TEMPO", 10, 708, 670, 270)
level_slider(f, "PAR", [(p, P_DIM) for p in HOTBOX] + [(u, UK_DIM) for u in UKS] + [(m, MOS_DIM) for m in MOSS], 15, 35, h=225)
level_slider(f, "TÊTES +", [(h, H_DIM) for h in HEADS], 115, 35, h=225, value=0)   # ajout manuel
sd = ET.SubElement(f, "SpeedDial", {"Caption": "TEMPO — tape le beat", "ID": wid()})
winstate(sd, 220, 35, 230, 225)
appearance(sd, font=BOLD)
ET.SubElement(sd, "AbsoluteValue", {"Minimum": "0", "Maximum": "10000"})
ET.SubElement(sd, "Time").text = "500"
ET.SubElement(sd, "Key").text = "T"
for fid_ in TEMPO_FX:
    ET.SubElement(sd, "Function", {"FadeIn": "0", "FadeOut": "0", "Duration": "6"}).text = str(fid_)
for k in ("Cercle", "Huit", "Diamant"):  # 1 tour = 8 temps
    ET.SubElement(sd, "Function", {"FadeIn": "0", "FadeOut": "0", "Duration": "9"}).text = str(MOVES[k])
# mode auto : 1 look = 16 temps
ET.SubElement(sd, "Function", {"FadeIn": "0", "FadeOut": "0", "Duration": "10"}).text = str(auto_mode)
button(f, "STROBE\nPAR", strobe_par, 465, 35, 95, 72, "Flash", 0xFFFFFF, "S", BOLD)
button(f, "BLINDER", blinder, 568, 35, 95, 72, "Flash", 0xFFE070, "B", BOLD)
button(f, "STROBE TÊTES", strobe_heads, 465, 113, 95, 72, "Flash", 0xC8C8C8, "D", BOLD)
button(f, "STROBE FOU", strobe_rand, 568, 113, 95, 72, "Flash", 0xA0A0FF, "F", BOLD)
button(f, "BLACKOUT", NO_FUNC, 465, 191, 95, 72, "Blackout", 0x000000, "X", BOLD)
b = button(f, "FONDU\nAU NOIR", NO_FUNC, 568, 191, 95, 72, "StopAll", 0x602020, "N", BOLD)
b.find("Action").set("FadeOut", "2000")

# --- FOH : lekos, jamais plus de 70 %
f = frame(root, "FOH — LEKOS (max 70 %)", 1260, 568, 290, 170, bg=0x1A2430)
level_slider(f, "FOH", [(FOH, c) for c in range(FOH_LEKOS)], 8, 28, w=66, h=74, value=0, high=FOH_MAX, style="Knob")
for i in range(FOH_LEKOS):
    level_slider(f, f"L{i + 1}", [(FOH, i)], 78 + i * 68, 28, w=66, h=74, value=0, high=FOH_MAX, style="Knob")
# touches : un appui = allumé (fondu 1,5 s), un 2e appui = éteint. Jamais plus de 70 %.
for i, (cap, fid_, key) in enumerate([("FOH\n70 %", foh_70, "Alt+7"), ("FOH\n40 %", foh_40, "Alt+4"),
                                      ("L1", foh_l[0], "Ctrl+1"), ("L2", foh_l[1], "Ctrl+2"),
                                      ("L3", foh_l[2], "Ctrl+3")]):
    button(f, cap, fid_, 8 + i * 56, 108, 52, 54, "Toggle", 0xF2D8A0, key)

# --- Têtes
f = frame(root, "TÊTES — COULEUR", 690, 258, 560, 175, solo=True)
grid(f, [(n, head_color[n], bg) for n, _, bg in HEAD_COLORS], cols=5, keys=L("Ctrl+Shift+", "ABCDEFGHIJ"))
f = frame(root, "TÊTES — GOBO", 690, 443, 560, 175, solo=True)
grid(f, [(n, gobo[n], 0x303058) for n, _ in GOBOS], cols=5, keys=L("Ctrl+Shift+", "KLMNOPQR"))
f = frame(root, "TÊTES — FX", 690, 628, 560, 110)
grid(f, [("Rotation gobo", gobo_rot, 0x2F5A2F), ("Rotation rapide", gobo_rot_fast, 0x2F5A2F),
         ("Prisme", prism, 0x2F5A2F), ("Chase couleurs", head_chase_col, 0x2F5A2F),
         ("Chase gobos", head_chase_gobo, 0x2F5A2F)], cols=5, keys=L("Ctrl+Shift+", "TUVWY"))

f = frame(root, "TÊTES — POSITION (fondu 1,2 s)", 1260, 258, 590, 175, solo=True)
grid(f, [(n, pos[n], 0x204060) for n, _ in POSITIONS], cols=6, w=88, keys=L("Shift+", "ABCDEFGHIJK"))

xy = ET.SubElement(root, "XYPad", {"Caption": "VISER EN LIVE (4 têtes)", "ID": wid(),
                                   "InvertedAppearance": "0"})
winstate(xy, 1260, 443, 290, 120)
appearance(xy)
for i, h in enumerate(HEADS):
    fx = ET.SubElement(xy, "Fixture", {"ID": str(h), "Head": "0"})
    ET.SubElement(fx, "Axis", {"ID": "X", "LowLimit": "0", "HighLimit": "1",
                               "Reverse": "True" if PAN_INVERT[i] else "False"})
    ET.SubElement(fx, "Axis", {"ID": "Y", "LowLimit": "0", "HighLimit": "1", "Reverse": "False"})
ET.SubElement(xy, "Pan", {"Position": "127"})
ET.SubElement(xy, "Tilt", {"Position": "127"})

f = frame(root, "TÊTES — MOUVEMENT", 1560, 443, 290, 295, solo=True)
grid(f, [(n, i, 0x5A2A5A) for n, i in MOVES.items()], cols=2, w=130, h=72, keys=L("Shift+", "LMNOPQ"))

f = frame(root, "FLASH & BUMPS (maintenir)", 690, 748, 560, 230)
grid(f, [("BUMP\nGAUCHE", bump_left, 0xFFFFFF), ("BUMP\nDROITE", bump_right, 0xFFFFFF),
         ("FLASH\nROUGE", flash_red, 0xE01010), ("FLASH\nBLEU", flash_blue, 0x1030E0),
         ("FLASH\nUV", flash_uv, 0x5010B0), ("FLASH\nTÊTES", flash_heads, 0xD8D8D8)],
     cols=3, w=172, h=88, action="Flash", font=BIG, keys=["G", "H", "J", "K", "L", "M"])

f = frame(root, "STREAM DECK (plugin QLC+) : allumé tant que la touche est tenue", 1260, 748, 590, 230,
          bg=0x181818)
grid(f, [("STROBE\nPAR", strobe_par, 0xFFFFFF), ("BLINDER", blinder, 0xFFE070),
         ("STROBE\nTÊTES", strobe_heads, 0xC8C8C8), ("STROBE\nFOU", strobe_rand, 0xA0A0FF),
         ("BUMP\nGAUCHE", bump_left, 0xFFFFFF), ("BUMP\nDROITE", bump_right, 0xFFFFFF),
         ("FLASH\nROUGE", flash_red, 0xE01010), ("FLASH\nBLEU", flash_blue, 0x1030E0),
         ("FLASH\nUV", flash_uv, 0x5010B0), ("FLASH\nTÊTES", flash_heads, 0xD8D8D8)],
     cols=5, w=106, h=88, font=BOLD, keys=L("Alt+Shift+", "KLMNOPQRST"))
HOLD_KEYS = L("Alt+Shift+", "KLMNOPQRST")     # touches « maintenues » côté Stream Deck

props = ET.SubElement(vc, "Properties")
ET.SubElement(props, "Size", {"Width": "1920", "Height": "1080"})
ET.SubElement(props, "GrandMaster", {"ChannelMode": "Intensity", "ValueMode": "Reduce",
                                     "SliderMode": "Normal"})

# ---------------------------------------------------------------- Écriture
os.makedirs(os.path.dirname(OUT), exist_ok=True)
ET.indent(ws, space=" ")
xml = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE Workspace>\n' + ET.tostring(ws, encoding="unicode") + "\n"
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(xml)
print(f"OK -> {os.path.abspath(OUT)}  ({_fid[0]} fonctions, {_wid[0]} widgets)")

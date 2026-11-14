# Chauvet Intimidator Spot 260X — profil QLC+ et show rock

Profil de fixture QLC+ (`.qxf`) pour la Chauvet Intimidator Spot 260X, modes **14 Channel** et **8 Channel**, basé sur le manuel utilisateur 260X (Rev. 1).

## Installation du profil (Windows)
1. Télécharger `Chauvet-Intimidator-Spot-260X.qxf`
2. Le copier dans `Documents\QLC+\Fixtures` (créer le dossier au besoin)
3. Redémarrer QLC+ → Chauvet → Intimidator Spot 260X

---

# Show Rock — board QLC+ prêt à jouer

![Aperçu de la Virtual Console](show/apercu-virtual-console.png)

## Ouvrir le show
1. Télécharger le dossier `show/` au complet (le `.qxw` et le `.qxf` ensemble).
2. Dans QLC+ : **Fichier → Ouvrir** → `Show-Rock.qxw`.
   Le profil 260X est trouvé automatiquement s'il est installé ou s'il est dans le même dossier que le `.qxw`.
3. **Inputs/Outputs** → Universe 1 → vérifier que la sortie **DMX USB** (câble SH-RS09B) est cochée.
4. Cliquer sur le **▶ vert** (mode opération) et jouer dans la Virtual Console.

## Patch (Universe 1)

| Fixture | Profil / mode | Adresses DMX |
|---|---|---|
| Têtes 1 à 4 | Chauvet Intimidator Spot 260X — 14 Channel | 1, 15, 29, 43 |
| PAR 1 à 4 (gauche → droite) | Blizzard Lighting Hotbox EXA — 11 Channel Mode | 66, 77, 88, 99 |

Sur chaque PAR : menu → mode **11CH** et l'adresse de la table.

## Comment jouer
1. **Choisis un LOOK** dans la rangée du haut : tout le rig change d'un coup, avec des fondus. Les flèches orange en haut à droite donnent la **page 2**.
   Ou appuie sur **▶ AUTO** : les looks s'enchaînent tout seuls aux 16 temps.
2. **Raffine en live** : une couleur PAR, un gobo, une position ou un mouvement par-dessus le look. Le bouton remplace juste cette partie-là.
3. **Tape le beat** sur TEMPO : les effets PAR et les mouvements suivent la toune.
4. **Fin de toune** : FONDU AU NOIR (2 s) ou BLACKOUT.

## Les looks

| Look | PAR | Têtes |
|---|---|---|
| **INTRO** | Bleu nuit + UV | Bleu, gobo 2 qui tourne, balayage lent sur le public |
| **COUPLET** | Ambre | CTO ouvert sur le band |
| **PRÉ-REFRAIN** | Alterné ambre/bleu (tempo) | Magenta, gobo 3, en éventail, vague de tilt |
| **REFRAIN** | Rouge | Blanc gobo 1, croisées, en huit |
| **GROS REFRAIN** | Pair/impair rouge-blanc (tempo) | Blanc + prisme, éventail, ballyhoo |
| **BALLADE** | Plasma lent | Magenta, gobo 5 qui tourne, sur le chanteur |
| **SOLO GUITARE** | Rouge sang | Blanc ouvert au centre |
| **ÉNERGIE** | Vague rouge (tempo) | Rouge, gobo 4 en rotation rapide, V inversé, cercle |
| **PSYCHÉ** | Arc-en-ciel | Arc-en-ciel, gobo 6, prisme, ballyhoo au plafond |
| **FINAL** | Blanc chaud | Blanc sur le public |

**Page 2**

| Look | PAR | Têtes |
|---|---|---|
| **OUVERTURE** | Blanc froid | Blanc ouvert, balayage lent sur le public |
| **FEU** | Remplir du centre orange (tempo) | Orange, gobo 4 qui tourne, vague de tilt sur le band |
| **OCÉAN** | Vague bleue (tempo) | Cyan, gobo 2 qui tourne, balayage lent |
| **DISCO** | Chase couleurs (tempo) | Chase couleurs, gobo 7, prisme, cercle au plafond |
| **SOMBRE** | UV | Bleu, gobo 5, prisme, balayage lent |
| **ROCK BLANC** | Blanc froid | Blanc gobo 1, croisées, en huit |
| **ACOUSTIQUE** | Bords bleus / centre ambre | CTO ouvert sur le chanteur |
| **MONTÉE** | Un par un (tempo) | Jaune, gobo 3 rapide, éventail, vague de tilt |
| **CHAOS** | Pair/impair (tempo) | Chase couleurs + chase gobos, prisme, ballyhoo |
| **APOTHÉOSE** | Arc-en-ciel | Blanc + prisme, éventail, ballyhoo |

## La Virtual Console

| Zone | Ce que ça fait |
|---|---|
| **PAR — Couleurs** | 14 couleurs + 6 combinaisons (pair/impair, bords/centre). Fondu de 0,4 s entre les couleurs. |
| **PAR — Effets** | Vagues, pair/impair, alterné, un par un, remplir du centre, arc-en-ciel, plasma, chase, fondu lent |
| **Masters & tempo** | Fader **PAR** et fader **TÊTES** (dimmers). **TEMPO** : tape le beat sur *Tap*. |
| **Flash** (maintenir) | Strobe PAR `S`, Blinder `B`, Strobe têtes `D`, Strobe fou `F` |
| **Urgence** | **BLACKOUT** `X`, **FONDU AU NOIR** `N` (arrête tout en 2 s) |
| **Flash & bumps** (maintenir) | Bump gauche `1`, bump droite `2`, flash rouge `3`, bleu `4`, UV `5`, flash têtes `6` |
| **Têtes — Couleur / Gobo / FX** | Roue de couleurs, 7 gobos + ouvert, rotation lente/rapide, prisme, chase couleurs, chase gobos |
| **Têtes — Position** | 8 positions avec fondu de 1,2 s + **pad XY** pour viser en live |
| **Têtes — Mouvement** | Cercle, huit, balayage lent, vague tilt, diamant, ballyhoo. Ils sont **relatifs** : ils bougent autour de la position active, alors garde toujours une position allumée. |

Les têtes s'allument dès que tu choisis une couleur ou un gobo, parce que ces scènes ouvrent le shutter.

## Anti-bug : la scène BASE
Certains canaux (strobe des PAR, prisme, rotation de gobo, shutter des têtes) gardent leur dernière valeur quand un flash ou un bouton s'arrête. La scène **BASE (toujours active)** démarre toute seule en mode show et fait partie de chaque look : elle remet ces canaux à zéro dès qu'un flash est relâché.
Après un **FONDU AU NOIR**, relance un look avant d'utiliser les flashs (le fondu arrête aussi BASE).

## À ajuster sur place
- **Positions** : les valeurs pan/tilt sont des points de départ. Dans **Functions → Têtes/Positions**, ouvre la scène et ajuste les têtes pendant qu'elles sont allumées.
- **Ordre des têtes** : le show suppose que Tête 1 (adresse 1) est à gauche. Sinon, change l'adresse dans **Fixtures**.
- **Lekos** : pas encore dans le show. Il faut ajouter leurs adresses.

## Regénérer le show
```
python3 tools/generate_show.py
```
Les adresses, couleurs et positions sont en haut du script.

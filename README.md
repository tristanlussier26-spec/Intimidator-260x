# Chauvet Intimidator Spot 260X — profil QLC+ et show rock

Profil de fixture QLC+ (`.qxf`) pour la Chauvet Intimidator Spot 260X, modes **14 Channel** et **8 Channel**, basé sur le manuel utilisateur 260X (Rev. 1).

## Installation du profil (Windows)
1. Télécharger `Chauvet-Intimidator-Spot-260X.qxf`
2. Le copier dans `Documents\QLC+\Fixtures` (créer le dossier au besoin)
3. Redémarrer QLC+ → Chauvet → Intimidator Spot 260X

---

# Show Rock — board QLC+ prêt à jouer

![Aperçu de la Virtual Console](show/apercu-virtual-console.png)

## Tout installer en une commande (Windows)
Ouvre **PowerShell** et colle :

```powershell
irm https://github.com/tristanlussier26-spec/Intimidator-260x/raw/main/install.ps1 | iex
```

La commande ([`install.ps1`](install.ps1)) :
1. télécharge la dernière version dans `Documents\Show-Rock` : le show, le profil des têtes, le lanceur, le plugin et le profil Stream Deck ;
2. installe le plugin Stream Deck (confirme dans Stream Deck) ;
3. importe le profil XL ;
4. lance QLC+ avec l'accès web, en mode show.

Relance la même commande pour mettre à jour après un changement sur le GitHub.

## Corrections têtes (audit)
- **Mouvements** : le mode « relatif » des EFX ne bouge pas dans QLC+ 4.12 (testé). Chaque mouvement est maintenant un EFX **absolu par tête**, centré sur la position du look. Les boutons de mouvement manuels tournent autour de la position **Centre**. Choisis la position **avant** le mouvement : une position lancée après fige les têtes.
- **Prisme / rotation** ne sont plus effacés par les chases de couleurs ou de gobos (DISCO, CHAOS).
- **Rien ne reste coincé**, même après FONDU AU NOIR : rotation, prisme, fonctions des têtes et strobe/programmes des PAR sont forcés en HTP (ils retombent à 0).
- **Intensité des têtes** : elle vient maintenant des scènes de couleur. Une tête sans couleur est éteinte. Le fader **TÊTES +** (à 0 au départ) sert juste à ajouter de la lumière à la main.
- **Plugin 1.1.1** : il tolère les messages abîmés de QLC+ et ne recharge plus la page de QLC+ à chaque reconnexion (ça doublait les messages et causait des coupures en cascade).

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
| M1 à M4 : contre-jours au fond de la scène (gauche → droite) | MOSFiATA PAR 36 RGB → `MOSFiATA-PAR-36-RGB.qxf`, **7 canaux** | 160, 167, 174, 181 |
| M5 face gauche · M6 face droite (coins avant de la scène) | MOSFiATA, 7 canaux | 188, 195 |
| M7 · M8 : public, mur gauche (avant · arrière) | MOSFiATA, 7 canaux | 202, 209 |
| 3 lekos FOH | Dimmer Chauvet DMX-4 → Generic dimmer 4 canaux (lekos sur les sorties 1, 2, 3) | 150 (canaux 150-152) |
| U1 face gauche · U2 face droite (bord de scène) | U`King ZQ01061 18x10W RGBW → `UKing-ZQ01061-RGBW-Par.qxf`, **8 canaux** (menu `A001`) | 134, 142 |

- Sur chaque Hotbox : menu → mode **11CH** et l'adresse de la table.
- Les MOSFiATA sont en 7 canaux : dimmer, R, G, B, strobe, mode, vitesse (profil `MOSFiATA-PAR-36-RGB.qxf`, à côté du show). BASE garde strobe et mode à 0 ; le strobe du show est fait par QLC+ (clignotement).
- Les U`King sont en 8 canaux : dimmer, R, G, B, W, strobe, fonction, vitesse. Leur profil `UKing-ZQ01061-RGBW-Par.qxf` doit être **à côté de `Show-Rock.qxw`** (le script d'installation le met là). La scène BASE garde strobe et fonction à 0, et le dimmer suit le fader PAR.
- **M7 et M8 éclairent le public** : ils restent éteints dans les couleurs et les looks, et ne s'allument qu'avec le blinder, les strobes, les bumps et les flashs.
- **Lekos FOH** : hors du show. Aucun look, effet, flash ni blinder n'y touche. On les contrôle seulement avec le cadre **FOH — LEKOS**, tout plafonné à **70 %** (valeur DMX 178) :
  - touches (un appui = allumé en fondu 1,5 s, 2e appui = éteint) : **FOH 70 %** `Alt+7`, **FOH 40 %** `Alt+4`, **L1** `Ctrl+1`, **L2** `Ctrl+2`, **L3** `Ctrl+3` ;
  - boutons rotatifs pour doser : FOH (les 3) et L1 à L3 ;
  - Stream Deck : FOH 70 % et FOH 40 % sur la page 1 SHOW ; FOH 70 % et LEKO 1-3 sur la page 2 LOOKS ;
  - page **6 FOH** du Stream Deck (plugin 1.1, action « Niveau QLC+ ») : pour FOH, L1, L2 et L3, une rangée **− / niveau / +**. Chaque appui = 10 %, tenir = ça défile, la touche du milieu affiche le niveau en direct (un appui dessus = 0 %). Les boutons rotatifs de QLC+ bougent en même temps ;
  - si plusieurs commandes sont actives, c'est la plus haute qui gagne, jamais plus de 70 %. Sur le DMX-4 : mode DMX, adresse `R150`, sorties en dimmer (pas en switch). Le BLACKOUT les coupe aussi. FONDU AU NOIR éteint les touches FOH, mais pas les boutons rotatifs.
- Toutes les couleurs du show (ambre, blanc chaud, UV…) sont converties automatiquement en RGB ou RGBW.
- Si l'ordre des canaux MOSFiATA est différent dans le manuel, corrige `MOSFiATA-PAR-36-RGB.qxf` et `MOS_*` dans `tools/generate_show.py`.

## Comment jouer
1. **Choisis un LOOK** dans les 3 rangées du haut (30 looks) : tout le rig change d'un coup, avec des fondus.
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

**Rangée 2**

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

**Rangée 3**

| Look | PAR | Têtes |
|---|---|---|
| **SPOT CHANTEUR** | Bleu nuit | Blanc ouvert, les 4 sur le chanteur |
| **SOLO BATTERIE** | Pair/impair (tempo) | Rouge, gobo 1 rapide, sur la batterie, cercle |
| **SOLO BASSE** | Mauve | Magenta, gobo 3 qui tourne, sur la basse |
| **COUCHER SOLEIL** | Orange | Orange, gobo 5 qui tourne, éventail, balayage lent |
| **NÉON** | Magenta / cyan | Cyan, gobo 7, prisme, plafond, cercle |
| **TEMPÊTE** | Strobe aléatoire | Blanc, gobo 6 rapide, croisées, huit |
| **ROUGE & UV** | Rouge / UV | Rouge, gobo 2 qui tourne, public, vague tilt |
| **BLEU GLACE** | Cyan | Bleu, gobo 2, V inversé, balayage lent |
| **FEU D'ARTIFICE** | Arc-en-ciel | Chase couleurs + gobos, prisme, ballyhoo |
| **ENTRACTE** | Bleu nuit | Bleu, gobo 5 lent au plafond, balayage lent |

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

## Stream Deck

### Plugin QLC+ Show + profil XL
![Aperçu Stream Deck](show/apercu-streamdeck.png)

Le Stream Deck contrôle QLC+ **par son accès web** grâce au plugin `QLC+ Show` (dossier `streamdeck-plugin/`).
- QLC+ n'a **pas besoin d'être en avant-plan**.
- Une touche **s'allume** (cadre blanc) quand son bouton est actif dans QLC+, même s'il a été lancé ailleurs.
- L'appui et le relâchement sont envoyés séparément, donc les strobes, le blinder, les bumps et les flashs restent **allumés tant que la touche est tenue** et s'éteignent dès que tu lâches.
- Le plugin se reconnecte tout seul si QLC+ est fermé puis rouvert.

**Installation (une fois)**
1. Double-clique **`show/QLC-Plus-Show.streamDeckPlugin`**. Le logiciel Stream Deck l'installe.
2. Double-clique **`show/Show-Rock-XL.streamDeckProfile`**, puis choisis le profil **Show Rock (QLC+)** pour ton XL.

**À chaque show**
- Lance QLC+ avec **`show/Lancer-QLC.bat`** (QLC+ avec `-w` pour l'accès web, `-p` pour le mode show, et le show chargé).
- Si QLC+ est installé ailleurs que `C:\QLC+`, corrige le chemin dans le .bat.

**Réglage d'une touche** (glisse **QLC+ Show → Bouton QLC+** sur une touche) :
- choisis le bouton dans la liste du board, ou tape son ID ;
- comportement **Appui** = comme un clic sur le board, ou **Maintenu** = allumé tant que la touche est tenue ;
- l'adresse de QLC+ est `127.0.0.1:9999` par défaut. Tu peux mettre l'IP d'un autre PC.

**5 pages** (◀ PAGE / PAGE ▶ en bas à droite de chaque page) :
1. **SHOW** : les 10 looks de la rangée 1, AUTO, TAP, strobes, blinder, bumps et flashs (maintenus), 3 positions rapides, FONDU, BLACKOUT
2. **LOOKS** : les 20 autres looks
3. **PAR** : 20 couleurs et 10 effets
4. **TÊTES** : couleurs, gobos, rotation, prisme, chases
5. **POSITIONS** : 11 positions et 6 mouvements

**TAP** reste un raccourci clavier (`T`), car QLC+ ne permet pas de taper le tempo par le web. Pour TAP seulement, QLC+ doit être en avant-plan.

Le profil est généré par `tools/make_streamdeck.py` à partir du show (IDs des boutons). Relance-le après chaque `generate_show.py`, puis réimporte-le.

### Les raccourcis clavier
Chaque bouton du board a aussi un raccourci clavier, pratique au clavier ou sans le plugin. QLC+ doit alors être **en avant-plan** et en **mode show (▶)**.
- Les flashs `S B D F G-M` marchent tant que la touche du clavier est tenue.
- Les touches `Alt+Shift+K…T` (cadre STREAM DECK) sont en on/off au clavier ; le plugin les rend « maintenues ».


**LOOKS DU SHOW — un bouton = tout le rig  **

| Bouton | Touche |
|---|---|
| INTRO | `F1` |
| COUPLET | `F2` |
| PRÉ-REFRAIN | `F3` |
| REFRAIN | `F4` |
| GROS REFRAIN | `F5` |
| BALLADE | `F6` |
| SOLO GUITARE | `F7` |
| ÉNERGIE | `F8` |
| PSYCHÉ | `F9` |
| FINAL | `F10` |
| OUVERTURE | `Shift+F1` |
| FEU | `Shift+F2` |
| OCÉAN | `Shift+F3` |
| DISCO | `Shift+F4` |
| SOMBRE | `Shift+F5` |
| ROCK BLANC | `Shift+F6` |
| ACOUSTIQUE | `Shift+F7` |
| MONTÉE | `Shift+F8` |
| CHAOS | `Shift+F9` |
| APOTHÉOSE | `Shift+F10` |
| SPOT CHANTEUR | `Ctrl+F1` |
| SOLO BATTERIE | `Ctrl+F2` |
| SOLO BASSE | `Ctrl+F3` |
| COUCHER SOLEIL | `Ctrl+F4` |
| NÉON | `Ctrl+F5` |
| TEMPÊTE | `Ctrl+F6` |
| ROUGE & UV | `Ctrl+F7` |
| BLEU GLACE | `Ctrl+F8` |
| FEU D'ARTIFICE | `Ctrl+F9` |
| ENTRACTE | `Ctrl+F10` |
| ▶ AUTO | `F11` |

**PAR — COULEURS**

| Bouton | Touche |
|---|---|
| Rouge | `Alt+A` |
| Rouge sang | `Alt+B` |
| Orange | `Alt+C` |
| Ambre | `Alt+D` |
| Or | `Alt+E` |
| Blanc chaud | `Alt+F` |
| Blanc froid | `Alt+G` |
| Cyan | `Alt+H` |
| Bleu | `Alt+I` |
| Bleu nuit | `Alt+J` |
| Mauve | `Alt+K` |
| Magenta | `Alt+L` |
| Vert | `Alt+M` |
| UV | `Alt+N` |
| Rouge / Ambre | `Alt+O` |
| Bleu / Ambre | `Alt+P` |
| Rouge / Bleu | `Alt+Q` |
| Magenta / Cyan | `Alt+R` |
| Bords bleus | `Alt+S` |
| Bords rouges | `Alt+T` |

**PAR — EFFETS**

| Bouton | Touche |
|---|---|
| Vague rouge | `Alt+Shift+A` |
| Vague bleue | `Alt+Shift+B` |
| Pair / Impair | `Alt+Shift+C` |
| Alterné ambre/bleu | `Alt+Shift+D` |
| Un par un | `Alt+Shift+E` |
| Remplir centre | `Alt+Shift+F` |
| Arc-en-ciel | `Alt+Shift+G` |
| Plasma lent | `Alt+Shift+H` |
| Chase couleurs | `Alt+Shift+I` |
| Fondu lent | `Alt+Shift+J` |

**MASTERS & TEMPO**

| Bouton | Touche |
|---|---|
| TAP tempo | `T` |
| STROBE PAR | `S` |
| BLINDER | `B` |
| STROBE TÊTES | `D` |
| STROBE FOU | `F` |
| BLACKOUT | `X` |
| FONDU AU NOIR | `N` |

**TÊTES — COULEUR**

| Bouton | Touche |
|---|---|
| Blanc | `Ctrl+Shift+A` |
| Rouge | `Ctrl+Shift+B` |
| Orange | `Ctrl+Shift+C` |
| Jaune | `Ctrl+Shift+D` |
| Vert | `Ctrl+Shift+E` |
| Bleu | `Ctrl+Shift+F` |
| CTO | `Ctrl+Shift+G` |
| Cyan | `Ctrl+Shift+H` |
| Magenta | `Ctrl+Shift+I` |
| Arc-en-ciel | `Ctrl+Shift+J` |

**TÊTES — GOBO**

| Bouton | Touche |
|---|---|
| Ouvert | `Ctrl+Shift+K` |
| Gobo 1 | `Ctrl+Shift+L` |
| Gobo 2 | `Ctrl+Shift+M` |
| Gobo 3 | `Ctrl+Shift+N` |
| Gobo 4 | `Ctrl+Shift+O` |
| Gobo 5 | `Ctrl+Shift+P` |
| Gobo 6 | `Ctrl+Shift+Q` |
| Gobo 7 | `Ctrl+Shift+R` |

**TÊTES — FX**

| Bouton | Touche |
|---|---|
| Rotation gobo | `Ctrl+Shift+T` |
| Rotation rapide | `Ctrl+Shift+U` |
| Prisme | `Ctrl+Shift+V` |
| Chase couleurs | `Ctrl+Shift+W` |
| Chase gobos | `Ctrl+Shift+Y` |

**TÊTES — POSITION**

| Bouton | Touche |
|---|---|
| Centre | `Shift+A` |
| Public | `Shift+B` |
| Band | `Shift+C` |
| Chanteur | `Shift+D` |
| Croisé | `Shift+E` |
| Éventail | `Shift+F` |
| V inversé | `Shift+G` |
| Batterie | `Shift+H` |
| Guitare | `Shift+I` |
| Basse | `Shift+J` |
| Plafond | `Shift+K` |

**TÊTES — MOUVEMENT**

| Bouton | Touche |
|---|---|
| Cercle | `Shift+L` |
| Huit | `Shift+M` |
| Balayage lent | `Shift+N` |
| Vague tilt | `Shift+O` |
| Diamant | `Shift+P` |
| Ballyhoo | `Shift+Q` |

**FLASH & BUMPS**

| Bouton | Touche |
|---|---|
| BUMP GAUCHE | `G` |
| BUMP DROITE | `H` |
| FLASH ROUGE | `J` |
| FLASH BLEU | `K` |
| FLASH UV | `L` |
| FLASH TÊTES | `M` |

## Anti-bug : la scène BASE
Certains canaux (strobe des PAR, prisme, rotation de gobo, shutter des têtes) gardent leur dernière valeur quand un flash ou un bouton s'arrête. La scène **BASE (toujours active)** démarre toute seule en mode show et fait partie de chaque look : elle remet ces canaux à zéro dès qu'un flash est relâché.
Après un **FONDU AU NOIR**, relance un look avant d'utiliser les flashs (le fondu arrête aussi BASE).

## Positions des têtes
Les 8 positions sont **calculées à partir du plan de la salle** (têtes en ligne au-dessus du public, Tête 1 près de la scène) :
- têtes à **11 pi** du sol et scène à **2 pi** (valeurs supposées : `H_LIGHTS` et `H_STAGE` dans `tools/generate_show.py`) ;
- sens du pan vérifié dans la salle (`PAN_SIGN = -1`).

## Lekos
Pas encore dans le show : il faut ajouter leurs adresses.

## Regénérer le show
```
python3 tools/generate_show.py
```
Les adresses, couleurs et positions sont en haut du script.

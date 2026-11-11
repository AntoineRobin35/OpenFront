import pyxel
from random import randint, choice
from colorsys import rgb_to_hls, hls_to_rgb

LIGNES = 40
COLLONNES = 40
LARGEUR_ECRAN = 1200
HAUTEUR_ECRAN = 800
TAILLE_CASE = 10

ORIGINE_X = LARGEUR_ECRAN // 2 - (TAILLE_CASE * COLLONNES) // 2
ORIGINE_Y = HAUTEUR_ECRAN // 2 - (TAILLE_CASE * LIGNES) // 2

VITESSE_ATTAQUE = 3

COUT_TERRAIN = [16.5, 20, 100]
VITESSE = 0.1

derniere_case_cliquee = None

JOUEUR_ACTUEL = 1
attaques = []


### PARTIE COULEUR

def assombrir(hexa, quantite=0.15):
    r, g, b = ((hexa >> 16) & 255) / 255, ((hexa >> 8) & 255) / 255, (hexa & 255) / 255
    h, l, s = rgb_to_hls(r, g, b)
    r, g, b = hls_to_rgb(h, max(0, l - quantite), s)
    return (round(r * 255) << 16) | (round(g * 255) << 8) | round(b * 255)


TERRAINS = [0x4E7A47, 0x6E5A44, 0xC9CED3, 0x1B3A5C]

JOUEURS = [0xC8484F, 0x4F8FC7, 0x5FAE6B, 0xD9B84A, 0x8D6BB8]

NATIONS = [0xE6A23C, 0x3FB6A8, 0xE0706B, 0x6C8EBF, 0xB5C25A,
           0xC77DB5, 0x5BB5E0, 0xE88B4D, 0x7FD1A0, 0xA88BE0]

TRIBUS = [0x6B6B6B, 0x8A8A8A, 0x555B61, 0x9A9690, 0x73706A,
          0x7A5C45, 0x8F6B4E, 0x5E4636, 0xA17F5F, 0x6D5A48]

ENTITES = JOUEURS + NATIONS + TRIBUS
N = len(ENTITES)

PALETTE = TERRAINS + ENTITES + [assombrir(c) for c in ENTITES]
pyxel.colors[:] = PALETTE

ID_COULEUR_ENTITES = {i + 1: {"remplissage": i + 4, "frontiere": i + 4 + N} for i in range(N)}

### FIN PARTIE COULEUR



PREMIERE_TRIBU = len(JOUEURS) + len(NATIONS) + 1
MAG_TERRAIN = [80, 100, 120]
MAG_PRIORITE = [1, 1.5, 2]

nb_case = {j:0 for j in range(N + 1)}
frontiere = {j: set() for j in range(1, N + 1)}

troupes = {j:25000 for j in range(1, N + 1)}
for j in range(PREMIERE_TRIBU, N + 1):
    troupes[j] = 10000

prochain_coup_bot = {j: randint(10, 50) for j in range(PREMIERE_TRIBU, N + 1)}

RESTITUTION = 1.0
RESERVE = 0.35
EXPANSION = 0.15

## Init ZOOM
ZONE_JEU_X, ZONE_JEU_Y = 0, 0
ZONE_JEU_LARGEUR, ZONE_JEU_HAUTEUR = LARGEUR_ECRAN, HAUTEUR_ECRAN
ZOOM_MIN = 1.0
ZOOM_MAX = 40.0
FACTEUR_ZOOM_PAR_CRAN = 1.15

zoom = 4.0
camera_colonne = 0.0
camera_ligne = 0.0
point_ancre = None
## Fin Init ZOOM


pyxel.init(LARGEUR_ECRAN, HAUTEUR_ECRAN, title="OpenFront")
pyxel.mouse(True)

carte = pyxel.Image(LIGNES, COLLONNES)

grille = [[0 for y in range(COLLONNES)] for x in range(LIGNES)]

terrain = [
    [0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0,
     0, 3],
    [0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1,
     0, 0],
    [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1,
     1, 0],
    [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2,
     1, 1],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2,
     2, 1],
    [2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2,
     2, 2],
    [2, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2,
     2, 2],
    [2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2,
     2, 2],
    [2, 2, 2, 2, 1, 1, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1, 1, 2, 2, 2,
     2, 2],
    [2, 2, 2, 1, 1, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 1, 2, 2, 2,
     2, 2],
    [2, 2, 2, 1, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 1, 2, 2,
     2, 2],
    [2, 2, 1, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 2, 2,
     2, 2],
    [2, 2, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 1, 2,
     2, 2],
    [2, 2, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 2,
     2, 2],
    [2, 1, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 2,
     2, 2],
    [2, 1, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 1,
     2, 2],
    [1, 1, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1,
     2, 2],
    [1, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 0, 0, 0, 0, 0, 1,
     1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0,
     0, 0],
    [3, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0,
     3, 3],
    [3, 3, 0, 0, 1, 1, 1, 2, 2, 2, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 1, 1, 1, 0, 0, 0, 3,
     3, 3],
    [3, 3, 0, 0, 1, 1, 2, 2, 2, 2, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 3,
     3, 3],
    [3, 3, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 0, 0, 3, 3,
     3, 3],
    [3, 3, 3, 0, 0, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 3, 3,
     3, 3],
    [3, 3, 3, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 3, 3,
     3, 3],
    [3, 3, 3, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 1, 1, 0, 0, 3, 3, 3,
     3, 3],
    [3, 3, 3, 3, 0, 0, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 1, 1, 0, 0, 0, 3, 3, 3,
     3, 3],
    [3, 3, 3, 3, 3, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 3, 3, 3, 3,
     3, 3],
    [3, 3, 3, 3, 3, 3, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 0, 0, 0, 0, 3, 3, 3, 3, 3,
     3, 3],
    [3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3,
     3, 3],
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3,
     3, 3],
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3,
     3, 3],
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
     3, 3],
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
     3, 0],
    [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
     0, 0],
    [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0,
     0, 1],
    [0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0,
     0, 1],
    [1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0,
     1, 2],
]

grille[20][20] = 1

grille[19][5] = 16
grille[19][12] = 17
grille[19][26] = 18
grille[19][34] = 19

grille[30][30] = 2
grille[31][30] = 2
grille[30][31] = 2
grille[31][31] = 2


TERRAINS_CONQUERABLE = (0, 1, 2)


def pointSousCurseur():
    return (camera_colonne + (pyxel.mouse_x - ZONE_JEU_X) / zoom,
            camera_ligne + (pyxel.mouse_y - ZONE_JEU_Y) / zoom)

def limiterCamera():
    global camera_colonne, camera_ligne
    case_visible_largeur = ZONE_JEU_LARGEUR / zoom
    case_visible_hauteur = ZONE_JEU_HAUTEUR / zoom
    camera_colonne = borner(camera_colonne, -case_visible_largeur / 2, COLLONNES - case_visible_largeur / 2)
    camera_ligne = borner(camera_ligne, -case_visible_hauteur / 2, LIGNES - case_visible_hauteur / 2)

def deplacerCamera():
    global zoom, camera_colonne, camera_ligne, point_ancre

    if pyxel.mouse_wheel != 0:
        colonne_sous_souris, ligne_sous_souris = pointSousCurseur()
        zoom = borner(zoom * FACTEUR_ZOOM_PAR_CRAN ** pyxel.mouse_wheel, ZOOM_MIN, ZOOM_MAX)
        camera_colonne = colonne_sous_souris - (pyxel.mouse_x - ZONE_JEU_X) / zoom
        camera_ligne = ligne_sous_souris - (pyxel.mouse_y - ZONE_JEU_Y) / zoom

    if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
        point_ancre = pointSousCurseur()
    if pyxel.btn(pyxel.MOUSE_BUTTON_RIGHT) and point_ancre is not None:
        camera_colonne = point_ancre[0] - (pyxel.mouse_x - ZONE_JEU_X) / zoom
        camera_ligne = point_ancre[1] - (pyxel.mouse_y - ZONE_JEU_Y) / zoom
    else:
        point_ancre = None

    vitesse_en_cases = 20 / zoom
    if pyxel.btn(pyxel.KEY_LEFT):
        camera_colonne -= vitesse_en_cases
    if pyxel.btn(pyxel.KEY_RIGHT):
        camera_colonne += vitesse_en_cases
    if pyxel.btn(pyxel.KEY_UP):
        camera_ligne -= vitesse_en_cases
    if pyxel.btn(pyxel.KEY_DOWN):
        camera_ligne += vitesse_en_cases

    limiterCamera()


def centrerCarte():
    global zoom, camera_colonne, camera_ligne
    zoom = borner(min(ZONE_JEU_LARGEUR/ COLLONNES, ZONE_JEU_HAUTEUR / LIGNES), ZOOM_MIN, ZOOM_MAX)
    camera_colonne = COLLONNES / 2 - ZONE_JEU_LARGEUR / zoom / 2
    camera_ligne = LIGNES / 2 - ZONE_JEU_HAUTEUR / zoom / 2


def caseSousCurseur():
    if not (ZONE_JEU_X <= pyxel.mouse_x < ZONE_JEU_X + ZONE_JEU_LARGEUR and ZONE_JEU_Y <= pyxel.mouse_y < ZONE_JEU_Y + ZONE_JEU_HAUTEUR):
        return None

    colonne_decimal, ligne_decimal = pointSousCurseur()
    colonne = int(colonne_decimal // 1)
    ligne = int(ligne_decimal // 1)
    if not (0 <= ligne < LIGNES and 0 <= colonne < COLLONNES):
        return None
    return ligne, colonne


def estConquerable(x, y):
    return terrain[x][y] in TERRAINS_CONQUERABLE


def isFrontiere(x, y):
    proprietaire = grille[x][y]

    if proprietaire == 0:
        return False

    if x > 0 and grille[x - 1][y] != proprietaire:
        return True

    if y > 0 and grille[x][y - 1] != proprietaire:
        return True

    if x < LIGNES - 1 and grille[x + 1][y] != proprietaire:
        return True

    if y < COLLONNES - 1 and grille[x][y + 1] != proprietaire:
        return True

    return False


def candidatsInitiaux(attaquant, cible):
    resultat = set()
    for x, y in frontiere[attaquant]:
        for nx, ny in voisins(x, y):
            if grille[nx][ny] == cible and estConquerable(nx, ny):
                resultat.add((nx, ny))
    return resultat


def initFrontiere():
    for x in range(LIGNES):
        for y in range(COLLONNES):
            proprietaire = grille[x][y]
            if proprietaire != 0 and isFrontiere(x, y):
                frontiere[proprietaire].add((x, y))
initFrontiere()

def compteCase():
    for ligne in grille:
        for proprietaire in ligne:
            nb_case[proprietaire] += 1
compteCase()


def couleurCase(x, y):
    proprietaire = grille[x][y]
    if proprietaire == 0:
        return terrain[x][y]
    if isFrontiere(x, y):
        return ID_COULEUR_ENTITES[proprietaire]["frontiere"]
    return ID_COULEUR_ENTITES[proprietaire]["remplissage"]


def reddessiner(cases):
    a_refaire = set()
    for x, y in cases:
        a_refaire.add((x, y))
        a_refaire.update(voisins(x, y))
    for x, y in a_refaire:
        carte.pset(y, x, couleurCase(x, y))


def reddessinerTout():
    for x in range(LIGNES):
        for y in range(COLLONNES):
            carte.pset(y, x, couleurCase(x, y))
reddessinerTout()


def trouverAttaquer(attaquant, cible):
    for a in attaques:
        if a["attaquant"] == attaquant and a["cible"] == cible:
            return a
    return None


def lancerAttaque(attaquant, cible, part=0.2):
    envoyee = int(troupes[attaquant] * part)
    if envoyee < 1:
        return
    troupes[attaquant] -= envoyee

    oposant = trouverAttaquer(cible, attaquant)
    if oposant is not None:
        annulees = min(envoyee, oposant["troupes"])
        envoyee -= annulees
        oposant["troupes"] -= annulees
        if envoyee < 1:
            return

    existante = trouverAttaquer(attaquant, cible)
    if existante is not None:
        existante["troupes"] += envoyee
        return

    candidats = candidatsInitiaux(attaquant, cible)
    attaques.append({"attaquant": attaquant, "cible": cible, "candidats": candidats, "troupes": envoyee})


def click():
    global derniere_case_cliquee
    case = caseSousCurseur()
    if case is None:
        return

    ligne, collones = case
    proprietaire = grille[ligne][collones]
    derniere_case_cliquee = (ligne, collones, proprietaire)

    if proprietaire != JOUEUR_ACTUEL and estConquerable(ligne, collones):
        lancerAttaque(JOUEUR_ACTUEL, proprietaire)


def voisins(x, y):
    resultat = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < LIGNES and 0 <= ny < COLLONNES:
            resultat.append((nx, ny))
    return resultat


def prioriteCase(attaquant, x, y):
    case_voisines = 0
    for nx, ny in voisins(x, y):
        if grille[nx][ny] == attaquant:
            case_voisines += 1
    mag = MAG_PRIORITE[terrain[x][y]]
    return (randint(0, 6) + 10) * (1 - 0.5 * case_voisines + mag / 2)


def caseAttaquable(attaquant, cible):
    resultat = []
    for x in range(LIGNES):
        for y in range(COLLONNES):
            if grille[x][y] == cible:
                for nx, ny in voisins(x, y):
                    if grille[nx][ny] == attaquant:
                        resultat.append((x, y))
                        break
    return resultat


def maxTroupe(proprietaire):
    maxi = 2 * (1000 * nb_case[proprietaire] ** 0.6 + 50000)
    if proprietaire >= PREMIERE_TRIBU:
        maxi /= 3
    return maxi


def generationTroupe():
    for proprietaire in range(1, N + 1):
        if nb_case[proprietaire] == 0:
            continue
        troupe_actuel = troupes[proprietaire]
        maxi = maxTroupe(proprietaire)
        ajout = (10 + troupe_actuel ** 0.73 / 4) * (1 - troupe_actuel / maxi)
        if proprietaire >= PREMIERE_TRIBU:
            ajout *= 0.5
        troupes[proprietaire] = min(troupe_actuel + ajout, maxi)

def borner(valeur, mini, maxi):
    return max(mini, min(maxi, valeur))


def couts(attaque, x, y, front):
    type_t = terrain[x][y]
    mag, cout_case = MAG_TERRAIN[type_t], COUT_TERRAIN[type_t]
    A = attaque["troupes"]
    cible = attaque["cible"]

    if cible == 0:
        fraction = borner(2000 * cout_case / A, 5, 100) / (2 * front)
        return mag / 5, 0, fraction

    D = troupes[cible]
    densite = D / max(1, nb_case[cible])
    rapport = D / A
    perte_attaque = mag * borner(rapport, 0.6, 2) * (0.463 + 0.0039 * densite)
    cout_vitesse = borner(rapport, 0.82, 7.5) * borner(rapport / 20, 1, 50) / 8.55
    fraction = cout_vitesse * cout_case / front
    return perte_attaque, densite, fraction

### PARTIE BOTS

def choisirCible(bot):
    case_voisines = set()
    for x, y in frontiere[bot]:
        for nx, ny in voisins(x, y):
            proprietaire = grille[nx][ny]
            if proprietaire != bot and estConquerable(nx, ny):
                case_voisines.add(proprietaire)
    if not case_voisines:
        return None
    if 0 in case_voisines:
        return 0
    return choice(list(case_voisines))


def tourBots():
    for j in range(PREMIERE_TRIBU, N + 1):
        if nb_case[j] == 0:
            continue
        prochain_coup_bot[j] -= 1
        if prochain_coup_bot[j] > 0:
            continue
        prochain_coup_bot[j] = randint(40, 80)

        cible = choisirCible(j)
        if cible is None:
            continue

        if cible == 0 or cible >= PREMIERE_TRIBU:
            plancher = EXPANSION
        else:
            plancher = RESERVE

        disponibles = troupes[j] - plancher * maxTroupe(j)
        if disponibles >= 1:
            lancerAttaque(j, cible, part=disponibles / troupes[j])

### FIN PARTIE BOTS


def majFrontiere(cases, ancien_proprietaire):
    if ancien_proprietaire != 0:
        for case in cases:
            frontiere[ancien_proprietaire].discard(case)

    a_refaire = set(cases)

    for x, y in cases:
        a_refaire.update(voisins(x, y))

    for x, y in a_refaire:
        proprietaire = grille[x][y]
        if proprietaire == 0:
            continue
        if isFrontiere(x, y):
            frontiere[proprietaire].add((x, y))
        else:
            frontiere[proprietaire].discard((x, y))


def changerProprietaire(cases, ancien, nouveau):
    for x, y in cases:
        grille[x][y] = nouveau
    nb_case[ancien] -= len(cases)
    nb_case[nouveau] += len(cases)
    majFrontiere(cases, ancien)

def verifierFrontiere():
    for entite in range(1, N + 1):
        attendu = {(x, y) for x in range(LIGNES) for y in range(COLLONNES) if grille[x][y] == entite and isFrontiere(x, y)}
        if attendu != frontiere[entite]:
            print("frontière incohérente pour", entite)
            return False
    return True

def etapeAttaque():
    global attaques

    for attaque in attaques:
        if attaque["troupes"] < 1:
            continue
        attaquant, cible = attaque["attaquant"], attaque["cible"]

        valides = [(x, y) for (x, y) in attaque["candidats"] if grille[x][y] == cible]


        valides.sort(key=lambda case: prioriteCase(attaquant, case[0], case[1]))
        a_prendre = []
        front = max(1, len(valides))
        budget = 1
        for x, y in valides:
            perte_att, perte_def, fraction = couts(attaque, x, y, front)
            a_prendre.append((x, y))
            attaque["troupes"] -= perte_att
            if cible != 0:
                troupes[cible] = max(0, troupes[cible] - perte_def)
            budget -= fraction
            if budget <= 0 or attaque["troupes"] < 1:
                break
        candidats_suivant = set(valides[len(a_prendre):])

        changerProprietaire(a_prendre, cible, attaquant)

        for x, y in a_prendre:
            for nx, ny in voisins(x, y):
                if grille[nx][ny] == cible and estConquerable(nx, ny):
                    candidats_suivant.add((nx, ny))

        attaque["candidats"] = candidats_suivant
        reddessiner(a_prendre)
    attaque_active = []
    for a in attaques:
        if a["candidats"] and a["troupes"] >= 1:
            attaque_active.append(a)
        else:
            troupes[a["attaquant"]] += int(max(0, a["troupes"]) * RESTITUTION)
    attaques = attaque_active



def update():
    deplacerCamera()
    if pyxel.btnp(pyxel.KEY_C):
        centrerCarte()
    if pyxel.btnp(pyxel.KEY_ESCAPE):
        pyxel.quit()
    if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
        click()
    if pyxel.btnp(pyxel.KEY_V):
        print(verifierFrontiere())
    if pyxel.frame_count % VITESSE_ATTAQUE == 0:
        etapeAttaque()
        generationTroupe()
        tourBots()


def draw():
    pyxel.cls(20)
    colonne_debut = max(0, int(camera_colonne // 1))
    colonne_fin = min(COLLONNES, int(-(-(camera_colonne + ZONE_JEU_LARGEUR/ zoom) // 1)))
    ligne_debut = max(0, int(camera_ligne // 1))
    ligne_fin = min(LIGNES, int(-(-(camera_ligne + ZONE_JEU_HAUTEUR / zoom) // 1)))

    largeur_dessinee = colonne_fin - colonne_debut
    hauteur_dessinee = ligne_fin - ligne_debut
    if largeur_dessinee <= 0 or hauteur_dessinee <= 0:
        centrerCarte()
        return

    ecran_x_premiere_case = ZONE_JEU_X + (colonne_debut - camera_colonne) * zoom
    ecran_y_premiere_case = ZONE_JEU_Y + (ligne_debut - camera_ligne) * zoom

    pyxel.clip(ZONE_JEU_X, ZONE_JEU_Y, ZONE_JEU_LARGEUR, ZONE_JEU_HAUTEUR)

    pyxel.blt(ecran_x_premiere_case + (largeur_dessinee * zoom - largeur_dessinee) / 2,
              ecran_y_premiere_case + (hauteur_dessinee * zoom - hauteur_dessinee) / 2,
              carte,
              colonne_debut, ligne_debut,
              largeur_dessinee, hauteur_dessinee,
              scale=zoom)

    pyxel.clip()


pyxel.run(update, draw)

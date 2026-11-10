import pyxel
from random import random
import colorsys

LIGNES = 40
COLLONNES = 40
LARGEUR_ECRAN = 1200
HAUTEUR_ECRAN = 800
TAILLE_CASE = 10

ORIGINE_X = LARGEUR_ECRAN // 2 - (TAILLE_CASE * COLLONNES) // 2
ORIGINE_Y = HAUTEUR_ECRAN // 2 - (TAILLE_CASE * LIGNES) // 2

VITESSE_ATTAQUE = 5
CASE_PAR_ETAPE = 8

derniere_case_cliquee = None

JOUEUR_ACTUEL = 1
attaques = []


### PARTIE COULEUR

def assombrir(hexa, quantite=0.15):
    r, g, b = ((hexa >> 16) & 255) / 255, ((hexa >> 8) & 255) / 255, (hexa & 255) / 255
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(h, max(0, l - quantite), s)
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

grille[0][1] = 1


grille[30][30] = 2
grille[31][30] = 2
grille[30][31] = 2
grille[31][31] = 2


TERRAINS_CONQUERABLE = (0, 1, 2)


def estConquerable(x, y):
    return terrain[x][y] in TERRAINS_CONQUERABLE


def candidatsInitiaux(attaquant, cible):
    resultat = set()
    for x in range(LIGNES):
        for y in range(COLLONNES):
            if grille[x][y] == cible and estConquerable(x, y):
                for nx, ny in voisins(x, y):
                    if grille[nx][ny] == attaquant:
                        resultat.add((x, y))
                        break

    return resultat


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


def caseSousCurseur():
    # Position de la souris dans la grille
    collonnes = (pyxel.mouse_x - ORIGINE_X) // TAILLE_CASE
    ligne = (pyxel.mouse_y - ORIGINE_Y) // TAILLE_CASE

    if not (0 <= ligne < LIGNES and 0 <= collonnes < COLLONNES):
        return None
    return ligne, collonnes


def estAttaquer(attaquant, cible):
    for a in attaques:
        if a["attaquant"] == attaquant and a["cible"] == cible:
            return a
    return None


def lancerAttaque(attaquant, cible):
    if estAttaquer(attaquant, cible):
        return
    candidats = candidatsInitiaux(attaquant, cible)
    attaques.append({"attaquant": attaquant, "cible": cible, "candidats": candidats})


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


def scoreCase(attaquant, x, y):
    score = 0
    for nx, ny in voisins(x, y):
        if grille[nx][ny] == attaquant:
            score += 1
    return score + random()


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


def etapeAttaque():
    global attaques

    for attaque in attaques:
        attaquant, cible = attaque["attaquant"], attaque["cible"]

        valides = [(x, y) for (x, y) in attaque["candidats"] if grille[x][y] == cible]
        valides.sort(key=lambda case: scoreCase(attaquant, case[0], case[1]), reverse=True)
        a_prendre = valides[:CASE_PAR_ETAPE]
        restant = set(valides[CASE_PAR_ETAPE:])

        for x, y in a_prendre:
            grille[x][y] = attaquant

        for x, y in a_prendre:
            for nx, ny in voisins(x, y):
                if grille[nx][ny] == cible and estConquerable(nx, ny):
                    restant.add((nx, ny))

        attaque["candidats"] = restant
        reddessiner(a_prendre)
    attaques = [a for a in attaques if a["candidats"]]


def update():
    if pyxel.btnp(pyxel.KEY_ESCAPE):
        pyxel.quit()
    if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
        click()
    if pyxel.frame_count % VITESSE_ATTAQUE == 0:
        etapeAttaque()


reddessinerTout()
def draw():
    pyxel.cls(20)
    largeur_finale = COLLONNES * TAILLE_CASE
    hauteur_finale = LIGNES * TAILLE_CASE
    # blt(scale) agrandit autour du centre : on compense la moitié de l'agrandissement
    dx = (largeur_finale - COLLONNES) / 2
    dy = (hauteur_finale - LIGNES) / 2
    pyxel.blt(ORIGINE_X + dx, ORIGINE_Y + dy, carte, 0, 0, COLLONNES, LIGNES, scale=TAILLE_CASE)


print(candidatsInitiaux(2, 0))
pyxel.run(update, draw)

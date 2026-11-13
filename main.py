## Imports
import pyxel
from random import randint, choice, Random, randrange
from colorsys import rgb_to_hls, hls_to_rgb
import os
## Fin des imports


## Dimensions de la carte et de l'écran
LIGNES = 500 # Nombre de lignes
COLLONNES = 500 # Nombre de colonnes
LARGEUR_ECRAN = 1200 # Taille de la largeur de l'écran
HAUTEUR_ECRAN = 800 # Taille de la hauteur de l'écran
HAUTEUR_BARRE = 96
## Fin des dimensions de la carte et de l'écran


## Outils généraux utilisés partout
def borner(valeur, mini, maxi):
    """Garde une valeur entre deux bornes.
    Entrée : la valeur, le minimum, le maximum.
    Sortie : la valeur, ramenée au minimum ou au maximum si elle dépasse (nombre)."""
    return max(mini, min(maxi, valeur))


def voisins(x, y):
    """Trouve les voisins horizontaux et verticaux d'une case.
    Entrée : la ligne x et la colonne y de la case. Utilise LIGNES et COLLONNES pour rester dans la carte.
    Sortie : la liste des cases voisines, chacune sous la forme (ligne, colonne)."""
    resultat = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < LIGNES and 0 <= ny < COLLONNES:
            resultat.append((nx, ny))
    return resultat
## Fin des outils généraux


## Génération du terrain (bruit lisse, mer, herbe, terre, montagne)
# (taille d'une maille pour une carte de 500 cases, poids dans le mélange)
TAILLES_DES_OCTAVES = [64, 32, 16, 8]
PARAMETRES_CARTE_PAR_DEFAUT = {
    "poids_octave_64": 1.0, "poids_octave_32": 0.5, "poids_octave_16": 0.25, "poids_octave_8": 0.125,
    "force_ile": 0.2, "niveau_mer": 0.30, "limite_herbe": 0.56, "limite_terre": 0.70,
}

TERRAINS_CONQUERABLE = (0, 1, 2)

terrain = []


def genererBruitLisse(nombre_ligne, nombre_colonnes, taille_maille, generateur_aleatoire):
    """Crée une grille de bruit lisse : des valeurs aléatoires placées aux coins de grosses mailles, adoucies entre elles.
    Entrée : le nombre de lignes, le nombre de colonnes, la taille d'une maille, le générateur aléatoire à utiliser.
    Sortie : une grille (liste de listes) de nombres entre 0 et 1."""
    nbr_maille_hauteur = nombre_ligne // taille_maille + 2
    nbr_maille_largeur = nombre_colonnes // taille_maille + 2

    valeur_aux_coins= [[generateur_aleatoire.random() for _ in range(nbr_maille_largeur)]
                        for _ in range(nbr_maille_hauteur)]

    progression_lisse = []
    for decalage_dans_la_maille in range(taille_maille):
        avancement = decalage_dans_la_maille / taille_maille
        progression_lisse.append(avancement * avancement * (3 - 2 * avancement))

    bruit = []
    for ligne in range(nombre_ligne):
        numero_maille_ligne = ligne // taille_maille
        progression_vertical_local = progression_lisse[ligne % taille_maille]
        coins_du_haut_gauche = valeur_aux_coins[numero_maille_ligne]
        coins_du_bas_gauche = valeur_aux_coins[numero_maille_ligne + 1]
        valeur_final_ligne = []
        for colonnes in range(nombre_colonnes):
            numero_maille_colonnes = colonnes // taille_maille
            progression_horizontale_locale = progression_lisse[colonnes % taille_maille]
            valeur_en_haut = (coins_du_haut_gauche[numero_maille_colonnes] * (1 - progression_horizontale_locale)
                             + coins_du_haut_gauche[numero_maille_colonnes + 1] * progression_horizontale_locale)
            valeur_en_bas = (coins_du_bas_gauche[numero_maille_colonnes] * (1 - progression_horizontale_locale)
                             + coins_du_bas_gauche[numero_maille_colonnes + 1] * progression_horizontale_locale)
            valeur_final_ligne.append(valeur_en_haut * (1 - progression_vertical_local) + valeur_en_bas * progression_vertical_local)
        bruit.append(valeur_final_ligne)
    return bruit


def genererTerrain(nombre_lignes, nombre_colonnes, graine=None, parametres=PARAMETRES_CARTE_PAR_DEFAUT):
    """Génère la carte : mélange plusieurs bruits lisses, creuse les bords pour faire une île, puis découpe en types de terrain.
    Entrée : le nombre de lignes, le nombre de colonnes, une graine (facultative, aléatoire si absente),
    le dictionnaire de paramètres de la carte. Utilise TAILLES_DES_OCTAVES.
    Sortie : une grille (liste de listes) de numéros de terrain : 0 herbe, 1 terre, 2 montagne, 3 mer."""
    graine_effective = graine if graine is not None else randrange(10 ** 9)

    octaves = []
    for taille_reference in TAILLES_DES_OCTAVES:
        poids = parametres[f"poids_octave_{taille_reference}"]
        if poids > 0:
            octaves.append((taille_reference, poids))
    if not octaves:                                     # tous les poids à 0 : on garde la grosse octave
        octaves = [(64, 1.0)]
    somme_des_poids = sum(poids for _, poids in octaves)

    altitude = [[0.0] * nombre_colonnes for _ in range(nombre_lignes)]
    for taille_maille_reference, poids in octaves:
        generateur_de_l_octave = Random(f"{graine_effective}-{taille_maille_reference}")
        taille_maille = max(2, round(taille_maille_reference * max(nombre_lignes, nombre_colonnes) / 500))
        bruit = genererBruitLisse(nombre_lignes, nombre_colonnes, taille_maille, generateur_de_l_octave)
        for ligne in range(nombre_lignes):
            for colonne in range(nombre_colonnes):
                altitude[ligne][colonne] += bruit[ligne][colonne] * poids / somme_des_poids

    terrain = []
    for lignes in range(nombre_lignes):
        ecart_vertical_au_centre = (lignes / nombre_lignes - 0.5) * 2
        hauteur_ligne = []
        for colonnes in range(nombre_colonnes):
            ecart_horizontal_au_centre = (colonnes / nombre_colonnes - 0.5) * 2
            distance_au_centre = min(1.0, (ecart_horizontal_au_centre ** 2 + ecart_vertical_au_centre ** 2) ** 0.5)
            hauteur = altitude[lignes][colonnes] - parametres["force_ile"] * distance_au_centre ** 3

            if hauteur < parametres["niveau_mer"]:
                hauteur_ligne.append(3)
            elif hauteur < parametres["limite_herbe"]:
                hauteur_ligne.append(0)
            elif hauteur < parametres["limite_terre"]:
                hauteur_ligne.append(1)
            else:
                hauteur_ligne.append(2)
        terrain.append(hauteur_ligne)
    return terrain


def estConquerable(x, y):
    """Dit si une case peut être conquise (tout sauf la mer).
    Entrée : la ligne x et la colonne y de la case. Utilise la grille terrain et TERRAINS_CONQUERABLE.
    Sortie : True si la case est conquérable, False sinon."""
    return terrain[x][y] in TERRAINS_CONQUERABLE
## Fin de la génération du terrain


## Couleurs (terrains, joueurs, nations, tribus, palette Pyxel)
def assombrir(hexa, quantite=0.15):
    """Assombrit une couleur, pour en faire la couleur de frontière d'un territoire.
    Entrée : la couleur en hexadécimal (entier), la quantité de luminosité à retirer.
    Sortie : la couleur assombrie, en hexadécimal (entier)."""
    r, g, b = ((hexa >> 16) & 255) / 255, ((hexa >> 8) & 255) / 255, (hexa & 255) / 255 # découpage des trois octets hexadecimal en trois valeurs
    h, l, s = rgb_to_hls(r, g, b) # passge au hls
    r, g, b = hls_to_rgb(h, max(0, l - quantite), s) # diminution de la luminosité pour assombrir et passage au rgb
    return (round(r * 255) << 16) | (round(g * 255) << 8) | round(b * 255) # recréation de la forme hexadecimal et envoie


TERRAINS = [0x4E7A47, 0x6E5A44, 0xC9CED3, 0x1B3A5C]

JOUEURS = [0xC8484F, 0x4F8FC7, 0x5FAE6B, 0xD9B84A, 0x8D6BB8]

NATIONS = [0xE6A23C, 0x3FB6A8, 0xE0706B, 0x6C8EBF, 0xB5C25A,
           0xC77DB5, 0x5BB5E0, 0xE88B4D, 0x7FD1A0, 0xA88BE0]

TRIBUS = [0x6B6B6B, 0x8A8A8A, 0x555B61, 0x9A9690, 0x73706A,
          0x7A5C45, 0x8F6B4E, 0x5E4636, 0xA17F5F, 0x6D5A48]

COULEURS_INTERFACE = {
    "fond": 0x1E2430,
    "panneau": 0x2A3245,
    "bordure": 0x4A5878,
    "bouton": 0x3A4A66,
    "bouton_survole": 0x5A6E94,
    "bouton_principal": 0xE6A23C,
    "bouton_principal_survole": 0xF2BC6B,
    "texte": 0xF2F2F2,
    "texte_discret": 0x9AA5BD,
    "texte_sur_principal": 0x1E2430,
    "rouge": 0xC8484F,
}
ENTITES = JOUEURS + NATIONS + TRIBUS
N = len(ENTITES)
PREMIERE_TRIBU = len(JOUEURS) + len(NATIONS) + 1

PALETTE = TERRAINS + ENTITES + [assombrir(c) for c in ENTITES] + list(COULEURS_INTERFACE.values())
pyxel.colors[:] = PALETTE

ID_COULEUR_ENTITES = {i + 1: {"remplissage": i + 4, "frontiere": i + 4 + N} for i in range(N)}
PREMIERE_COULEUR_INTERFACE = len(TERRAINS) + 2 * N
COULEUR = {nom: PREMIERE_COULEUR_INTERFACE + numero for numero, nom in enumerate(COULEURS_INTERFACE)}
## Fin des couleurs


## Paramètres et état du jeu (troupes, attaques, bots, coûts)
# Joueur
JOUEUR_ACTUEL = 1

# Coûts et réglages des combats
VITESSE_ATTAQUE = 3
COUT_TERRAIN = [16.5, 20, 100]
MAG_TERRAIN = [80, 100, 120]
MAG_PRIORITE = [1, 1.5, 2]
RESTITUTION = 1.0
FORCE_COMPACITE = 0.25

# Réglages de la partie
SEUIL_DE_VICTOIRE = 80              # % des terres conquérables
IMAGES_PAR_SECONDE = 30
RAYON_DE_DEPART = 4          # chaque entité commence avec un disque d'environ 49 cases
ESPACEMENT_RELATIF = 0.6     # distance minimale entre deux départs, par rapport à l'espacement naturel

REGLAGES_PAR_DEFAUT = {
    "graine": None,
    "nombre_de_tribus": 10,
    "troupes_de_depart": 25000,
    "difficulte": "Normale",
    **PARAMETRES_CARTE_PAR_DEFAUT,
}

DIFFICULTES = {
    "Facile":    {"delais": (60, 120), "expansion": 0.30, "reserve": 0.50},
    "Normale":   {"delais": (40, 80),  "expansion": 0.15, "reserve": 0.35},
    "Difficile": {"delais": (20, 45),  "expansion": 0.08, "reserve": 0.25},
}
difficulte_en_cours = DIFFICULTES["Normale"]

# État de la partie en cours
numero_d_etape = 0
attaques = []
nb_case = {}
frontiere = {}
troupes = {}
prochain_coup_bot = {}
total_cases_conquerables = 1

resultat_de_la_partie = None        # "victoire", "defaite" ou None
message_de_fin = ""
part_maximale_de_territoire = 0.0
adversaires_au_depart = 0
derniers_reglages = None
## Fin des paramètres et de l'état du jeu


## Fenêtre Pyxel, image de la carte et grille des propriétaires
pyxel.init(LARGEUR_ECRAN, HAUTEUR_ECRAN, title="OpenFront")
pyxel.mouse(True)

carte = pyxel.Image(LIGNES, COLLONNES)

grille = []
## Fin de la fenêtre Pyxel, de la carte et de la grille


## Territoires et frontières (comptage des cases, frontières, changements de propriétaire)
def isFrontiere(x, y):
    """Dit si une case est sur la frontière de son propriétaire (au moins un voisin d'un autre propriétaire).
    Entrée : la ligne x et la colonne y de la case. Utilise la grille des propriétaires et LIGNES / COLLONNES.
    Sortie : True si c'est une case de frontière, False sinon (toujours False pour une case sans propriétaire)."""
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


def initFrontiere():
    """Remplit l'ensemble des cases de frontière de chaque entité, en parcourant toute la carte.
    Entrée : rien. Utilise la grille des propriétaires et le dictionnaire frontiere.
    Sortie : rien, le dictionnaire frontiere est modifié."""
    for x in range(LIGNES):
        for y in range(COLLONNES):
            proprietaire = grille[x][y]
            if proprietaire != 0 and isFrontiere(x, y):
                frontiere[proprietaire].add((x, y))


def compteCase():
    """Compte combien de cases possède chaque entité.
    Entrée : rien. Utilise la grille des propriétaires et le dictionnaire nb_case.
    Sortie : rien, le dictionnaire nb_case est modifié."""
    for ligne in grille:
        for proprietaire in ligne:
            nb_case[proprietaire] += 1


def candidatsInitiaux(attaquant, cible):
    """Trouve les cases de la cible qui touchent le territoire de l'attaquant, point de départ d'une attaque.
    Entrée : le numéro de l'attaquant, le numéro de la cible. Utilise frontiere et la grille des propriétaires.
    Sortie : un ensemble de cases conquérables, chacune sous la forme (ligne, colonne)."""
    resultat = set()
    for x, y in frontiere[attaquant]:
        for nx, ny in voisins(x, y):
            if grille[nx][ny] == cible and estConquerable(nx, ny):
                resultat.add((nx, ny))
    return resultat


def majFrontiere(cases, ancien_proprietaire):
    """Met à jour les frontières après un changement de propriétaire (pour les cases et leurs voisines).
    Entrée : la liste des cases qui ont changé, le numéro de leur ancien propriétaire. Utilise grille et frontiere.
    Sortie : rien, le dictionnaire frontiere est modifié."""
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
    """Donne des cases à un nouveau propriétaire et met à jour les compteurs et les frontières.
    Entrée : la liste des cases, le numéro de l'ancien propriétaire, le numéro du nouveau. Utilise grille et nb_case.
    Sortie : rien, la grille, nb_case et frontiere sont modifiés."""
    for x, y in cases:
        grille[x][y] = nouveau
    nb_case[ancien] -= len(cases)
    nb_case[nouveau] += len(cases)
    majFrontiere(cases, ancien)


def verifierFrontiere():
    """Outil de débogage (touche V) : recalcule toutes les frontières depuis la grille et les compare à celles stockées.
    Entrée : rien. Utilise grille et frontiere.
    Sortie : True si tout est cohérent, False à la première entité incohérente (qui est alors affichée)."""
    for entite in range(1, N + 1):
        attendu = {(x, y) for x in range(LIGNES) for y in range(COLLONNES) if grille[x][y] == entite and isFrontiere(x, y)}
        if attendu != frontiere[entite]:
            print("frontière incohérente pour", entite)
            return False
    return True
## Fin des territoires et frontières


## Dessin de la carte (couleur des cases et mise à jour de l'image)
def couleurCase(x, y):
    """Choisit la couleur d'une case : terrain si elle n'appartient à personne, sinon couleur de son propriétaire (plus sombre sur la frontière).
    Entrée : la ligne x et la colonne y de la case. Utilise grille, terrain et ID_COULEUR_ENTITES.
    Sortie : le numéro de couleur de la palette Pyxel (entier)."""
    proprietaire = grille[x][y]
    if proprietaire == 0:
        return terrain[x][y]
    if isFrontiere(x, y):
        return ID_COULEUR_ENTITES[proprietaire]["frontiere"]
    return ID_COULEUR_ENTITES[proprietaire]["remplissage"]


def reddessiner(cases):
    """Redessine sur l'image de la carte les cases données et leurs voisines (leur frontière a pu changer).
    Entrée : la liste des cases modifiées. Utilise l'image carte.
    Sortie : rien, l'image carte est modifiée."""
    a_refaire = set()
    for x, y in cases:
        a_refaire.add((x, y))
        a_refaire.update(voisins(x, y))
    for x, y in a_refaire:
        carte.pset(y, x, couleurCase(x, y))


def reddessinerTout():
    """Redessine toute la carte, case par case.
    Entrée : rien. Utilise l'image carte, LIGNES et COLLONNES.
    Sortie : rien, l'image carte est modifiée."""
    for x in range(LIGNES):
        for y in range(COLLONNES):
            carte.pset(y, x, couleurCase(x, y))
## Fin du dessin de la carte


## Zoom et caméra (déplacement, zoom à la molette, conversion souris -> case)
ZONE_JEU_X, ZONE_JEU_Y = 0, 0
ZONE_JEU_LARGEUR, ZONE_JEU_HAUTEUR = LARGEUR_ECRAN, HAUTEUR_ECRAN - HAUTEUR_BARRE
ZOOM_MIN = 1.0
ZOOM_MAX = 40.0
FACTEUR_ZOOM_PAR_CRAN = 1.15

zoom = 4.0
camera_colonne = 0.0
camera_ligne = 0.0
point_ancre = None


def pointSousCurseur():
    """Calcule le point de la carte situé sous la souris (position décimale, pas forcément une case entière).
    Entrée : rien. Utilise la position de la souris, le zoom et la position de la caméra.
    Sortie : la colonne et la ligne du point (deux nombres décimaux)."""
    return (camera_colonne + (pyxel.mouse_x - ZONE_JEU_X) / zoom,
            camera_ligne + (pyxel.mouse_y - ZONE_JEU_Y) / zoom)


def limiterCamera():
    """Empêche la caméra de sortir trop loin de la carte.
    Entrée : rien. Utilise la caméra, le zoom, la taille de la zone de jeu et de la carte.
    Sortie : rien, camera_colonne et camera_ligne sont modifiés."""
    global camera_colonne, camera_ligne
    case_visible_largeur = ZONE_JEU_LARGEUR / zoom
    case_visible_hauteur = ZONE_JEU_HAUTEUR / zoom
    camera_colonne = borner(camera_colonne, -case_visible_largeur / 2, COLLONNES - case_visible_largeur / 2)
    camera_ligne = borner(camera_ligne, -case_visible_hauteur / 2, LIGNES - case_visible_hauteur / 2)


def deplacerCamera():
    """Gère le zoom à la molette, le déplacement en glissant avec le clic droit et le déplacement avec les flèches.
    Entrée : rien. Utilise la souris, le clavier, le zoom et la position de la caméra.
    Sortie : rien, zoom, camera_colonne et camera_ligne sont modifiés."""
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
    """Règle le zoom et la caméra pour voir toute la carte, centrée dans la zone de jeu.
    Entrée : rien. Utilise la taille de la carte et de la zone de jeu.
    Sortie : rien, zoom, camera_colonne et camera_ligne sont modifiés."""
    global zoom, camera_colonne, camera_ligne
    zoom = borner(min(ZONE_JEU_LARGEUR/ COLLONNES, ZONE_JEU_HAUTEUR / LIGNES), ZOOM_MIN, ZOOM_MAX)
    camera_colonne = COLLONNES / 2 - ZONE_JEU_LARGEUR / zoom / 2
    camera_ligne = LIGNES / 2 - ZONE_JEU_HAUTEUR / zoom / 2


def centrerSurCase(ligne, colonne, nouveau_zoom):
    """Centre la caméra sur une case donnée avec un zoom choisi.
    Entrée : la ligne et la colonne de la case, le nouveau zoom. Utilise la taille de la zone de jeu.
    Sortie : rien, zoom, camera_colonne et camera_ligne sont modifiés."""
    global zoom, camera_colonne, camera_ligne
    zoom = borner(nouveau_zoom, ZOOM_MIN, ZOOM_MAX)
    camera_colonne = colonne + 0.5 - ZONE_JEU_LARGEUR / zoom / 2
    camera_ligne = ligne + 0.5 - ZONE_JEU_HAUTEUR / zoom / 2
    limiterCamera()


def caseSousCurseur():
    """Trouve la case de la carte située sous la souris.
    Entrée : rien. Utilise la position de la souris, la zone de jeu, la caméra et la taille de la carte.
    Sortie : la ligne et la colonne de la case (deux entiers), ou None si la souris est hors de la zone de jeu ou de la carte."""
    if not (ZONE_JEU_X <= pyxel.mouse_x < ZONE_JEU_X + ZONE_JEU_LARGEUR and ZONE_JEU_Y <= pyxel.mouse_y < ZONE_JEU_Y + ZONE_JEU_HAUTEUR):
        return None

    colonne_decimal, ligne_decimal = pointSousCurseur()
    colonne = int(colonne_decimal // 1)
    ligne = int(ligne_decimal // 1)
    if not (0 <= ligne < LIGNES and 0 <= colonne < COLLONNES):
        return None
    return ligne, colonne
## Fin du zoom et de la caméra


## Troupes et combats (génération de troupes, coûts, attaques)
def maxTroupe(proprietaire):
    """Calcule le nombre maximum de troupes d'une entité (il grandit avec son territoire, et est divisé par 3 pour une tribu).
    Entrée : le numéro de l'entité. Utilise nb_case et PREMIERE_TRIBU.
    Sortie : le maximum de troupes (nombre décimal)."""
    maxi = 2 * (1000 * nb_case[proprietaire] ** 0.6 + 50000)
    if proprietaire >= PREMIERE_TRIBU:
        maxi /= 3
    return maxi


def generationTroupe():
    """Fait gagner des troupes à chaque entité qui a encore du territoire (la croissance ralentit près du maximum, et les tribus sont plus lentes).
    Entrée : rien. Utilise troupes, nb_case et maxTroupe.
    Sortie : rien, le dictionnaire troupes est modifié."""
    for proprietaire in range(1, N + 1):
        if nb_case[proprietaire] == 0:
            continue
        troupe_actuel = troupes[proprietaire]
        maxi = maxTroupe(proprietaire)
        ajout = (10 + troupe_actuel ** 0.73 / 4) * (1 - troupe_actuel / maxi)
        if proprietaire >= PREMIERE_TRIBU:
            ajout *= 0.5
        troupes[proprietaire] = min(troupe_actuel + ajout, maxi)


def prioriteCase(attaquant, x, y, etape_de_decouverte):
    """Calcule la priorité d'une case à conquérir : plus le nombre est petit, plus elle est prise tôt.
    Dépend du hasard, du nombre de voisins déjà à l'attaquant, du terrain et de l'ancienneté de la case dans l'attaque.
    Entrée : le numéro de l'attaquant, la ligne x et la colonne y de la case, l'étape où elle a été découverte.
    Utilise grille, terrain, MAG_PRIORITE et FORCE_COMPACITE.
    Sortie : la priorité (nombre décimal)."""
    case_voisines = 0
    for nx, ny in voisins(x, y):
        if grille[nx][ny] == attaquant:
            case_voisines += 1
    mag = MAG_PRIORITE[terrain[x][y]]
    return (randint(0, 6) + 10) * (1 - FORCE_COMPACITE * case_voisines + mag / 2) + etape_de_decouverte


def couts(attaque, x, y, front):
    """Calcule ce que coûte la conquête d'une case : pertes de l'attaquant, pertes du défenseur et part de l'effort de l'étape consommée.
    Entrée : l'attaque (dictionnaire), la ligne x et la colonne y de la case, la taille du front (nombre de cases attaquables).
    Utilise terrain, troupes, nb_case, COUT_TERRAIN et MAG_TERRAIN.
    Sortie : les pertes de l'attaquant, les pertes du défenseur et la part de l'effort consommée (trois nombres)."""
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


def trouverAttaquer(attaquant, cible):
    """Cherche l'attaque en cours d'un attaquant contre une cible.
    Entrée : le numéro de l'attaquant, le numéro de la cible. Utilise la liste attaques.
    Sortie : l'attaque (dictionnaire), ou None s'il n'y en a pas."""
    for a in attaques:
        if a["attaquant"] == attaquant and a["cible"] == cible:
            return a
    return None


def lancerAttaque(attaquant, cible, part=0.2):
    """Lance une attaque en envoyant une part des troupes de l'attaquant.
    Si la cible attaque déjà l'attaquant, les troupes s'annulent ; si une attaque identique existe, on lui ajoute les troupes.
    Entrée : le numéro de l'attaquant, le numéro de la cible, la part des troupes envoyée (0.2 par défaut).
    Utilise troupes et attaques.
    Sortie : rien, troupes et attaques sont modifiés."""
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

    candidats = {case: numero_d_etape for case in candidatsInitiaux(attaquant, cible)}
    attaques.append({"attaquant": attaquant, "cible": cible, "candidats": candidats, "troupes": envoyee})


def etapeAttaque():
    """Fait avancer toutes les attaques d'une étape : conquiert des cases tant que le budget et les troupes le permettent,
    découvre les nouvelles cases à attaquer, redessine, puis termine les attaques finies (les troupes restantes retournent à l'attaquant).
    Entrée : rien. Utilise attaques, grille, troupes, numero_d_etape et RESTITUTION.
    Sortie : rien, attaques, la grille, troupes et l'image de la carte sont modifiés."""
    global attaques, numero_d_etape
    numero_d_etape += 1

    for attaque in attaques:
        if attaque["troupes"] < 1:
            continue
        attaquant, cible = attaque["attaquant"], attaque["cible"]
        decouvertes = attaque["candidats"]

        valides = [(x, y) for (x, y) in decouvertes if grille[x][y] == cible]
        valides.sort(key=lambda case: prioriteCase(attaquant, case[0], case[1], decouvertes[case]))
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
        candidats_suivant = {case: decouvertes[case] for case in valides[len(a_prendre):]}

        changerProprietaire(a_prendre, cible, attaquant)

        for x, y in a_prendre:
            for nx, ny in voisins(x, y):
                if grille[nx][ny] == cible and estConquerable(nx, ny):
                    candidats_suivant.setdefault((nx, ny), numero_d_etape)

        attaque["candidats"] = candidats_suivant
        reddessiner(a_prendre)
    attaque_active = []
    for a in attaques:
        if a["candidats"] and a["troupes"] >= 1:
            attaque_active.append(a)
        else:
            troupes[a["attaquant"]] += int(max(0, a["troupes"]) * RESTITUTION)
    attaques = attaque_active
## Fin des troupes et des combats


## Bots (choix de la cible et décisions des tribus)
def choisirCible(bot):
    """Choisit qui un bot va attaquer parmi les voisins de son territoire (le terrain libre est toujours prioritaire).
    Entrée : le numéro du bot. Utilise frontiere et la grille des propriétaires.
    Sortie : le numéro de la cible (0 pour le terrain libre), ou None s'il n'y a rien à attaquer."""
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
    """Fait jouer les tribus : quand le délai d'un bot est écoulé, il choisit une cible et attaque avec ses troupes au-delà d'une réserve (selon la difficulté).
    Entrée : rien. Utilise difficulte_en_cours, prochain_coup_bot, nb_case, troupes et PREMIERE_TRIBU.
    Sortie : rien, prochain_coup_bot est modifié (et les attaques sont lancées)."""
    delai_mini, delai_maxi = difficulte_en_cours["delais"]
    for j in range(PREMIERE_TRIBU, N + 1):
        if nb_case[j] == 0:
            continue
        prochain_coup_bot[j] -= 1
        if prochain_coup_bot[j] > 0:
            continue
        prochain_coup_bot[j] = randint(delai_mini, delai_maxi)

        cible = choisirCible(j)
        if cible is None:
            continue

        if cible == 0 or cible >= PREMIERE_TRIBU:
            plancher = difficulte_en_cours["expansion"]
        else:
            plancher = difficulte_en_cours["reserve"]

        disponibles = troupes[j] - plancher * maxTroupe(j)
        if disponibles >= 1:
            lancerAttaque(j, cible, part=disponibles / troupes[j])
## Fin des bots


## Interaction du joueur (clic de souris)
def click():
    """Gère un clic gauche sur la carte : lance une attaque du joueur sur le propriétaire de la case cliquée.
    Entrée : rien. Utilise la case sous la souris, la grille, ratio_attaque et RECTANGLE_CLASSEMENT (clic ignoré sur le classement).
    Sortie : rien, une attaque est lancée si la case est conquérable et n'est pas déjà au joueur."""
    if sourisDansRectangle(*RECTANGLE_CLASSEMENT):
        return
    case = caseSousCurseur()
    if case is None:
        return

    ligne, colonne = case
    proprietaire = grille[ligne][colonne]

    if proprietaire != JOUEUR_ACTUEL and estConquerable(ligne, colonne):
        lancerAttaque(JOUEUR_ACTUEL, proprietaire, ratio_attaque)
## Fin de l'interaction du joueur


## Lancement d'une partie
def territoireDepart(ligne_du_centre, colonne_du_centre, rayon):
    """Génère les cases d'un disque autour d'un centre (sans sortir de la carte).
    Entrée : la ligne et la colonne du centre, le rayon. Utilise LIGNES et COLLONNES.
    Sortie : les cases du disque, une par une, chacune sous la forme (ligne, colonne) (générateur)."""
    for ligne in range(max(0, ligne_du_centre - rayon), min(LIGNES, ligne_du_centre + rayon + 1)):
        for colonne in range(max(0, colonne_du_centre - rayon), min(COLLONNES, colonne_du_centre + rayon + 1)):
            if (ligne - ligne_du_centre) ** 2 + (colonne - colonne_du_centre) ** 2 <= rayon ** 2:
                yield ligne, colonne


def choisirPositionDepart(entites, generateur_aleatoire):
    """Place chaque entité sur de l'herbe, assez loin des autres (la distance exigée diminue si c'est trop dur).
    Entrée : la liste des entités à placer, le générateur aléatoire. Utilise terrain, RAYON_DE_DEPART et ESPACEMENT_RELATIF.
    Sortie : la liste des centres de départ, un par entité, chacun sous la forme (ligne, colonne)."""
    cases_d_herbe = [(ligne, colonne) for ligne in range(LIGNES) for colonne in range(COLLONNES)
                     if terrain[ligne][colonne] == 0]
    if not cases_d_herbe:
        raise ValueError("aucune case d'herbe pour placer les entités")
    cases_conquerables = sum(1 for ligne in range(LIGNES) for colonne in range(COLLONNES)
                             if estConquerable(ligne, colonne))
    distance_minimale = ESPACEMENT_RELATIF * (cases_conquerables / len(entites)) ** 0.5

    centres = []
    echecs_de_suite = 0
    while len(centres) < len(entites):
        ligne, colonne = generateur_aleatoire.choice(cases_d_herbe)
        assez_loin_des_autres = all(
            (ligne - autre_ligne) ** 2 + (colonne - autre_colonne) ** 2 >= distance_minimale ** 2
            for autre_ligne, autre_colonne in centres)
        cases_du_disque_sur_la_terre = [case for case in territoireDepart(ligne, colonne, RAYON_DE_DEPART)
                                        if estConquerable(case[0], case[1])]
        disque_assez_plein = len(cases_du_disque_sur_la_terre) >= 0.8 * 3 * RAYON_DE_DEPART ** 2
        if assez_loin_des_autres and disque_assez_plein:
            centres.append((ligne, colonne))
            echecs_de_suite = 0
        else:
            echecs_de_suite += 1
            if echecs_de_suite > 3000:         # trop dur : on relâche la contrainte de distance
                distance_minimale *= 0.9
                echecs_de_suite = 0

    return centres


def placerLesEntites(entites, generateur_aleatoire):
    """Donne à chaque entité son territoire de départ (un disque) sur la grille des propriétaires.
    Entrée : la liste des entités, le générateur aléatoire. Utilise grille et RAYON_DE_DEPART.
    Sortie : la liste des centres de départ, dans l'ordre des entités (ligne, colonne) ; la grille est modifiée."""
    positions = choisirPositionDepart(entites, generateur_aleatoire)
    for entite, (ligne_du_centre, colonne_du_centre) in zip(entites, positions):
        for ligne, colonne in territoireDepart(ligne_du_centre, colonne_du_centre, RAYON_DE_DEPART):
            if estConquerable(ligne, colonne) and grille[ligne][colonne] == 0:
                grille[ligne][colonne] = entite
    return positions


def lancerPartie(reglages):
    """Prépare une nouvelle partie : génère la carte, place le joueur et les tribus, remet à zéro l'état du jeu et centre la caméra sur le joueur.
    Entrée : le dictionnaire de réglages de la partie (graine, tribus, troupes de départ, difficulté, paramètres de carte).
    Utilise LIGNES, COLLONNES, DIFFICULTES et toutes les variables d'état du jeu.
    Sortie : rien, l'état du jeu, la grille, le terrain et l'image de la carte sont modifiés."""
    global terrain, grille, attaques, nb_case, frontiere, troupes, prochain_coup_bot, difficulte_en_cours, total_cases_conquerables, \
        resultat_de_la_partie, message_de_fin, part_maximale_de_territoire, adversaires_au_depart, numero_d_etape
    resultat_de_la_partie = None
    message_de_fin = ""
    part_maximale_de_territoire = 0.0
    numero_d_etape = 0                  # le compteur d'étapes sert à mesurer la durée

    graine = reglages["graine"] if reglages["graine"] is not None else randrange(10 ** 9)
    terrain = genererTerrain(LIGNES, COLLONNES, graine, reglages)
    total_cases_conquerables = sum(1 for ligne in terrain for code in ligne if code in TERRAINS_CONQUERABLE)
    grille = [[0] * COLLONNES for _ in range(LIGNES)]

    nombre_de_tribus = borner(reglages["nombre_de_tribus"], 0, N - PREMIERE_TRIBU + 1)
    tribus = list(range(PREMIERE_TRIBU, PREMIERE_TRIBU + nombre_de_tribus))
    centres = placerLesEntites([JOUEUR_ACTUEL] + tribus, Random(reglages["graine"]))

    adversaires_au_depart = nombre_de_tribus

    difficulte_en_cours = DIFFICULTES[reglages["difficulte"]]

    attaques = []
    nb_case = {j: 0 for j in range(N + 1)}
    frontiere = {j: set() for j in range(1, N + 1)}
    troupes_de_depart = reglages["troupes_de_depart"]
    troupes = {j: troupes_de_depart for j in range(1, N + 1)}
    for j in range(PREMIERE_TRIBU, N + 1):
        troupes[j] = int(troupes_de_depart * 0.4)
    prochain_coup_bot = {j: randint(10, 50) for j in range(PREMIERE_TRIBU, N + 1)}

    initFrontiere()
    compteCase()
    reddessinerTout()

    ligne_du_joueur, colonne_du_joueur = centres[0]
    centrerSurCase(ligne_du_joueur, colonne_du_joueur, 8)
## Fin du lancement d'une partie


## Outils d'interface (polices, texte, souris, boutons)
CHEMINS_DE_POLICE = [
    "police.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
TAILLES_DE_POLICE = {"titre": 72, "titre_moyen": 44, "bouton": 28, "legende": 18, "petit": 16}


def chargerPolice(taille):
    """Charge la première police trouvée dans la liste des chemins possibles.
    Entrée : la taille de la police. Utilise CHEMINS_DE_POLICE.
    Sortie : la police Pyxel, ou None si aucun fichier de police n'existe."""
    for chemin in CHEMINS_DE_POLICE:
        if os.path.exists(chemin):
            return pyxel.Font(chemin, taille)
    return None


POLICES = {nom: chargerPolice(taille) for nom, taille in TAILLES_DE_POLICE.items()}


def largeurDuTexte(texte, nom_police):
    """Calcule la largeur d'un texte à l'écran.
    Entrée : le texte, le nom de la police. Utilise POLICES.
    Sortie : la largeur en pixels (entier), estimée si la police n'existe pas."""
    police = POLICES[nom_police]
    return police.text_width(texte) if police else 4 * len(texte)


def ecrire(texte, x, y, nom_couleur, nom_police):
    """Écrit un texte à l'écran, son coin haut gauche en (x, y).
    Entrée : le texte, la position x et y, le nom de la couleur, le nom de la police. Utilise COULEUR et POLICES.
    Sortie : rien, le texte est dessiné."""
    pyxel.text(x, y, texte, COULEUR[nom_couleur], POLICES[nom_police])


def ecrireCentre(texte, centre_x, y, nom_couleur, nom_police):
    """Écrit un texte centré horizontalement autour d'une position.
    Entrée : le texte, le x du centre, le y, le nom de la couleur, le nom de la police.
    Sortie : rien, le texte est dessiné."""
    ecrire(texte, centre_x - largeurDuTexte(texte, nom_police) // 2, y, nom_couleur, nom_police)


def ecrireADroite(texte, droite_x, y, nom_couleur, nom_police):
    """Écrit un texte aligné sur son bord droit.
    Entrée : le texte, le x du bord droit, le y, le nom de la couleur, le nom de la police.
    Sortie : rien, le texte est dessiné."""
    ecrire(texte, droite_x - largeurDuTexte(texte, nom_police), y, nom_couleur, nom_police)


def sourisDansRectangle(x, y, largeur, hauteur):
    """Dit si la souris est dans un rectangle.
    Entrée : le x, le y, la largeur et la hauteur du rectangle. Utilise la position de la souris.
    Sortie : True si la souris est dedans, False sinon."""
    return x <= pyxel.mouse_x < x + largeur and y <= pyxel.mouse_y < y + hauteur


def boutonClique(x, y, largeur, hauteur):
    """Dit si on vient de cliquer (clic gauche) dans un rectangle.
    Entrée : le x, le y, la largeur et la hauteur du rectangle.
    Sortie : True si le clic vient d'avoir lieu dedans, False sinon."""
    return pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and sourisDansRectangle(x, y, largeur, hauteur)


def dessinerBouton(x, y, largeur, hauteur, texte, legende=None, principal=False):
    """Dessine un bouton (plus clair quand la souris le survole), avec un texte et éventuellement une légende en dessous.
    Entrée : le x, le y, la largeur, la hauteur, le texte, une légende (facultative), si c'est le bouton principal (mis en avant).
    Utilise COULEUR et TAILLES_DE_POLICE.
    Sortie : rien, le bouton est dessiné."""
    survole = sourisDansRectangle(x, y, largeur, hauteur)
    if principal:
        couleur_fond = "bouton_principal_survole" if survole else "bouton_principal"
        couleur_texte = "texte_sur_principal"
    else:
        couleur_fond = "bouton_survole" if survole else "bouton"
        couleur_texte = "texte"

    pyxel.rect(x, y, largeur, hauteur, COULEUR[couleur_fond])
    pyxel.rectb(x, y, largeur, hauteur, COULEUR["bordure"])
    if survole and not principal:
        pyxel.rect(x, y, 6, hauteur, COULEUR["bouton_principal"])      # barre d'accent à gauche

    taille_texte = TAILLES_DE_POLICE["bouton"]
    centre_x = x + largeur // 2
    if legende:
        ecrireCentre(texte, centre_x, y + 10, couleur_texte, "bouton")
        couleur_legende = couleur_texte if (principal or survole) else "texte_discret"
        ecrireCentre(legende, centre_x, y + 10 + taille_texte + 8, couleur_legende, "legende")
    else:
        ecrireCentre(texte, centre_x, y + (hauteur - taille_texte) // 2 - 2, couleur_texte, "bouton")


def dessinerEnTete(titre, sous_titre):
    """Dessine le grand titre d'un écran, avec un trait et un sous-titre en dessous.
    Entrée : le titre, le sous-titre. Utilise LARGEUR_ECRAN.
    Sortie : rien, l'en-tête est dessiné."""
    centre_x = LARGEUR_ECRAN // 2
    ecrireCentre(titre, centre_x, 130, "texte", "titre")
    pyxel.rect(centre_x - 90, 225, 180, 4, COULEUR["bouton_principal"])
    ecrireCentre(sous_titre, centre_x, 245, "texte_discret", "bouton")
## Fin des outils d'interface


## Interface en jeu (barre du bas, curseur d'attaque, classement)
BARRE_Y = HAUTEUR_ECRAN - HAUTEUR_BARRE

TROUPES_X, TROUPES_LARGEUR = 24, 380
RECTANGLE_CURSEUR_ATTAQUE = (470, BARRE_Y + 70, 300, 10)
CLASSEMENT_LARGEUR, CLASSEMENT_HAUTEUR_LIGNE = 260, 28
NOMBRE_DE_LIGNES_DU_CLASSEMENT = 5
RECTANGLE_CLASSEMENT = (LARGEUR_ECRAN - CLASSEMENT_LARGEUR - 12, 12, CLASSEMENT_LARGEUR,
                        44 + (NOMBRE_DE_LIGNES_DU_CLASSEMENT + 1) * CLASSEMENT_HAUTEUR_LIGNE)

ratio_attaque = 0.2
curseur_attaque_saisi = False


def nomDeLEntite(entite):
    """Donne le nom affiché d'une entité.
    Entrée : le numéro de l'entité. Utilise JOUEUR_ACTUEL, PREMIERE_TRIBU et JOUEURS.
    Sortie : son nom, par exemple "Toi", "Nation 2" ou "Tribu 3" (texte)."""
    if entite == JOUEUR_ACTUEL:
        return "Toi"
    if entite >= PREMIERE_TRIBU:
        return f"Tribu {entite - PREMIERE_TRIBU + 1}"
    if entite > len(JOUEURS):
        return f"Nation {entite - len(JOUEURS)}"
    return f"Joueur {entite}"


def formaterTroupes(valeur):
    """Met un nombre de troupes en forme pour l'affichage (divisé par 10, avec des espaces entre les milliers).
    Entrée : le nombre de troupes.
    Sortie : le nombre formaté, par exemple "25 000" (texte)."""
    return f"{int(valeur / 10):,}".replace(",", " ")


def formaterPourcentage(valeur):
    """Met un pourcentage en forme pour l'affichage (une décimale, virgule française).
    Entrée : le pourcentage (nombre).
    Sortie : le pourcentage formaté, par exemple "12,5 %" (texte)."""
    return f"{valeur:.1f} %".replace(".", ",")


def pourcentageDeTerritoire(entite):
    """Calcule la part des terres conquérables que possède une entité.
    Entrée : le numéro de l'entité. Utilise nb_case et total_cases_conquerables.
    Sortie : le pourcentage de territoire (nombre décimal)."""
    return 100 * nb_case[entite] / total_cases_conquerables


def classementDesEntites():
    """Classe les entités encore en vie, de la plus grande à la plus petite.
    Entrée : rien. Utilise nb_case.
    Sortie : la liste des numéros d'entités, la première étant celle qui a le plus de cases."""
    entites_en_vie = [entite for entite in range(1, N + 1) if nb_case[entite] > 0]
    entites_en_vie.sort(key=lambda entite: nb_case[entite], reverse=True)
    return entites_en_vie


def dessinerBarreDeProgression(x, y, largeur, hauteur, part, nom_couleur):
    """Dessine une barre de progression remplie selon une part.
    Entrée : le x, le y, la largeur, la hauteur, la part remplie (entre 0 et 1), le nom de la couleur de remplissage.
    Sortie : rien, la barre est dessinée."""
    pyxel.rect(x, y, largeur, hauteur, COULEUR["fond"])
    pyxel.rect(x, y, int(largeur * borner(part, 0, 1)), hauteur, COULEUR[nom_couleur])
    pyxel.rectb(x, y, largeur, hauteur, COULEUR["bordure"])


def mettreAJourCurseurAttaque():
    """Gère le curseur qui règle la part de troupes envoyée à chaque attaque (glisser avec la souris).
    Entrée : rien. Utilise la souris et RECTANGLE_CURSEUR_ATTAQUE.
    Sortie : rien, ratio_attaque et curseur_attaque_saisi sont modifiés."""
    global ratio_attaque, curseur_attaque_saisi
    x, y, largeur, hauteur = RECTANGLE_CURSEUR_ATTAQUE
    if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and sourisDansRectangle(x - 12, y - 18, largeur + 24, hauteur + 36):
        curseur_attaque_saisi = True
    if not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
        curseur_attaque_saisi = False
    if curseur_attaque_saisi:
        ratio_attaque = borner(round((pyxel.mouse_x - x) / largeur, 2), 0.01, 1.0)


def dessinerBarreDeJeu():
    """Dessine la barre du bas : troupes du joueur, curseur d'attaque, territoire et rang.
    Entrée : rien. Utilise troupes, ratio_attaque, le classement et les positions de la barre.
    Sortie : rien, la barre est dessinée."""
    pyxel.rect(0, BARRE_Y, LARGEUR_ECRAN, HAUTEUR_BARRE, COULEUR["panneau"])
    pyxel.line(0, BARRE_Y, LARGEUR_ECRAN, BARRE_Y, COULEUR["bordure"])


    # --- troupes
    troupes_actuelles = troupes[JOUEUR_ACTUEL]
    troupes_maximales = maxTroupe(JOUEUR_ACTUEL)
    ecrire("Troupes", TROUPES_X, BARRE_Y + 8, "texte_discret", "legende")
    ecrire(f"{formaterTroupes(troupes_actuelles)} / {formaterTroupes(troupes_maximales)}",
           TROUPES_X, BARRE_Y + 28, "texte", "bouton")
    dessinerBarreDeProgression(TROUPES_X, BARRE_Y + 70, TROUPES_LARGEUR, 12,
                               troupes_actuelles / troupes_maximales, "bouton_principal")

    # --- curseur d'attaque
    x, y, largeur, hauteur = RECTANGLE_CURSEUR_ATTAQUE
    troupes_envoyees = formaterTroupes(troupes_actuelles * ratio_attaque)
    ecrire("Envoi par attaque", x, BARRE_Y + 8, "texte_discret", "legende")
    ecrire(f"{round(ratio_attaque * 100)} %", x, BARRE_Y + 28, "texte", "bouton")
    ecrireADroite(f"≈ {troupes_envoyees} troupes", x + largeur, BARRE_Y + 34, "texte_discret", "legende")
    pyxel.rect(x, y, largeur, hauteur, COULEUR["fond"])
    pyxel.rect(x, y, int(largeur * ratio_attaque), hauteur, COULEUR["bouton_survole"])
    pyxel.rectb(x, y, largeur, hauteur, COULEUR["bordure"])
    poignee_x = x + int(largeur * ratio_attaque)
    couleur_poignee = "bouton_principal_survole" if curseur_attaque_saisi else "bouton_principal"
    pyxel.rect(poignee_x - 5, y - 8, 10, hauteur + 16, COULEUR[couleur_poignee])

    # --- territoire et rang
    classement = classementDesEntites()
    droite_x = LARGEUR_ECRAN - 24
    ecrireADroite("Territoire", droite_x, BARRE_Y + 8, "texte_discret", "legende")
    ecrireADroite(formaterPourcentage(pourcentageDeTerritoire(JOUEUR_ACTUEL)), droite_x, BARRE_Y + 28, "texte", "bouton")
    if JOUEUR_ACTUEL in classement:
        rang = classement.index(JOUEUR_ACTUEL) + 1
        ecrireADroite(f"Rang {rang} sur {len(classement)}", droite_x, BARRE_Y + 68, "texte_discret", "petit")


def dessinerClassement():
    """Dessine le classement des meilleures entités en haut à droite (le joueur y figure toujours, même hors du top).
    Entrée : rien. Utilise le classement, nb_case et RECTANGLE_CLASSEMENT.
    Sortie : rien, le classement est dessiné."""
    x, y, largeur, hauteur = RECTANGLE_CLASSEMENT
    classement = classementDesEntites()
    lignes_a_afficher = classement[:NOMBRE_DE_LIGNES_DU_CLASSEMENT]
    if JOUEUR_ACTUEL in classement and JOUEUR_ACTUEL not in lignes_a_afficher:
        lignes_a_afficher.append(JOUEUR_ACTUEL)                 # toi, même hors du top 5

    hauteur_utilisee = 44 + len(lignes_a_afficher) * CLASSEMENT_HAUTEUR_LIGNE
    pyxel.rect(x, y, largeur, hauteur_utilisee, COULEUR["panneau"])
    pyxel.rectb(x, y, largeur, hauteur_utilisee, COULEUR["bordure"])
    ecrire("Classement", x + 14, y + 10, "texte_discret", "legende")

    for numero, entite in enumerate(lignes_a_afficher):
        ligne_y = y + 38 + numero * CLASSEMENT_HAUTEUR_LIGNE
        if entite == JOUEUR_ACTUEL:
            pyxel.rect(x + 4, ligne_y - 3, largeur - 8, CLASSEMENT_HAUTEUR_LIGNE - 2, COULEUR["bouton"])
        rang = classement.index(entite) + 1
        ecrire(str(rang), x + 14, ligne_y, "texte_discret", "petit")
        pyxel.rect(x + 40, ligne_y + 1, 14, 14, ID_COULEUR_ENTITES[entite]["remplissage"])
        ecrire(nomDeLEntite(entite), x + 64, ligne_y, "texte", "petit")
        ecrireADroite(formaterPourcentage(pourcentageDeTerritoire(entite)), x + largeur - 14, ligne_y, "texte", "petit")


def dessinerInterfaceDeJeu():
    """Dessine toute l'interface par-dessus la carte : la barre du bas et le classement.
    Entrée : rien.
    Sortie : rien, l'interface est dessinée."""
    dessinerBarreDeJeu()
    dessinerClassement()
## Fin de l'interface en jeu


## Interface des menus (menu, réglages, aperçu de la carte)
BOUTON_LARGEUR, BOUTON_HAUTEUR = 420, 84
BOUTON_X = LARGEUR_ECRAN // 2 - BOUTON_LARGEUR // 2
ESPACE_ENTRE_BOUTONS = 20
BOUTON_PARTIE_RAPIDE_Y = 330
BOUTON_PARTIE_PERSONNALISEE_Y = BOUTON_PARTIE_RAPIDE_Y + BOUTON_HAUTEUR + ESPACE_ENTRE_BOUTONS
BOUTON_QUITTER_Y = BOUTON_PARTIE_PERSONNALISEE_Y + BOUTON_HAUTEUR + ESPACE_ENTRE_BOUTONS
BOUTON_QUITTER_HAUTEUR = 56

CONSEILS_DE_JEU = "Molette : zoom     Clic droit : déplacer     C : vue d'ensemble     Échap : quitter"

POIDS_D_OCTAVE = [0.0, 0.125, 0.25, 0.5, 0.75, 1.0]
OPTIONS_PAR_ONGLET = {
    "Partie": [
        ("Tribus", "nombre_de_tribus", list(range(0, 11))),
        ("Troupes de départ", "troupes_de_depart", [10000, 25000, 50000, 100000]),
        ("Difficulté des tribus", "difficulte", ["Facile", "Normale", "Difficile"]),
    ],
    "Carte": [
        ("Grandes formes (64)", "poids_octave_64", POIDS_D_OCTAVE),
        ("Formes moyennes (32)", "poids_octave_32", POIDS_D_OCTAVE),
        ("Petites formes (16)", "poids_octave_16", POIDS_D_OCTAVE),
        ("Détails (8)", "poids_octave_8", POIDS_D_OCTAVE),
        ("Force de l'île", "force_ile", [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]),
        ("Niveau de la mer", "niveau_mer", [0.2, 0.25, 0.3, 0.35, 0.4, 0.45]),
        ("Limite herbe", "limite_herbe", [0.46, 0.51, 0.56, 0.61, 0.66]),
        ("Limite terre", "limite_terre", [0.60, 0.65, 0.70, 0.75, 0.80]),
        ("Carte n°", "graine", [None] + list(range(1, 13))),
    ],
}
ONGLETS = ["Partie", "Carte"]
onglet_actuel = "Partie"

LISTE_X, LISTE_LARGEUR, LISTE_Y = 60, 660, 130
LIGNE_HAUTEUR = 58
FLECHE_TAILLE, VALEUR_LARGEUR = 46, 180
SELECTEUR_X = LISTE_X + LISTE_LARGEUR - (2 * FLECHE_TAILLE + VALEUR_LARGEUR)

ONGLET_LARGEUR, ONGLET_HAUTEUR, ONGLET_Y = 150, 48, 22
ONGLET_PREMIER_X = 560
APERCU_TAILLE, APERCU_ECHELLE = 125, 3
APERCU_X, APERCU_Y = 790, 130
BOUTON_NOUVEL_APERCU = (APERCU_X, APERCU_Y + APERCU_TAILLE * APERCU_ECHELLE + 20, APERCU_TAILLE * APERCU_ECHELLE, 56)
BOUTON_RETOUR = (60, 720, 220, 56)
BOUTON_LANCER = (LARGEUR_ECRAN - 60 - 380, 720, 380, 56)

image_apercu = pyxel.Image(APERCU_TAILLE, APERCU_TAILLE)
graine_apercu_aleatoire = randrange(10 ** 9)
apercu_a_refaire = True


def graineDeLApercu():
    """Donne la graine à utiliser pour l'aperçu de la carte (celle choisie dans les réglages, sinon une graine aléatoire).
    Entrée : rien. Utilise reglages_en_cours et graine_apercu_aleatoire.
    Sortie : la graine (entier)."""
    graine_choisie = reglages_en_cours["graine"]
    return graine_choisie if graine_choisie is not None else graine_apercu_aleatoire


def actualiserApercu():
    """Régénère l'aperçu réduit de la carte à partir des réglages en cours.
    Entrée : rien. Utilise reglages_en_cours, APERCU_TAILLE et image_apercu.
    Sortie : rien, image_apercu est modifiée et apercu_a_refaire repasse à False."""
    global apercu_a_refaire
    terrain_apercu = genererTerrain(APERCU_TAILLE, APERCU_TAILLE, graineDeLApercu(), reglages_en_cours)
    for ligne in range(APERCU_TAILLE):
        for colonne in range(APERCU_TAILLE):
            image_apercu.pset(colonne, ligne, terrain_apercu[ligne][colonne])   # 0 à 3 = les 4 couleurs de terrain
    apercu_a_refaire = False


def ligneY(numero_de_ligne):
    """Calcule la position verticale d'une ligne de la liste des réglages.
    Entrée : le numéro de la ligne. Utilise LISTE_Y et LIGNE_HAUTEUR.
    Sortie : le y de la ligne en pixels (entier)."""
    return LISTE_Y + numero_de_ligne * LIGNE_HAUTEUR


def rectanglesDuSelecteur(numero_de_ligne):
    """Calcule les rectangles des deux flèches (gauche et droite) d'une ligne de réglage.
    Entrée : le numéro de la ligne. Utilise SELECTEUR_X, FLECHE_TAILLE et VALEUR_LARGEUR.
    Sortie : deux rectangles (x, y, largeur, hauteur) : la flèche gauche, puis la flèche droite."""
    y = ligneY(numero_de_ligne)
    fleche_gauche = (SELECTEUR_X, y, FLECHE_TAILLE, FLECHE_TAILLE)
    fleche_droite = (SELECTEUR_X + FLECHE_TAILLE + VALEUR_LARGEUR, y, FLECHE_TAILLE, FLECHE_TAILLE)
    return fleche_gauche, fleche_droite


def rectangleDeLOnglet(numero_d_onglet):
    """Calcule le rectangle d'un onglet des réglages.
    Entrée : le numéro de l'onglet. Utilise les constantes ONGLET_*.
    Sortie : un rectangle (x, y, largeur, hauteur)."""
    return (ONGLET_PREMIER_X + numero_d_onglet * (ONGLET_LARGEUR + 10), ONGLET_Y, ONGLET_LARGEUR, ONGLET_HAUTEUR)


def texteDeLaValeur(cle, valeur):
    """Met la valeur d'un réglage en forme pour l'affichage.
    Entrée : la clé du réglage, sa valeur.
    Sortie : le texte à afficher ("Aléatoire" si pas de valeur, troupes divisées par 10 avec espaces, sinon la valeur simple)."""
    if valeur is None:
        return "Aléatoire"
    if cle == "troupes_de_depart":
        return f"{valeur // 10:,}".replace(",", " ")
    if isinstance(valeur, float):
        return f"{valeur:g}"
    return str(valeur)
## Fin de l'interface des menus


## Écrans (menu, réglages, fin de partie)
ecran_actuel = "menu"
reglages_en_cours = dict(REGLAGES_PAR_DEFAUT)

PANNEAU_FIN_X, PANNEAU_FIN_Y, PANNEAU_FIN_LARGEUR, PANNEAU_FIN_HAUTEUR = 300, 130, 600, 560
BOUTON_REJOUER = (LARGEUR_ECRAN // 2 - 240, 590, 230, 60)
BOUTON_RETOUR_AU_MENU = (LARGEUR_ECRAN // 2 + 10, 590, 230, 60)


def updateMenu():
    """Gère les clics du menu principal : partie rapide, partie personnalisée, quitter.
    Entrée : rien. Utilise la souris et les rectangles des boutons.
    Sortie : rien, peut lancer une partie, changer d'écran ou fermer le jeu."""
    global ecran_actuel
    if boutonClique(BOUTON_X, BOUTON_PARTIE_RAPIDE_Y, BOUTON_LARGEUR, BOUTON_HAUTEUR):
        commencerPartie({**REGLAGES_PAR_DEFAUT, "graine": None})
    if boutonClique(BOUTON_X, BOUTON_PARTIE_PERSONNALISEE_Y, BOUTON_LARGEUR, BOUTON_HAUTEUR):
        ecran_actuel = "reglages"
    if boutonClique(BOUTON_X, BOUTON_QUITTER_Y, BOUTON_LARGEUR, BOUTON_QUITTER_HAUTEUR):
        pyxel.quit()


def drawMenu():
    """Dessine le menu principal : titre, boutons et conseils de jeu.
    Entrée : rien. Utilise les positions des boutons et CONSEILS_DE_JEU.
    Sortie : rien, l'écran est dessiné."""
    pyxel.cls(COULEUR["fond"])
    dessinerEnTete("OPENFRONT", "Conquiers le territoire")

    panneau_x, panneau_y = BOUTON_X - 30, BOUTON_PARTIE_RAPIDE_Y - 30
    panneau_largeur = BOUTON_LARGEUR + 60
    panneau_hauteur = (BOUTON_QUITTER_Y + BOUTON_QUITTER_HAUTEUR + 30) - panneau_y
    pyxel.rect(panneau_x, panneau_y, panneau_largeur, panneau_hauteur, COULEUR["panneau"])
    pyxel.rectb(panneau_x, panneau_y, panneau_largeur, panneau_hauteur, COULEUR["bordure"])

    dessinerBouton(BOUTON_X, BOUTON_PARTIE_RAPIDE_Y, BOUTON_LARGEUR, BOUTON_HAUTEUR,
                   "Partie rapide", "Carte aléatoire, c'est parti", principal=True)
    dessinerBouton(BOUTON_X, BOUTON_PARTIE_PERSONNALISEE_Y, BOUTON_LARGEUR, BOUTON_HAUTEUR,
                   "Partie personnalisée", "Bots, troupes, carte")
    dessinerBouton(BOUTON_X, BOUTON_QUITTER_Y, BOUTON_LARGEUR, BOUTON_QUITTER_HAUTEUR, "Quitter")

    pyxel.line(80, HAUTEUR_ECRAN - 70, LARGEUR_ECRAN - 80, HAUTEUR_ECRAN - 70, COULEUR["bordure"])
    ecrireCentre(CONSEILS_DE_JEU, LARGEUR_ECRAN // 2, HAUTEUR_ECRAN - 52, "texte_discret", "petit")
    ecrire("v0.1", 16, HAUTEUR_ECRAN - 28, "texte_discret", "petit")


def updateReglages():
    """Gère les clics de l'écran de réglages : onglets, flèches de chaque réglage, nouvel aperçu, retour, lancement de la partie.
    Entrée : rien. Utilise la souris, reglages_en_cours, OPTIONS_PAR_ONGLET et onglet_actuel.
    Sortie : rien, les réglages, l'onglet et l'aperçu sont modifiés (ou on change d'écran / on lance la partie)."""
    global ecran_actuel, onglet_actuel, graine_apercu_aleatoire, apercu_a_refaire

    for numero, nom_onglet in enumerate(ONGLETS):
        if boutonClique(*rectangleDeLOnglet(numero)):
            onglet_actuel = nom_onglet

    for numero, (libelle, cle, options) in enumerate(OPTIONS_PAR_ONGLET[onglet_actuel]):
        fleche_gauche, fleche_droite = rectanglesDuSelecteur(numero)
        position = options.index(reglages_en_cours[cle])
        nouvelle_position = position
        if boutonClique(*fleche_gauche):
            nouvelle_position = max(0, position - 1)
        if boutonClique(*fleche_droite):
            nouvelle_position = min(len(options) - 1, position + 1)
        if nouvelle_position != position:
            reglages_en_cours[cle] = options[nouvelle_position]
            apercu_a_refaire = True

    if boutonClique(*BOUTON_NOUVEL_APERCU):
        graine_apercu_aleatoire = randrange(10 ** 9)
        apercu_a_refaire = True
    if boutonClique(*BOUTON_RETOUR):
        ecran_actuel = "menu"
        return
    if boutonClique(*BOUTON_LANCER):
        commencerPartie({**reglages_en_cours, "graine": graineDeLApercu()})
        return
    if apercu_a_refaire:
        actualiserApercu()


def drawReglages():
    """Dessine l'écran de réglages : onglets, liste des réglages avec leurs flèches, aperçu de la carte et boutons du bas.
    Entrée : rien. Utilise reglages_en_cours, onglet_actuel, OPTIONS_PAR_ONGLET et image_apercu.
    Sortie : rien, l'écran est dessiné."""
    pyxel.cls(COULEUR["fond"])
    ecrire("RÉGLAGES", 60, 18, "texte", "titre_moyen")
    for numero, nom_onglet in enumerate(ONGLETS):
        dessinerBouton(*rectangleDeLOnglet(numero), nom_onglet, principal=(nom_onglet == onglet_actuel))
    pyxel.line(40, 90, LARGEUR_ECRAN - 40, 90, COULEUR["bordure"])

    options_de_l_onglet = OPTIONS_PAR_ONGLET[onglet_actuel]
    panneau_hauteur = len(options_de_l_onglet) * LIGNE_HAUTEUR + 8
    pyxel.rect(LISTE_X - 20, LISTE_Y - 14, LISTE_LARGEUR + 40, panneau_hauteur, COULEUR["panneau"])
    pyxel.rectb(LISTE_X - 20, LISTE_Y - 14, LISTE_LARGEUR + 40, panneau_hauteur, COULEUR["bordure"])
    decalage_texte = (FLECHE_TAILLE - TAILLES_DE_POLICE["bouton"]) // 2 - 2
    for numero, (libelle, cle, options) in enumerate(options_de_l_onglet):
        y = ligneY(numero)
        ecrire(libelle, LISTE_X, y + decalage_texte, "texte", "bouton")
        fleche_gauche, fleche_droite = rectanglesDuSelecteur(numero)
        dessinerBouton(*fleche_gauche, "<")
        dessinerBouton(*fleche_droite, ">")
        valeur_x = SELECTEUR_X + FLECHE_TAILLE
        pyxel.rect(valeur_x, y, VALEUR_LARGEUR, FLECHE_TAILLE, COULEUR["fond"])
        pyxel.rectb(valeur_x, y, VALEUR_LARGEUR, FLECHE_TAILLE, COULEUR["bordure"])
        ecrireCentre(texteDeLaValeur(cle, reglages_en_cours[cle]), valeur_x + VALEUR_LARGEUR // 2,
                     y + decalage_texte, "bouton_principal", "bouton")

    cote_apercu = APERCU_TAILLE * APERCU_ECHELLE
    pyxel.rect(APERCU_X - 6, APERCU_Y - 6, cote_apercu + 12, cote_apercu + 12, COULEUR["panneau"])
    pyxel.rectb(APERCU_X - 6, APERCU_Y - 6, cote_apercu + 12, cote_apercu + 12, COULEUR["bordure"])
    pyxel.blt(APERCU_X + APERCU_TAILLE * (APERCU_ECHELLE - 1) / 2,
              APERCU_Y + APERCU_TAILLE * (APERCU_ECHELLE - 1) / 2,
              image_apercu, 0, 0, APERCU_TAILLE, APERCU_TAILLE, scale=APERCU_ECHELLE)
    dessinerBouton(*BOUTON_NOUVEL_APERCU, "Nouvel aperçu")
    ecrire("Aperçu réduit de la vraie carte", APERCU_X, BOUTON_NOUVEL_APERCU[1] + 70, "texte_discret", "petit")

    pyxel.line(40, 700, LARGEUR_ECRAN - 40, 700, COULEUR["bordure"])
    dessinerBouton(*BOUTON_RETOUR, "Retour")
    dessinerBouton(*BOUTON_LANCER, "Lancer la partie", principal=True)


def formaterDuree(secondes):
    """Met une durée en forme pour l'affichage.
    Entrée : la durée en secondes.
    Sortie : la durée sous la forme "minutes:secondes", par exemple "03:07" (texte)."""
    secondes = int(secondes)
    return f"{secondes // 60:02d}:{secondes % 60:02d}"


def updateFin():
    """Gère les clics de l'écran de fin : rejouer avec les mêmes réglages ou retourner au menu.
    Entrée : rien. Utilise la souris et derniers_reglages.
    Sortie : rien, peut relancer une partie ou changer d'écran."""
    global ecran_actuel
    if boutonClique(*BOUTON_REJOUER):
        commencerPartie(derniers_reglages)
    if boutonClique(*BOUTON_RETOUR_AU_MENU):
        ecran_actuel = "menu"


def drawFin():
    """Dessine l'écran de fin : la partie figée en fond, puis le panneau victoire ou défaite avec les statistiques et les boutons.
    Entrée : rien. Utilise resultat_de_la_partie, message_de_fin, nb_case, numero_d_etape et part_maximale_de_territoire.
    Sortie : rien, l'écran est dessiné."""
    drawJeu()                                                   # la partie, figée, en arrière-plan
    centre_x = LARGEUR_ECRAN // 2
    pyxel.rect(PANNEAU_FIN_X, PANNEAU_FIN_Y, PANNEAU_FIN_LARGEUR, PANNEAU_FIN_HAUTEUR, COULEUR["panneau"])
    pyxel.rectb(PANNEAU_FIN_X, PANNEAU_FIN_Y, PANNEAU_FIN_LARGEUR, PANNEAU_FIN_HAUTEUR, COULEUR["bordure"])

    est_victoire = resultat_de_la_partie == "victoire"
    couleur_du_titre = "bouton_principal" if est_victoire else "rouge"
    ecrireCentre("VICTOIRE" if est_victoire else "DÉFAITE", centre_x, PANNEAU_FIN_Y + 30, couleur_du_titre, "titre")
    pyxel.rect(centre_x - 90, PANNEAU_FIN_Y + 125, 180, 4, COULEUR[couleur_du_titre])
    ecrireCentre(message_de_fin, centre_x, PANNEAU_FIN_Y + 150, "texte_discret", "legende")

    adversaires_restants = len([e for e in range(1, N + 1) if e != JOUEUR_ACTUEL and nb_case[e] > 0])
    lignes = [
        ("Durée", formaterDuree(numero_d_etape * VITESSE_ATTAQUE / IMAGES_PAR_SECONDE)),
        ("Territoire maximal", formaterPourcentage(part_maximale_de_territoire)),
        ("Territoire final", formaterPourcentage(pourcentageDeTerritoire(JOUEUR_ACTUEL))),
        ("Adversaires restants", f"{adversaires_restants} sur {adversaires_au_depart}"),
    ]
    for numero, (libelle, valeur) in enumerate(lignes):
        ligne_y = PANNEAU_FIN_Y + 215 + numero * 56
        ecrire(libelle, PANNEAU_FIN_X + 50, ligne_y, "texte_discret", "bouton")
        ecrireADroite(valeur, PANNEAU_FIN_X + PANNEAU_FIN_LARGEUR - 50, ligne_y, "texte", "bouton")
        pyxel.line(PANNEAU_FIN_X + 40, ligne_y + 40, PANNEAU_FIN_X + PANNEAU_FIN_LARGEUR - 40, ligne_y + 40, COULEUR["bordure"])

    dessinerBouton(*BOUTON_REJOUER, "Rejouer", principal=True)
    dessinerBouton(*BOUTON_RETOUR_AU_MENU, "Menu")
## Fin des écrans


## Boucle de jeu
def commencerPartie(reglages):
    """Lance une partie avec des réglages, mémorise ces réglages (pour rejouer) et passe à l'écran de jeu.
    Entrée : le dictionnaire de réglages de la partie.
    Sortie : rien, derniers_reglages et ecran_actuel sont modifiés."""
    global ecran_actuel, derniers_reglages
    derniers_reglages = dict(reglages)
    lancerPartie(reglages)
    ecran_actuel = "jeu"


def updateJeu():
    """Fait avancer le jeu d'une image : caméra, curseur d'attaque, touches (C, Échap, V), clic, puis une étape de jeu à intervalle régulier.
    Entrée : rien. Utilise le clavier, la souris, pyxel.frame_count et VITESSE_ATTAQUE.
    Sortie : rien, l'état du jeu est modifié."""
    deplacerCamera()
    mettreAJourCurseurAttaque()
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


def drawJeu():
    """Dessine la partie : la partie visible de la carte (zoomée) puis l'interface par-dessus.
    Entrée : rien. Utilise l'image carte, la caméra, le zoom et la zone de jeu.
    Sortie : rien, l'écran est dessiné (la carte est recentrée si rien n'est visible)."""
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
    dessinerInterfaceDeJeu()


def verifierFinDePartie():
    """Vérifie si la partie est terminée (défaite si plus de territoire ou si un adversaire atteint le seuil, victoire si le joueur atteint le seuil ou reste seul), et suit son territoire maximal.
    Entrée : rien. Utilise nb_case, le classement, SEUIL_DE_VICTOIRE et adversaires_au_depart.
    Sortie : rien, resultat_de_la_partie, message_de_fin et part_maximale_de_territoire sont modifiés, et on passe à l'écran de fin si la partie est finie."""
    global ecran_actuel, resultat_de_la_partie, message_de_fin, part_maximale_de_territoire
    part_maximale_de_territoire = max(part_maximale_de_territoire, pourcentageDeTerritoire(JOUEUR_ACTUEL))

    classement = classementDesEntites()
    if nb_case[JOUEUR_ACTUEL] == 0:
        resultat_de_la_partie = "defaite"
        message_de_fin = "Tu n'as plus aucun territoire."
    elif classement and pourcentageDeTerritoire(classement[0]) >= SEUIL_DE_VICTOIRE:
        if classement[0] == JOUEUR_ACTUEL:
            resultat_de_la_partie = "victoire"
            message_de_fin = f"Tu contrôles {formaterPourcentage(pourcentageDeTerritoire(JOUEUR_ACTUEL))} des terres."
        else:
            resultat_de_la_partie = "defaite"
            message_de_fin = f"{nomDeLEntite(classement[0])} contrôle {SEUIL_DE_VICTOIRE} % des terres."
    elif adversaires_au_depart > 0 and classement == [JOUEUR_ACTUEL]:
        resultat_de_la_partie = "victoire"
        message_de_fin = "Tous tes adversaires ont été éliminés."

    if resultat_de_la_partie is not None:
        ecran_actuel = "fin"
## Fin de la boucle de jeu


## Boucle globale
def update():
    """Appelle la mise à jour de l'écran actuel (menu, réglages, fin ou jeu).
    Entrée : rien. Utilise ecran_actuel.
    Sortie : rien."""
    if ecran_actuel == "menu":
        updateMenu()
    elif ecran_actuel == "reglages":
        updateReglages()
    elif ecran_actuel == "fin":
        updateFin()
    else:
        updateJeu()


def draw():
    """Appelle le dessin de l'écran actuel (menu, réglages, fin ou jeu).
    Entrée : rien. Utilise ecran_actuel.
    Sortie : rien."""
    if ecran_actuel == "menu":
        drawMenu()
    elif ecran_actuel == "reglages":
        drawReglages()
    elif ecran_actuel == "fin":
        drawFin()
    else:
        drawJeu()
## Fin de la boucle globale


pyxel.run(update, draw)

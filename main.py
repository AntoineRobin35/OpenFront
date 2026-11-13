## Imports
import pyxel
from random import randint, choice, Random, randrange
from colorsys import rgb_to_hls, hls_to_rgb
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
    """Garde une valeur entre un minimum et un maximum.
    Entrée : la valeur, le minimum, le maximum.
    Sortie : la valeur, ramenée au minimum ou au maximum si elle dépasse (nombre)."""
    return max(mini, min(maxi, valeur))


def voisins(x, y):
    """Trouve les voisins horizontaux et verticaux d'une case.
    Entrée : la ligne x et la colonne y de la case. Utilise LIGNES et COLLONNES pour rester dans la carte.
    Sortie : liste des cases voisines, chacune sous la forme (ligne, colonne)."""
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
    """Crée une grille de bruit lisse : estimer en fonction de la position de la case sa valeur en fonction des coins de la maille.
    Entrée : le nombre de lignes, le nombre de colonnes, la taille d'une maille, le générateur aléatoire à utiliser.
    Sortie : une grille (liste de listes) de nombres entre 0 et 1 qui représente la forme de la carte."""
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
    """Génère la carte : mélange plusieurs bruits lisses, abaisse les bords pour faire une île, puis transforme les valeurs en type de terrain.
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
    Sortie : ensemble de cases conquérables, chacune sous la forme (ligne, colonne)."""
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
    """Outil de débogage : recalcule toutes les frontières depuis la grille et les compare à celles stockées.
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
    """Redessine sur l'image de la carte des cases données et leurs voisines (leur frontière a pu changer).
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
    """Calcule le nombre maximum de troupes qu'une entité peut avoir (il grandit avec son territoire, et est divisé par 3 pour une tribu).
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
    met à jour les troupes, découvre les nouvelles cases à attaquer, redessine, puis termine les attaques finies
    (les troupes restantes retournent à l'attaquant).
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
    """Fait jouer les tribus : quand le délai d'un bot est écoulé, il choisit une cible et un seuil de troupes selon la difficulté.
    Entrée : rien. Utilise difficulte_en_cours, prochain_coup_bot, nb_case et PREMIERE_TRIBU.
    Sortie : rien, prochain_coup_bot est modifié (et les attaques lancées)."""
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

        # (la suite de ton fichier n'était pas dans ce que tu m'as envoyé)
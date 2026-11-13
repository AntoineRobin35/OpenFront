## Imports
import pyxel  # la bibliothèque de jeu : fenêtre, dessin, souris, clavier
from random import randint, choice, Random, randrange  # outils de hasard : entier, choix dans une liste, générateur à graine, entier dans [0, n[
from colorsys import rgb_to_hls, hls_to_rgb  # conversions de couleurs (sert à assombrir une couleur)
import os  # sert à vérifier si un fichier de police existe
## Fin des imports


## Dimensions de la carte et de l'écran
LIGNES = 500 # Nombre de lignes
COLLONNES = 500 # Nombre de colonnes
LARGEUR_ECRAN = 1200 # Taille de la largeur de l'écran
HAUTEUR_ECRAN = 800 # Taille de la hauteur de l'écran
HAUTEUR_BARRE = 96  # hauteur en pixels de la barre d'info en bas de l'écran
## Fin des dimensions de la carte et de l'écran


## Outils généraux utilisés partout
def borner(valeur, mini, maxi):
    """Garde une valeur entre deux bornes.
    Entrée : la valeur, le minimum, le maximum.
    Sortie : la valeur, ramenée au minimum ou au maximum si elle dépasse (nombre)."""
    return max(mini, min(maxi, valeur))  # min(...) empêche de dépasser le maximum, max(...) empêche de passer sous le minimum


def voisins(x, y):
    """Trouve les voisins horizontaux et verticaux d'une case.
    Entrée : la ligne x et la colonne y de la case. Utilise LIGNES et COLLONNES pour rester dans la carte.
    Sortie : la liste des cases voisines, chacune sous la forme (ligne, colonne)."""
    resultat = []  # la liste des voisins, remplie au fur et à mesure
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):  # les 4 décalages : bas, haut, droite, gauche (pas les diagonales)
        nx, ny = x + dx, y + dy  # position du voisin = position de la case + le décalage
        if 0 <= nx < LIGNES and 0 <= ny < COLLONNES:  # on ignore les voisins qui sortent de la carte
            resultat.append((nx, ny))  # voisin valide : on le garde
    return resultat
## Fin des outils généraux


## Génération du terrain (bruit lisse, mer, herbe, terre, montagne)
# (taille d'une maille pour une carte de 500 cases, poids dans le mélange)
TAILLES_DES_OCTAVES = [64, 32, 16, 8]  # tailles de mailles : grosses = grandes formes, petites = détails
PARAMETRES_CARTE_PAR_DEFAUT = {
    "poids_octave_64": 1.0, "poids_octave_32": 0.5, "poids_octave_16": 0.25, "poids_octave_8": 0.125,  # importance de chaque taille de forme dans la carte finale
    "force_ile": 0.2, "niveau_mer": 0.30, "limite_herbe": 0.56, "limite_terre": 0.70,  # force_ile : plus c'est grand, plus les bords sont de l'eau ; les 3 autres sont des seuils d'altitude
}

TERRAINS_CONQUERABLE = (0, 1, 2)  # herbe, terre, montagne : tout sauf la mer (3)

terrain = []  # grille du type de terrain de chaque case (0 herbe, 1 terre, 2 montagne, 3 mer), remplie au lancement d'une partie


def genererBruitLisse(nombre_ligne, nombre_colonnes, taille_maille, generateur_aleatoire):
    """Crée une grille de bruit lisse : des valeurs aléatoires placées aux coins de grosses mailles, adoucies entre elles.
    Entrée : le nombre de lignes, le nombre de colonnes, la taille d'une maille, le générateur aléatoire à utiliser.
    Sortie : une grille (liste de listes) de nombres entre 0 et 1."""
    nbr_maille_hauteur = nombre_ligne // taille_maille + 2  # nombre de rangées de coins nécessaires ; le +2 assure un coin de plus en bas
    nbr_maille_largeur = nombre_colonnes // taille_maille + 2  # pareil en largeur, un coin de plus à droite

    valeur_aux_coins= [[generateur_aleatoire.random() for _ in range(nbr_maille_largeur)]  # une valeur aléatoire entre 0 et 1 pour chaque coin de maille
                        for _ in range(nbr_maille_hauteur)]  # on répète pour chaque rangée de coins

    progression_lisse = []  # pour chaque position dans une maille, le "poids" lissé (entre 0 et 1) à utiliser
    for decalage_dans_la_maille in range(taille_maille):  # on passe en revue chaque position possible dans une maille
        avancement = decalage_dans_la_maille / taille_maille  # avancement linéaire : 0 au bord de la maille, presque 1 à l'autre bord
        progression_lisse.append(avancement * avancement * (3 - 2 * avancement))  # courbe en S : la transition entre deux coins est douce, sans angle visible

    bruit = []  # la grille finale, ligne par ligne
    for ligne in range(nombre_ligne):  # on calcule la valeur de chaque case de la carte
        numero_maille_ligne = ligne // taille_maille  # dans quelle rangée de mailles se trouve cette ligne
        progression_vertical_local = progression_lisse[ligne % taille_maille]  # où on est dans la maille verticalement (0 = en haut, vers 1 = en bas), lissé
        coins_du_haut_gauche = valeur_aux_coins[numero_maille_ligne]  # en fait : toute la rangée de coins du haut de la maille
        coins_du_bas_gauche = valeur_aux_coins[numero_maille_ligne + 1]  # et toute la rangée de coins du bas de la maille
        valeur_final_ligne = []  # les valeurs de cette ligne
        for colonnes in range(nombre_colonnes):  # pour chaque case de la ligne
            numero_maille_colonnes = colonnes // taille_maille  # dans quelle colonne de mailles on est
            progression_horizontale_locale = progression_lisse[colonnes % taille_maille]  # où on est dans la maille horizontalement, lissé
            valeur_en_haut = (coins_du_haut_gauche[numero_maille_colonnes] * (1 - progression_horizontale_locale)  # le coin haut-gauche compte beaucoup si on est près de lui...
                             + coins_du_haut_gauche[numero_maille_colonnes + 1] * progression_horizontale_locale)  # ...le coin haut-droit compte beaucoup si on s'en approche
            valeur_en_bas = (coins_du_bas_gauche[numero_maille_colonnes] * (1 - progression_horizontale_locale)  # même mélange horizontal pour la rangée du bas : coin bas-gauche
                             + coins_du_bas_gauche[numero_maille_colonnes + 1] * progression_horizontale_locale)  # et coin bas-droit
            valeur_final_ligne.append(valeur_en_haut * (1 - progression_vertical_local) + valeur_en_bas * progression_vertical_local)  # puis on mélange le haut et le bas selon la position verticale
        bruit.append(valeur_final_ligne)  # la ligne est terminée, on l'ajoute à la grille
    return bruit


def genererTerrain(nombre_lignes, nombre_colonnes, graine=None, parametres=PARAMETRES_CARTE_PAR_DEFAUT):
    """Génère la carte : mélange plusieurs bruits lisses, creuse les bords pour faire une île, puis découpe en types de terrain.
    Entrée : le nombre de lignes, le nombre de colonnes, une graine (facultative, aléatoire si absente),
    le dictionnaire de paramètres de la carte. Utilise TAILLES_DES_OCTAVES.
    Sortie : une grille (liste de listes) de numéros de terrain : 0 herbe, 1 terre, 2 montagne, 3 mer."""
    graine_effective = graine if graine is not None else randrange(10 ** 9)  # la graine fixe la carte : même graine = même carte ; sans graine on en tire une au hasard

    octaves = []  # liste des (taille de maille, poids) réellement utilisés
    for taille_reference in TAILLES_DES_OCTAVES:  # on regarde chaque taille de forme
        poids = parametres[f"poids_octave_{taille_reference}"]  # son importance, lue dans les paramètres (ex : "poids_octave_64")
        if poids > 0:  # une octave de poids 0 est simplement ignorée
            octaves.append((taille_reference, poids))
    if not octaves:                                     # tous les poids à 0 : on garde la grosse octave
        octaves = [(64, 1.0)]  # valeur de secours pour avoir quand même une carte
    somme_des_poids = sum(poids for _, poids in octaves)  # sert à normaliser : le mélange final reste entre 0 et 1

    altitude = [[0.0] * nombre_colonnes for _ in range(nombre_lignes)]  # grille d'altitude, au départ plate (0 partout)
    for taille_maille_reference, poids in octaves:  # on ajoute les octaves une par une
        generateur_de_l_octave = Random(f"{graine_effective}-{taille_maille_reference}")  # un générateur par octave, tiré de la graine : reproductible
        taille_maille = max(2, round(taille_maille_reference * max(nombre_lignes, nombre_colonnes) / 500))  # adapte la taille des mailles si la carte n'a pas 500 cases (ex : l'aperçu) ; minimum 2
        bruit = genererBruitLisse(nombre_lignes, nombre_colonnes, taille_maille, generateur_de_l_octave)  # le bruit de cette octave
        for ligne in range(nombre_lignes):  # on parcourt toutes les cases
            for colonne in range(nombre_colonnes):
                altitude[ligne][colonne] += bruit[ligne][colonne] * poids / somme_des_poids  # chaque octave s'ajoute à l'altitude, pondérée par son importance

    terrain = []  # grille locale des types de terrain (renvoyée à la fin)
    for lignes in range(nombre_lignes):  # on décide du terrain de chaque case
        ecart_vertical_au_centre = (lignes / nombre_lignes - 0.5) * 2  # -1 tout en haut, 0 au centre, +1 tout en bas
        hauteur_ligne = []  # les types de terrain de cette ligne
        for colonnes in range(nombre_colonnes):
            ecart_horizontal_au_centre = (colonnes / nombre_colonnes - 0.5) * 2  # -1 à gauche, 0 au centre, +1 à droite
            distance_au_centre = min(1.0, (ecart_horizontal_au_centre ** 2 + ecart_vertical_au_centre ** 2) ** 0.5)  # distance au centre (Pythagore), plafonnée à 1 : 0 au centre, 1 sur les bords
            hauteur = altitude[lignes][colonnes] - parametres["force_ile"] * distance_au_centre ** 3  # on abaisse le terrain vers les bords (surtout tout au bord, à cause du cube) : ça forme une île

            if hauteur < parametres["niveau_mer"]:  # du plus bas au plus haut : mer, herbe, terre, montagne
                hauteur_ligne.append(3)  # trop bas : mer
            elif hauteur < parametres["limite_herbe"]:
                hauteur_ligne.append(0)  # entre la mer et la limite d'herbe : herbe
            elif hauteur < parametres["limite_terre"]:
                hauteur_ligne.append(1)  # entre l'herbe et la limite de terre : terre
            else:
                hauteur_ligne.append(2)  # tout en haut : montagne
        terrain.append(hauteur_ligne)  # la ligne est terminée
    return terrain


def estConquerable(x, y):
    """Dit si une case peut être conquise (tout sauf la mer).
    Entrée : la ligne x et la colonne y de la case. Utilise la grille terrain et TERRAINS_CONQUERABLE.
    Sortie : True si la case est conquérable, False sinon."""
    return terrain[x][y] in TERRAINS_CONQUERABLE  # vrai si le type de terrain de la case est dans la liste des terrains conquérables
## Fin de la génération du terrain


## Couleurs (terrains, joueurs, nations, tribus, palette Pyxel)
def assombrir(hexa, quantite=0.15):
    """Assombrit une couleur, pour en faire la couleur de frontière d'un territoire.
    Entrée : la couleur en hexadécimal (entier), la quantité de luminosité à retirer.
    Sortie : la couleur assombrie, en hexadécimal (entier)."""
    r, g, b = ((hexa >> 16) & 255) / 255, ((hexa >> 8) & 255) / 255, (hexa & 255) / 255 # découpage des trois octets hexadecimal en trois valeurs (rouge, vert, bleu) entre 0 et 1
    h, l, s = rgb_to_hls(r, g, b) # passge au hls (teinte, luminosité, saturation) : plus simple pour assombrir
    r, g, b = hls_to_rgb(h, max(0, l - quantite), s) # diminution de la luminosité pour assombrir (sans passer sous 0) et retour au rgb
    return (round(r * 255) << 16) | (round(g * 255) << 8) | round(b * 255) # recréation de la forme hexadecimal et envoie

NOMBRE_DE_TRIBUS_MAX = 80  # nombre maximal de tribus, donc de couleurs à générer

def genererCouleursDeTribus(nombre):
    """Génère des couleurs vives dont les teintes se répartissent sur tout le cercle des couleurs.
    Entrée : le nombre de couleurs voulues.
    Sortie : la liste des couleurs, en hexadécimal."""
    couleurs = []
    for numero in range(nombre):
        teinte = (numero * 0.618034) % 1  # le nombre d'or éloigne chaque teinte des précédentes sans jamais se répéter
        luminosite = (0.42, 0.56, 0.7)[numero % 3]  # on alterne sombre, moyenne et claire
        rouge, vert, bleu = hls_to_rgb(teinte, luminosite, 0.9)  # saturation élevée : couleurs vives
        couleurs.append((round(rouge * 255) << 16) | (round(vert * 255) << 8) | round(bleu * 255))
    return couleurs


TERRAINS = [0x4E7A47, 0x6E5A44, 0xC9CED3, 0x1B3A5C]  # couleurs des terrains, dans l'ordre : herbe, terre, montagne, mer

JOUEURS = [0xC8484F, 0x4F8FC7, 0x5FAE6B, 0xD9B84A, 0x8D6BB8]  # couleurs des 5 joueurs (le 1er est le joueur humain)

NATIONS = [0xE6A23C, 0x3FB6A8, 0xE0706B, 0x6C8EBF, 0xB5C25A,
           0xC77DB5, 0x5BB5E0, 0xE88B4D, 0x7FD1A0, 0xA88BE0]  # couleurs des 10 nations

TRIBUS = genererCouleursDeTribus(NOMBRE_DE_TRIBUS_MAX)
  # couleurs des 10 tribus (les bots), dans des tons gris-marron

COULEURS_INTERFACE = {  # couleurs de l'interface, accessibles par leur nom
    "fond": 0x1E2430,  # fond des écrans
    "panneau": 0x2A3245,  # fond des panneaux
    "bordure": 0x4A5878,  # contours
    "bouton": 0x3A4A66,  # bouton normal
    "bouton_survole": 0x5A6E94,  # bouton quand la souris est dessus
    "bouton_principal": 0xE6A23C,  # bouton mis en avant (orange)
    "bouton_principal_survole": 0xF2BC6B,  # bouton mis en avant quand la souris est dessus
    "texte": 0xF2F2F2,  # texte normal (presque blanc)
    "texte_discret": 0x9AA5BD,  # texte secondaire (gris-bleu)
    "texte_sur_principal": 0x1E2430,  # texte sur un bouton orange (foncé pour rester lisible)
    "rouge": 0xC8484F,  # rouge (défaite)
}
ENTITES = JOUEURS + NATIONS + TRIBUS  # toutes les entités qui peuvent posséder des cases, numérotées dans cet ordre à partir de 1
N = len(ENTITES)  # nombre total d'entités
PREMIERE_TRIBU = len(JOUEURS) + len(NATIONS) + 1  # numéro de la première tribu ; +1 car les entités sont numérotées à partir de 1 (0 = case sans propriétaire)

PALETTE = TERRAINS + ENTITES + [assombrir(c) for c in ENTITES] + list(COULEURS_INTERFACE.values())  # ordre important : terrains, remplissages, frontières (versions sombres), interface
pyxel.colors[:] = PALETTE  # remplace la palette de Pyxel par la nôtre

ID_COULEUR_ENTITES = {i + 1: {"remplissage": i + 4, "frontiere": i + 4 + N} for i in range(N)}  # pour chaque entité (numérotée dès 1) : numéro de sa couleur dans la palette ; +4 car les 4 premières couleurs sont les terrains ; +N car les frontières viennent après tous les remplissages
PREMIERE_COULEUR_INTERFACE = len(TERRAINS) + 2 * N  # numéro de la première couleur d'interface dans la palette (après terrains, remplissages et frontières)
COULEUR = {nom: PREMIERE_COULEUR_INTERFACE + numero for numero, nom in enumerate(COULEURS_INTERFACE)}  # permet d'écrire COULEUR["texte"] au lieu d'un numéro de palette
## Fin des couleurs


## Paramètres et état du jeu (troupes, attaques, bots, coûts)
# Joueur
JOUEUR_ACTUEL = 1  # numéro de l'entité contrôlée par le joueur humain

# Coûts et réglages des combats
VITESSE_ATTAQUE = 3  # une étape de combat toutes les 3 images (plus c'est grand, plus le jeu est lent)
COUT_TERRAIN = [16.5, 20, 100]  # un coût par type de terrain : herbe, terre, montagne ; plus c'est haut, plus la case est lente à prendre
MAG_TERRAIN = [80, 100, 120]  # un coefficient de pertes par type de terrain : herbe, terre, montagne ; plus c'est haut, plus ça coûte de troupes
MAG_PRIORITE = [1, 1.5, 2]  # un coefficient de priorité par type de terrain ; plus c'est haut, plus la case est prise tard
RESTITUTION = 1.0  # part des troupes restantes rendue à l'attaquant quand son attaque se termine (1.0 = tout)
FORCE_COMPACITE = 0.25  # plus c'est grand, plus les attaques préfèrent les cases entourées par l'attaquant

# Réglages de la partie
SEUIL_DE_VICTOIRE = 80              # % des terres conquérables
IMAGES_PAR_SECONDE = 30  # vitesse de rafraîchissement du jeu (sert à convertir les images en secondes)
RAYON_DE_DEPART = 4          # chaque entité commence avec un disque d'environ 49 cases
ESPACEMENT_RELATIF = 0.6     # distance minimale entre deux départs, par rapport à l'espacement naturel

REGLAGES_PAR_DEFAUT = {  # réglages d'une partie quand le joueur ne change rien
    "graine": None,  # None = carte aléatoire
    "nombre_de_tribus": 10,  # nombre de bots
    "troupes_de_depart": 25000,  # troupes de chaque entité au début
    "difficulte": "Normale",  # clé de DIFFICULTES
    **PARAMETRES_CARTE_PAR_DEFAUT,  # on recopie ici tous les paramètres de la carte
}

DIFFICULTES = {
    "Facile":    {"delais": (60, 120), "expansion": 0.30, "reserve": 0.50, "depart": 0.4, "plafond": 1 / 3, "croissance": 0.5},
    "Normale":   {"delais": (40, 80),  "expansion": 0.15, "reserve": 0.35, "depart": 1.0, "plafond": 1.0,   "croissance": 1.0},
    "Difficile": {"delais": (20, 45),  "expansion": 0.08, "reserve": 0.25, "depart": 1.5, "plafond": 1.5,   "croissance": 1.25},
}
difficulte_en_cours = DIFFICULTES["Normale"]  # la difficulté de la partie en cours (changée au lancement d'une partie)

# État de la partie en cours
numero_d_etape = 0  # nombre d'étapes de combat écoulées depuis le début (sert à mesurer la durée)
attaques = []  # liste des attaques en cours (une par couple attaquant / cible)
nb_case = {}  # nombre de cases de chaque entité (clé 0 = cases sans propriétaire)
frontiere = {}  # pour chaque entité, l'ensemble de ses cases de frontière
troupes = {}  # troupes de chaque entité
prochain_coup_bot = {}  # compte à rebours avant la prochaine décision de chaque bot
total_cases_conquerables = 1  # nombre de cases conquérables de la carte (sert de 100 %) ; 1 au départ pour éviter une division par 0

resultat_de_la_partie = None        # "victoire", "defaite" ou None
message_de_fin = ""  # phrase affichée sur l'écran de fin
part_maximale_de_territoire = 0.0  # record de territoire du joueur pendant la partie (en %)
adversaires_au_depart = 0  # nombre d'adversaires au début de la partie
derniers_reglages = None  # réglages de la dernière partie, pour pouvoir rejouer
## Fin des paramètres et de l'état du jeu

## Economie
REVENU_JOUEUR_PAR_ETAPE = 100
REVENU_TRIBU_PAR_ETAPE = 50
BONUS_TROUPES_VILLE = 250000
PORTEE_POSTE_DE_DEFENSE = 30
MULTIPLICATEUR_PERTES_POSTE = 5
MULTIPLICATEUR_LENTEUR_POSTE = 3

argent = {}
batiments = []
batiment_a_placer = None          # None, "ville" ou "poste"

RECTANGLE_CONSTRUCTION = (12, 12, 250, 262)
BOUTON_VILLE = (24, 118, 226, 48)
BOUTON_POSTE = (24, 174, 226, 48)
## Fin economie

## Fenêtre Pyxel, image de la carte et grille des propriétaires
pyxel.init(LARGEUR_ECRAN, HAUTEUR_ECRAN, title="OpenFront")  # crée la fenêtre du jeu
pyxel.mouse(True)  # affiche le curseur de la souris

carte = pyxel.Image(LIGNES, COLLONNES)  # 1 pixel = 1 case, agrandi ensuite à l'affichage grâce au zoom

grille = []  # numéro du propriétaire de chaque case (0 = personne)
## Fin de la fenêtre Pyxel, de la carte et de la grille


## Territoires et frontières (comptage des cases, frontières, changements de propriétaire)
def isFrontiere(x, y):
    """Dit si une case est sur la frontière de son propriétaire (au moins un voisin d'un autre propriétaire).
    Entrée : la ligne x et la colonne y de la case. Utilise la grille des propriétaires et LIGNES / COLLONNES.
    Sortie : True si c'est une case de frontière, False sinon (toujours False pour une case sans propriétaire)."""
    proprietaire = grille[x][y]  # à qui appartient la case

    if proprietaire == 0:  # une case sans propriétaire n'a pas de frontière
        return False

    if x > 0 and grille[x - 1][y] != proprietaire:  # voisin du haut (on vérifie qu'il existe) : s'il est à quelqu'un d'autre, c'est une frontière
        return True

    if y > 0 and grille[x][y - 1] != proprietaire:  # voisin de gauche
        return True

    if x < LIGNES - 1 and grille[x + 1][y] != proprietaire:  # voisin du bas
        return True

    if y < COLLONNES - 1 and grille[x][y + 1] != proprietaire:  # voisin de droite
        return True

    return False  # tous les voisins sont au même propriétaire : case intérieure


def initFrontiere():
    """Remplit l'ensemble des cases de frontière de chaque entité, en parcourant toute la carte.
    Entrée : rien. Utilise la grille des propriétaires et le dictionnaire frontiere.
    Sortie : rien, le dictionnaire frontiere est modifié."""
    for x in range(LIGNES):  # on parcourt toutes les cases
        for y in range(COLLONNES):
            proprietaire = grille[x][y]  # propriétaire de la case
            if proprietaire != 0 and isFrontiere(x, y):  # case possédée et en bordure
                frontiere[proprietaire].add((x, y))  # on l'ajoute à la frontière de son propriétaire


def compteCase():
    """Compte combien de cases possède chaque entité.
    Entrée : rien. Utilise la grille des propriétaires et le dictionnaire nb_case.
    Sortie : rien, le dictionnaire nb_case est modifié."""
    for ligne in grille:  # chaque ligne de la grille
        for proprietaire in ligne:  # chaque case de la ligne (on ne garde que son propriétaire)
            nb_case[proprietaire] += 1  # +1 case pour ce propriétaire


def candidatsInitiaux(attaquant, cible):
    """Trouve les cases de la cible qui touchent le territoire de l'attaquant, point de départ d'une attaque.
    Entrée : le numéro de l'attaquant, le numéro de la cible. Utilise frontiere et la grille des propriétaires.
    Sortie : un ensemble de cases conquérables, chacune sous la forme (ligne, colonne)."""
    resultat = set()  # un ensemble : pas de doublons si une case touche plusieurs cases de l'attaquant
    for x, y in frontiere[attaquant]:  # chaque case de frontière de l'attaquant
        for nx, ny in voisins(x, y):  # chacun de ses voisins
            if grille[nx][ny] == cible and estConquerable(nx, ny):  # voisin qui appartient à la cible et qui n'est pas de la mer
                resultat.add((nx, ny))
    return resultat


def majFrontiere(cases, ancien_proprietaire):
    """Met à jour les frontières après un changement de propriétaire (pour les cases et leurs voisines).
    Entrée : la liste des cases qui ont changé, le numéro de leur ancien propriétaire. Utilise grille et frontiere.
    Sortie : rien, le dictionnaire frontiere est modifié."""
    if ancien_proprietaire != 0:  # le terrain libre (0) n'a pas de frontière à mettre à jour
        for case in cases:
            frontiere[ancien_proprietaire].discard(case)  # ces cases ne sont plus à l'ancien propriétaire ; discard ne plante pas si la case n'y était pas

    a_refaire = set(cases)  # cases dont il faut recalculer le statut de frontière : d'abord celles qui ont changé

    for x, y in cases:
        a_refaire.update(voisins(x, y))  # les voisins aussi : leur statut de frontière a pu changer

    for x, y in a_refaire:  # on recalcule chaque case concernée
        proprietaire = grille[x][y]
        if proprietaire == 0:  # une case sans propriétaire n'a pas de frontière
            continue
        if isFrontiere(x, y):
            frontiere[proprietaire].add((x, y))  # elle est en bordure : on l'ajoute
        else:
            frontiere[proprietaire].discard((x, y))  # n'est plus en bordure : on la retire


def changerProprietaire(cases, ancien, nouveau):
    """Donne des cases à un nouveau propriétaire et met à jour les compteurs et les frontières.
    Entrée : la liste des cases, le numéro de l'ancien propriétaire, le numéro du nouveau. Utilise grille et nb_case.
    Sortie : rien, la grille, nb_case et frontiere sont modifiés."""
    for x, y in cases:
        grille[x][y] = nouveau  # la case change de propriétaire
    nb_case[ancien] -= len(cases)  # l'ancien propriétaire perd ces cases
    nb_case[nouveau] += len(cases)  # le nouveau les gagne
    majFrontiere(cases, ancien)  # les frontières doivent suivre


def verifierFrontiere():
    """Outil de débogage (touche V) : recalcule toutes les frontières depuis la grille et les compare à celles stockées.
    Entrée : rien. Utilise grille et frontiere.
    Sortie : True si tout est cohérent, False à la première entité incohérente (qui est alors affichée)."""
    for entite in range(1, N + 1):  # chaque entité
        attendu = {(x, y) for x in range(LIGNES) for y in range(COLLONNES) if grille[x][y] == entite and isFrontiere(x, y)}  # la "vraie" frontière, recalculée de zéro sur toute la carte
        if attendu != frontiere[entite]:  # différente de celle qu'on a stockée : il y a un bug quelque part
            print("frontière incohérente pour", entite)
            return False
    return True
## Fin des territoires et frontières


## Dessin de la carte (couleur des cases et mise à jour de l'image)
def couleurCase(x, y):
    """Choisit la couleur d'une case : terrain si elle n'appartient à personne, sinon couleur de son propriétaire (plus sombre sur la frontière).
    Entrée : la ligne x et la colonne y de la case. Utilise grille, terrain et ID_COULEUR_ENTITES.
    Sortie : le numéro de couleur de la palette Pyxel (entier)."""
    proprietaire = grille[x][y]  # à qui est la case
    if proprietaire == 0:
        return terrain[x][y]  # le numéro de terrain (0 à 3) est aussi le numéro de sa couleur dans la palette
    if isFrontiere(x, y):
        return ID_COULEUR_ENTITES[proprietaire]["frontiere"]  # case de bord : couleur sombre
    return ID_COULEUR_ENTITES[proprietaire]["remplissage"]  # case intérieure : couleur normale


def reddessiner(cases):
    """Redessine sur l'image de la carte les cases données et leurs voisines (leur frontière a pu changer).
    Entrée : la liste des cases modifiées. Utilise l'image carte.
    Sortie : rien, l'image carte est modifiée."""
    a_refaire = set()  # cases à redessiner
    for x, y in cases:
        a_refaire.add((x, y))  # la case elle-même
        a_refaire.update(voisins(x, y))  # les voisins peuvent devenir (ou cesser d'être) une frontière
    for x, y in a_refaire:
        carte.pset(y, x, couleurCase(x, y))  # pset veut (colonne, ligne), donc y avant x


def reddessinerTout():
    """Redessine toute la carte, case par case.
    Entrée : rien. Utilise l'image carte, LIGNES et COLLONNES.
    Sortie : rien, l'image carte est modifiée."""
    for x in range(LIGNES):  # chaque ligne
        for y in range(COLLONNES):  # chaque colonne
            carte.pset(y, x, couleurCase(x, y))  # on peint le pixel de la case de la bonne couleur
## Fin du dessin de la carte


## Zoom et caméra (déplacement, zoom à la molette, conversion souris -> case)
ZONE_JEU_X, ZONE_JEU_Y = 0, 0  # coin haut gauche de la zone où la carte est affichée
ZONE_JEU_LARGEUR, ZONE_JEU_HAUTEUR = LARGEUR_ECRAN, HAUTEUR_ECRAN - HAUTEUR_BARRE  # la zone de jeu occupe tout l'écran sauf la barre du bas
ZOOM_MIN = 1.0  # zoom minimal : 1 pixel d'écran par case
ZOOM_MAX = 40.0  # zoom maximal : 40 pixels d'écran par case
FACTEUR_ZOOM_PAR_CRAN = 1.15  # chaque cran de molette multiplie (ou divise) le zoom par 1,15

zoom = 4.0  # nombre de pixels d'écran par case
camera_colonne = 0.0  # colonne de la carte affichée tout à gauche de l'écran
camera_ligne = 0.0  # ligne de la carte affichée tout en haut de l'écran
point_ancre = None  # point de la carte "attrapé" quand on glisse avec le clic droit (None = on ne glisse pas)


def pointSousCurseur():
    """Calcule le point de la carte situé sous la souris (position décimale, pas forcément une case entière).
    Entrée : rien. Utilise la position de la souris, le zoom et la position de la caméra.
    Sortie : la colonne et la ligne du point (deux nombres décimaux)."""
    return (camera_colonne + (pyxel.mouse_x - ZONE_JEU_X) / zoom,  # colonne = colonne de la caméra + distance de la souris au bord gauche, convertie en cases (pixels / zoom)
            camera_ligne + (pyxel.mouse_y - ZONE_JEU_Y) / zoom)  # pareil pour la ligne


def limiterCamera():
    """Empêche la caméra de sortir trop loin de la carte.
    Entrée : rien. Utilise la caméra, le zoom, la taille de la zone de jeu et de la carte.
    Sortie : rien, camera_colonne et camera_ligne sont modifiés."""
    global camera_colonne, camera_ligne
    case_visible_largeur = ZONE_JEU_LARGEUR / zoom  # nombre de cases visibles à l'écran en largeur
    case_visible_hauteur = ZONE_JEU_HAUTEUR / zoom  # et en hauteur
    camera_colonne = borner(camera_colonne, -case_visible_largeur / 2, COLLONNES - case_visible_largeur / 2)  # on peut dépasser du bord jusqu'à la moitié de l'écran
    camera_ligne = borner(camera_ligne, -case_visible_hauteur / 2, LIGNES - case_visible_hauteur / 2)  # pareil en hauteur


def deplacerCamera():
    """Gère le zoom à la molette, le déplacement en glissant avec le clic droit et le déplacement avec les flèches.
    Entrée : rien. Utilise la souris, le clavier, le zoom et la position de la caméra.
    Sortie : rien, zoom, camera_colonne et camera_ligne sont modifiés."""
    global zoom, camera_colonne, camera_ligne, point_ancre

    if pyxel.mouse_wheel != 0:  # la molette a tourné
        colonne_sous_souris, ligne_sous_souris = pointSousCurseur()  # on retient le point de la carte visé avant de zoomer
        zoom = borner(zoom * FACTEUR_ZOOM_PAR_CRAN ** pyxel.mouse_wheel, ZOOM_MIN, ZOOM_MAX)  # nouveau zoom : multiplié par 1,15 par cran (puissance négative = dézoom), dans les limites
        camera_colonne = colonne_sous_souris - (pyxel.mouse_x - ZONE_JEU_X) / zoom  # on recale la caméra pour que le point visé reste sous la souris
        camera_ligne = ligne_sous_souris - (pyxel.mouse_y - ZONE_JEU_Y) / zoom

    if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):  # le clic droit vient d'être appuyé
        point_ancre = pointSousCurseur()  # début du glissement : on attrape ce point de la carte
    if pyxel.btn(pyxel.MOUSE_BUTTON_RIGHT) and point_ancre is not None:  # clic droit maintenu
        camera_colonne = point_ancre[0] - (pyxel.mouse_x - ZONE_JEU_X) / zoom  # la caméra est placée pour que le point attrapé reste collé au curseur
        camera_ligne = point_ancre[1] - (pyxel.mouse_y - ZONE_JEU_Y) / zoom
    else:
        point_ancre = None  # clic droit relâché : on lâche la carte

    vitesse_en_cases = 20 / zoom  # plus on est zoomé, moins on avance en cases (la vitesse à l'écran reste la même : 20 pixels par image)
    if pyxel.btn(pyxel.KEY_LEFT):  # flèche gauche maintenue
        camera_colonne -= vitesse_en_cases
    if pyxel.btn(pyxel.KEY_RIGHT):  # flèche droite
        camera_colonne += vitesse_en_cases
    if pyxel.btn(pyxel.KEY_UP):  # flèche haut
        camera_ligne -= vitesse_en_cases
    if pyxel.btn(pyxel.KEY_DOWN):  # flèche bas
        camera_ligne += vitesse_en_cases

    limiterCamera()  # on remet la caméra dans les limites


def centrerCarte():
    """Règle le zoom et la caméra pour voir toute la carte, centrée dans la zone de jeu.
    Entrée : rien. Utilise la taille de la carte et de la zone de jeu.
    Sortie : rien, zoom, camera_colonne et camera_ligne sont modifiés."""
    global zoom, camera_colonne, camera_ligne
    zoom = borner(min(ZONE_JEU_LARGEUR/ COLLONNES, ZONE_JEU_HAUTEUR / LIGNES), ZOOM_MIN, ZOOM_MAX)  # le plus grand zoom qui fait tenir toute la carte (limité par le côté le plus serré)
    camera_colonne = COLLONNES / 2 - ZONE_JEU_LARGEUR / zoom / 2  # le milieu de la carte au milieu de l'écran (la moitié de l'écran en cases est retirée)
    camera_ligne = LIGNES / 2 - ZONE_JEU_HAUTEUR / zoom / 2


def centrerSurCase(ligne, colonne, nouveau_zoom):
    """Centre la caméra sur une case donnée avec un zoom choisi.
    Entrée : la ligne et la colonne de la case, le nouveau zoom. Utilise la taille de la zone de jeu.
    Sortie : rien, zoom, camera_colonne et camera_ligne sont modifiés."""
    global zoom, camera_colonne, camera_ligne
    zoom = borner(nouveau_zoom, ZOOM_MIN, ZOOM_MAX)  # on applique le zoom demandé, dans les limites
    camera_colonne = colonne + 0.5 - ZONE_JEU_LARGEUR / zoom / 2  # +0.5 : on vise le milieu de la case, pas son coin ; puis on retire la moitié de l'écran pour la placer au centre
    camera_ligne = ligne + 0.5 - ZONE_JEU_HAUTEUR / zoom / 2
    limiterCamera()  # on remet la caméra dans les limites


def caseSousCurseur():
    """Trouve la case de la carte située sous la souris.
    Entrée : rien. Utilise la position de la souris, la zone de jeu, la caméra et la taille de la carte.
    Sortie : la ligne et la colonne de la case (deux entiers), ou None si la souris est hors de la zone de jeu ou de la carte."""
    if not (ZONE_JEU_X <= pyxel.mouse_x < ZONE_JEU_X + ZONE_JEU_LARGEUR and ZONE_JEU_Y <= pyxel.mouse_y < ZONE_JEU_Y + ZONE_JEU_HAUTEUR):
        return None  # la souris est sur la barre du bas, pas sur la carte

    colonne_decimal, ligne_decimal = pointSousCurseur()  # position décimale du point visé
    colonne = int(colonne_decimal // 1)  # partie entière (arrondi vers le bas) : le numéro de la case touchée
    ligne = int(ligne_decimal // 1)
    if not (0 <= ligne < LIGNES and 0 <= colonne < COLLONNES):  # on est dans la zone de jeu mais à côté de la carte
        return None
    return ligne, colonne
## Fin du zoom et de la caméra


## Troupes et combats (génération de troupes, coûts, attaques)
def maxTroupe(proprietaire):
    """Calcule le nombre maximum de troupes d'une entité (il grandit avec son territoire, et est divisé par 3 pour une tribu).
    Entrée : le numéro de l'entité. Utilise nb_case et PREMIERE_TRIBU.
    Sortie : le maximum de troupes (nombre décimal)."""
    maxi = 2 * (1000 * nb_case[proprietaire] ** 0.6 + 50000) # grandit avec le nombre de cases, mais de moins en moins vite (puissance 0,6)
    maxi += BONUS_TROUPES_VILLE * nombreDeBatiments(proprietaire, "ville")
    if proprietaire >= PREMIERE_TRIBU:
        maxi *= difficulte_en_cours["plafond"]
    return maxi

def generationTroupe():
    """Fait gagner des troupes à chaque entité qui a encore du territoire (la croissance ralentit près du maximum, et les tribus sont plus lentes).
    Entrée : rien. Utilise troupes, nb_case et maxTroupe.
    Sortie : rien, le dictionnaire troupes est modifié."""
    for proprietaire in range(1, N + 1):  # chaque entité
        if nb_case[proprietaire] == 0:  # une entité éliminée ne produit plus rien
            continue
        troupe_actuel = troupes[proprietaire]  # ses troupes actuelles
        maxi = maxTroupe(proprietaire)  # son maximum
        ajout = (10 + troupe_actuel ** 0.73 / 4) * (1 - troupe_actuel / maxi)  # base de production qui grandit avec les troupes, multipliée par (1 - remplissage) : tend vers 0 près du max, donc la croissance ralentit
        if proprietaire >= PREMIERE_TRIBU:
            ajout *= difficulte_en_cours["croissance"]
        troupes[proprietaire] = min(troupe_actuel + ajout, maxi)  # on ajoute sans jamais dépasser le maximum


def prioriteCase(attaquant, x, y, etape_de_decouverte):
    """Calcule la priorité d'une case à conquérir : plus le nombre est petit, plus elle est prise tôt.
    Dépend du hasard, du nombre de voisins déjà à l'attaquant, du terrain et de l'ancienneté de la case dans l'attaque.
    Entrée : le numéro de l'attaquant, la ligne x et la colonne y de la case, l'étape où elle a été découverte.
    Utilise grille, terrain, MAG_PRIORITE et FORCE_COMPACITE.
    Sortie : la priorité (nombre décimal)."""
    case_voisines = 0  # nombre de voisins de la case qui sont déjà à l'attaquant
    for nx, ny in voisins(x, y):
        if grille[nx][ny] == attaquant:  # on compte les voisins qui sont déjà à l'attaquant
            case_voisines += 1
    mag = MAG_PRIORITE[terrain[x][y]]  # coefficient du terrain de la case (montagne = prise plus tard)
    return (randint(0, 6) + 10) * (1 - FORCE_COMPACITE * case_voisines + mag / 2) + etape_de_decouverte  # le hasard (10 à 16) rend le front irrégulier ; plus de voisins = nombre plus petit = pris plus tôt (le territoire reste compact) ; + l'étape : les vieilles cases passent avant


def couts(attaque, x, y, front):
    """Calcule ce que coûte la conquête d'une case : pertes de l'attaquant, pertes du défenseur et part de l'effort de l'étape consommée.
    Entrée : l'attaque (dictionnaire), la ligne x et la colonne y de la case, la taille du front (nombre de cases attaquables).
    Utilise terrain, troupes, nb_case, COUT_TERRAIN et MAG_TERRAIN.
    Sortie : les pertes de l'attaquant, les pertes du défenseur et la part de l'effort consommée (trois nombres)."""
    type_t = terrain[x][y]  # type de terrain de la case (0 herbe, 1 terre, 2 montagne)
    mag, cout_case = MAG_TERRAIN[type_t], COUT_TERRAIN[type_t]  # coefficient de pertes et coût de ce terrain
    A = attaque["troupes"]  # troupes de l'attaquant engagées dans cette attaque
    cible = attaque["cible"]  # qui est attaqué

    if cible == 0:  # cible 0 = terrain libre : personne ne se défend
        fraction = borner(2000 * cout_case / A, 5, 100) / (2 * front)
        return mag / 5, 0, fraction

    if aUnPosteDeDefenseProche(cible, x, y):  # le défenseur a un poste de défense à moins de 30 cases
        mag *= MULTIPLICATEUR_PERTES_POSTE  # l'attaquant perd 5 fois plus de troupes
        cout_case *= MULTIPLICATEUR_LENTEUR_POSTE  # et avance 3 fois plus lentement

    D = troupes[cible]  # troupes du défenseur
    densite = D / max(1, nb_case[cible])  # nombre de défenseurs par case : plus c'est dense, plus c'est dur de percer (max(1, ...) évite de diviser par 0)
    rapport = D / A  # rapport de force : > 1 si le défenseur est plus fort
    perte_attaque = mag * borner(rapport, 0.6, 2) * (0.463 + 0.0039 * densite)  # l'attaquant perd plus si le défenseur est fort et dense (rapport limité entre 0,6 et 2)
    cout_vitesse = borner(rapport, 0.82, 7.5) * borner(rapport / 20, 1, 50) / 8.55  # plus le défenseur est fort, plus la conquête est lente
    fraction = cout_vitesse * cout_case / front  # part du budget de l'étape mangée par cette case (divisée entre toutes les cases du front)
    return perte_attaque, densite, fraction  # la perte du défenseur est sa densité de troupes


def trouverAttaquer(attaquant, cible):
    """Cherche l'attaque en cours d'un attaquant contre une cible.
    Entrée : le numéro de l'attaquant, le numéro de la cible. Utilise la liste attaques.
    Sortie : l'attaque (dictionnaire), ou None s'il n'y en a pas."""
    for a in attaques:  # chaque attaque en cours
        if a["attaquant"] == attaquant and a["cible"] == cible:  # c'est celle qu'on cherche
            return a
    return None  # aucune trouvée


def lancerAttaque(attaquant, cible, part=0.2):
    """Lance une attaque en envoyant une part des troupes de l'attaquant.
    Si la cible attaque déjà l'attaquant, les troupes s'annulent ; si une attaque identique existe, on lui ajoute les troupes.
    Entrée : le numéro de l'attaquant, le numéro de la cible, la part des troupes envoyée (0.2 par défaut).
    Utilise troupes et attaques.
    Sortie : rien, troupes et attaques sont modifiés."""
    envoyee = int(troupes[attaquant] * part)  # nombre de troupes envoyées (entier)
    if envoyee < 1:  # rien à envoyer
        return
    troupes[attaquant] -= envoyee  # les troupes envoyées quittent la réserve

    oposant = trouverAttaquer(cible, attaquant)  # la cible est-elle déjà en train de nous attaquer ?
    if oposant is not None:
        annulees = min(envoyee, oposant["troupes"])  # les deux armées se détruisent à parts égales, au maximum de la plus petite
        envoyee -= annulees  # il reste à l'attaquant ce qui n'a pas été annulé
        oposant["troupes"] -= annulees  # et à l'adversaire pareil
        if envoyee < 1:  # tout a été annulé : pas de nouvelle attaque
            return

    existante = trouverAttaquer(attaquant, cible)  # a-t-on déjà une attaque identique en cours ?
    if existante is not None:
        existante["troupes"] += envoyee  # même attaque déjà en cours : on la renforce au lieu d'en créer une deuxième
        return

    candidats = {case: numero_d_etape for case in candidatsInitiaux(attaquant, cible)}  # cases attaquables au départ : case -> étape où elle a été découverte
    attaques.append({"attaquant": attaquant, "cible": cible, "candidats": candidats, "troupes": envoyee})  # on enregistre la nouvelle attaque


def etapeAttaque():
    """Fait avancer toutes les attaques d'une étape : conquiert des cases tant que le budget et les troupes le permettent,
    découvre les nouvelles cases à attaquer, redessine, puis termine les attaques finies (les troupes restantes retournent à l'attaquant).
    Entrée : rien. Utilise attaques, grille, troupes, numero_d_etape et RESTITUTION.
    Sortie : rien, attaques, la grille, troupes et l'image de la carte sont modifiés."""
    global attaques, numero_d_etape
    numero_d_etape += 1  # une étape de plus

    for attaque in attaques:  # on fait avancer chaque attaque
        if attaque["troupes"] < 1:  # plus de troupes : elle sera supprimée à la fin
            continue
        attaquant, cible = attaque["attaquant"], attaque["cible"]  # qui attaque qui
        decouvertes = attaque["candidats"]  # cases attaquables (case -> étape de découverte)

        valides = [(x, y) for (x, y) in decouvertes if grille[x][y] == cible]  # on retire les cases qui ont changé de propriétaire entre-temps
        valides.sort(key=lambda case: prioriteCase(attaquant, case[0], case[1], decouvertes[case]))  # on trie : les plus prioritaires (nombre le plus petit) d'abord
        a_prendre = []  # cases conquises pendant cette étape
        front = max(1, len(valides))  # taille du front : le coût est réparti dessus (au moins 1 pour éviter une division par 0)
        budget = 1  # effort disponible pour cette étape ; chaque case prise en consomme une part
        for x, y in valides:  # on prend les cases dans l'ordre de priorité
            perte_att, perte_def, fraction = couts(attaque, x, y, front)  # ce que coûte cette case
            a_prendre.append((x, y))  # la case est conquise
            attaque["troupes"] -= perte_att  # l'attaquant perd des troupes
            if cible != 0:
                troupes[cible] = max(0, troupes[cible] - perte_def)  # le défenseur aussi, sans descendre sous 0
            budget -= fraction  # une part du budget de l'étape est consommée
            if budget <= 0 or attaque["troupes"] < 1:  # plus de budget ou plus de troupes : on arrête pour cette étape
                break
        candidats_suivant = {case: decouvertes[case] for case in valides[len(a_prendre):]}  # les cases non prises restent candidates pour la prochaine étape

        changerProprietaire(a_prendre, cible, attaquant)  # les cases conquises passent à l'attaquant

        for x, y in a_prendre:  # autour de chaque case conquise...
            for nx, ny in voisins(x, y):
                if grille[nx][ny] == cible and estConquerable(nx, ny):  # ...les voisins encore à la cible deviennent attaquables
                    candidats_suivant.setdefault((nx, ny), numero_d_etape)  # nouvelle case à portée ; setdefault garde l'ancienne étape si elle était déjà connue

        attaque["candidats"] = candidats_suivant  # on met à jour la liste des cases attaquables
        reddessiner(a_prendre)  # on redessine les cases conquises
    attaque_active = []  # attaques qui continuent
    for a in attaques:
        if a["candidats"] and a["troupes"] >= 1:  # l'attaque continue tant qu'il reste des cases à prendre et des troupes
            attaque_active.append(a)
        else:
            troupes[a["attaquant"]] += int(max(0, a["troupes"]) * RESTITUTION)  # attaque finie : les troupes restantes rentrent à la maison
    attaques = attaque_active  # on ne garde que les attaques encore actives
## Fin des troupes et des combats


## Bots (choix de la cible et décisions des tribus)
def choisirCible(bot):
    """Choisit qui un bot va attaquer parmi les voisins de son territoire (le terrain libre est toujours prioritaire).
    Entrée : le numéro du bot. Utilise frontiere et la grille des propriétaires.
    Sortie : le numéro de la cible (0 pour le terrain libre), ou None s'il n'y a rien à attaquer."""
    case_voisines = set()  # en fait : l'ensemble des propriétaires voisins (0 compris), pas des cases
    for x, y in frontiere[bot]:  # chaque case de frontière du bot
        for nx, ny in voisins(x, y):  # chacun de ses voisins
            proprietaire = grille[nx][ny]  # à qui est le voisin
            if proprietaire != bot and estConquerable(nx, ny):  # pas à lui, et pas de la mer
                case_voisines.add(proprietaire)  # ce propriétaire est une cible possible
    if not case_voisines:  # personne à attaquer
        return None
    if 0 in case_voisines:  # du terrain libre est à portée : on le prend avant d'attaquer quelqu'un
        return 0
    return choice(list(case_voisines))  # sinon on choisit un voisin au hasard


def tourBots():
    """Fait jouer les tribus : quand le délai d'un bot est écoulé, il choisit une cible et attaque avec ses troupes au-delà d'une réserve (selon la difficulté).
    Entrée : rien. Utilise difficulte_en_cours, prochain_coup_bot, nb_case, troupes et PREMIERE_TRIBU.
    Sortie : rien, prochain_coup_bot est modifié (et les attaques sont lancées)."""
    delai_mini, delai_maxi = difficulte_en_cours["delais"]  # délai minimal et maximal entre deux décisions
    for j in range(PREMIERE_TRIBU, N + 1):  # seules les tribus sont des bots
        if nb_case[j] == 0:  # tribu éliminée
            continue
        prochain_coup_bot[j] -= 1  # compte à rebours avant la prochaine décision
        if prochain_coup_bot[j] > 0:  # pas encore l'heure
            continue
        prochain_coup_bot[j] = randint(delai_mini, delai_maxi)  # nouveau délai aléatoire pour la fois suivante

        cible = choisirCible(j)  # qui attaquer
        if cible is None:  # rien à attaquer
            continue

        if cible == 0 or cible >= PREMIERE_TRIBU:
            plancher = difficulte_en_cours["expansion"]  # terrain libre ou autre tribu : le bot ose se vider davantage
        else:
            plancher = difficulte_en_cours["reserve"]  # joueur ou nation : il garde plus de troupes en réserve

        disponibles = troupes[j] - plancher * maxTroupe(j)  # troupes au-dessus de la réserve (réserve = part du maximum de troupes)
        if disponibles >= 1:  # il y a de quoi attaquer
            lancerAttaque(j, cible, part=disponibles / troupes[j])  # lancerAttaque attend une part des troupes, pas un nombre : on divise
## Fin des bots


## Interaction du joueur (clic de souris)
def click():
    """Gère un clic gauche sur la carte : lance une attaque du joueur sur le propriétaire de la case cliquée.
    Entrée : rien. Utilise la case sous la souris, la grille, ratio_attaque et RECTANGLE_CLASSEMENT (clic ignoré sur le classement).
    Sortie : rien, une attaque est lancée si la case est conquérable et n'est pas déjà au joueur."""
    if sourisDansRectangle(*RECTANGLE_CLASSEMENT) or sourisDansRectangle(*RECTANGLE_CONSTRUCTION):
        return
    case = caseSousCurseur()# case visée (ou None)
    if case is None: # la souris n'est pas sur la carte
        return

    ligne, colonne = case # on sépare la ligne et la colonne
    if batiment_a_placer is not None:
        essayerDeConstruire(batiment_a_placer, ligne, colonne)
        return

    proprietaire = grille[ligne][colonne] # à qui est la case cliquée
    if proprietaire != JOUEUR_ACTUEL and estConquerable(ligne, colonne): # pas déjà à nous, et pas de la mer
        lancerAttaque(JOUEUR_ACTUEL, proprietaire, ratio_attaque) # on attaque son propriétaire avec la part choisie sur le curseur
## Fin de l'interaction du joueur


## Economie
def nombreDeBatiments(proprietaire, type_de_batiment):
    return sum(1 for b in batiments if b["proprietaire"] == proprietaire and b["type"] == type_de_batiment)


def coutDuBatiment(type_de_batiment, proprietaire):
    nombre_deja_construit = nombreDeBatiments(proprietaire, type_de_batiment)
    if type_de_batiment == "ville":
        return min(1_000_000, 125_000 * 2 ** nombre_deja_construit)
    return min(250_000, 50_000 * (nombre_deja_construit + 1))


def generationDeLArgent():
    for entite in range(1, N + 1):
        if nb_case[entite] > 0:
            argent[entite] += REVENU_TRIBU_PAR_ETAPE if entite >= PREMIERE_TRIBU else REVENU_JOUEUR_PAR_ETAPE


def retirerLesBatimentsPerdus():
    global batiments
    batiments = [b for b in batiments if grille[b["ligne"]][b["colonne"]] == b["proprietaire"]]


def aUnPosteDeDefenseProche(proprietaire, ligne, colonne):
    for b in batiments:
        if b["type"] == "poste" and b["proprietaire"] == proprietaire:
            if (b["ligne"] - ligne) ** 2 + (b["colonne"] - colonne) ** 2 <= PORTEE_POSTE_DE_DEFENSE ** 2:
                return True
    return False


def batimentSurLaCase(ligne, colonne):
    for b in batiments:
        if b["ligne"] == ligne and b["colonne"] == colonne:
            return b
    return None


def essayerDeConstruire(type_de_batiment, ligne, colonne):
    global batiment_a_placer
    if grille[ligne][colonne] != JOUEUR_ACTUEL or batimentSurLaCase(ligne, colonne) is not None:
        return
    cout = coutDuBatiment(type_de_batiment, JOUEUR_ACTUEL)
    if argent[JOUEUR_ACTUEL] < cout:
        return
    argent[JOUEUR_ACTUEL] -= cout
    batiments.append({"type": type_de_batiment, "proprietaire": JOUEUR_ACTUEL, "ligne": ligne, "colonne": colonne})
    batiment_a_placer = None

def formaterOr(valeur):
    if valeur >= 1_000_000:
        return f"{valeur / 1_000_000:.2f} M".replace(".", ",")
    if valeur >= 1000:
        return f"{valeur / 1000:.1f} K".replace(".", ",").replace(",0 K", " K")
    return str(int(valeur))


def mettreAJourConstruction():
    global batiment_a_placer
    for type_de_batiment, rectangle in (("ville", BOUTON_VILLE), ("poste", BOUTON_POSTE)):
        if boutonClique(*rectangle):
            batiment_a_placer = None if batiment_a_placer == type_de_batiment else type_de_batiment


def dessinerBoutonDeConstruction(rectangle, libelle, type_de_batiment):
    x, y, largeur, hauteur = rectangle
    cout = coutDuBatiment(type_de_batiment, JOUEUR_ACTUEL)
    abordable = argent[JOUEUR_ACTUEL] >= cout
    selectionne = batiment_a_placer == type_de_batiment
    survole = abordable and sourisDansRectangle(x, y, largeur, hauteur)

    if selectionne:
        couleur_fond = "bouton_principal"
    else:
        couleur_fond = "bouton_survole" if survole else "bouton"
    couleur_texte = "texte_sur_principal" if selectionne else ("texte" if abordable else "texte_discret")
    pyxel.rect(x, y, largeur, hauteur, COULEUR[couleur_fond])
    pyxel.rectb(x, y, largeur, hauteur, COULEUR["bordure"])
    decalage_texte = (hauteur - TAILLES_DE_POLICE["bouton"]) // 2 - 2
    ecrire(libelle, x + 14, y + decalage_texte, couleur_texte, "bouton")
    ecrireADroite(formaterOr(cout), x + largeur - 14, y + decalage_texte, couleur_texte, "bouton")


def dessinerPanneauDeConstruction():
    x, y, largeur, hauteur = RECTANGLE_CONSTRUCTION
    pyxel.rect(x, y, largeur, hauteur, COULEUR["panneau"])
    pyxel.rectb(x, y, largeur, hauteur, COULEUR["bordure"])

    revenu_par_seconde = REVENU_JOUEUR_PAR_ETAPE * IMAGES_PAR_SECONDE / VITESSE_ATTAQUE
    ecrire("Or", x + 14, y + 8, "texte_discret", "legende")
    ecrire(formaterOr(argent[JOUEUR_ACTUEL]), x + 14, y + 28, "bouton_principal", "bouton")
    ecrireADroite(f"+{int(revenu_par_seconde):,} / s".replace(",", " "), x + largeur - 14, y + 36, "texte_discret", "petit")
    pyxel.line(x + 10, y + 72, x + largeur - 10, y + 72, COULEUR["bordure"])
    ecrire("Construire", x + 14, y + 84, "texte_discret", "legende")

    dessinerBoutonDeConstruction(BOUTON_VILLE, "Ville", "ville")
    dessinerBoutonDeConstruction(BOUTON_POSTE, "Poste", "poste")
    if batiment_a_placer is not None:
        ecrire("Clique sur ton territoire", x + 14, y + 236, "texte", "petit")


def dessinerBatiments():
    taille = max(4, int(zoom * 2))
    for batiment in batiments:
        x = ZONE_JEU_X + (batiment["colonne"] + 0.5 - camera_colonne) * zoom
        y = ZONE_JEU_Y + (batiment["ligne"] + 0.5 - camera_ligne) * zoom
        if not (-taille <= x <= ZONE_JEU_LARGEUR + taille and -taille <= y <= ZONE_JEU_HAUTEUR + taille):
            continue
        couleur_du_type = COULEUR["bouton_principal"] if batiment["type"] == "ville" else COULEUR["texte"]
        pyxel.rect(x - taille / 2 - 1, y - taille / 2 - 1, taille + 2, taille + 2, COULEUR["fond"])
        pyxel.rect(x - taille / 2, y - taille / 2, taille, taille, couleur_du_type)

    if batiment_a_placer == "poste" and sourisDansRectangle(ZONE_JEU_X, ZONE_JEU_Y, ZONE_JEU_LARGEUR, ZONE_JEU_HAUTEUR):
        pyxel.circb(pyxel.mouse_x, pyxel.mouse_y, int(PORTEE_POSTE_DE_DEFENSE * zoom), COULEUR["texte_discret"])
        
## Fin economie
        
## Lancement d'une partie
def territoireDepart(ligne_du_centre, colonne_du_centre, rayon):
    """Génère les cases d'un disque autour d'un centre (sans sortir de la carte).
    Entrée : la ligne et la colonne du centre, le rayon. Utilise LIGNES et COLLONNES.
    Sortie : les cases du disque, une par une, chacune sous la forme (ligne, colonne) (générateur)."""
    for ligne in range(max(0, ligne_du_centre - rayon), min(LIGNES, ligne_du_centre + rayon + 1)):  # on parcourt le carré autour du centre (limité à la carte)...
        for colonne in range(max(0, colonne_du_centre - rayon), min(COLLONNES, colonne_du_centre + rayon + 1)):
            if (ligne - ligne_du_centre) ** 2 + (colonne - colonne_du_centre) ** 2 <= rayon ** 2:  # ...et on ne garde que celles dans le cercle (équation d'un cercle)
                yield ligne, colonne  # yield : on donne la case puis on continue (c'est ce qui fait de la fonction un générateur)


def choisirPositionDepart(entites, generateur_aleatoire):
    """Place chaque entité sur de l'herbe, assez loin des autres (la distance exigée diminue si c'est trop dur).
    Entrée : la liste des entités à placer, le générateur aléatoire. Utilise terrain, RAYON_DE_DEPART et ESPACEMENT_RELATIF.
    Sortie : la liste des centres de départ, un par entité, chacun sous la forme (ligne, colonne)."""
    cases_d_herbe = [(ligne, colonne) for ligne in range(LIGNES) for colonne in range(COLLONNES)  # toutes les cases d'herbe : les seuls endroits de départ autorisés
                     if terrain[ligne][colonne] == 0]
    if not cases_d_herbe:  # carte sans herbe : impossible de placer quelqu'un
        raise ValueError("aucune case d'herbe pour placer les entités")
    cases_conquerables = sum(1 for ligne in range(LIGNES) for colonne in range(COLLONNES)  # nombre total de cases qui ne sont pas de la mer
                             if estConquerable(ligne, colonne))
    distance_minimale = ESPACEMENT_RELATIF * (cases_conquerables / len(entites)) ** 0.5  # espace "naturel" d'une entité = racine de la surface qui lui revient, réduit par ESPACEMENT_RELATIF

    centres = []  # centres déjà choisis
    echecs_de_suite = 0  # nombre d'essais ratés d'affilée
    while len(centres) < len(entites):  # on continue jusqu'à avoir un centre par entité
        ligne, colonne = generateur_aleatoire.choice(cases_d_herbe)  # on tire un point au hasard, puis on vérifie s'il convient
        assez_loin_des_autres = all(  # vrai si la distance à chaque centre déjà choisi est suffisante
            (ligne - autre_ligne) ** 2 + (colonne - autre_colonne) ** 2 >= distance_minimale ** 2  # on compare les distances au carré (évite une racine)
            for autre_ligne, autre_colonne in centres)
        cases_du_disque_sur_la_terre = [case for case in territoireDepart(ligne, colonne, RAYON_DE_DEPART)  # cases du futur territoire qui ne sont pas de la mer
                                        if estConquerable(case[0], case[1])]
        disque_assez_plein = len(cases_du_disque_sur_la_terre) >= 0.8 * 3 * RAYON_DE_DEPART ** 2  # au moins 80 % du disque doit être sur la terre (3 ≈ π, donc 3 × rayon² ≈ aire du disque)
        if assez_loin_des_autres and disque_assez_plein:  # le point convient
            centres.append((ligne, colonne))
            echecs_de_suite = 0  # on repart à zéro
        else:
            echecs_de_suite += 1  # un échec de plus
            if echecs_de_suite > 3000:         # trop dur : on relâche la contrainte de distance
                distance_minimale *= 0.9  # on accepte des départs un peu plus proches (-10 %)
                echecs_de_suite = 0

    return centres


def placerLesEntites(entites, generateur_aleatoire):
    """Donne à chaque entité son territoire de départ (un disque) sur la grille des propriétaires.
    Entrée : la liste des entités, le générateur aléatoire. Utilise grille et RAYON_DE_DEPART.
    Sortie : la liste des centres de départ, dans l'ordre des entités (ligne, colonne) ; la grille est modifiée."""
    positions = choisirPositionDepart(entites, generateur_aleatoire)  # un centre par entité
    for entite, (ligne_du_centre, colonne_du_centre) in zip(entites, positions):  # la i-ème entité reçoit la i-ème position
        for ligne, colonne in territoireDepart(ligne_du_centre, colonne_du_centre, RAYON_DE_DEPART):  # chaque case de son disque
            if estConquerable(ligne, colonne) and grille[ligne][colonne] == 0:  # pas de mer, et on n'écrase pas un voisin
                grille[ligne][colonne] = entite  # la case devient à l'entité
    return positions


def lancerPartie(reglages):
    """Prépare une nouvelle partie : génère la carte, place le joueur et les tribus, remet à zéro l'état du jeu et centre la caméra sur le joueur.
    Entrée : le dictionnaire de réglages de la partie (graine, tribus, troupes de départ, difficulté, paramètres de carte).
    Utilise LIGNES, COLLONNES, DIFFICULTES et toutes les variables d'état du jeu.
    Sortie : rien, l'état du jeu, la grille, le terrain et l'image de la carte sont modifiés."""
    global terrain, grille, attaques, nb_case, frontiere, troupes, prochain_coup_bot, difficulte_en_cours, total_cases_conquerables, \
        resultat_de_la_partie, message_de_fin, part_maximale_de_territoire, adversaires_au_depart, numero_d_etape, argent, batiments, batiment_a_placer  # global : on modifie les variables du jeu, pas des copies locales
    resultat_de_la_partie = None  # la partie n'est pas finie
    message_de_fin = ""  # pas de message
    part_maximale_de_territoire = 0.0  # on repart sans record
    numero_d_etape = 0                  # le compteur d'étapes sert à mesurer la durée

    graine = reglages["graine"] if reglages["graine"] is not None else randrange(10 ** 9)  # graine de la carte : celle choisie, sinon une au hasard
    terrain = genererTerrain(LIGNES, COLLONNES, graine, reglages)  # on génère la carte (reglages contient aussi les paramètres de carte)
    total_cases_conquerables = sum(1 for ligne in terrain for code in ligne if code in TERRAINS_CONQUERABLE)  # nombre de cases qui ne sont pas de la mer : sert de 100 % pour les pourcentages de territoire
    grille = [[0] * COLLONNES for _ in range(LIGNES)]  # grille des propriétaires vide : personne ne possède rien

    nombre_de_tribus = borner(reglages["nombre_de_tribus"], 0, N - PREMIERE_TRIBU + 1)  # jamais plus de tribus que de couleurs prévues
    tribus = list(range(PREMIERE_TRIBU, PREMIERE_TRIBU + nombre_de_tribus))  # numéros des tribus de cette partie
    centres = placerLesEntites([JOUEUR_ACTUEL] + tribus, Random(reglages["graine"]))  # le joueur est placé en premier : centres[0] est sa position

    adversaires_au_depart = nombre_de_tribus  # sert aux statistiques de fin

    difficulte_en_cours = DIFFICULTES[reglages["difficulte"]]  # on retient la difficulté choisie

    attaques = []  # aucune attaque en cours
    nb_case = {j: 0 for j in range(N + 1)}  # de 0 à N : la clé 0 compte les cases sans propriétaire
    frontiere = {j: set() for j in range(1, N + 1)}  # un ensemble de frontière vide par entité
    troupes_de_depart = reglages["troupes_de_depart"]  # troupes de départ choisies
    troupes = {j: troupes_de_depart for j in range(1, N + 1)}  # toutes les entités démarrent avec ce nombre...
    for j in range(PREMIERE_TRIBU, N + 1):
        troupes[j] = int(troupes_de_depart * difficulte_en_cours["depart"])  # depend de la difficulté choisit
    prochain_coup_bot = {j: randint(10, 50) for j in range(PREMIERE_TRIBU, N + 1)}  # premier tour des bots décalé au hasard, pour qu'ils ne jouent pas tous en même temps
    
    argent = {j: 0 for j in range(1, N + 1)}
    batiments = []
    batiment_a_placer = None
    
    initFrontiere()  # calcule les frontières de départ
    compteCase()  # compte les cases de chacun
    reddessinerTout()  # dessine la carte complète

    ligne_du_joueur, colonne_du_joueur = centres[0]  # position de départ du joueur
    centrerSurCase(ligne_du_joueur, colonne_du_joueur, 8)  # la caméra se place sur lui, zoom 8
## Fin du lancement d'une partie


## Outils d'interface (polices, texte, souris, boutons)
CHEMINS_DE_POLICE = [  # polices essayées dans l'ordre : la première trouvée est utilisée
    "police.ttf",  # une police placée à côté du jeu
    "C:/Windows/Fonts/segoeuib.ttf",  # Segoe UI gras (Windows)
    "C:/Windows/Fonts/arialbd.ttf",  # Arial gras (Windows)
]
TAILLES_DE_POLICE = {"titre": 72, "titre_moyen": 44, "bouton": 28, "legende": 18, "petit": 16}  # nom de chaque style de texte -> sa taille en pixels


def chargerPolice(taille):
    """Charge la première police trouvée dans la liste des chemins possibles.
    Entrée : la taille de la police. Utilise CHEMINS_DE_POLICE.
    Sortie : la police Pyxel, ou None si aucun fichier de police n'existe."""
    for chemin in CHEMINS_DE_POLICE:  # on essaie chaque chemin
        if os.path.exists(chemin):  # le fichier existe
            return pyxel.Font(chemin, taille)  # on charge la police à la taille demandée
    return None  # aucune police trouvée : le jeu utilisera la police par défaut de Pyxel


POLICES = {nom: chargerPolice(taille) for nom, taille in TAILLES_DE_POLICE.items()}  # on charge une police par style de texte


def largeurDuTexte(texte, nom_police):
    """Calcule la largeur d'un texte à l'écran.
    Entrée : le texte, le nom de la police. Utilise POLICES.
    Sortie : la largeur en pixels (entier), estimée si la police n'existe pas."""
    police = POLICES[nom_police]  # la police du style demandé (ou None)
    return police.text_width(texte) if police else 4 * len(texte)  # sans police : on estime 4 pixels par lettre (police par défaut de Pyxel)


def ecrire(texte, x, y, nom_couleur, nom_police):
    """Écrit un texte à l'écran, son coin haut gauche en (x, y).
    Entrée : le texte, la position x et y, le nom de la couleur, le nom de la police. Utilise COULEUR et POLICES.
    Sortie : rien, le texte est dessiné."""
    pyxel.text(x, y, texte, COULEUR[nom_couleur], POLICES[nom_police])  # on convertit les noms en numéro de couleur et en police réelle


def ecrireCentre(texte, centre_x, y, nom_couleur, nom_police):
    """Écrit un texte centré horizontalement autour d'une position.
    Entrée : le texte, le x du centre, le y, le nom de la couleur, le nom de la police.
    Sortie : rien, le texte est dessiné."""
    ecrire(texte, centre_x - largeurDuTexte(texte, nom_police) // 2, y, nom_couleur, nom_police)  # on décale vers la gauche de la moitié de la largeur du texte


def ecrireADroite(texte, droite_x, y, nom_couleur, nom_police):
    """Écrit un texte aligné sur son bord droit.
    Entrée : le texte, le x du bord droit, le y, le nom de la couleur, le nom de la police.
    Sortie : rien, le texte est dessiné."""
    ecrire(texte, droite_x - largeurDuTexte(texte, nom_police), y, nom_couleur, nom_police)  # on décale vers la gauche de toute la largeur du texte


def sourisDansRectangle(x, y, largeur, hauteur):
    """Dit si la souris est dans un rectangle.
    Entrée : le x, le y, la largeur et la hauteur du rectangle. Utilise la position de la souris.
    Sortie : True si la souris est dedans, False sinon."""
    return x <= pyxel.mouse_x < x + largeur and y <= pyxel.mouse_y < y + hauteur  # la souris est entre les bords gauche/droit ET entre les bords haut/bas


def boutonClique(x, y, largeur, hauteur):
    """Dit si on vient de cliquer (clic gauche) dans un rectangle.
    Entrée : le x, le y, la largeur et la hauteur du rectangle.
    Sortie : True si le clic vient d'avoir lieu dedans, False sinon."""
    return pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and sourisDansRectangle(x, y, largeur, hauteur)  # btnp = vrai une seule image, au moment de l'appui (pas tant qu'on maintient)


def dessinerBouton(x, y, largeur, hauteur, texte, legende=None, principal=False):
    """Dessine un bouton (plus clair quand la souris le survole), avec un texte et éventuellement une légende en dessous.
    Entrée : le x, le y, la largeur, la hauteur, le texte, une légende (facultative), si c'est le bouton principal (mis en avant).
    Utilise COULEUR et TAILLES_DE_POLICE.
    Sortie : rien, le bouton est dessiné."""
    survole = sourisDansRectangle(x, y, largeur, hauteur)  # la souris est-elle sur le bouton ?
    if principal:  # bouton mis en avant : orange
        couleur_fond = "bouton_principal_survole" if survole else "bouton_principal"  # plus clair si survolé
        couleur_texte = "texte_sur_principal"  # texte foncé sur fond orange
    else:  # bouton normal
        couleur_fond = "bouton_survole" if survole else "bouton"
        couleur_texte = "texte"

    pyxel.rect(x, y, largeur, hauteur, COULEUR[couleur_fond])  # le fond du bouton
    pyxel.rectb(x, y, largeur, hauteur, COULEUR["bordure"])  # son contour
    if survole and not principal:
        pyxel.rect(x, y, 6, hauteur, COULEUR["bouton_principal"])      # barre d'accent à gauche

    taille_texte = TAILLES_DE_POLICE["bouton"]  # hauteur du texte, pour le placer
    centre_x = x + largeur // 2  # milieu du bouton, horizontalement
    if legende:  # avec légende : texte en haut, légende en dessous
        ecrireCentre(texte, centre_x, y + 10, couleur_texte, "bouton")  # le texte, à 10 pixels du haut
        couleur_legende = couleur_texte if (principal or survole) else "texte_discret"  # légende discrète, sauf si le bouton est mis en avant ou survolé
        ecrireCentre(legende, centre_x, y + 10 + taille_texte + 8, couleur_legende, "legende")  # sous le texte, avec 8 pixels d'écart
    else:  # sans légende : texte centré verticalement
        ecrireCentre(texte, centre_x, y + (hauteur - taille_texte) // 2 - 2, couleur_texte, "bouton")  # (hauteur - taille) / 2 centre le texte ; le -2 est un petit ajustement visuel


def dessinerEnTete(titre, sous_titre):
    """Dessine le grand titre d'un écran, avec un trait et un sous-titre en dessous.
    Entrée : le titre, le sous-titre. Utilise LARGEUR_ECRAN.
    Sortie : rien, l'en-tête est dessiné."""
    centre_x = LARGEUR_ECRAN // 2  # milieu de l'écran
    ecrireCentre(titre, centre_x, 130, "texte", "titre")  # le grand titre
    pyxel.rect(centre_x - 90, 225, 180, 4, COULEUR["bouton_principal"])  # un trait orange de 180 pixels sous le titre
    ecrireCentre(sous_titre, centre_x, 245, "texte_discret", "bouton")  # le sous-titre sous le trait
## Fin des outils d'interface


## Interface en jeu (barre du bas, curseur d'attaque, classement)
BARRE_Y = HAUTEUR_ECRAN - HAUTEUR_BARRE  # position verticale du haut de la barre du bas

TROUPES_X, TROUPES_LARGEUR = 24, 380  # position gauche et largeur de la zone "troupes" dans la barre
RECTANGLE_CURSEUR_ATTAQUE = (470, BARRE_Y + 70, 300, 10)  # (x, y, largeur, hauteur) de la glissière du curseur d'attaque
CLASSEMENT_LARGEUR, CLASSEMENT_HAUTEUR_LIGNE = 260, 28  # largeur du classement et hauteur d'une ligne
NOMBRE_DE_LIGNES_DU_CLASSEMENT = 5  # nombre d'entités affichées dans le top
RECTANGLE_CLASSEMENT = (LARGEUR_ECRAN - CLASSEMENT_LARGEUR - 12, 12, CLASSEMENT_LARGEUR,  # (x, y, largeur, hauteur) : collé en haut à droite avec 12 pixels de marge
                        44 + (NOMBRE_DE_LIGNES_DU_CLASSEMENT + 1) * CLASSEMENT_HAUTEUR_LIGNE)  # taille maximale : 44 pixels d'en-tête + top 5 + la ligne du joueur

ratio_attaque = 0.2  # part des troupes envoyée à chaque clic
curseur_attaque_saisi = False  # vrai tant qu'on garde le bouton enfoncé sur le curseur


def nomDeLEntite(entite):
    """Donne le nom affiché d'une entité.
    Entrée : le numéro de l'entité. Utilise JOUEUR_ACTUEL, PREMIERE_TRIBU et JOUEURS.
    Sortie : son nom, par exemple "Toi", "Nation 2" ou "Tribu 3" (texte)."""
    if entite == JOUEUR_ACTUEL:  # c'est le joueur humain
        return "Toi"
    if entite >= PREMIERE_TRIBU:  # c'est une tribu
        return f"Tribu {entite - PREMIERE_TRIBU + 1}"  # on recompte à partir de 1 pour l'affichage
    if entite > len(JOUEURS):  # c'est une nation (après les joueurs)
        return f"Nation {entite - len(JOUEURS)}"  # on retire les joueurs pour recompter à partir de 1
    return f"Joueur {entite}"  # sinon, un autre joueur


def formaterTroupes(valeur):
    """Met un nombre de troupes en forme pour l'affichage (divisé par 10, avec des espaces entre les milliers).
    Entrée : le nombre de troupes.
    Sortie : le nombre formaté, par exemple "25 000" (texte)."""
    return f"{int(valeur / 10):,}".replace(",", " ")  # divisé par 10 pour l'affichage ; le format anglais met des virgules entre les milliers, on les change en espaces


def formaterPourcentage(valeur):
    """Met un pourcentage en forme pour l'affichage (une décimale, virgule française).
    Entrée : le pourcentage (nombre).
    Sortie : le pourcentage formaté, par exemple "12,5 %" (texte)."""
    return f"{valeur:.1f} %".replace(".", ",")  # une décimale, puis le point devient une virgule


def pourcentageDeTerritoire(entite):
    """Calcule la part des terres conquérables que possède une entité.
    Entrée : le numéro de l'entité. Utilise nb_case et total_cases_conquerables.
    Sortie : le pourcentage de territoire (nombre décimal)."""
    return 100 * nb_case[entite] / total_cases_conquerables  # ses cases divisées par toutes les cases conquérables, en pourcentage


def classementDesEntites():
    """Classe les entités encore en vie, de la plus grande à la plus petite.
    Entrée : rien. Utilise nb_case.
    Sortie : la liste des numéros d'entités, la première étant celle qui a le plus de cases."""
    entites_en_vie = [entite for entite in range(1, N + 1) if nb_case[entite] > 0]  # une entité sans case est éliminée
    entites_en_vie.sort(key=lambda entite: nb_case[entite], reverse=True)  # tri par nombre de cases, du plus grand au plus petit
    return entites_en_vie


def dessinerBarreDeProgression(x, y, largeur, hauteur, part, nom_couleur):
    """Dessine une barre de progression remplie selon une part.
    Entrée : le x, le y, la largeur, la hauteur, la part remplie (entre 0 et 1), le nom de la couleur de remplissage.
    Sortie : rien, la barre est dessinée."""
    pyxel.rect(x, y, largeur, hauteur, COULEUR["fond"])  # le fond de la barre (vide)
    pyxel.rect(x, y, int(largeur * borner(part, 0, 1)), hauteur, COULEUR[nom_couleur])  # la partie remplie : largeur × part (part gardée entre 0 et 1)
    pyxel.rectb(x, y, largeur, hauteur, COULEUR["bordure"])  # le contour


def mettreAJourCurseurAttaque():
    """Gère le curseur qui règle la part de troupes envoyée à chaque attaque (glisser avec la souris).
    Entrée : rien. Utilise la souris et RECTANGLE_CURSEUR_ATTAQUE.
    Sortie : rien, ratio_attaque et curseur_attaque_saisi sont modifiés."""
    global ratio_attaque, curseur_attaque_saisi
    x, y, largeur, hauteur = RECTANGLE_CURSEUR_ATTAQUE  # position et taille de la glissière
    if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and sourisDansRectangle(x - 12, y - 18, largeur + 24, hauteur + 36):  # clic sur le curseur : la zone de saisie est plus large que la glissière, pour l'attraper facilement
        curseur_attaque_saisi = True  # on l'attrape
    if not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
        curseur_attaque_saisi = False  # bouton relâché : on lâche le curseur
    if curseur_attaque_saisi:  # tant qu'on le tient
        ratio_attaque = borner(round((pyxel.mouse_x - x) / largeur, 2), 0.01, 1.0)  # position de la souris sur la glissière convertie en part (0 à 1), arrondie à 2 décimales, entre 1 % et 100 %


def dessinerBarreDeJeu():
    """Dessine la barre du bas : troupes du joueur, curseur d'attaque, territoire et rang.
    Entrée : rien. Utilise troupes, ratio_attaque, le classement et les positions de la barre.
    Sortie : rien, la barre est dessinée."""
    pyxel.rect(0, BARRE_Y, LARGEUR_ECRAN, HAUTEUR_BARRE, COULEUR["panneau"])  # le fond de la barre
    pyxel.line(0, BARRE_Y, LARGEUR_ECRAN, BARRE_Y, COULEUR["bordure"])  # un trait en haut de la barre


    # --- troupes
    troupes_actuelles = troupes[JOUEUR_ACTUEL]  # troupes du joueur
    troupes_maximales = maxTroupe(JOUEUR_ACTUEL)  # son maximum
    ecrire("Troupes", TROUPES_X, BARRE_Y + 8, "texte_discret", "legende")  # le titre de la zone
    ecrire(f"{formaterTroupes(troupes_actuelles)} / {formaterTroupes(troupes_maximales)}",  # "actuelles / maximum"
           TROUPES_X, BARRE_Y + 28, "texte", "bouton")
    dessinerBarreDeProgression(TROUPES_X, BARRE_Y + 70, TROUPES_LARGEUR, 12,  # barre qui montre le remplissage des troupes
                               troupes_actuelles / troupes_maximales, "bouton_principal")  # part remplie = actuelles / maximum

    # --- curseur d'attaque
    x, y, largeur, hauteur = RECTANGLE_CURSEUR_ATTAQUE  # position et taille de la glissière
    troupes_envoyees = formaterTroupes(troupes_actuelles * ratio_attaque)  # nombre de troupes qui partiraient à l'attaque, formaté
    ecrire("Envoi par attaque", x, BARRE_Y + 8, "texte_discret", "legende")  # le titre de la zone
    ecrire(f"{round(ratio_attaque * 100)} %", x, BARRE_Y + 28, "texte", "bouton")  # la part choisie, en pourcentage
    ecrireADroite(f"≈ {troupes_envoyees} troupes", x + largeur, BARRE_Y + 34, "texte_discret", "legende")  # le nombre de troupes correspondant, aligné à droite de la glissière
    pyxel.rect(x, y, largeur, hauteur, COULEUR["fond"])  # fond de la glissière
    pyxel.rect(x, y, int(largeur * ratio_attaque), hauteur, COULEUR["bouton_survole"])  # partie remplie jusqu'à la part choisie
    pyxel.rectb(x, y, largeur, hauteur, COULEUR["bordure"])  # contour de la glissière
    poignee_x = x + int(largeur * ratio_attaque)  # la poignée suit la part choisie
    couleur_poignee = "bouton_principal_survole" if curseur_attaque_saisi else "bouton_principal"  # plus claire quand on la tient
    pyxel.rect(poignee_x - 5, y - 8, 10, hauteur + 16, COULEUR[couleur_poignee])  # la poignée : un rectangle de 10 pixels, centré sur la position

    # --- territoire et rang
    classement = classementDesEntites()  # classement actuel
    droite_x = LARGEUR_ECRAN - 24  # bord droit de la zone, avec 24 pixels de marge
    ecrireADroite("Territoire", droite_x, BARRE_Y + 8, "texte_discret", "legende")  # le titre de la zone
    ecrireADroite(formaterPourcentage(pourcentageDeTerritoire(JOUEUR_ACTUEL)), droite_x, BARRE_Y + 28, "texte", "bouton")  # le territoire du joueur, en %
    if JOUEUR_ACTUEL in classement:  # si le joueur est éliminé, il n'a plus de rang
        rang = classement.index(JOUEUR_ACTUEL) + 1  # position dans le classement (index commence à 0, donc +1)
        ecrireADroite(f"Rang {rang} sur {len(classement)}", droite_x, BARRE_Y + 68, "texte_discret", "petit")


def dessinerClassement():
    """Dessine le classement des meilleures entités en haut à droite (le joueur y figure toujours, même hors du top).
    Entrée : rien. Utilise le classement, nb_case et RECTANGLE_CLASSEMENT.
    Sortie : rien, le classement est dessiné."""
    x, y, largeur, hauteur = RECTANGLE_CLASSEMENT  # position et taille maximales du panneau (la hauteur n'est pas utilisée : on la recalcule)
    classement = classementDesEntites()  # toutes les entités en vie, classées
    lignes_a_afficher = classement[:NOMBRE_DE_LIGNES_DU_CLASSEMENT]  # on garde les 5 premières
    if JOUEUR_ACTUEL in classement and JOUEUR_ACTUEL not in lignes_a_afficher:  # le joueur est en vie mais hors du top
        lignes_a_afficher.append(JOUEUR_ACTUEL)                 # toi, même hors du top 5

    hauteur_utilisee = 44 + len(lignes_a_afficher) * CLASSEMENT_HAUTEUR_LIGNE  # le panneau s'adapte au nombre de lignes affichées (44 = en-tête)
    pyxel.rect(x, y, largeur, hauteur_utilisee, COULEUR["panneau"])  # fond du panneau
    pyxel.rectb(x, y, largeur, hauteur_utilisee, COULEUR["bordure"])  # contour du panneau
    ecrire("Classement", x + 14, y + 10, "texte_discret", "legende")  # titre du panneau

    for numero, entite in enumerate(lignes_a_afficher):  # une ligne par entité affichée
        ligne_y = y + 38 + numero * CLASSEMENT_HAUTEUR_LIGNE  # position verticale de la ligne (sous l'en-tête, une hauteur de ligne par entité)
        if entite == JOUEUR_ACTUEL:
            pyxel.rect(x + 4, ligne_y - 3, largeur - 8, CLASSEMENT_HAUTEUR_LIGNE - 2, COULEUR["bouton"])  # surligne la ligne du joueur
        rang = classement.index(entite) + 1  # le vrai rang, pas la position dans la liste affichée (le joueur peut être 12e)
        ecrire(str(rang), x + 14, ligne_y, "texte_discret", "petit")  # le rang
        pyxel.rect(x + 40, ligne_y + 1, 14, 14, ID_COULEUR_ENTITES[entite]["remplissage"])  # un carré de la couleur de l'entité
        ecrire(nomDeLEntite(entite), x + 64, ligne_y, "texte", "petit")  # son nom
        ecrireADroite(formaterPourcentage(pourcentageDeTerritoire(entite)), x + largeur - 14, ligne_y, "texte", "petit")  # son territoire, aligné à droite


def dessinerInterfaceDeJeu():
    """Dessine toute l'interface par-dessus la carte : la barre du bas et le classement.
    Entrée : rien.
    Sortie : rien, l'interface est dessinée."""
    dessinerBarreDeJeu()  # la barre du bas
    dessinerClassement()  # le classement en haut à droite
    dessinerPanneauDeConstruction()  # or et boutons de construction
    dessinerPanneauDesAttaques()  # qui attaque qui
    dessinerInfobulleDeSurvol()  # nom et troupes de la case survolée

## Fin de l'interface en jeu


## Interface des menus (menu, réglages, aperçu de la carte)
BOUTON_LARGEUR, BOUTON_HAUTEUR = 420, 84  # taille des gros boutons du menu
BOUTON_X = LARGEUR_ECRAN // 2 - BOUTON_LARGEUR // 2  # x du bouton pour qu'il soit centré
ESPACE_ENTRE_BOUTONS = 20  # écart vertical entre deux boutons
BOUTON_PARTIE_RAPIDE_Y = 330  # y du premier bouton
BOUTON_PARTIE_PERSONNALISEE_Y = BOUTON_PARTIE_RAPIDE_Y + BOUTON_HAUTEUR + ESPACE_ENTRE_BOUTONS  # le deuxième se place sous le premier
BOUTON_QUITTER_Y = BOUTON_PARTIE_PERSONNALISEE_Y + BOUTON_HAUTEUR + ESPACE_ENTRE_BOUTONS  # le troisième sous le deuxième
BOUTON_QUITTER_HAUTEUR = 56  # le bouton Quitter est plus petit

CONSEILS_DE_JEU = "Molette : zoom     Clic droit : déplacer     C : vue d'ensemble     Échap : quitter"  # texte d'aide affiché en bas du menu

POIDS_D_OCTAVE = [0.0, 0.125, 0.25, 0.5, 0.75, 1.0]  # valeurs proposées pour le poids d'une octave
OPTIONS_PAR_ONGLET = {  # pour chaque onglet, la liste des réglages : (texte affiché, clé dans les réglages, valeurs possibles)
    "Partie": [
        ("Tribus", "nombre_de_tribus", list(range(0, 11))),  # de 0 à 10 tribus
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
        ("Carte n°", "graine", [None] + list(range(1, 13))),  # None = carte aléatoire, sinon une des 12 cartes numérotées
    ],
}
ONGLETS = ["Partie", "Carte"]  # noms des onglets, dans l'ordre d'affichage
onglet_actuel = "Partie"  # onglet affiché en ce moment

LISTE_X, LISTE_LARGEUR, LISTE_Y = 60, 660, 130  # position gauche, largeur et position haute de la liste des réglages
LIGNE_HAUTEUR = 58  # hauteur d'une ligne de réglage
FLECHE_TAILLE, VALEUR_LARGEUR = 46, 180  # taille (carrée) d'une flèche et largeur de la zone de valeur
SELECTEUR_X = LISTE_X + LISTE_LARGEUR - (2 * FLECHE_TAILLE + VALEUR_LARGEUR)  # le sélecteur (flèche, valeur, flèche) est collé au bord droit de la liste

ONGLET_LARGEUR, ONGLET_HAUTEUR, ONGLET_Y = 150, 48, 22  # taille des onglets et leur position verticale
ONGLET_PREMIER_X = 560  # position gauche du premier onglet
APERCU_TAILLE, APERCU_ECHELLE = 125, 3  # l'aperçu fait 125 cases de côté, affiché 3 fois plus grand
APERCU_X, APERCU_Y = 790, 130  # position de l'aperçu
BOUTON_NOUVEL_APERCU = (APERCU_X, APERCU_Y + APERCU_TAILLE * APERCU_ECHELLE + 20, APERCU_TAILLE * APERCU_ECHELLE, 56)  # (x, y, largeur, hauteur) : sous l'aperçu, de la même largeur
BOUTON_RETOUR = (60, 720, 220, 56)  # (x, y, largeur, hauteur) du bouton Retour
BOUTON_LANCER = (LARGEUR_ECRAN - 60 - 380, 720, 380, 56)  # collé à droite, avec 60 pixels de marge

image_apercu = pyxel.Image(APERCU_TAILLE, APERCU_TAILLE)  # image de l'aperçu (1 pixel = 1 case de l'aperçu)
graine_apercu_aleatoire = randrange(10 ** 9)  # graine tirée au hasard, utilisée quand "Carte n°" est sur Aléatoire
apercu_a_refaire = True  # vrai dès qu'un réglage change : l'aperçu doit être régénéré


def graineDeLApercu():
    """Donne la graine à utiliser pour l'aperçu de la carte (celle choisie dans les réglages, sinon une graine aléatoire).
    Entrée : rien. Utilise reglages_en_cours et graine_apercu_aleatoire.
    Sortie : la graine (entier)."""
    graine_choisie = reglages_en_cours["graine"]  # la carte choisie dans les réglages (ou None)
    return graine_choisie if graine_choisie is not None else graine_apercu_aleatoire  # la même graine sert à l'aperçu et à la vraie partie : ce qu'on voit est ce qu'on joue


def actualiserApercu():
    """Régénère l'aperçu réduit de la carte à partir des réglages en cours.
    Entrée : rien. Utilise reglages_en_cours, APERCU_TAILLE et image_apercu.
    Sortie : rien, image_apercu est modifiée et apercu_a_refaire repasse à False."""
    global apercu_a_refaire
    terrain_apercu = genererTerrain(APERCU_TAILLE, APERCU_TAILLE, graineDeLApercu(), reglages_en_cours)  # on génère une petite carte avec les réglages actuels
    for ligne in range(APERCU_TAILLE):  # chaque ligne de l'aperçu
        for colonne in range(APERCU_TAILLE):  # chaque colonne
            image_apercu.pset(colonne, ligne, terrain_apercu[ligne][colonne])   # 0 à 3 = les 4 couleurs de terrain
    apercu_a_refaire = False  # l'aperçu est à jour


def ligneY(numero_de_ligne):
    """Calcule la position verticale d'une ligne de la liste des réglages.
    Entrée : le numéro de la ligne. Utilise LISTE_Y et LIGNE_HAUTEUR.
    Sortie : le y de la ligne en pixels (entier)."""
    return LISTE_Y + numero_de_ligne * LIGNE_HAUTEUR  # position de départ + une hauteur de ligne par ligne précédente


def rectanglesDuSelecteur(numero_de_ligne):
    """Calcule les rectangles des deux flèches (gauche et droite) d'une ligne de réglage.
    Entrée : le numéro de la ligne. Utilise SELECTEUR_X, FLECHE_TAILLE et VALEUR_LARGEUR.
    Sortie : deux rectangles (x, y, largeur, hauteur) : la flèche gauche, puis la flèche droite."""
    y = ligneY(numero_de_ligne)  # hauteur de la ligne
    fleche_gauche = (SELECTEUR_X, y, FLECHE_TAILLE, FLECHE_TAILLE)  # la flèche gauche est tout à gauche du sélecteur
    fleche_droite = (SELECTEUR_X + FLECHE_TAILLE + VALEUR_LARGEUR, y, FLECHE_TAILLE, FLECHE_TAILLE)  # la zone de valeur est entre les deux flèches, donc la flèche droite est après elle
    return fleche_gauche, fleche_droite


def rectangleDeLOnglet(numero_d_onglet):
    """Calcule le rectangle d'un onglet des réglages.
    Entrée : le numéro de l'onglet. Utilise les constantes ONGLET_*.
    Sortie : un rectangle (x, y, largeur, hauteur)."""
    return (ONGLET_PREMIER_X + numero_d_onglet * (ONGLET_LARGEUR + 10), ONGLET_Y, ONGLET_LARGEUR, ONGLET_HAUTEUR)  # chaque onglet est décalé d'une largeur d'onglet + 10 pixels d'écart


def texteDeLaValeur(cle, valeur):
    """Met la valeur d'un réglage en forme pour l'affichage.
    Entrée : la clé du réglage, sa valeur.
    Sortie : le texte à afficher ("Aléatoire" si pas de valeur, troupes divisées par 10 avec espaces, sinon la valeur simple)."""
    if valeur is None:  # None = pas de carte choisie
        return "Aléatoire"
    if cle == "troupes_de_depart":
        return f"{valeur // 10:,}".replace(",", " ")  # même affichage que formaterTroupes (divisé par 10, espaces entre les milliers)
    if isinstance(valeur, float):
        return f"{valeur:g}"  # enlève les zéros inutiles : 0.30 devient 0.3
    return str(valeur)  # entiers et textes : tels quels
## Fin de l'interface des menus


## Infobulle

NOMS_DES_TERRAINS = ["Herbe", "Terre", "Montagne", "Mer"]  # dans l'ordre des numéros de terrain


def sourisSurUnPanneau():
    """Dit si la souris est sur un panneau d'interface (pour que les clics et l'infobulle l'ignorent).
    Entrée : rien.
    Sortie : True si la souris est sur le classement, la construction ou les attaques."""
    rectangle_des_attaques = rectangleDesAttaques()
    return (sourisDansRectangle(*RECTANGLE_CLASSEMENT) or sourisDansRectangle(*RECTANGLE_CONSTRUCTION)
            or (rectangle_des_attaques is not None and sourisDansRectangle(*rectangle_des_attaques)))


def dessinerInfobulleDeSurvol():
    """Dessine près de la souris une infobulle sur la case survolée : propriétaire, troupes, territoire, terrain, bâtiment.
    Entrée : rien. Utilise la case sous la souris, grille, terrain, troupes et batiments.
    Sortie : rien, l'infobulle est dessinée (rien si la souris n'est pas sur la carte)."""
    if resultat_de_la_partie is not None or sourisSurUnPanneau():
        return
    case = caseSousCurseur()
    if case is None:
        return
    ligne, colonne = case
    proprietaire = grille[ligne][colonne]
    type_de_terrain = terrain[ligne][colonne]

    if proprietaire == 0:  # personne ne possède la case
        lignes = ["Mer" if type_de_terrain == 3 else "Terre libre"]
        if type_de_terrain != 3:
            lignes.append(NOMS_DES_TERRAINS[type_de_terrain])
        couleur_de_la_pastille = type_de_terrain  # la couleur du terrain a le même numéro dans la palette
    else:
        lignes = [nomDeLEntite(proprietaire),
                  f"Troupes : {formaterTroupes(troupes[proprietaire])}",
                  f"Territoire : {formaterPourcentage(pourcentageDeTerritoire(proprietaire))}",
                  NOMS_DES_TERRAINS[type_de_terrain]]
        couleur_de_la_pastille = ID_COULEUR_ENTITES[proprietaire]["remplissage"]
    batiment = batimentSurLaCase(ligne, colonne)
    if batiment is not None:
        lignes.append("Ville" if batiment["type"] == "ville" else "Poste de défense")

    largeur = max(largeurDuTexte(texte, "petit") for texte in lignes) + 52
    hauteur = 16 + len(lignes) * 22
    x, y = pyxel.mouse_x + 18, pyxel.mouse_y + 18  # à droite et sous le curseur
    if x + largeur > LARGEUR_ECRAN - 8:  # déborde à droite : on la met à gauche du curseur
        x = pyxel.mouse_x - 18 - largeur
    if y + hauteur > BARRE_Y - 8:  # déborde sur la barre du bas : on la met au-dessus du curseur
        y = pyxel.mouse_y - 18 - hauteur
    pyxel.rect(x, y, largeur, hauteur, COULEUR["panneau"])
    pyxel.rectb(x, y, largeur, hauteur, COULEUR["bordure"])
    pyxel.rect(x + 12, y + 11, 14, 14, couleur_de_la_pastille)
    for numero, texte in enumerate(lignes):
        ecrire(texte, x + 36, y + 10 + numero * 22, "texte" if numero == 0 else "texte_discret", "petit")
## Fin infobulle

##Interface en jeu

NOMBRE_MAX_DE_LIGNES_PAR_SECTION = 5  # lignes affichées par section avant "+ n autres"
ATTAQUES_X, ATTAQUES_Y, ATTAQUES_LARGEUR = 12, 286, 250  # sous le panneau de construction
ATTAQUES_HAUTEUR_TITRE, ATTAQUES_HAUTEUR_LIGNE = 30, 26


def attaquesAffichees():
    """Sépare les attaques qui concernent le joueur, de la plus grosse à la plus petite.
    Entrée : rien. Utilise la liste attaques.
    Sortie : deux listes : les attaques lancées par le joueur, puis celles qu'il subit."""
    sortantes = sorted((a for a in attaques if a["attaquant"] == JOUEUR_ACTUEL), key=lambda a: a["troupes"], reverse=True)
    entrantes = sorted((a for a in attaques if a["cible"] == JOUEUR_ACTUEL), key=lambda a: a["troupes"], reverse=True)
    return sortantes, entrantes


def nombreDeLignesDeLaSection(section):
    """Nombre de lignes dessinées pour une section (les lignes affichées, plus une ligne "+ n autres" si besoin)."""
    return min(len(section), NOMBRE_MAX_DE_LIGNES_PAR_SECTION) + (1 if len(section) > NOMBRE_MAX_DE_LIGNES_PAR_SECTION else 0)


def rectangleDesAttaques():
    """Calcule la position et la taille actuelles du panneau des attaques.
    Entrée : rien.
    Sortie : un rectangle (x, y, largeur, hauteur), ou None s'il n'y a aucune attaque à afficher."""
    sortantes, entrantes = attaquesAffichees()
    hauteur = 14  # marges haut et bas
    for section in (sortantes, entrantes):
        if section:
            hauteur += ATTAQUES_HAUTEUR_TITRE + nombreDeLignesDeLaSection(section) * ATTAQUES_HAUTEUR_LIGNE
    if hauteur == 14:  # aucune section : pas de panneau
        return None
    return (ATTAQUES_X, ATTAQUES_Y, ATTAQUES_LARGEUR, hauteur)


def dessinerSectionDAttaques(x, y, largeur, titre, couleur_du_titre, section, cote):
    """Dessine une section du panneau (titre, puis une ligne par attaque).
    Entrée : la position x, y, la largeur, le titre, sa couleur (nom), la liste d'attaques, et le côté à afficher
    ("attaquant" pour les attaques subies, "cible" pour celles qu'on lance).
    Sortie : la position y où la section suivante peut commencer."""
    ecrire(titre, x + 14, y, couleur_du_titre, "legende")
    y += ATTAQUES_HAUTEUR_TITRE
    for attaque in section[:NOMBRE_MAX_DE_LIGNES_PAR_SECTION]:
        entite = attaque[cote]  # l'adversaire de cette ligne
        if entite == 0:  # 0 = terrain libre
            nom, couleur_de_la_pastille = "Terre libre", 0  # la couleur 0 de la palette est celle de l'herbe
        else:
            nom, couleur_de_la_pastille = nomDeLEntite(entite), ID_COULEUR_ENTITES[entite]["remplissage"]
        pyxel.rect(x + 14, y + 2, 14, 14, couleur_de_la_pastille)  # un carré à la couleur de l'adversaire
        ecrire(nom, x + 36, y, "texte", "petit")
        ecrireADroite(formaterTroupes(attaque["troupes"]), x + largeur - 14, y, "texte", "petit")  # troupes engagées dans cette attaque
        y += ATTAQUES_HAUTEUR_LIGNE
    nombre_cache = len(section) - NOMBRE_MAX_DE_LIGNES_PAR_SECTION
    if nombre_cache > 0:
        ecrire(f"+ {nombre_cache} autres", x + 36, y, "texte_discret", "petit")
        y += ATTAQUES_HAUTEUR_LIGNE
    return y


def dessinerPanneauDesAttaques():
    """Dessine le panneau des attaques en cours qui concernent le joueur (rien s'il n'y en a pas).
    Entrée : rien.
    Sortie : rien, le panneau est dessiné."""
    rectangle = rectangleDesAttaques()
    if rectangle is None:
        return
    x, y, largeur, hauteur = rectangle
    pyxel.rect(x, y, largeur, hauteur, COULEUR["panneau"])
    pyxel.rectb(x, y, largeur, hauteur, COULEUR["bordure"])
    sortantes, entrantes = attaquesAffichees()
    curseur_y = y + 8
    if entrantes:
        curseur_y = dessinerSectionDAttaques(x, curseur_y, largeur, "Attaques subies", "rouge", entrantes, "attaquant")
    if sortantes:
        curseur_y = dessinerSectionDAttaques(x, curseur_y, largeur, "Tu attaques", "texte_discret", sortantes, "cible")
        
## Fin interface en jeu
## Écrans (menu, réglages, fin de partie)
ecran_actuel = "menu"  # écran affiché : "menu", "reglages", "jeu" ou "fin"
reglages_en_cours = dict(REGLAGES_PAR_DEFAUT)  # copie : modifier les réglages ne touche pas aux valeurs par défaut

PANNEAU_FIN_X, PANNEAU_FIN_Y, PANNEAU_FIN_LARGEUR, PANNEAU_FIN_HAUTEUR = 300, 130, 600, 560  # position et taille du panneau de fin
BOUTON_REJOUER = (LARGEUR_ECRAN // 2 - 240, 590, 230, 60)  # (x, y, largeur, hauteur) : à gauche du milieu de l'écran
BOUTON_RETOUR_AU_MENU = (LARGEUR_ECRAN // 2 + 10, 590, 230, 60)  # à droite du milieu de l'écran


def updateMenu():
    """Gère les clics du menu principal : partie rapide, partie personnalisée, quitter.
    Entrée : rien. Utilise la souris et les rectangles des boutons.
    Sortie : rien, peut lancer une partie, changer d'écran ou fermer le jeu."""
    global ecran_actuel
    if boutonClique(BOUTON_X, BOUTON_PARTIE_RAPIDE_Y, BOUTON_LARGEUR, BOUTON_HAUTEUR):  # clic sur "Partie rapide"
        commencerPartie({**REGLAGES_PAR_DEFAUT, "graine": None})  # réglages par défaut, mais carte aléatoire
    if boutonClique(BOUTON_X, BOUTON_PARTIE_PERSONNALISEE_Y, BOUTON_LARGEUR, BOUTON_HAUTEUR):  # clic sur "Partie personnalisée"
        ecran_actuel = "reglages"  # on passe à l'écran de réglages
    if boutonClique(BOUTON_X, BOUTON_QUITTER_Y, BOUTON_LARGEUR, BOUTON_QUITTER_HAUTEUR):  # clic sur "Quitter"
        pyxel.quit()  # on ferme le jeu


def drawMenu():
    """Dessine le menu principal : titre, boutons et conseils de jeu.
    Entrée : rien. Utilise les positions des boutons et CONSEILS_DE_JEU.
    Sortie : rien, l'écran est dessiné."""
    pyxel.cls(COULEUR["fond"])  # on efface l'écran avec la couleur de fond
    dessinerEnTete("OPENFRONT", "Conquiers le territoire")  # titre et sous-titre

    panneau_x, panneau_y = BOUTON_X - 30, BOUTON_PARTIE_RAPIDE_Y - 30  # le panneau entoure les trois boutons avec 30 pixels de marge : coin haut gauche
    panneau_largeur = BOUTON_LARGEUR + 60  # largeur d'un bouton + 30 de chaque côté
    panneau_hauteur = (BOUTON_QUITTER_Y + BOUTON_QUITTER_HAUTEUR + 30) - panneau_y  # du haut du panneau jusqu'à 30 pixels sous le dernier bouton
    pyxel.rect(panneau_x, panneau_y, panneau_largeur, panneau_hauteur, COULEUR["panneau"])  # fond du panneau
    pyxel.rectb(panneau_x, panneau_y, panneau_largeur, panneau_hauteur, COULEUR["bordure"])  # contour du panneau

    dessinerBouton(BOUTON_X, BOUTON_PARTIE_RAPIDE_Y, BOUTON_LARGEUR, BOUTON_HAUTEUR,
                   "Partie rapide", "Carte aléatoire, c'est parti", principal=True)  # le bouton principal, en orange
    dessinerBouton(BOUTON_X, BOUTON_PARTIE_PERSONNALISEE_Y, BOUTON_LARGEUR, BOUTON_HAUTEUR,
                   "Partie personnalisée", "Bots, troupes, carte")
    dessinerBouton(BOUTON_X, BOUTON_QUITTER_Y, BOUTON_LARGEUR, BOUTON_QUITTER_HAUTEUR, "Quitter")

    pyxel.line(80, HAUTEUR_ECRAN - 70, LARGEUR_ECRAN - 80, HAUTEUR_ECRAN - 70, COULEUR["bordure"])  # un trait au-dessus des conseils
    ecrireCentre(CONSEILS_DE_JEU, LARGEUR_ECRAN // 2, HAUTEUR_ECRAN - 52, "texte_discret", "petit")  # les conseils, centrés
    ecrire("v0.1", 16, HAUTEUR_ECRAN - 28, "texte_discret", "petit")  # numéro de version, en bas à gauche


def updateReglages():
    """Gère les clics de l'écran de réglages : onglets, flèches de chaque réglage, nouvel aperçu, retour, lancement de la partie.
    Entrée : rien. Utilise la souris, reglages_en_cours, OPTIONS_PAR_ONGLET et onglet_actuel.
    Sortie : rien, les réglages, l'onglet et l'aperçu sont modifiés (ou on change d'écran / on lance la partie)."""
    global ecran_actuel, onglet_actuel, graine_apercu_aleatoire, apercu_a_refaire

    for numero, nom_onglet in enumerate(ONGLETS):  # chaque onglet
        if boutonClique(*rectangleDeLOnglet(numero)):  # clic sur l'onglet
            onglet_actuel = nom_onglet  # on affiche cet onglet

    for numero, (libelle, cle, options) in enumerate(OPTIONS_PAR_ONGLET[onglet_actuel]):  # chaque réglage de l'onglet affiché
        fleche_gauche, fleche_droite = rectanglesDuSelecteur(numero)  # ses deux flèches
        position = options.index(reglages_en_cours[cle])  # place de la valeur actuelle dans la liste des options possibles
        nouvelle_position = position  # par défaut, on ne bouge pas
        if boutonClique(*fleche_gauche):
            nouvelle_position = max(0, position - 1)  # valeur précédente ; max / min : on s'arrête aux extrémités de la liste
        if boutonClique(*fleche_droite):
            nouvelle_position = min(len(options) - 1, position + 1)  # valeur suivante
        if nouvelle_position != position:  # une flèche a été cliquée
            reglages_en_cours[cle] = options[nouvelle_position]  # on applique la nouvelle valeur
            apercu_a_refaire = True  # un réglage a changé : l'aperçu n'est plus à jour

    if boutonClique(*BOUTON_NOUVEL_APERCU):  # clic sur "Nouvel aperçu"
        graine_apercu_aleatoire = randrange(10 ** 9)  # nouvelle graine aléatoire
        apercu_a_refaire = True
    if boutonClique(*BOUTON_RETOUR):  # clic sur "Retour"
        ecran_actuel = "menu"
        return  # on arrête là : on a quitté l'écran
    if boutonClique(*BOUTON_LANCER):  # clic sur "Lancer la partie"
        commencerPartie({**reglages_en_cours, "graine": graineDeLApercu()})  # on fige la graine de l'aperçu : la partie aura exactement la carte vue
        return
    if apercu_a_refaire:  # l'aperçu est périmé
        actualiserApercu()  # on le régénère


def drawReglages():
    """Dessine l'écran de réglages : onglets, liste des réglages avec leurs flèches, aperçu de la carte et boutons du bas.
    Entrée : rien. Utilise reglages_en_cours, onglet_actuel, OPTIONS_PAR_ONGLET et image_apercu.
    Sortie : rien, l'écran est dessiné."""
    pyxel.cls(COULEUR["fond"])  # on efface l'écran
    ecrire("RÉGLAGES", 60, 18, "texte", "titre_moyen")  # titre en haut à gauche
    for numero, nom_onglet in enumerate(ONGLETS):  # chaque onglet
        dessinerBouton(*rectangleDeLOnglet(numero), nom_onglet, principal=(nom_onglet == onglet_actuel))  # l'onglet actuel est mis en avant (orange)
    pyxel.line(40, 90, LARGEUR_ECRAN - 40, 90, COULEUR["bordure"])  # trait sous les onglets

    options_de_l_onglet = OPTIONS_PAR_ONGLET[onglet_actuel]  # réglages de l'onglet affiché
    panneau_hauteur = len(options_de_l_onglet) * LIGNE_HAUTEUR + 8  # le panneau s'adapte au nombre de réglages de l'onglet
    pyxel.rect(LISTE_X - 20, LISTE_Y - 14, LISTE_LARGEUR + 40, panneau_hauteur, COULEUR["panneau"])  # fond du panneau (débordant de 20 pixels autour de la liste)
    pyxel.rectb(LISTE_X - 20, LISTE_Y - 14, LISTE_LARGEUR + 40, panneau_hauteur, COULEUR["bordure"])  # contour du panneau
    decalage_texte = (FLECHE_TAILLE - TAILLES_DE_POLICE["bouton"]) // 2 - 2  # pour centrer verticalement le texte par rapport aux flèches
    for numero, (libelle, cle, options) in enumerate(options_de_l_onglet):  # chaque réglage
        y = ligneY(numero)  # hauteur de la ligne
        ecrire(libelle, LISTE_X, y + decalage_texte, "texte", "bouton")  # le nom du réglage, à gauche
        fleche_gauche, fleche_droite = rectanglesDuSelecteur(numero)  # ses flèches
        dessinerBouton(*fleche_gauche, "<")  # flèche gauche
        dessinerBouton(*fleche_droite, ">")  # flèche droite
        valeur_x = SELECTEUR_X + FLECHE_TAILLE  # la zone de valeur commence juste après la flèche gauche
        pyxel.rect(valeur_x, y, VALEUR_LARGEUR, FLECHE_TAILLE, COULEUR["fond"])  # fond de la zone de valeur
        pyxel.rectb(valeur_x, y, VALEUR_LARGEUR, FLECHE_TAILLE, COULEUR["bordure"])  # son contour
        ecrireCentre(texteDeLaValeur(cle, reglages_en_cours[cle]), valeur_x + VALEUR_LARGEUR // 2,  # la valeur actuelle, centrée dans sa zone
                     y + decalage_texte, "bouton_principal", "bouton")

    cote_apercu = APERCU_TAILLE * APERCU_ECHELLE  # côté de l'aperçu à l'écran, en pixels
    pyxel.rect(APERCU_X - 6, APERCU_Y - 6, cote_apercu + 12, cote_apercu + 12, COULEUR["panneau"])  # cadre derrière l'aperçu (6 pixels de marge)
    pyxel.rectb(APERCU_X - 6, APERCU_Y - 6, cote_apercu + 12, cote_apercu + 12, COULEUR["bordure"])  # contour du cadre
    pyxel.blt(APERCU_X + APERCU_TAILLE * (APERCU_ECHELLE - 1) / 2,  # scale agrandit autour du centre de l'image : ce décalage la remet à la bonne place
              APERCU_Y + APERCU_TAILLE * (APERCU_ECHELLE - 1) / 2,
              image_apercu, 0, 0, APERCU_TAILLE, APERCU_TAILLE, scale=APERCU_ECHELLE)  # on dessine l'aperçu agrandi
    dessinerBouton(*BOUTON_NOUVEL_APERCU, "Nouvel aperçu")  # bouton pour regénérer
    ecrire("Aperçu réduit de la vraie carte", APERCU_X, BOUTON_NOUVEL_APERCU[1] + 70, "texte_discret", "petit")  # légende sous le bouton

    pyxel.line(40, 700, LARGEUR_ECRAN - 40, 700, COULEUR["bordure"])  # trait au-dessus des boutons du bas
    dessinerBouton(*BOUTON_RETOUR, "Retour")  # bouton Retour
    dessinerBouton(*BOUTON_LANCER, "Lancer la partie", principal=True)  # bouton Lancer, en orange


def formaterDuree(secondes):
    """Met une durée en forme pour l'affichage.
    Entrée : la durée en secondes.
    Sortie : la durée sous la forme "minutes:secondes", par exemple "03:07" (texte)."""
    secondes = int(secondes)  # on enlève les décimales
    return f"{secondes // 60:02d}:{secondes % 60:02d}"  # minutes = division entière par 60, secondes = reste ; 02d ajoute un zéro devant si besoin


def updateFin():
    """Gère les clics de l'écran de fin : rejouer avec les mêmes réglages ou retourner au menu.
    Entrée : rien. Utilise la souris et derniers_reglages.
    Sortie : rien, peut relancer une partie ou changer d'écran."""
    global ecran_actuel
    if boutonClique(*BOUTON_REJOUER):  # clic sur "Rejouer"
        commencerPartie(derniers_reglages)  # nouvelle partie avec les mêmes réglages
    if boutonClique(*BOUTON_RETOUR_AU_MENU):  # clic sur "Menu"
        ecran_actuel = "menu"


def drawFin():
    """Dessine l'écran de fin : la partie figée en fond, puis le panneau victoire ou défaite avec les statistiques et les boutons.
    Entrée : rien. Utilise resultat_de_la_partie, message_de_fin, nb_case, numero_d_etape et part_maximale_de_territoire.
    Sortie : rien, l'écran est dessiné."""
    drawJeu()                                                   # la partie, figée, en arrière-plan
    centre_x = LARGEUR_ECRAN // 2  # milieu de l'écran
    pyxel.rect(PANNEAU_FIN_X, PANNEAU_FIN_Y, PANNEAU_FIN_LARGEUR, PANNEAU_FIN_HAUTEUR, COULEUR["panneau"])  # fond du panneau
    pyxel.rectb(PANNEAU_FIN_X, PANNEAU_FIN_Y, PANNEAU_FIN_LARGEUR, PANNEAU_FIN_HAUTEUR, COULEUR["bordure"])  # contour du panneau

    est_victoire = resultat_de_la_partie == "victoire"  # vrai si le joueur a gagné
    couleur_du_titre = "bouton_principal" if est_victoire else "rouge"  # orange pour une victoire, rouge pour une défaite
    ecrireCentre("VICTOIRE" if est_victoire else "DÉFAITE", centre_x, PANNEAU_FIN_Y + 30, couleur_du_titre, "titre")  # le grand titre
    pyxel.rect(centre_x - 90, PANNEAU_FIN_Y + 125, 180, 4, COULEUR[couleur_du_titre])  # trait de la même couleur sous le titre
    ecrireCentre(message_de_fin, centre_x, PANNEAU_FIN_Y + 150, "texte_discret", "legende")  # la phrase qui explique la fin

    adversaires_restants = len([e for e in range(1, N + 1) if e != JOUEUR_ACTUEL and nb_case[e] > 0])  # entités encore en vie, sans compter le joueur
    lignes = [  # les statistiques : (nom, valeur affichée)
        ("Durée", formaterDuree(numero_d_etape * VITESSE_ATTAQUE / IMAGES_PAR_SECONDE)),  # étapes × images par étape = images ; ÷ images par seconde = secondes
        ("Territoire maximal", formaterPourcentage(part_maximale_de_territoire)),  # le record du joueur
        ("Territoire final", formaterPourcentage(pourcentageDeTerritoire(JOUEUR_ACTUEL))),  # son territoire à la fin
        ("Adversaires restants", f"{adversaires_restants} sur {adversaires_au_depart}"),  # exemple : "3 sur 10"
    ]
    for numero, (libelle, valeur) in enumerate(lignes):  # une ligne par statistique
        ligne_y = PANNEAU_FIN_Y + 215 + numero * 56  # position verticale : sous le message, 56 pixels par ligne
        ecrire(libelle, PANNEAU_FIN_X + 50, ligne_y, "texte_discret", "bouton")  # le nom, à gauche
        ecrireADroite(valeur, PANNEAU_FIN_X + PANNEAU_FIN_LARGEUR - 50, ligne_y, "texte", "bouton")  # la valeur, alignée à droite
        pyxel.line(PANNEAU_FIN_X + 40, ligne_y + 40, PANNEAU_FIN_X + PANNEAU_FIN_LARGEUR - 40, ligne_y + 40, COULEUR["bordure"])  # un trait séparateur sous la ligne

    dessinerBouton(*BOUTON_REJOUER, "Rejouer", principal=True)  # bouton Rejouer, en orange
    dessinerBouton(*BOUTON_RETOUR_AU_MENU, "Menu")  # bouton Menu
## Fin des écrans


## Boucle de jeu
def commencerPartie(reglages):
    """Lance une partie avec des réglages, mémorise ces réglages (pour rejouer) et passe à l'écran de jeu.
    Entrée : le dictionnaire de réglages de la partie.
    Sortie : rien, derniers_reglages et ecran_actuel sont modifiés."""
    global ecran_actuel, derniers_reglages
    derniers_reglages = dict(reglages)  # copie, pour que "Rejouer" reprenne exactement les mêmes réglages
    lancerPartie(reglages)  # prépare la partie
    ecran_actuel = "jeu"  # on affiche le jeu


def updateJeu():
    """Fait avancer le jeu d'une image : caméra, curseur d'attaque, touches (C, Échap, V), clic, puis une étape de jeu à intervalle régulier.
    Entrée : rien. Utilise le clavier, la souris, pyxel.frame_count et VITESSE_ATTAQUE.
    Sortie : rien, l'état du jeu est modifié."""
    deplacerCamera()  # zoom et déplacement
    mettreAJourCurseurAttaque()  # curseur de la part de troupes
    mettreAJourConstruction()
    if pyxel.btnp(pyxel.KEY_C):  # touche C
        centrerCarte()  # vue d'ensemble de la carte
    if pyxel.btnp(pyxel.KEY_ESCAPE):  # touche Échap
        pyxel.quit()  # on ferme le jeu
    if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):  # clic gauche
        click()  # on traite le clic (attaque)
    if pyxel.btnp(pyxel.KEY_V):  # touche V
        print(verifierFrontiere())  # débogage : affiche True si les frontières sont cohérentes
    if pyxel.frame_count % VITESSE_ATTAQUE == 0:  # le combat n'avance qu'une image sur 3 (frame_count = numéro de l'image) : ça règle la vitesse du jeu
        etapeAttaque()  # les attaques avancent
        generationTroupe()  # les troupes augmentent
        tourBots()  # les bots décident
        generationDeLArgent()  # l'or augmente
        retirerLesBatimentsPerdus()  # un bâtiment dont la case a été conquise disparaît
        verifierFinDePartie()  # victoire ou défaite ?


def drawJeu():
    """Dessine la partie : la partie visible de la carte (zoomée) puis l'interface par-dessus.
    Entrée : rien. Utilise l'image carte, la caméra, le zoom et la zone de jeu.
    Sortie : rien, l'écran est dessiné (la carte est recentrée si rien n'est visible)."""
    pyxel.cls(COULEUR["fond"])  # on efface l'écran avec la couleur n°20 de la palette (le fond autour de la carte)
    colonne_debut = max(0, int(camera_colonne // 1))  # première colonne visible (jamais avant la colonne 0)
    colonne_fin = min(COLLONNES, int(-(-(camera_colonne + ZONE_JEU_LARGEUR/ zoom) // 1)))  # dernière colonne visible ; -(-a // 1) est une astuce pour arrondir vers le haut
    ligne_debut = max(0, int(camera_ligne // 1))  # première ligne visible
    ligne_fin = min(LIGNES, int(-(-(camera_ligne + ZONE_JEU_HAUTEUR / zoom) // 1)))  # dernière ligne visible (arrondie vers le haut)

    largeur_dessinee = colonne_fin - colonne_debut  # nombre de colonnes à dessiner
    hauteur_dessinee = ligne_fin - ligne_debut  # nombre de lignes à dessiner
    if largeur_dessinee <= 0 or hauteur_dessinee <= 0:  # la caméra a perdu la carte : on la recentre
        centrerCarte()
        return

    ecran_x_premiere_case = ZONE_JEU_X + (colonne_debut - camera_colonne) * zoom  # position à l'écran de la première case visible (décalage par rapport à la caméra, en pixels)
    ecran_y_premiere_case = ZONE_JEU_Y + (ligne_debut - camera_ligne) * zoom

    pyxel.clip(ZONE_JEU_X, ZONE_JEU_Y, ZONE_JEU_LARGEUR, ZONE_JEU_HAUTEUR)  # le dessin est limité à la zone de jeu (la carte ne déborde pas sur la barre)

    pyxel.blt(ecran_x_premiere_case + (largeur_dessinee * zoom - largeur_dessinee) / 2,  # scale agrandit autour du centre de l'image : on décale pour compenser et garder le coin au bon endroit
              ecran_y_premiere_case + (hauteur_dessinee * zoom - hauteur_dessinee) / 2,
              carte,  # l'image source : toute la carte, 1 pixel par case
              colonne_debut, ligne_debut,  # coin haut gauche du morceau à copier
              largeur_dessinee, hauteur_dessinee,  # taille du morceau à copier
              scale=zoom)  # agrandissement : chaque case devient un carré de "zoom" pixels
    dessinerBatiments()
    pyxel.clip()  # on enlève la limite pour pouvoir dessiner l'interface partout
    dessinerInterfaceDeJeu()  # barre du bas et classement


def verifierFinDePartie():
    """Vérifie si la partie est terminée (défaite si plus de territoire ou si un adversaire atteint le seuil, victoire si le joueur atteint le seuil ou reste seul), et suit son territoire maximal.
    Entrée : rien. Utilise nb_case, le classement, SEUIL_DE_VICTOIRE et adversaires_au_depart.
    Sortie : rien, resultat_de_la_partie, message_de_fin et part_maximale_de_territoire sont modifiés, et on passe à l'écran de fin si la partie est finie."""
    global ecran_actuel, resultat_de_la_partie, message_de_fin, part_maximale_de_territoire
    part_maximale_de_territoire = max(part_maximale_de_territoire, pourcentageDeTerritoire(JOUEUR_ACTUEL))  # garde le record du joueur, pour les stats de fin

    classement = classementDesEntites()  # classement actuel
    if nb_case[JOUEUR_ACTUEL] == 0:  # le joueur n'a plus de case
        resultat_de_la_partie = "defaite"
        message_de_fin = "Tu n'as plus aucun territoire."
    elif classement and pourcentageDeTerritoire(classement[0]) >= SEUIL_DE_VICTOIRE:  # classement[0] = le plus grand : a-t-il atteint le seuil ? (classement non vide)
        if classement[0] == JOUEUR_ACTUEL:  # c'est le joueur
            resultat_de_la_partie = "victoire"
            message_de_fin = f"Tu contrôles {formaterPourcentage(pourcentageDeTerritoire(JOUEUR_ACTUEL))} des terres."
        else:  # c'est quelqu'un d'autre
            resultat_de_la_partie = "defaite"
            message_de_fin = f"{nomDeLEntite(classement[0])} contrôle {SEUIL_DE_VICTOIRE} % des terres."
    elif adversaires_au_depart > 0 and classement == [JOUEUR_ACTUEL]:  # il y avait des adversaires et le joueur est le seul encore en vie
        resultat_de_la_partie = "victoire"
        message_de_fin = "Tous tes adversaires ont été éliminés."

    if resultat_de_la_partie is not None:  # un résultat a été trouvé
        ecran_actuel = "fin"  # on passe à l'écran de fin
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
    else:  # "jeu"
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
    else:  # "jeu"
        drawJeu()
## Fin de la boucle globale


pyxel.run(update, draw)  # lance le jeu : Pyxel appelle update() puis draw() à chaque image, jusqu'à la fermeture

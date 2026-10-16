import pyxel

LIGNES = 40
COLLONNES = 40
LARGEUR_ECRAN = 1600
HAUTEUR_ECRAN = 1200
TAILLE_CASE = 10


# --- NUANCES DE GRIS ---
pyxel.colors.append(0x1F1F1F)
pyxel.colors.append(0x404040)
pyxel.colors.append(0x737373)
pyxel.colors.append(0xB0B0B0)

# --- NUANCES DE MARRON ---
pyxel.colors.append(0x2B1810)
pyxel.colors.append(0x4A2E1B)
pyxel.colors.append(0x784F31)
pyxel.colors.append(0xA67A56)


pyxel.init(LARGEUR_ECRAN, HAUTEUR_ECRAN, title="OpenFront")

grille = [[0 for y in range(LIGNES)] for x in range(COLLONNES)]

grille[10][10] = 1
grille[30][30] = 2

def update():
    if pyxel.btnp(pyxel.KEY_ESCAPE):
        pyxel.quit()

def draw():
    pyxel.cls(0)
    for indice_ligne, ligne in enumerate(grille):
        for indice_collonnes, collonnes in enumerate(ligne):
            x = LARGEUR_ECRAN // 2 - (TAILLE_CASE * LIGNES) / 2 + indice_ligne * TAILLE_CASE
            y = HAUTEUR_ECRAN // 2 - (TAILLE_CASE * COLLONNES) / 2 + indice_collonnes * TAILLE_CASE
            
            pyxel.rect(
                x,
                y,
                TAILLE_CASE,
                TAILLE_CASE,
                11)

pyxel.run(update, draw)

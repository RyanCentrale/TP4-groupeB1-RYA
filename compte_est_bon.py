#! /usr/bin/env python3

"""
Ce programme prendra sur son entrée standard les 6 cartons tirés au sort suivis du nombre à
trouver. Par exemple, si les cartons tirés sont 3 5 7 9 25 50 et que le nombre à découvrir est
859, il devra être appelé ainsi : echo 3 5 7 9 25 50 859  | ./compte_est_bon.py

Argument optionnel : naif (parcours de l'énoncé), ameliore (parcours améliorés) ou tout (défaut).
Exemple : ./generer_probleme.py ardu | ./compte_est_bon.py ameliore
"""

from recherche_compte_est_bon import *
from recherche_amelioree import parcours_DFS_ameliore, parcours_BFS_ameliore, parcours_DFS_recursif_ameliore
from notation_polonaise_inverse import eval_NPI_liste
import sys
import time


def lire_stdin():
    """Lit l'entrée standard en invitant l'utilisateur à l'aide d'un message si le flux d'entrée n'est pas redirigé"""
    if sys.stdin.isatty():
        sys.stderr.write("Saisissez du texte (Ctrl+D pour terminer) :\n")
    return sys.stdin.read()


def lancer(nom, parcours, cartons, nombre):
    print(f"\n=== {nom}")
    debut = time.perf_counter()
    expression, nb_noeuds = parcours(cartons, nombre)
    fin = time.perf_counter()
    _, valeur = eval_NPI_liste(expression)
    print(f"Meilleure solution : {npi_vers_infixe(expression)} = {valeur}"
          f"  ({'le compte est bon' if valeur == nombre else f'écart {abs(valeur - nombre)}'})")
    print(f"Noeuds parcourus : {nb_noeuds} (valides {STATS['nb_valides']}, invalides {STATS['nb_invalides']})")
    print(f"Taille max {'de la file' if 'BFS' in nom else 'de la pile'} : {STATS['taille_max']}"
          f" | hauteur max : {STATS['hauteur_max']} | largeur max : {largeur_max()}")
    print(f"{nom} : {fin - debut:.6f} s")
    return valeur


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "tout"
    cartons_nombre = lire_stdin()
    *cartons, nombre = map(int, cartons_nombre.split())
    print(f"Recherche de {nombre} avec {cartons}")

    # Recherche rapide (silencieuse) pour savoir s'il existe une solution exacte
    exact = eval_NPI_liste(parcours_DFS_ameliore(cartons, nombre, verbeux=False)[0])[1] == nombre

    if mode in ("ameliore", "tout"):
        lancer("DFS amélioré", parcours_DFS_ameliore, cartons, nombre)
        lancer("DFS récursif amélioré", parcours_DFS_recursif_ameliore, cartons, nombre)
        lancer("BFS amélioré", parcours_BFS_ameliore, cartons, nombre)

    if mode in ("naif", "tout"):
        lancer("DFS", parcours_DFS, cartons, nombre)
        lancer("DFS récursif", parcours_DFS_recursif, cartons, nombre)
        if exact or "--forcer" in sys.argv:
            lancer("BFS", parcours_BFS, cartons, nombre)
        else:
            # Sans solution exacte, le BFS naïf parcourt tout l'arbre (25 millions de noeuds)
            # et sa file monte à ~14 millions de noeuds : plusieurs Go de mémoire.
            print("\n=== BFS : ignoré (pas de solution exacte, la file dépasserait 14 millions de noeuds ;"
                  " ajouter --forcer pour le lancer quand même)")

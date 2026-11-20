#! /usr/bin/env python3

""" Parcours améliorés de l'arbre de calculs du compte est bon.

Même arbre et mêmes parcours que dans recherche_compte_est_bon.py, avec deux améliorations :

1. Ne générer que des enfants valides.
   Chaque noeud mémorise, en plus de l'expression NPI, la pile des valeurs déjà calculées.
   On n'ajoute donc un opérateur que si la pile contient au moins 2 valeurs et que le
   résultat est un entier naturel non nul. Plus aucun noeud invalide n'est parcouru,
   et il n'est plus nécessaire de réévaluer toute l'expression avec eval_NPI_liste.

2. Commutativité (paramètre commutativite).
   a+b et b+a donnent le même résultat : on ne garde a+b (et a*b) que si a <= b.

Un noeud est un tuple (expression, valeurs, restants) :
- expression : expression NPI partielle (liste de cartons et d'opérateurs)
- valeurs    : pile d'évaluation de cette expression (liste python)
- restants   : cartons non encore utilisés
"""

from TAD.piles_listes_python import Pile
# Les fichiers de TAD/ importent leurs listes chaînées sans le préfixe "TAD." :
# on ajoute donc le dossier TAD au chemin de recherche des modules.
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "TAD"))
from files_listes_doublement_chainees import File
from recherche_compte_est_bon import STATS, reinitialiser_stats, noter_noeud, afficher_progres, npi_vers_infixe


def enfants_valides(noeud, commutativite=True):
    """Génère uniquement les enfants valides d'un noeud"""
    expression, valeurs, restants = noeud
    liste_enfants = []
    # ajout d'un des cartons restants
    for i in range(len(restants)):
        liste_enfants.append((expression + [restants[i]],
                              valeurs + [restants[i]],
                              restants[:i] + restants[i+1:]))
    # ajout d'un opérateur : il faut au moins deux valeurs dans la pile
    if len(valeurs) >= 2:
        a, b = valeurs[-2], valeurs[-1]
        debut = valeurs[:-2]
        resultats = []
        if not commutativite or a <= b:
            resultats.append(('+', a + b))
            resultats.append(('*', a * b))
        if a - b >= 1:                      # résultat entier naturel non nul
            resultats.append(('-', a - b))
        if a % b == 0:                      # division exacte
            resultats.append(('/', a // b))
        for op, v in resultats:
            liste_enfants.append((expression + [op], debut + [v], restants))
    return liste_enfants


def valeur_noeud(noeud):
    """Valeur de l'expression si elle est complète (une seule valeur dans la pile), sinon None"""
    valeurs = noeud[1]
    return valeurs[0] if len(valeurs) == 1 else None


def parcours_DFS_ameliore(cartons, cible, commutativite=True, verbeux=True):
    reinitialiser_stats()
    nb_noeuds = 0
    meilleure_expression = []
    meilleur_ecart = None

    pile = Pile()
    pile.empiler(([], [], list(cartons)))
    taille = STATS["taille_max"] = 1

    while not pile.est_vide():
        noeud = pile.depiler()
        taille -= 1
        nb_noeuds += 1
        noter_noeud(len(noeud[0]), True)

        valeur = valeur_noeud(noeud)
        if valeur is not None:
            ecart = abs(valeur - cible)
            if meilleur_ecart is None or ecart < meilleur_ecart:
                meilleur_ecart = ecart
                meilleure_expression = noeud[0]
                if verbeux:
                    afficher_progres("DFS+", noeud[0], valeur, cible)
                if ecart == 0:
                    break

        for enfant in reversed(enfants_valides(noeud, commutativite)):
            pile.empiler(enfant)
            taille += 1
        if taille > STATS["taille_max"]:
            STATS["taille_max"] = taille

    return meilleure_expression, nb_noeuds


def parcours_BFS_ameliore(cartons, cible, commutativite=True, verbeux=True):
    reinitialiser_stats()
    nb_noeuds = 0
    meilleure_expression = []
    meilleur_ecart = None

    file = File()
    file.enfiler(([], [], list(cartons)))
    taille = STATS["taille_max"] = 1

    while not file.est_vide():
        noeud = file.defiler()
        taille -= 1
        nb_noeuds += 1
        noter_noeud(len(noeud[0]), True)

        valeur = valeur_noeud(noeud)
        if valeur is not None:
            ecart = abs(valeur - cible)
            if meilleur_ecart is None or ecart < meilleur_ecart:
                meilleur_ecart = ecart
                meilleure_expression = noeud[0]
                if verbeux:
                    afficher_progres("BFS+", noeud[0], valeur, cible)
                if ecart == 0:
                    break

        for enfant in enfants_valides(noeud, commutativite):
            file.enfiler(enfant)
            taille += 1
        if taille > STATS["taille_max"]:
            STATS["taille_max"] = taille

    return meilleure_expression, nb_noeuds


def parcours_DFS_recursif_ameliore(cartons, cible, commutativite=True, verbeux=True):
    reinitialiser_stats()
    meilleure_expression = []
    meilleur_ecart = None
    nb_noeuds = 0
    trouve = False

    def aux(noeud, profondeur_appel):
        nonlocal meilleure_expression, meilleur_ecart, nb_noeuds, trouve
        nb_noeuds += 1
        noter_noeud(len(noeud[0]), True)
        if profondeur_appel > STATS["taille_max"]:
            STATS["taille_max"] = profondeur_appel

        valeur = valeur_noeud(noeud)
        if valeur is not None:
            ecart = abs(valeur - cible)
            if meilleur_ecart is None or ecart < meilleur_ecart:
                meilleur_ecart = ecart
                meilleure_expression = noeud[0]
                if verbeux:
                    afficher_progres("DFS récursif+", noeud[0], valeur, cible)
                if ecart == 0:
                    trouve = True
                    return

        for enfant in enfants_valides(noeud, commutativite):
            aux(enfant, profondeur_appel + 1)
            if trouve:
                return

    aux(([], [], list(cartons)), 1)
    return meilleure_expression, nb_noeuds


if __name__ == "__main__":
    for parcours in (parcours_DFS_ameliore, parcours_DFS_recursif_ameliore, parcours_BFS_ameliore):
        expr, n = parcours([3, 5, 7, 9, 25, 50], 859)
        print(f"{parcours.__name__} -> {npi_vers_infixe(expr)} en {n} noeuds")

#! /usr/bin/env python3

""" Implémentation des parcours de l’arbre de calculs à la volée :
- parcours en profondeur d’abord itératif
- parcours en profondeur d’abord récursif
- parcours en largeur d’abord itératif

Version "naïve", qui suit l'énoncé du TP :
- un noeud est un tuple (expression NPI partielle, cartons restants)
- chaque noeud a D+4 enfants : un par carton restant + un par opérateur
- chaque noeud parcouru est évalué avec eval_NPI_liste ; s'il est invalide,
  son sous-arbre est élagué (ses enfants ne sont pas générés)

Chaque parcours renvoie (meilleure_expression, nb_noeuds) et remplit le
dictionnaire global STATS avec les mesures demandées dans les questions d'analyse.
"""

from TAD.piles_listes_python import Pile
# File à base de liste doublement chaînée : defiler() en O(1)
# (la File à base de liste python fait pop(0), en O(n) : très lent pour le BFS)
# Les fichiers de TAD/ importent leurs listes chaînées sans le préfixe "TAD." :
# on ajoute donc le dossier TAD au chemin de recherche des modules.
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "TAD"))
from files_listes_doublement_chainees import File
from notation_polonaise_inverse import eval_NPI_liste

OPERATEURS = ['+', '-', '*', '/']

# Mesures du dernier parcours lancé (remplies par les fonctions de parcours)
STATS = {}


def reinitialiser_stats():
    STATS.clear()
    STATS.update({
        "nb_noeuds": 0,       # noeuds parcourus (évalués), valides ou non
        "nb_valides": 0,
        "nb_invalides": 0,
        "taille_max": 0,      # taille max de la pile (DFS), de la file (BFS) ou de la pile d'appels (DFS récursif)
        "hauteur_max": 0,     # profondeur max atteinte (racine = profondeur 0)
        "largeur": {},        # nombre de noeuds parcourus à chaque profondeur
    })


def noter_noeud(profondeur, valide):
    """Met à jour les statistiques lorsqu'un noeud est parcouru"""
    STATS["nb_noeuds"] += 1
    if valide:
        STATS["nb_valides"] += 1
    else:
        STATS["nb_invalides"] += 1
    if profondeur > STATS["hauteur_max"]:
        STATS["hauteur_max"] = profondeur
    STATS["largeur"][profondeur] = STATS["largeur"].get(profondeur, 0) + 1


def largeur_max():
    return max(STATS["largeur"].values()) if STATS["largeur"] else 0


def enfants(noeud):
    """Génère à la volée les D+4 enfants d'un noeud (expression, restants)"""
    expression, restants = noeud
    liste_enfants = []
    for i in range(len(restants)):
        liste_enfants.append((expression + [restants[i]], restants[:i] + restants[i+1:]))
    for op in OPERATEURS:
        liste_enfants.append((expression + [op], restants))
    return liste_enfants


def npi_vers_infixe(expression):
    """Traduit une expression NPI complète en notation infixe parenthésée (pour l'affichage)"""
    pile = []
    for elt in expression:
        if elt in OPERATEURS:
            b = pile.pop()
            a = pile.pop()
            pile.append(f"({a} {elt} {b})")
        else:
            pile.append(str(elt))
    return pile[-1] if len(pile) == 1 else " ".join(pile)


def afficher_progres(nom, expression, valeur, cible):
    print(f"  [{nom}] {npi_vers_infixe(expression)} = {valeur}"
          f"  (écart {abs(valeur - cible)})  NPI : {' '.join(map(str, expression))}")


def parcours_DFS(cartons, cible, verbeux=True):
    """Parcours en profondeur d'abord, itératif, à l'aide d'une pile"""
    # cartons : une liste
    # cible : entier
    reinitialiser_stats()
    nb_noeuds = 0
    meilleure_expression = []
    meilleur_ecart = None

    pile = Pile()
    pile.empiler(([], list(cartons)))
    taille = 1                      # taille courante de la pile, maintenue à la main :
    STATS["taille_max"] = 1         # Pile.longueur() n'est pas en O(1) pour toutes les implémentations

    while not pile.est_vide():
        noeud = pile.depiler()
        taille -= 1
        expression, restants = noeud
        nb_noeuds += 1

        valide, valeur = eval_NPI_liste(expression)
        noter_noeud(len(expression), valide)
        if not valide:
            continue                # élagage : inutile de parcourir le sous-arbre

        if valeur is not None:
            ecart = abs(valeur - cible)
            if meilleur_ecart is None or ecart < meilleur_ecart:
                meilleur_ecart = ecart
                meilleure_expression = expression
                if verbeux:
                    afficher_progres("DFS", expression, valeur, cible)
                if ecart == 0:
                    break           # le compte est bon : on arrête le parcours

        # On empile les enfants en ordre inverse pour que le premier enfant
        # soit traité en premier (même ordre de parcours que la version récursive)
        for enfant in reversed(enfants(noeud)):
            pile.empiler(enfant)
            taille += 1
        if taille > STATS["taille_max"]:
            STATS["taille_max"] = taille

    return meilleure_expression, nb_noeuds


def parcours_BFS(cartons, cible, verbeux=True):
    """Parcours en largeur d'abord, itératif, à l'aide d'une file"""
    # cartons : une liste
    # cible : entier
    reinitialiser_stats()
    nb_noeuds = 0
    meilleure_expression = []
    meilleur_ecart = None

    file = File()
    file.enfiler(([], list(cartons)))
    taille = 1
    STATS["taille_max"] = 1

    while not file.est_vide():
        noeud = file.defiler()
        taille -= 1
        expression, restants = noeud
        nb_noeuds += 1

        valide, valeur = eval_NPI_liste(expression)
        noter_noeud(len(expression), valide)
        if not valide:
            continue

        if valeur is not None:
            ecart = abs(valeur - cible)
            if meilleur_ecart is None or ecart < meilleur_ecart:
                meilleur_ecart = ecart
                meilleure_expression = expression
                if verbeux:
                    afficher_progres("BFS", expression, valeur, cible)
                if ecart == 0:
                    break

        for enfant in enfants(noeud):
            file.enfiler(enfant)
            taille += 1
        if taille > STATS["taille_max"]:
            STATS["taille_max"] = taille

    return meilleure_expression, nb_noeuds


def parcours_DFS_recursif(cartons, cible, verbeux=True):
    """Parcours en profondeur d'abord, récursif : la pile d'exécution remplace la pile explicite"""
    reinitialiser_stats()
    meilleure_expression = []
    meilleur_ecart = None
    nb_noeuds = 0
    trouve = False

    def parcours_DFSR_aux(choisis, restants, profondeur_appel):
        # choisis : expression NPI partielle ; restants : cartons non utilisés
        nonlocal meilleure_expression, meilleur_ecart, nb_noeuds, trouve
        nb_noeuds += 1
        if profondeur_appel > STATS["taille_max"]:
            STATS["taille_max"] = profondeur_appel

        valide, valeur = eval_NPI_liste(choisis)
        noter_noeud(len(choisis), valide)
        if not valide:
            return

        if valeur is not None:
            ecart = abs(valeur - cible)
            if meilleur_ecart is None or ecart < meilleur_ecart:
                meilleur_ecart = ecart
                meilleure_expression = choisis
                if verbeux:
                    afficher_progres("DFS récursif", choisis, valeur, cible)
                if ecart == 0:
                    trouve = True
                    return

        for enfant_choisis, enfant_restants in enfants((choisis, restants)):
            parcours_DFSR_aux(enfant_choisis, enfant_restants, profondeur_appel + 1)
            if trouve:
                return

    parcours_DFSR_aux([], list(cartons), 1)

    return meilleure_expression, nb_noeuds


if __name__ == "__main__":
    for parcours in (parcours_DFS, parcours_DFS_recursif, parcours_BFS):
        print(parcours.__name__)
        expr, n = parcours([3, 5, 7, 9, 25, 50], 859)
        print(f"  -> {npi_vers_infixe(expr)} en {n} noeuds, stats : "
              f"taille max {STATS['taille_max']}, hauteur max {STATS['hauteur_max']}, largeur max {largeur_max()}")

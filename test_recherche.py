"""Tests des parcours (lancer avec : python -m pytest -q)"""

import random
from collections import Counter

import pytest

from notation_polonaise_inverse import eval_NPI_liste
from recherche_compte_est_bon import parcours_DFS, parcours_DFS_recursif, parcours_BFS, enfants
from recherche_amelioree import parcours_DFS_ameliore, parcours_DFS_recursif_ameliore, parcours_BFS_ameliore

NAIFS_RAPIDES = [parcours_DFS, parcours_DFS_recursif]
AMELIORES = [parcours_DFS_ameliore, parcours_DFS_recursif_ameliore, parcours_BFS_ameliore]


def verifier(expression, cartons, cible_attendue):
    valide, valeur = eval_NPI_liste(expression)
    assert valide and valeur == cible_attendue
    # chaque carton n'est utilisé qu'une fois
    utilises = Counter(e for e in expression if isinstance(e, int))
    assert not utilises - Counter(cartons)


def test_enfants_racine():
    # D+4 enfants
    assert len(enfants(([], [1, 2, 3]))) == 3 + 4


@pytest.mark.parametrize("parcours", NAIFS_RAPIDES + [parcours_BFS] + AMELIORES)
def test_exemple_cours(parcours):
    cartons = [3, 5, 7, 9, 25, 50]
    expr, n = parcours(cartons, 859, verbeux=False)
    verifier(expr, cartons, 859)
    assert n > 0


@pytest.mark.parametrize("parcours", AMELIORES)
def test_ardu(parcours):
    cartons = [1, 4, 6, 25, 50, 100]
    expr, _ = parcours(cartons, 263, verbeux=False)
    verifier(expr, cartons, 263)


@pytest.mark.parametrize("parcours", AMELIORES)
def test_impossible_meilleur_ecart(parcours):
    # 365 est impossible avec ces cartons ; 364 et 366 sont atteignables
    cartons = [7, 7, 8, 9, 9, 25]
    expr, _ = parcours(cartons, 365, verbeux=False)
    _, valeur = eval_NPI_liste(expr)
    assert abs(valeur - 365) == 1


@pytest.mark.parametrize("graine", range(5))
def test_ameliore_coherent_avec_naif(graine):
    """Sur des tirages aléatoires, le DFS amélioré (avec ou sans commutativité) trouve
    le même écart à la cible que le DFS naïf, qui sert de référence"""
    rnd = random.Random(graine)
    plaques = list(range(1, 11)) * 2 + [25, 50, 75, 100]
    cartons = rnd.sample(plaques, 6)
    cible = rnd.randint(100, 999)
    ref, _ = parcours_DFS(cartons, cible, verbeux=False)
    ecart_ref = abs(eval_NPI_liste(ref)[1] - cible)
    for commutativite in (True, False):
        expr, _ = parcours_DFS_ameliore(cartons, cible, commutativite=commutativite, verbeux=False)
        assert abs(eval_NPI_liste(expr)[1] - cible) == ecart_ref

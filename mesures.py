#! /usr/bin/env python3

"""Campagne de mesures pour le rapport du TP4.

Usage :
    python mesures.py                                    # 3 problèmes par défaut
    python mesures.py "naissance=$(./generer_probleme.py 17081936)" \\
                      "impossible=$(./generer_probleme.py impossible)" \\
                      "ardu=$(./generer_probleme.py ardu)"
Options :
    --forcer   lance aussi le BFS naïf sur les problèmes sans solution exacte
               (attention : plusieurs Go de mémoire et plusieurs minutes)

Produit dans le dossier resultats/ :
    resultats.csv  une ligne par (problème, parcours) avec toutes les mesures
    largeurs.csv   nombre de noeuds parcourus à chaque profondeur
    *.png          graphiques (si matplotlib est installé)
et affiche des tableaux markdown sur la sortie standard.
"""

import csv
import os
import sys
import time

from recherche_compte_est_bon import (parcours_DFS, parcours_BFS, parcours_DFS_recursif,
                                      STATS, largeur_max, npi_vers_infixe)
from recherche_amelioree import (parcours_DFS_ameliore, parcours_BFS_ameliore,
                                 parcours_DFS_recursif_ameliore)
from notation_polonaise_inverse import eval_NPI_liste

PROBLEMES_DEFAUT = [
    ("exemple", "3 5 7 9 25 50 859"),
    ("impossible", "7 7 8 9 9 25 365"),
    ("ardu", "1 4 6 25 50 100 263"),
]

PARCOURS = [
    ("DFS", parcours_DFS),
    ("DFS récursif", parcours_DFS_recursif),
    ("BFS", parcours_BFS),
    # amélioration 1 seule (enfants valides), puis améliorations 1 + 2 (commutativité)
    ("DFS valides seulement", lambda c, t, **kw: parcours_DFS_ameliore(c, t, commutativite=False, **kw)),
    ("DFS amélioré", parcours_DFS_ameliore),
    ("DFS récursif amélioré", parcours_DFS_recursif_ameliore),
    ("BFS amélioré", parcours_BFS_ameliore),
]

DOSSIER = "resultats"


def mesurer(fonction, cartons, cible, **kw):
    debut = time.perf_counter()
    expression, nb = fonction(cartons, cible, verbeux=False, **kw)
    duree = time.perf_counter() - debut
    _, valeur = eval_NPI_liste(expression)
    return {
        "solution": npi_vers_infixe(expression),
        "npi": " ".join(map(str, expression)),
        "valeur": valeur,
        "ecart": abs(valeur - cible),
        "noeuds": nb,
        "valides": STATS["nb_valides"],
        "invalides": STATS["nb_invalides"],
        "taille_max": STATS["taille_max"],
        "hauteur_max": STATS["hauteur_max"],
        "largeur_max": largeur_max(),
        "temps_s": round(duree, 4),
        "largeurs": dict(STATS["largeur"]),
    }


def tableau_markdown(lignes, colonnes):
    print("| " + " | ".join(colonnes) + " |")
    print("|" + "---|" * len(colonnes))
    for l in lignes:
        print("| " + " | ".join(str(l[c]) for c in colonnes) + " |")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    forcer = "--forcer" in sys.argv
    problemes = []
    for a in args:
        nom, _, valeurs = a.partition("=") if "=" in a else (a, "", a)
        problemes.append((nom, valeurs))
    if not problemes:
        problemes = PROBLEMES_DEFAUT

    os.makedirs(DOSSIER, exist_ok=True)
    resultats, largeurs = [], []

    for nom, valeurs in problemes:
        *cartons, cible = map(int, valeurs.split())
        print(f"\n## Problème {nom} : {cartons} -> {cible}", flush=True)
        exact = mesurer(parcours_DFS_ameliore, cartons, cible)["ecart"] == 0

        for nom_parcours, f in PARCOURS:
            if nom_parcours == "BFS" and not exact and not forcer:
                print(f"  {nom_parcours} : ignoré (pas de solution exacte -> file de ~14 M de noeuds, voir --forcer)")
                continue
            print(f"  {nom_parcours} ...", end=" ", flush=True)
            r = mesurer(f, cartons, cible)
            print(f"{r['noeuds']} noeuds, {r['temps_s']} s", flush=True)
            for prof, n in sorted(r.pop("largeurs").items()):
                largeurs.append({"probleme": nom, "parcours": nom_parcours, "profondeur": prof, "noeuds": n})
            resultats.append({"probleme": nom, "cartons": " ".join(map(str, cartons)), "cible": cible,
                              "parcours": nom_parcours, **r})

    cols = ["probleme", "parcours", "ecart", "noeuds", "valides", "invalides", "taille_max",
            "hauteur_max", "largeur_max", "temps_s", "solution"]
    print("\n### Résultats\n")
    tableau_markdown(resultats, cols)

    for fichier, donnees in (("resultats.csv", resultats), ("largeurs.csv", largeurs)):
        with open(os.path.join(DOSSIER, fichier), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(donnees[0].keys()), delimiter=";")
            w.writeheader()
            w.writerows(donnees)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n(matplotlib absent : pas de graphiques)")
        return

    # Graphique 1 : largeur de l'arbre parcouru à chaque profondeur, un graphique par problème
    for nom, _ in problemes:
        fig, ax = plt.subplots(figsize=(7, 4))
        for nom_parcours, _ in PARCOURS:
            pts = [(l["profondeur"], l["noeuds"]) for l in largeurs
                   if l["probleme"] == nom and l["parcours"] == nom_parcours]
            if pts:
                ax.plot(*zip(*pts), marker="o", label=nom_parcours)
        ax.set_yscale("log")
        ax.set_xlabel("profondeur (nombre de jetons de l'expression NPI)")
        ax.set_ylabel("noeuds parcourus (échelle log)")
        ax.set_title(f"Noeuds parcourus par profondeur - problème {nom}")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(DOSSIER, f"largeurs_{nom}.png"), dpi=150)
        plt.close(fig)

    # Graphique 2 : nombre de noeuds et temps par parcours et par problème
    for mesure, titre in (("noeuds", "Noeuds parcourus"), ("temps_s", "Temps d'exécution (s)")):
        fig, ax = plt.subplots(figsize=(8, 4))
        noms_pb = [p for p, _ in problemes]
        largeur_barre = 0.8 / len(PARCOURS)
        for i, (nom_parcours, _) in enumerate(PARCOURS):
            ys = []
            for p in noms_pb:
                v = [r[mesure] for r in resultats if r["probleme"] == p and r["parcours"] == nom_parcours]
                ys.append(v[0] if v else 0)
            ax.bar([j + i * largeur_barre for j in range(len(noms_pb))], ys, largeur_barre, label=nom_parcours)
        ax.set_xticks([j + 0.4 - largeur_barre / 2 for j in range(len(noms_pb))])
        ax.set_xticklabels(noms_pb)
        ax.set_yscale("log")
        ax.set_title(titre + " (échelle log)")
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(os.path.join(DOSSIER, f"comparaison_{mesure}.png"), dpi=150)
        plt.close(fig)
    print(f"\nGraphiques et CSV écrits dans {DOSSIER}/")


if __name__ == "__main__":
    main()

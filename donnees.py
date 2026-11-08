from pathlib import Path
import pandas as pd
CHEMIN = Path(__file__).resolve().parent / "sales_data_brut.csv"
BRUT = pd.read_csv(CHEMIN, encoding="utf-8-sig")
REQUIS = [
    "Ligne_ID", "Commande_ID", "Date", "Produit", "Categorie",
    "Region", "Quantite", "Prix_Unitaire", "Cout_Unitaire",
    "Remise_Pct", "Chiffre_Affaires",
]
absentes = set(REQUIS) - set(BRUT.columns)
if absentes:
    raise ValueError(f"Colonnes manquantes : {sorted(absentes)}")
# 1. Suppression des doublons d'identifiant de transaction
df = BRUT.drop_duplicates(subset="Ligne_ID").copy()
# 2. Correction et typage des colonnes
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
for colonne in ["Quantite", "Prix_Unitaire", "Cout_Unitaire", "Remise_Pct", "Chiffre_Affaires"]:
    df[colonne] = pd.to_numeric(df[colonne], errors="coerce")
# 3. Élimination des lignes incomplètes et valeurs hors bornes
df = df.dropna(subset=REQUIS).copy()
df = df[
    (df["Quantite"] > 0)
    & (df["Prix_Unitaire"] > 0)
    & (df["Cout_Unitaire"] >= 0)
    & (df["Remise_Pct"].between(0, 1))
].copy()
# 4. Contrôle de cohérence arithmétique (CA = Quantité * Prix * (1 - Remise))
ca_recalcule = (
    df["Quantite"] * df["Prix_Unitaire"] * (1 - df["Remise_Pct"])
).round(2)
df = df[(df["Chiffre_Affaires"] - ca_recalcule).abs() <= 0.01].copy()
# 5. Calcul de la marge commerciale unitaire / totale
df["Marge"] = df["Chiffre_Affaires"] - df["Quantite"] * df["Cout_Unitaire"]
# 6. Tri chronologique pour les séries temporelles
df = df.sort_values("Date").reset_index(drop=True)
# Métriques de synthèse du nettoyage
STAT_QUALITE = {
    "brutes": len(BRUT),
    "doublons": int(BRUT["Ligne_ID"].duplicated().sum()),
    "retenues": len(df),
    "exclues_total": len(BRUT) - len(df),
}
def filtrer(date_debut=None, date_fin=None, categorie="Toutes"):
    """
    Renvoie les lignes correspondant à la période demandée et à la catégorie.
    Si categorie == 'Toutes' ou None, toutes les catégories sont conservées.
    """
    donnees = df
    if date_debut:
        donnees = donnees[donnees["Date"] >= pd.to_datetime(date_debut)]
    if date_fin:
        donnees = donnees[donnees["Date"] <= pd.to_datetime(date_fin)]
    if categorie and categorie != "Toutes":
        donnees = donnees[donnees["Categorie"] == categorie]
    return donnees.copy()
def calculer_kpis(donnees):
    """
    Calcule les indicateurs clés de performance (KPI) :
    - ca : Chiffre d'affaires cumulé
    - commandes : Nombre de commandes distinctes
    - panier : Panier moyen par commande
    - marge : Marge commerciale totale
    - taux_marque : Taux de marque en % (Marge / CA * 100)
    """
    ca = float(donnees["Chiffre_Affaires"].sum())
    nb = int(donnees["Commande_ID"].nunique())
    marge = float(donnees["Marge"].sum())
    return {
        "ca": ca,
        "commandes": nb,
        "panier": ca / nb if nb else 0.0,
        "marge": marge,
        "taux_marque": 100 * marge / ca if ca else 0.0,
    }
def mad(valeur):
    """
    Formate un montant en Dirhams marocains (MAD) avec séparateur de milliers et sans centimes.
    Exemple: 7671306 -> '7 671 306 MAD'
    """
    return f"{valeur:,.0f}".replace(",", " ") + " MAD"
if __name__ == "__main__":
    print("=== RAPPORT QUALITE DE DONNEES ===")
    print("STAT_QUALITE :", STAT_QUALITE)
    print("\n=== TYPES DES COLONNES ===")
    print(df.dtypes)
    print("\n=== KPI GLOBAUX DU DATASET ===")
    kpis = calculer_kpis(df)
    for k, v in kpis.items():
        if k in ("ca", "panier", "marge"):
            print(f"  {k:12} : {mad(v)}")
        elif k == "taux_marque":
            print(f"  {k:12} : {v:.2f} %")
        else:
            print(f"  {k:12} : {v}")

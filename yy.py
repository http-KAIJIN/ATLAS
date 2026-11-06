
from dash import Dash, dcc, html, Input, Output, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import du module de préparation et de nettoyage des données métier
from donnees import df, filtrer, calculer_kpis, mad

# Initialisation de l'application avec thème Bootstrap FLATLY moderne
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="Atlas Commerce | Dashboard décisionnel"
)
server = app.server

# Bornes chronologiques calculées dynamiquement sur le dataset validé
DATE_MIN = df["Date"].min().date().isoformat()
DATE_MAX = df["Date"].max().date().isoformat()

# ==============================================================================
# ZONE_FONCTIONS : Composants graphiques et aides visuelles réutilisables
# ==============================================================================

def carte_kpi(titre: str, identifiant: str):
    """Construit une carte d'indicateur clé (KPI) responsive et stylisée."""
    return dbc.Card(
        dbc.CardBody([
            html.Div(titre, className="kpi-label"),
            html.Div("--", id=identifiant, className="kpi-valeur")
        ]),
        className="kpi-card"
    )

def carte_graphique(identifiant: str):
    """Enveloppe un graphique Plotly dans une carte Dash avec indicateur de chargement."""
    return dbc.Card(
        dbc.CardBody(
            dcc.Loading(
                dcc.Graph(
                    id=identifiant,
                    config={"displayModeBar": False, "responsive": True}
                )
            )
        ),
        className="graph-card"
    )

def figure_vide(titre: str):
    """Retourne une figure informative lorsque les filtres ne renvoient aucune donnée."""
    fig = go.Figure()
    fig.add_annotation(
        text="Aucune transaction trouvée pour ces filtres",
        x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=14, color="#64748b")
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(
        title=titre,
        template="plotly_white",
        height=360,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def harmoniser(fig):
    """Uniformise la typographie, les marges et le fond de chaque graphique Plotly."""
    fig.update_layout(
        template="plotly_white",
        height=360,
        margin=dict(l=30, r=25, t=55, b=35),
        title_font=dict(size=15, color="#1e293b", family="system-ui, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#475569", family="system-ui, sans-serif")
    )
    return fig


# ==============================================================================
# ARBORESCENCE DU LAYOUT (dbc.Container)
# ==============================================================================

app.layout = dbc.Container([

    # ZONE_ENTETE
    html.Div([
        dbc.Row([
            dbc.Col([
                html.H1("ATLAS COMMERCE", className="fw-bold mb-1"),
                html.P("Tableau de bord de pilotage des ventes | Jeu de données audité", className="mb-0 text-light-emphasis"),
            ], xs=12, md=8),
            dbc.Col([
                html.Div([
                    dbc.Badge("Qualité : 100% Certifiée", color="success", className="me-2 p-2"),
                    dbc.Badge("Devise : MAD", color="light", text_color="dark", className="p-2"),
                ], className="text-md-end mt-2 mt-md-0")
            ], xs=12, md=4)
        ])
    ], className="bandeau"),

    # ZONE_FILTRES
    dbc.Card(
        dbc.CardBody(
            dbc.Row([
                dbc.Col([
                    html.Label("Période d'analyse", className="etiquette"),
                    dcc.DatePickerRange(
                        id="dates",
                        start_date=DATE_MIN,
                        end_date=DATE_MAX,
                        min_date_allowed=DATE_MIN,
                        max_date_allowed=DATE_MAX,
                        display_format="DD/MM/YYYY",
                        className="w-100"
                    )
                ], xs=12, lg=5),

                dbc.Col([
                    html.Label("Catégorie de produit", className="etiquette"),
                    dcc.Dropdown(
                        id="categorie",
                        value="Toutes",
                        options=["Toutes"] + sorted(df["Categorie"].unique().tolist()),
                        clearable=False
                    )
                ], xs=12, lg=4),

                dbc.Col([
                    html.Label("Regroupement temporel", className="etiquette"),
                    dcc.RadioItems(
                        id="freq",
                        value="M",
                        inline=True,
                        options=[
                            {"label": " Jour", "value": "J"},
                            {"label": " Mois", "value": "M"}
                        ],
                        className="d-flex gap-3 align-items-center pt-2"
                    )
                ], xs=12, lg=3),
            ], className="g-3 align-items-center")
        ),
        className="filter-card mb-4"
    ),

    # ZONE_KPIS
    dbc.Row([
        dbc.Col(carte_kpi("Chiffre d'affaires", "ca"), xs=12, sm=6, lg=3),
        dbc.Col(carte_kpi("Commandes distinctes", "commandes"), xs=12, sm=6, lg=2),
        dbc.Col(carte_kpi("Panier moyen", "panier"), xs=12, sm=6, lg=2),
        dbc.Col(carte_kpi("Marge commerciale", "marge"), xs=12, sm=6, lg=3),
        dbc.Col(carte_kpi("Taux de marque", "taux-marque"), xs=12, sm=6, lg=2),
    ], className="g-3 mb-2"),

    html.P(id="etat", className="text-muted mb-4 ps-1"),

    # ZONE_EVOLUTION_UI
    dbc.Row([
        dbc.Col(carte_graphique("evolution"), xs=12)
    ], className="g-3 mb-4"),

    # Rangée double : Catégories & Régions
    dbc.Row([
        # ZONE_CATEGORIES_UI
        dbc.Col(carte_graphique("categories"), xs=12, lg=6),

        # ZONE_REGIONS_UI
        dbc.Col(carte_graphique("regions"), xs=12, lg=6),
    ], className="g-3 mb-4"),

    # Rangée double : Marges & Top Produits avec reset interactif
    dbc.Row([
        # ZONE_MARGES_UI
        dbc.Col(carte_graphique("marges"), xs=12, lg=5),

        # ZONE_TOP_UI
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(
                            html.H5(id="titre-top", className="fw-bold mb-0 text-secondary"),
                            xs=12, sm=7
                        ),
                        # ZONE_RESET_UI
                        dbc.Col(
                            dbc.Button(
                                "↺ Effacer le filtre région",
                                id="reset-region",
                                color="outline-secondary",
                                size="sm",
                                className="float-sm-end"
                            ),
                            xs=12, sm=5
                        )
                    ], className="align-items-center mb-3"),
                    dcc.Loading(
                        dcc.Graph(
                            id="top-produits",
                            config={"displayModeBar": False, "responsive": True}
                        )
                    )
                ]),
                className="graph-card h-100"
            )
        ], xs=12, lg=7),
    ], className="g-3 mb-4"),

    # Stockage de l'état du filtre interactif régional
    dcc.Store(id="region-active", data=None),

    # ZONE_MESSAGE_UI
    dbc.Alert(id="lecture-metier", color="info", className="mt-2 mb-4"),

], fluid=True, className="px-3 px-xl-5 py-4")


# ==============================================================================
# ZONE_CALLBACKS : Dynamisme et réactivité des composants
# ==============================================================================

# ZONE_KPI_CALLBACK
@app.callback(
    Output("ca", "children"),
    Output("commandes", "children"),
    Output("panier", "children"),
    Output("marge", "children"),
    Output("etat", "children"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value")
)
def actualiser_kpis(debut, fin, categorie):
    """Met à jour les 4 KPI principaux et la synthèse d'état des transactions."""
    ventes = filtrer(debut, fin, categorie)
    k = calculer_kpis(ventes)
    message = f"{len(ventes):,} lignes sélectionnées | {k['commandes']:,} commandes distinctes".replace(",", " ")
    return (
        mad(k["ca"]),
        f"{k['commandes']:,}".replace(",", " "),
        mad(k["panier"]),
        mad(k["marge"]),
        message
    )

# Callback additionnel pour le 5ème KPI (Bonus Data Analyst - Annexe G)
@app.callback(
    Output("taux-marque", "children"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value")
)
def actualiser_taux_marque(debut, fin, categorie):
    """Calcule le taux de marque commercial (Marge / CA)."""
    ventes = filtrer(debut, fin, categorie)
    k = calculer_kpis(ventes)
    return f"{k['taux_marque']:.1f} %"

# ZONE_EVOLUTION_CB
@app.callback(
    Output("evolution", "figure"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value"),
    Input("freq", "value")
)
def tracer_evolution(debut, fin, categorie, freq):
    """Trace la tendance temporelle du CA selon la granularité Jour ou Mois."""
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return figure_vide("Évolution du chiffre d'affaires")

    ventes["Periode"] = (
        ventes["Date"].dt.to_period("M").dt.to_timestamp()
        if freq == "M" else ventes["Date"]
    )
    evolution = (
        ventes.groupby("Periode", as_index=False)["Chiffre_Affaires"]
        .sum()
        .sort_values("Periode")
    )

    fig = px.line(
        evolution,
        x="Periode",
        y="Chiffre_Affaires",
        markers=True,
        title="Évolution chronologique du chiffre d'affaires",
        labels={"Chiffre_Affaires": "CA (MAD)", "Periode": "Date"}
    )
    fig.update_traces(
        line_color="#2563eb",
        marker=dict(size=6, color="#1d4ed8"),
        hovertemplate="<b>Date</b> : %{x|%Y-%m-%d}<br><b>CA</b> : %{y:,.0f} MAD<extra></extra>"
    )
    return harmoniser(fig)

# ZONE_CATEGORIES_CB
@app.callback(
    Output("categories", "figure"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value")
)
def tracer_categories(debut, fin, categorie):
    """Affiche le chiffre d'affaires agrégé par catégorie de produits."""
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return figure_vide("CA par catégorie")

    resume = (
        ventes.groupby("Categorie", as_index=False)["Chiffre_Affaires"]
        .sum()
        .sort_values("Chiffre_Affaires", ascending=False)
    )

    fig = px.bar(
        resume,
        x="Categorie",
        y="Chiffre_Affaires",
        color="Categorie",
        title="Chiffre d'affaires par catégorie",
        labels={"Chiffre_Affaires": "CA (MAD)", "Categorie": "Catégorie"},
        color_discrete_sequence=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>CA : %{y:,.0f} MAD<extra></extra>"
    )
    fig.update_layout(showlegend=False)
    return harmoniser(fig)

# ZONE_REGIONS_CB
@app.callback(
    Output("regions", "figure"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value")
)
def tracer_regions(debut, fin, categorie):
    """Donut chart représentant la part de chaque région dans le CA total."""
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return figure_vide("Part de chaque région")

    resume = (
        ventes.groupby("Region", as_index=False)["Chiffre_Affaires"]
        .sum()
    )

    fig = px.pie(
        resume,
        names="Region",
        values="Chiffre_Affaires",
        title="Répartition géographique du chiffre d'affaires",
        hole=0.42,
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig.update_traces(
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>CA : %{value:,.0f} MAD (%{percent})<extra></extra>"
    )
    return harmoniser(fig)

# ZONE_MARGES_CB
@app.callback(
    Output("marges", "figure"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value")
)
def tracer_marges(debut, fin, categorie):
    """Compare la marge commerciale brute générée par chaque catégorie."""
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return figure_vide("Marge par catégorie")

    resume = (
        ventes.groupby("Categorie", as_index=False)["Marge"]
        .sum()
        .sort_values("Marge", ascending=False)
    )

    fig = px.bar(
        resume,
        x="Categorie",
        y="Marge",
        color="Categorie",
        title="Marge commerciale par catégorie",
        labels={"Marge": "Marge (MAD)", "Categorie": "Catégorie"},
        color_discrete_sequence=["#059669", "#0284c7", "#d97706", "#7c3aed"]
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Marge : %{y:,.0f} MAD<extra></extra>"
    )
    fig.update_layout(showlegend=False)
    return harmoniser(fig)

# ZONE_TOP_CB
@app.callback(
    Output("top-produits", "figure"),
    Output("titre-top", "children"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value"),
    Input("region-active", "data")
)
def tracer_top(debut, fin, categorie, region):
    """Palmarès horizontal des 10 meilleures références en chiffre d'affaires."""
    ventes = filtrer(debut, fin, categorie)
    if region:
        ventes = ventes[ventes["Region"] == region].copy()

    titre = f"Top 10 références | {region}" if region else "Top 10 références | Toutes régions"

    if ventes.empty:
        return figure_vide(titre), titre

    resume = (
        ventes.groupby("Produit", as_index=False)["Chiffre_Affaires"]
        .sum()
        .nlargest(10, "Chiffre_Affaires")
        .sort_values("Chiffre_Affaires")
    )

    fig = px.bar(
        resume,
        x="Chiffre_Affaires",
        y="Produit",
        orientation="h",
        color="Chiffre_Affaires",
        color_continuous_scale="Blues",
        labels={"Chiffre_Affaires": "CA (MAD)", "Produit": "Article"}
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>CA : %{x:,.0f} MAD<extra></extra>"
    )
    fig.update_layout(coloraxis_showscale=False)
    return harmoniser(fig), titre

# ZONE_RESET_CB
@app.callback(
    Output("region-active", "data"),
    Input("regions", "clickData"),
    Input("reset-region", "n_clicks"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value"),
    prevent_initial_call=True
)
def selectionner_region(clic, _reset, _debut, _fin, _categorie):
    """
    Filtrage croisé : enregistre la région cliquée dans le donut ou réinitialise le filtre
    si l'utilisateur clique sur le bouton de réinitialisation.
    """
    if ctx.triggered_id == "regions" and clic and clic.get("points"):
        return clic["points"][0].get("label")
    return None

# ZONE_MESSAGE_CB
@app.callback(
    Output("lecture-metier", "children"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value")
)
def recommandation_metier(debut, fin, categorie):
    """Génère une synthèse managériale contextuelle selon les filtres actifs."""
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return "⚠️ Aucune transaction disponible pour les filtres sélectionnés. Élargissez la plage de dates."

    par_region = ventes.groupby("Region")["Chiffre_Affaires"].sum()
    par_categorie = ventes.groupby("Categorie")["Marge"].sum()

    region_max = par_region.idxmax()
    cat_max = par_categorie.idxmax()

    return (
        f"💡 Synthèse décisionnelle : Région leader en CA : {region_max} ({mad(par_region.max())}). "
        f"Catégorie générant la plus forte marge : {cat_max} ({mad(par_categorie.max())}). "
        "— Analyse dynamique calculée sur la sélection actuelle."
    )


# ==============================================================================
# POINT D'ENTRÉE DU SERVEUR LOCAL
# ==============================================================================

if __name__ == "__main__":
    app.run(debug=True, port=8050)

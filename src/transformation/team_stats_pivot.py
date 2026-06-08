"""
====================================================================
Mundial 2026 — Sports Analytics Pipeline
src/transformation/team_stats_pivot.py

Convierte el formato largo de team_stats en formato ancho
con nombres de métricas en español.

Una fila por partido. Una columna por métrica.
Columnas con prefijo col_ (Colombia) y riv_ (rival).

Importable desde actualizar.py y desde notebooks.
====================================================================
"""

import pandas as pd
import numpy as np

# ════════════════════════════════════════════════════════════
# Traducción y selección de métricas
# Solo las más relevantes para el análisis deportivo
# ════════════════════════════════════════════════════════════

METRICAS_ES = {
    # Posesión y juego general
    "Ball possession":          "posesion_pct",
    "Passes":                   "pases_totales",
    "Accurate passes":          "pases_precisos",
    "Long balls":               "pases_largos",
    "Crosses":                  "centros",
    "Through balls":            "pases_filtrados",

    # Ataque
    "Total shots":              "tiros_totales",
    "Shots on target":          "tiros_arco",
    "Shots off target":         "tiros_fuera",
    "Blocked shots":            "tiros_bloqueados",
    "Shots inside box":         "tiros_dentro_area",
    "Shots outside box":        "tiros_fuera_area",
    "Big chances":              "grandes_ocasiones",
    "Big chances scored":       "grandes_ocasiones_gol",
    "Expected goals":           "xG",
    "Hit woodwork":             "palos",
    "Offsides":                 "fueras_juego",
    "Corner kicks":             "corners",
    "Touches in penalty area":  "toques_area",

    # Duelos y físico
    "Duels":                    "duelos_totales",
    "Ground duels":             "duelos_suelo",
    "Aerial duels":             "duelos_aereos",
    "Dribbles":                 "dribbles",
    "Dispossessed":             "perdidas_balon",
    "Fouls":                    "faltas_cometidas",
    "Fouled in final third":    "faltas_recibidas_tercio_final",

    # Defensa
    "Tackles":                  "entradas",
    "Tackles won":              "entradas_ganadas",
    "Total tackles":            "entradas_totales",
    "Interceptions":            "intercepciones",
    "Recoveries":               "recuperaciones",
    "Clearances":               "despejes",
    "Errors lead to a shot":    "errores_tiro",

    # Portero
    "Goalkeeper saves":         "atajadas",
    "Total saves":              "atajadas_totales",
    "High claims":              "salidas_aereas",
    "Goal kicks":               "saques_puerta",

    # Disciplina
    "Yellow cards":             "tarjetas_amarillas",
    "Free kicks":               "tiros_libres",
    "Throw-ins":                "saques_banda",

    # Fase final
    "Final third entries":      "entradas_tercio_final",
    "Final third phase":        "fases_tercio_final",
}


def pivot_team_stats(
    df_stats: pd.DataFrame,
    df_matches: pd.DataFrame,
    team_id: int,
) -> pd.DataFrame:
    """
    Convierte el DataFrame largo de team_stats en formato ancho
    con métricas en español.

    Args:
        df_stats:   DataFrame con columnas match_id, period, stat_name,
                    home_value, away_value.
        df_matches: DataFrame con columnas match_id, home_team_id,
                    away_team_id y metadata del partido.
        team_id:    ID del equipo analizado.

    Returns:
        DataFrame ancho con una fila por partido.
        Columnas: match_id + metadata + col_{metrica} + riv_{metrica}
    """
    if df_stats.empty:
        return pd.DataFrame()

    # Solo período completo
    df = df_stats[df_stats["period"] == "ALL"].copy()

    # Traducir nombres de métricas
    df["metrica"] = df["stat_name"].map(METRICAS_ES)
    df = df[df["metrica"].notna()].copy()

    if df.empty:
        return pd.DataFrame()

    # Determinar side del equipo analizado por partido
    match_sides = df_matches[["match_id", "home_team_id", "away_team_id"]].copy()
    match_sides["match_id"] = pd.to_numeric(match_sides["match_id"], errors="coerce")
    df["match_id"] = pd.to_numeric(df["match_id"], errors="coerce")

    rows = []
    for match_id, group in df.groupby("match_id"):
        sides = match_sides[match_sides["match_id"] == match_id]
        if sides.empty:
            continue

        try:
            is_home = int(pd.to_numeric(sides.iloc[0]["home_team_id"], errors="coerce")) == int(team_id)
        except (TypeError, ValueError):
            is_home = True

        col_val = "home_value" if is_home else "away_value"
        riv_val = "away_value" if is_home else "home_value"

        row = {
            "match_id": match_id,
            "lado":     "local" if is_home else "visitante",
        }

        for _, sr in group.iterrows():
            metrica = sr["metrica"]
            row[f"col_{metrica}"] = sr[col_val]
            row[f"riv_{metrica}"] = sr[riv_val]

        rows.append(row)

    df_wide = pd.DataFrame(rows)

    if df_wide.empty:
        return pd.DataFrame()

    # Merge con metadata del partido
    meta_cols = [
        "match_id", "match_date", "tournament",
        "home_team", "away_team",
        "home_score", "away_score",
        "result", "goals_for", "goals_against", "clean_sheet"
    ]
    meta_cols = [c for c in meta_cols if c in df_matches.columns]
    df_wide = df_wide.merge(
        df_matches[meta_cols],
        on="match_id",
        how="left"
    )

    # Columna legible del rival
    df_wide["rival"] = df_wide.apply(
        lambda r: r["away_team"] if r.get("lado") == "local" else r.get("home_team"),
        axis=1
    )

    # Ordenar por fecha
    if "match_date" in df_wide.columns:
        df_wide["match_date"] = pd.to_datetime(df_wide["match_date"], errors="coerce")
        df_wide = df_wide.sort_values("match_date", ascending=False).reset_index(drop=True)

    # Redondear floats
    float_cols = [c for c in df_wide.columns if df_wide[c].dtype == float]
    for c in float_cols:
        df_wide[c] = df_wide[c].round(2)

    # ── PRIMERO: Parsear columnas con formato especial ───────────
    import re

    def parse_pct(val):
        if pd.isna(val): return None
        m = re.search(r'([\d.]+)\s*%', str(val).strip())
        return float(m.group(1)) if m else None

    def parse_fraction_ganados(val):
        if pd.isna(val): return None
        m = re.match(r'(\d+)\s*/\s*\d+', str(val).strip())
        return int(m.group(1)) if m else None

    def parse_fraction_disputados(val):
        if pd.isna(val): return None
        m = re.match(r'\d+\s*/\s*(\d+)', str(val).strip())
        return int(m.group(1)) if m else None

    def parse_fraction_pct(val):
        if pd.isna(val): return None
        m = re.search(r'\(([\d.]+)\s*%\)', str(val).strip())
        return float(m.group(1)) if m else None

    # Columnas de porcentaje simple (solo %)
    pct_only_cols = ["col_duelos_totales", "riv_duelos_totales"]
    for c in pct_only_cols:
        if c in df_wide.columns:
            df_wide[c] = df_wide[c].apply(parse_pct)

    # Columnas con formato ganados/disputados (%) — ANTES de la limpieza general
    fraction_cols = [
        ("col_duelos_suelo",       "col_duelos_suelo"),
        ("riv_duelos_suelo",       "riv_duelos_suelo"),
        ("col_duelos_aereos",      "col_duelos_aereos"),
        ("riv_duelos_aereos",      "riv_duelos_aereos"),
        ("col_dribbles",           "col_dribbles"),
        ("riv_dribbles",           "riv_dribbles"),
        ("col_fases_tercio_final", "col_fases_tercio_final"),
        ("riv_fases_tercio_final", "riv_fases_tercio_final"),
        ("col_pases_largos",       "col_pases_largos"),
        ("riv_pases_largos",       "riv_pases_largos"),
        ("col_centros",            "col_centros"),
        ("riv_centros",            "riv_centros"),
    ]

    new_cols = {}
    for orig_col, base_name in fraction_cols:
        if orig_col in df_wide.columns:
            new_cols[f"{base_name}_ganados"]    = df_wide[orig_col].apply(parse_fraction_ganados)
            new_cols[f"{base_name}_disputados"] = df_wide[orig_col].apply(parse_fraction_disputados)
            new_cols[f"{base_name}_pct"]        = df_wide[orig_col].apply(parse_fraction_pct)
            df_wide.drop(columns=[orig_col], inplace=True)

    if new_cols:
        df_wide = pd.concat([df_wide, pd.DataFrame(new_cols, index=df_wide.index)], axis=1)

    # ── DESPUÉS: Limpieza general de columnas restantes ──────────
    # Limpiar columnas de porcentaje simples
    pct_cols = [c for c in df_wide.columns if 'posesion' in c or 'pct' in c]
    for c in pct_cols:
        if df_wide[c].dtype == object:
            df_wide[c] = pd.to_numeric(
                df_wide[c].astype(str).str.replace('%','',regex=False)
                .str.replace(',','.',regex=False).str.strip(),
                errors='coerce'
            )

    # Limpiar TODAS las columnas col_ y riv_ que sean object
    metric_cols = [c for c in df_wide.columns if c.startswith('col_') or c.startswith('riv_')]
    for c in metric_cols:
        if df_wide[c].dtype == object:
            df_wide[c] = pd.to_numeric(
                df_wide[c].astype(str).str.replace('%','',regex=False)
                .str.replace(',','.',regex=False).str.strip(),
                errors='coerce'
            )

    # Limpiar columnas de porcentaje que vienen como string "45%"
    pct_cols = [c for c in df_wide.columns if 'posesion' in c or ('pct' in c and c not in pct_only_cols)]
    for c in pct_cols:
        if df_wide[c].dtype == object:
            df_wide[c] = (
                df_wide[c]
                .astype(str)
                .str.replace('%', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.strip()
            )
            df_wide[c] = pd.to_numeric(df_wide[c], errors='coerce')

    # Limpiar TODAS las columnas col_ y riv_ que sean object
    metric_cols = [c for c in df_wide.columns if c.startswith('col_') or c.startswith('riv_')]
    for c in metric_cols:
        if df_wide[c].dtype == object:
            df_wide[c] = (
                df_wide[c]
                .astype(str)
                .str.replace('%', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.strip()
            )
            df_wide[c] = pd.to_numeric(df_wide[c], errors='coerce')

    # Forzar punto decimal en todas las columnas numéricas
    for c in df_wide.select_dtypes(include='float').columns:
        df_wide[c] = df_wide[c].round(2)

    return df_wide


def get_metricas_disponibles() -> list[str]:
    """Retorna la lista de métricas en español disponibles."""
    return sorted(set(METRICAS_ES.values()))
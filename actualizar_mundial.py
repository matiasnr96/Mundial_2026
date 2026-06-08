"""
====================================================================
Mundial 2026 — Sports Analytics Pipeline
actualizar_mundial.py

Script de actualización para el Power BI UNIFICADO de 4 selecciones.

Descarga datos de Colombia, Argentina, España y México,
los combina en CSVs únicos con columna 'team' y los guarda
en exports/csv/mundial_2026/

También actualiza la tabla de posiciones de los grupos del Mundial.

USO:
    python actualizar_mundial.py

Para agregar/quitar selecciones: modificar la lista EQUIPOS.
====================================================================
"""

import sys
import json
import time
import logging
import importlib.util
from pathlib import Path
from datetime import datetime

try:
    from curl_cffi import requests
except ImportError:
    print("❌ curl_cffi no instalado. Ejecutar: pip install curl-cffi")
    sys.exit(1)

import pandas as pd
import numpy as np

# ════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(r"C:\Users\rodri\Desktop\Mundial 2026")

EQUIPOS = [
    {"team_id": 4820, "team_name": "Colombia"},
    {"team_id": 4819, "team_name": "Argentina"},
    {"team_id": 4698, "team_name": "España"},
    {"team_id": 4781, "team_name": "México"},
]

N_MATCHES = 10

# ════════════════════════════════════════════════════════════
# FILTRO MUNDIAL 2026 — descomentar cuando arranque el torneo
# ════════════════════════════════════════════════════════════
# WORLD_CUP_TOURNAMENT_ID = 16
# WORLD_CUP_SEASON_ID     = 58210
# SOLO_MUNDIAL = True   # ← cambiar a True el 11 de junio
SOLO_MUNDIAL = False

# Grupos del Mundial de nuestras 4 selecciones
GRUPOS_CONFIG = {
    "Colombia":  {"tournament_id": 3964, "group": "Grupo K"},
    "Argentina": {"tournament_id": 3963, "group": "Grupo J"},
    "España":    {"tournament_id": 3961, "group": "Grupo H"},
    "México":    {"tournament_id": 3954, "group": "Grupo A"},
}

NOMBRES_ES = {
    "Mexico": "México", "Spain": "España", "Argentina": "Argentina",
    "Colombia": "Colombia", "South Africa": "Sudáfrica",
    "South Korea": "Corea del Sur", "Czechia": "Rep. Checa",
    "Cabo Verde": "Cabo Verde", "Saudi Arabia": "Arabia Saudí",
    "Uruguay": "Uruguay", "Algeria": "Argelia", "Austria": "Austria",
    "Jordan": "Jordania", "Portugal": "Portugal",
    "DR Congo": "RD Congo", "Uzbekistan": "Uzbekistán",
}

OUTPUT_DIR = PROJECT_ROOT / "exports" / "csv" / "mundial_2026"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ── Logging ──────────────────────────────────────────────────
today = datetime.now().strftime("%Y%m%d_%H%M%S")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            LOGS_DIR / f"update_mundial_{today}.log",
            encoding="utf-8"
        ),
    ]
)
log = logging.getLogger("mundial")

# ── HTTP ─────────────────────────────────────────────────────
BASE_URL = "https://www.sofascore.com/api/v1"
DELAY    = 2.5

HEADERS = {
    "User-Agent":         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Accept":             "*/*",
    "Accept-Language":    "es-ES,es;q=0.9",
    "Referer":            "https://www.sofascore.com/es-la/football/match/argentina-zambia/vUbsuWb",
    "sec-ch-ua":          '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile":   "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest":     "empty",
    "sec-fetch-mode":     "cors",
    "sec-fetch-site":     "same-origin",
    "x-requested-with":   "2f0326",
    "x-captcha":          "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3ODA1NTY0NTQsImlwIjoiMTgxLjk3LjE4My4xMTMifQ.PtctkNB25wNzxN_lTMvNiHbFYumupKD2qvDCONLDaFs",
}

COOKIES = "_adv_sid=391d4c72-26fd-4180-a100-432112cd5c55; _adv_uid=51b01bff-b40e-4ba9-942f-88486014e14f; AD_VERGE_SESSION_COOKIE_V1=0d927cb0-ba9e-4be1-b8b2-bb6540527503; ssp_test=control; __gads=ID=d144400d71a5b95a:T=1780552850:RT=1780552850:S=ALNI_Mbz8Tt3oPZGEPMsitCcF6vnlhZ3wA; __gpi=UID=000013b2c8857087:T=1780552850:RT=1780552850:S=ALNI_MZ5dYgv6muQDhFyJv1N8ypSayTb3w; __eoi=ID=54cb5e738f10a4d8:T=1780552850:RT=1780552850:S=AA-AfjZ8hPmYJjI8z6mFTGj9hL-h; _gcl_au=1.1.1835862270.1780552850; _ga=GA1.1.1457987302.1780552850; hb_insticator_uid=846b577f-ecb8-4711-a4f3-5f8183ab41a0; cto_bundle=9sSUOV9DY2pka0h4N3IyMHdNTTRkTDBEYjRQQU9oVFZQVHc0Wk9ZUXBZMjE3OXlITHI0TkZVa0paS2NqMFVvVVIxZGRZa0JmR2s3UDdmSTZwZ2Zod3olMkJOT2V2YzhjSEkwbFJsT0FzVThOSFFsdEk4MVg5bDRFbDd2NXR6TCUyQlZaTEQxNHY; _ga_HNQ9P9MGZR=GS2.1.s1780552850$o1$g1$t1780552918$j60$l0$h0"

session = requests.Session(impersonate="chrome124")
session.headers.update(HEADERS)
session.cookies.update({k.strip(): v for k, v in (c.split("=", 1) for c in COOKIES.split("; ") if "=" in c)})


def get(endpoint: str) -> dict | None:
    url = f"{BASE_URL}{endpoint}"
    for attempt in range(1, 4):
        try:
            resp = session.get(url, timeout=10)
            if resp.status_code == 200:
                time.sleep(DELAY)
                return resp.json()
            elif resp.status_code == 429:
                wait = 6 * attempt
                log.warning(f"Rate limit — esperando {wait}s...")
                time.sleep(wait)
            elif resp.status_code == 404:
                return None
            else:
                time.sleep(4)
        except Exception as e:
            log.error(f"Error (intento {attempt}): {e}")
            time.sleep(4)
    return None


def save_json(data: dict, folder: Path, name: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ════════════════════════════════════════════════════════════
# PARSERS
# ════════════════════════════════════════════════════════════

def parse_match_statistics(data: dict, match_id: int) -> pd.DataFrame:
    rows = []
    for pb in data.get("statistics", []):
        period = pb.get("period", "ALL")
        for group in pb.get("groups", []):
            for item in group.get("statisticsItems", []):
                rows.append({
                    "match_id":   match_id,
                    "period":     period,
                    "group":      group.get("groupName"),
                    "stat_name":  item.get("name"),
                    "home_value": item.get("home"),
                    "away_value": item.get("away"),
                })
    return pd.DataFrame(rows)


def parse_lineups(data: dict, match_id: int) -> pd.DataFrame:
    rows = []
    def sf(v):
        try: return float(v) if v is not None else None
        except: return None

    for side in ["home", "away"]:
        if side not in data: continue
        sd = data[side]
        for entry in sd.get("players", []):
            p = entry.get("player", {})
            s = entry.get("statistics", {})
            rows.append({
                "match_id":          match_id,
                "side":              side,
                "formation":         sd.get("formation"),
                "player_id":         p.get("id"),
                "player_name":       p.get("name"),
                "player_shortname":  p.get("shortName"),
                "position":          p.get("position"),
                "jersey_number":     p.get("jerseyNumber"),
                "is_starter":        entry.get("substitute") is False,
                "country":           p.get("country", {}).get("name") if isinstance(p.get("country"), dict) else None,
                "rating":            sf(s.get("rating")),
                "minutes_played":    s.get("minutesPlayed"),
                "goals":             s.get("goals", 0),
                "assists":           s.get("goalAssist", 0),
                "shots_on_target":   s.get("onTargetScoringAttempt", 0),
                "shots_off_target":  s.get("shotOffTarget", 0),
                "key_passes":        s.get("keyPass", 0),
                "accurate_passes":   s.get("accuratePass"),
                "total_passes":      s.get("totalPass"),
                "pass_accuracy_pct": sf(s.get("accuratePassesPercentage")),
                "duels_won":         s.get("duelWon"),
                "duels_total":       s.get("totalDuels"),
                "interceptions":     s.get("interceptionWon"),
                "yellow_cards":      s.get("yellowCard", 0),
                "red_cards":         s.get("redCard", 0),
                "expected_goals":    sf(s.get("expectedGoals")),
                "expected_assists":  sf(s.get("expectedAssists")),
            })
    return pd.DataFrame(rows)


def parse_incidents(data: dict, match_id: int) -> pd.DataFrame:
    rows = []
    for inc in data.get("incidents", []):
        def gn(key, field):
            obj = inc.get(key)
            return obj.get(field) if isinstance(obj, dict) else None
        rows.append({
            "match_id":        match_id,
            "incident_type":   inc.get("incidentType"),
            "incident_class":  inc.get("incidentClass"),
            "minute":          inc.get("time"),
            "is_home":         inc.get("isHome"),
            "player_id":       gn("player", "id"),
            "player_name":     gn("player", "name"),
            "assist_name":     gn("assist1", "name"),
            "player_in_name":  gn("playerIn", "name"),
            "player_out_name": gn("playerOut", "name"),
            "score_home":      inc.get("homeScore"),
            "score_away":      inc.get("awayScore"),
        })
    return pd.DataFrame(rows)


# ════════════════════════════════════════════════════════════
# ENRIQUECIMIENTO DE STATS POR JUGADOR
# ════════════════════════════════════════════════════════════

def enrich_player_stats(df_lin: pd.DataFrame, match_ids: list, team_name: str = "") -> pd.DataFrame:
    """
    Enriquece el DataFrame de lineups con estadísticas detalladas
    por jugador usando /event/{match_id}/player/{player_id}/statistics.

    Mejoras aplicadas:
    1. Solo enriquece jugadores de nuestra selección (no el rival)
    2. Delay aleatorio entre 2 y 4 segundos
    3. Checkpointing — guarda JSONs en disco para no repetir requests
    4. Delay extra aleatorio entre partidos
    """
    import random

    if df_lin.empty:
        return df_lin

    log.info("  📡 Enriqueciendo stats por jugador (solo nuestra selección)...")
    enriched_rows = []
    players_enriched = 0
    skipped_cache = 0

    # Carpeta de cache para stats por jugador
    CACHE_DIR = PROJECT_ROOT / "data" / "raw" / "player_stats" / team_name
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    for match_id in match_ids:
        df_match = df_lin[df_lin["match_id"] == match_id]

        # ── MEJORA 1: Solo jugadores de nuestra selección ────
        if "is_target_team" in df_match.columns:
            df_match = df_match[df_match["is_target_team"] == True]

        players_played = df_match[
            df_match["minutes_played"].notna() &
            (df_match["minutes_played"] > 0)
        ]["player_id"].dropna().astype(int).tolist()

        for player_id in players_played:
            # ── MEJORA 3: Checkpointing ───────────────────────
            cache_path = CACHE_DIR / f"stats_{match_id}_{player_id}.json"
            if cache_path.exists():
                try:
                    with open(cache_path, encoding="utf-8") as f:
                        data = json.load(f)
                    skipped_cache += 1
                except:
                    data = None
            else:
                # ── MEJORA 2 y 4: Delay aleatorio ────────────
                time.sleep(random.uniform(2.0, 4.0))
                data = get(f"/event/{match_id}/player/{player_id}/statistics")
                if data:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False)

            if not data or "statistics" not in data:
                continue

            s = data["statistics"]

            d_won   = s.get("duelWon", 0) or 0
            d_lost  = s.get("duelLost", 0) or 0
            d_total = d_won + d_lost

            acc_p = s.get("accuratePass")
            tot_p = s.get("totalPass")
            pct_p = round(acc_p / tot_p * 100, 1) if acc_p and tot_p and tot_p > 0 else None

            enriched_rows.append({
                "match_id":             match_id,
                "player_id":            player_id,
                # Duelos
                "duels_total":          d_total if d_total > 0 else None,
                "duels_won":            d_won   if d_won  > 0 else None,
                "duels_lost":           d_lost  if d_lost > 0 else None,
                "duels_won_pct":        round(d_won / d_total * 100, 1) if d_total > 0 else None,
                # Duelos aéreos
                "aerial_won":           s.get("aerialWon"),
                "aerial_lost":          s.get("aerialLost"),
                "aerial_total":         (s.get("aerialWon") or 0) + (s.get("aerialLost") or 0) or None,
                "aerial_won_pct":       round(s.get("aerialWon",0) / ((s.get("aerialWon",0) + s.get("aerialLost",0)) or 1) * 100, 1)
                                        if (s.get("aerialWon") or s.get("aerialLost")) else None,
                # Entradas
                "tackles_total":        s.get("totalTackle"),
                "tackles_won":          s.get("wonTackle"),
                # Pases
                "pass_accuracy_pct":    pct_p,
                "long_balls_total":     s.get("totalLongBalls"),
                "long_balls_accurate":  s.get("accurateLongBalls"),
                "crosses_total":        s.get("totalCross"),
                "opp_half_passes":      s.get("totalOppositionHalfPasses"),
                "opp_half_passes_acc":  s.get("accurateOppositionHalfPasses"),
                # Defensa
                "ball_recoveries":      s.get("ballRecovery"),
                "clearances":           s.get("totalClearance"),
                "possession_lost":      s.get("possessionLostCtrl"),
                # Ataque
                "total_shots":          s.get("totalShots"),
                "big_chances_missed":   s.get("bigChanceMissed"),
                "big_chances_created":  s.get("bigChanceCreated"),
                "hit_woodwork":         s.get("hitWoodwork"),
                "touches":              s.get("touches"),
                "bad_touches":          s.get("unsuccessfulTouch"),
                "dispossessed":         s.get("dispossessed"),
                "dribbles_attempted":   s.get("totalContest"),
                "dribbles_won":         s.get("wonContest"),
                "dribbles":             s.get("ballCarriesCount"),
                "dribble_distance_m":   round(s.get("totalBallCarriesDistance", 0), 1),
                "progressive_carries":  s.get("progressiveBallCarriesCount"),
                # Disciplina
                "fouls_committed":      s.get("fouls"),
                "fouls_received":       s.get("wasFouled"),
                "offsides":             s.get("totalOffside"),
                # Porteros
                "saves":                s.get("saves"),
                "keeper_save_value":    s.get("keeperSaveValue"),
                # Valores de acción
                "shot_value":           s.get("shotValueNormalized"),
                "pass_value":           s.get("passValueNormalized"),
                "dribble_value":        s.get("dribbleValueNormalized"),
                "defensive_value":      s.get("defensiveValueNormalized"),
                "goalkeeper_value":     s.get("goalkeeperValueNormalized"),
            })
            players_enriched += 1

        # Pausa extra aleatoria entre partidos
        time.sleep(random.uniform(1.0, 3.0))

    log.info(f"  ✅ {players_enriched} jugadores enriquecidos ({skipped_cache} desde cache)")

    if not enriched_rows:
        return df_lin

    df_enriched = pd.DataFrame(enriched_rows)
    df_enriched["player_id"] = df_enriched["player_id"].astype("Int64")
    df_enriched["match_id"]  = df_enriched["match_id"].astype("Int64")

    df_lin["player_id"] = pd.to_numeric(df_lin["player_id"], errors="coerce").astype("Int64")
    df_lin["match_id"]  = pd.to_numeric(df_lin["match_id"],  errors="coerce").astype("Int64")

    cols_new = [c for c in df_enriched.columns if c not in ["match_id", "player_id"]]

    df_lin = df_lin.merge(
        df_enriched[["match_id", "player_id"] + cols_new],
        on=["match_id", "player_id"],
        how="left",
        suffixes=("", "_enr")
    )

    for col in cols_new:
        col_enr = f"{col}_enr"
        if col_enr in df_lin.columns:
            if col in df_lin.columns:
                df_lin[col] = df_lin[col].combine_first(df_lin[col_enr])
            else:
                df_lin[col] = df_lin[col_enr]
            df_lin.drop(columns=[col_enr], inplace=True)

    # Columnas calculadas
    if "shots_on_target" in df_lin.columns and "shots_off_target" in df_lin.columns:
        df_lin["total_shots"] = df_lin["total_shots"].combine_first(
            df_lin["shots_on_target"].fillna(0) + df_lin["shots_off_target"].fillna(0)
        )

    # Forzar tipos numéricos en TODAS las columnas antes de calcular
    numeric_cols = [
        "minutes_played", "total_shots", "shots_on_target", "shots_off_target",
        "goals", "assists", "accurate_passes", "total_passes",
        "ball_recoveries", "duels_won", "duels_total", "duels_lost",
        "tackles_total", "tackles_won", "crosses_total", "possession_lost",
        "touches", "dribbles", "progressive_carries",
        "pass_accuracy_pct", "duels_won_pct",
    ]
    for col in numeric_cols:
        if col in df_lin.columns:
            df_lin[col] = pd.to_numeric(df_lin[col], errors="coerce")

    # Forzar TODOS los tipos object a numérico antes de cualquier cálculo
    for col in df_lin.columns:
        if df_lin[col].dtype == object:
            try:
                cleaned = df_lin[col].astype(str).str.replace('%','',regex=False).str.strip()
                converted = pd.to_numeric(cleaned, errors="coerce")
                # Solo reemplazar si la mayoría son numéricos
                if converted.notna().sum() > df_lin[col].notna().sum() * 0.3:
                    df_lin[col] = converted
            except Exception:
                pass

    def safe_div(a, b, scale=1, decimals=1):
        """División segura que siempre retorna numérico."""
        num_a = pd.to_numeric(a, errors="coerce")
        num_b = pd.to_numeric(b, errors="coerce")
        result = num_a / num_b.replace(0, np.nan) * scale
        return result.round(decimals)

    # Recalcular pass_accuracy si sigue vacía
    if "pass_accuracy_pct" in df_lin.columns:
        acc = pd.to_numeric(df_lin.get("accurate_passes"), errors="coerce")
        tot = pd.to_numeric(df_lin.get("total_passes"), errors="coerce")
        pct = (acc / tot.replace(0, np.nan) * 100).round(1)
        df_lin["pass_accuracy_pct"] = pd.to_numeric(df_lin["pass_accuracy_pct"], errors="coerce")
        df_lin["pass_accuracy_pct"] = df_lin["pass_accuracy_pct"].combine_first(pct)

    # Columnas calculadas con división segura
    df_lin["mins_per_shot"] = safe_div(
        df_lin.get("minutes_played"), df_lin.get("total_shots"))

    df_lin["mins_per_shot_on_target"] = safe_div(
        df_lin.get("minutes_played"), df_lin.get("shots_on_target"))

    goals   = pd.to_numeric(df_lin.get("goals"), errors="coerce").fillna(0)
    assists = pd.to_numeric(df_lin.get("assists"), errors="coerce").fillna(0)
    mins    = pd.to_numeric(df_lin.get("minutes_played"), errors="coerce")
    df_lin["g_a_per90"] = ((goals + assists) / mins.replace(0, np.nan) * 90).round(2)

    df_lin["passes_per90"] = safe_div(
        pd.to_numeric(df_lin.get("accurate_passes"), errors="coerce").fillna(0),
        df_lin.get("minutes_played"), scale=90)

    if "ball_recoveries" in df_lin.columns:
        df_lin["recoveries_per90"] = safe_div(
            pd.to_numeric(df_lin.get("ball_recoveries"), errors="coerce").fillna(0),
            df_lin.get("minutes_played"), scale=90)

    return df_lin


# ════════════════════════════════════════════════════════════
# GRUPOS DEL MUNDIAL
# ════════════════════════════════════════════════════════════

def fetch_grupos_mundial() -> pd.DataFrame:
    """
    Descarga la tabla de posiciones actualizada de los 4 grupos
    de nuestras selecciones desde SofaScore.
    """
    log.info("📡 Actualizando tabla de grupos del Mundial 2026...")

    data = get("/unique-tournament/16/season/58210/standings/total")
    if not data or "standings" not in data:
        log.warning("⚠️  No se pudo obtener standings del Mundial")
        return pd.DataFrame()

    GRUPOS_INTERES = {
        "FIFA World Cup, Group A": "Grupo A",
        "FIFA World Cup, Group H": "Grupo H",
        "FIFA World Cup, Group J": "Grupo J",
        "FIFA World Cup, Group K": "Grupo K",
    }

    SELECCION_GRUPO = {
        "Grupo A": "México",
        "Grupo H": "España",
        "Grupo J": "Argentina",
        "Grupo K": "Colombia",
    }

    rows = []
    for standing in data["standings"]:
        grupo_raw = standing.get("tournament", {}).get("name", "")
        if grupo_raw not in GRUPOS_INTERES:
            continue

        grupo_es = GRUPOS_INTERES[grupo_raw]

        for row in standing.get("rows", []):
            team    = row.get("team", {})
            nombre  = NOMBRES_ES.get(team.get("name", ""), team.get("name", ""))
            team_id = team.get("id", "")

            rows.append({
                "grupo":               grupo_es,
                "seleccion_analizada": SELECCION_GRUPO[grupo_es],
                "posicion":            row.get("position"),
                "equipo":              nombre,
                "team_id":             team_id,
                "PJ":                  row.get("matches", 0),
                "PG":                  row.get("wins", 0),
                "PE":                  row.get("draws", 0),
                "PP":                  row.get("losses", 0),
                "GF":                  row.get("scoresFor", 0),
                "GC":                  row.get("scoresAgainst", 0),
                "DIF":                 row.get("scoreDiffFormatted", 0),
                "PTS":                 row.get("points", 0),
                "escudo_url":          f"https://api.sofascore.app/api/v1/team/{team_id}/image",
                "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

    df_grupos = pd.DataFrame(rows).sort_values(["grupo", "posicion"]).reset_index(drop=True)
    log.info(f"  ✅ Grupos actualizados: {len(df_grupos)} equipos en {df_grupos['grupo'].nunique()} grupos")
    return df_grupos


# ════════════════════════════════════════════════════════════
# POSICIÓN
# ════════════════════════════════════════════════════════════

POS_MAP = {
    "G": "GK", "GK": "GK",
    "D": "DEF", "DC": "DEF", "DL": "DEF", "DR": "DEF", "WB": "DEF",
    "M": "MID", "MC": "MID", "ML": "MID", "MR": "MID", "DM": "MID", "AM": "MID",
    "F": "FWD", "ST": "FWD", "SS": "FWD", "FW": "FWD", "LW": "FWD", "RW": "FWD",
}


# ════════════════════════════════════════════════════════════
# EXTRACCIÓN POR EQUIPO
# ════════════════════════════════════════════════════════════

def fetch_team_data(team_id: int, team_name: str) -> dict:
    log.info(f"{'─'*50}")
    log.info(f"  {team_name} (ID: {team_id})")
    log.info(f"{'─'*50}")

    RAW_STATS   = PROJECT_ROOT / "data" / "raw" / "stats"   / team_name
    RAW_LINEUPS = PROJECT_ROOT / "data" / "raw" / "lineups" / team_name
    RAW_EVENTS  = PROJECT_ROOT / "data" / "raw" / "events"  / team_name

    for d in [RAW_STATS, RAW_LINEUPS, RAW_EVENTS]:
        d.mkdir(parents=True, exist_ok=True)

    # ── Últimos partidos ──────────────────────────────────
    log.info("  📡 Obteniendo partidos...")
    all_matches_raw = []
    for page in range(3):
        data = get(f"/team/{team_id}/events/last/{page}")
        if not data or "events" not in data or len(data["events"]) == 0:
            break
        all_matches_raw.extend(data["events"])

    # ════════════════════════════════════════════════════
    # FILTRO MUNDIAL 2026
    # Descomentar el 11 de junio cuando arranque el torneo
    # if SOLO_MUNDIAL:
    #     all_matches_raw = [
    #         m for m in all_matches_raw
    #         if m.get("tournament", {}).get("uniqueTournament", {}).get("id") == 16
    #     ]
    #     log.info(f"  Filtro Mundial aplicado")
    # ════════════════════════════════════════════════════

    completed = [
        m for m in all_matches_raw
        if m.get("status", {}).get("description") in
        ["Ended", "Finished", "After Penalties", "After Extra Time"]
    ]
    completed = sorted(
        completed,
        key=lambda m: m.get("startTimestamp", 0),
        reverse=True
    )[:N_MATCHES]

    log.info(f"  ✅ {len(completed)} partidos")

    if not completed:
        log.warning(f"  ⚠️  Sin partidos para {team_name} — puede ser rate limit de SofaScore. Reintentá más tarde.")
        return {
            "matches":          pd.DataFrame(),
            "lineups_all":      pd.DataFrame(),
            "player_per_match": pd.DataFrame(),
            "player_master":    pd.DataFrame(),
            "team_stats":       pd.DataFrame(),
            "events":           pd.DataFrame(),
        }

    # ── DataFrame de partidos ─────────────────────────────
    rows_m = []
    for m in completed:
        home_id = m.get("homeTeam", {}).get("id")
        away_id = m.get("awayTeam", {}).get("id")
        is_home = home_id == team_id
        hs  = m.get("homeScore", {}).get("current")
        as_ = m.get("awayScore", {}).get("current")

        def get_result(hs, as_, is_home):
            try:
                hs, as_ = float(hs), float(as_)
                if is_home: return "W" if hs>as_ else ("L" if hs<as_ else "D")
                else:       return "W" if as_>hs else ("L" if as_<hs else "D")
            except: return None

        rows_m.append({
            "team":          team_name,
            "match_id":      m.get("id"),
            "tournament":    m.get("tournament", {}).get("name"),
            "status":        m.get("status", {}).get("description"),
            "match_date":    pd.to_datetime(m.get("startTimestamp"), unit="s", errors="coerce"),
            "home_team":     m.get("homeTeam", {}).get("name"),
            "home_team_id":  home_id,
            "away_team":     m.get("awayTeam", {}).get("name"),
            "away_team_id":  away_id,
            "home_score":    hs,
            "away_score":    as_,
            "side":          "home" if is_home else "away",
            "result":        get_result(hs, as_, is_home),
            "goals_for":     float(hs) if is_home else (float(as_) if hs is not None and as_ is not None else None),
            "goals_against": float(as_) if is_home else (float(hs) if hs is not None and as_ is not None else None),
            "rival":         m.get("awayTeam", {}).get("name") if is_home else m.get("homeTeam", {}).get("name"),
        })

    df_matches = pd.DataFrame(rows_m)
    if "goals_against" in df_matches.columns:
        df_matches["clean_sheet"] = df_matches["goals_against"] == 0

    match_ids = df_matches["match_id"].dropna().astype(int).tolist()

    # ── Detalles por partido ──────────────────────────────
    log.info("  📡 Descargando detalles de partidos...")
    all_lineups, all_stats, all_events = [], [], []
    nuevos = 0

    for mid in match_ids:
        sf_path = RAW_STATS   / f"match_stats_{mid}.json"
        lf_path = RAW_LINEUPS / f"lineups_{mid}.json"
        ef_path = RAW_EVENTS  / f"incidents_{mid}.json"

        stats_json = load_json(sf_path) if sf_path.exists() else get(f"/event/{mid}/statistics")
        if stats_json and not sf_path.exists():
            save_json(stats_json, RAW_STATS, f"match_stats_{mid}"); nuevos += 1
        if stats_json:
            df = parse_match_statistics(stats_json, mid)
            if not df.empty: all_stats.append(df)

        lineup_json = load_json(lf_path) if lf_path.exists() else get(f"/event/{mid}/lineups")
        if lineup_json and not lf_path.exists():
            save_json(lineup_json, RAW_LINEUPS, f"lineups_{mid}"); nuevos += 1
        if lineup_json:
            df = parse_lineups(lineup_json, mid)
            if not df.empty: all_lineups.append(df)

        events_json = load_json(ef_path) if ef_path.exists() else get(f"/event/{mid}/incidents")
        if events_json and not ef_path.exists():
            save_json(events_json, RAW_EVENTS, f"incidents_{mid}"); nuevos += 1
        if events_json:
            df = parse_incidents(events_json, mid)
            if not df.empty: all_events.append(df)

        time.sleep(0.5)

    log.info(f"  ✅ {nuevos} archivos nuevos descargados")

    # ── Consolidar y enriquecer lineups ──────────────────
    df_lin  = pd.DataFrame()
    df_team = pd.DataFrame()

    if all_lineups:
        df_lin = pd.concat(all_lineups, ignore_index=True)

        # Merge con matches ANTES del enriquecimiento para tener home_team_id
        df_lin = df_lin.merge(
            df_matches[["match_id","match_date","tournament","home_team",
                        "home_team_id","away_team","away_team_id",
                        "home_score","away_score","result","rival"]],
            on="match_id", how="left"
        )

        # Calcular is_target_team correctamente
        def get_side_pre(row):
            try:
                return "home" if int(pd.to_numeric(row.get("home_team_id"), errors="coerce")) == team_id else "away"
            except: return "away"

        df_lin["target_side"]    = df_lin.apply(get_side_pre, axis=1)
        df_lin["is_target_team"] = df_lin["side"] == df_lin["target_side"]
        df_lin["team"]           = team_name

        # Enriquecer SOLO jugadores de nuestra selección
        df_lin = enrich_player_stats(df_lin, match_ids, team_name=team_name)

        df_team = df_lin[df_lin["is_target_team"]].copy()

    # ── Player master ─────────────────────────────────────
    df_master = pd.DataFrame()
    if not df_team.empty and "player_name" in df_team.columns:
        agg = {}
        def add(key, col, func):
            if col in df_team.columns: agg[key] = (col, func)

        add("partidos",              "match_id",            "count")
        add("titularidades",         "is_starter",          "sum")
        add("rating_prom",           "rating",              "mean")
        add("rating_max",            "rating",              "max")
        add("minutos_total",         "minutes_played",      "sum")
        add("minutos_prom",          "minutes_played",      "mean")
        add("goles",                 "goals",               "sum")
        add("asistencias",           "assists",             "sum")
        add("xG_total",              "expected_goals",      "sum")
        add("tiros_arco",            "shots_on_target",     "sum")
        add("tiros_fuera",           "shots_off_target",    "sum")
        add("tiros_totales",         "total_shots",         "sum")
        add("pase_pct_prom",         "pass_accuracy_pct",   "mean")
        add("pases_precisos_total",  "accurate_passes",     "sum")
        add("pases_totales_total",   "total_passes",        "sum")
        add("duelos_ganados",        "duels_won",           "sum")
        add("duelos_totales",        "duels_total",         "sum")
        add("duelos_pct_prom",       "duels_won_pct",       "mean")
        add("recuperaciones",        "ball_recoveries",     "sum")
        add("dribbles",              "dribbles",            "sum")
        add("centros",               "crosses_total",       "sum")
        add("intercepciones",        "interceptions",       "sum")
        add("entradas_total",        "tackles_total",       "sum")
        add("entradas_ganadas",      "tackles_won",         "sum")
        add("amarillas",             "yellow_cards",        "sum")
        add("rojas",                 "red_cards",           "sum")
        add("g_a_per90_prom",        "g_a_per90",           "mean")
        add("passes_per90_prom",     "passes_per90",        "mean")
        add("recoveries_per90_prom", "recoveries_per90",    "mean")
        add("duelos_aereos_ganados", "aerial_won",          "sum")
        add("duelos_aereos_total",   "aerial_total",        "sum")
        add("duelos_aereos_pct",     "aerial_won_pct",      "mean")
        add("faltas_cometidas",      "fouls_committed",     "sum")
        add("faltas_recibidas",      "fouls_received",      "sum")
        add("grandes_ocasiones_falladas", "big_chances_missed", "sum")
        add("grandes_ocasiones_creadas",  "big_chances_created","sum")
        add("palos",                 "hit_woodwork",        "sum")
        add("despejes",              "clearances",          "sum")
        add("regates_intentados",    "dribbles_attempted",  "sum")
        add("regates_ganados",       "dribbles_won",        "sum")
        add("toques_malos",          "bad_touches",         "sum")
        add("fueras_juego",          "offsides",            "sum")
        add("atajadas",              "saves",               "sum")

        group_cols = ["player_name", "position", "player_id"] if "player_id" in df_team.columns else ["player_name", "position"]

        if agg:
            df_master = df_team.groupby(group_cols, as_index=False).agg(**agg).round(2)

            if "goles" in df_master.columns and "asistencias" in df_master.columns:
                df_master["contribuciones_gol"] = df_master["goles"] + df_master["asistencias"]
            if "position" in df_master.columns:
                df_master["position_group"] = df_master["position"].map(POS_MAP).fillna("Unknown")
            if "player_id" in df_master.columns:
                df_master["foto_url"] = df_master["player_id"].apply(
                    lambda pid: f"https://api.sofascore.app/api/v1/player/{int(pid)}/image"
                    if pd.notna(pid) and str(pid) != "" else ""
                )

            df_master["team"] = team_name
            df_master = df_master.sort_values("rating_prom", ascending=False).reset_index(drop=True)

    # Stats y eventos
    df_stats = pd.concat(all_stats, ignore_index=True) if all_stats else pd.DataFrame()
    if not df_stats.empty:
        df_stats["team"] = team_name

    df_events = pd.concat(all_events, ignore_index=True) if all_events else pd.DataFrame()
    if not df_events.empty:
        df_events["team"] = team_name
        df_events = df_events.merge(
            df_matches[["match_id","match_date","tournament","home_team","away_team","rival"]],
            on="match_id", how="left"
        )

    if not df_lin.empty:
        df_lin["team"] = team_name

    log.info(f"  ✅ {team_name} procesado")

    return {
        "matches":          df_matches,
        "lineups_all":      df_lin,
        "player_per_match": df_team,
        "player_master":    df_master,
        "team_stats":       df_stats,
        "events":           df_events,
    }


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════

def main():
    start = datetime.now()
    log.info("=" * 55)
    log.info(f"  MUNDIAL 2026 — Actualización completa")
    log.info(f"  {start.strftime('%d/%m/%Y %H:%M')}")
    log.info(f"  Selecciones: {[e['team_name'] for e in EQUIPOS]}")
    log.info("=" * 55)

    all_data = {key: [] for key in ["matches","lineups_all","player_per_match","player_master","team_stats","events"]}

    for equipo in EQUIPOS:
        try:
            result = fetch_team_data(equipo["team_id"], equipo["team_name"])
            for key in all_data:
                if isinstance(result[key], pd.DataFrame) and not result[key].empty:
                    all_data[key].append(result[key])
        except Exception as e:
            log.error(f"❌ Error procesando {equipo['team_name']}: {e}")
            import traceback
            log.error(traceback.format_exc())
            continue

    # ── Combinar y guardar CSVs ───────────────────────────
    log.info("")
    log.info("💾 Combinando y guardando CSVs unificados...")

    for name, dfs in all_data.items():
        if not dfs:
            log.warning(f"  ⚠️  {name}: sin datos")
            continue

        df_combined = pd.concat(dfs, ignore_index=True)

        # Pivot team_stats
        if name == "team_stats" and not df_combined.empty:
            try:
                spec = importlib.util.spec_from_file_location(
                    "team_stats_pivot",
                    PROJECT_ROOT / "src" / "transformation" / "team_stats_pivot.py"
                )
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                pivoted_dfs = []
                matches_combined = pd.concat(all_data["matches"], ignore_index=True) if all_data["matches"] else pd.DataFrame()

                for equipo in EQUIPOS:
                    tn = equipo["team_name"]
                    df_ts = df_combined[df_combined["team"] == tn]
                    df_tm = matches_combined[matches_combined["team"] == tn] if not matches_combined.empty else pd.DataFrame()

                    if not df_ts.empty and not df_tm.empty:
                        df_piv = mod.pivot_team_stats(df_ts, df_tm, equipo["team_id"])
                        if not df_piv.empty:
                            df_piv["team"] = tn
                            pivoted_dfs.append(df_piv)

                if pivoted_dfs:
                    df_combined = pd.concat(pivoted_dfs, ignore_index=True)
            except Exception as e:
                log.warning(f"  ⚠️  No se pudo pivotar team_stats: {e}")

        path = OUTPUT_DIR / f"final_{name}.csv"
        df_combined.to_csv(path, index=False, encoding="utf-8-sig", decimal=",")
        log.info(f"  ✅ final_{name}.csv  →  {df_combined.shape[0]} filas × {df_combined.shape[1]} cols")

    # ── Actualizar grupos del Mundial ─────────────────────
    log.info("")
    log.info("📊 Actualizando grupos del Mundial 2026...")
    df_grupos = fetch_grupos_mundial()
    if not df_grupos.empty:
        grupos_path = OUTPUT_DIR / "grupos_mundial_2026.csv"
        df_grupos.to_csv(grupos_path, index=False, encoding="utf-8-sig", decimal=",")
        # También actualizar en exports/csv/ para el pbix individual
        df_grupos.to_csv(
            PROJECT_ROOT / "exports" / "csv" / "grupos_mundial_2026.csv",
            index=False, encoding="utf-8-sig", decimal=","
        )
        log.info(f"  ✅ grupos_mundial_2026.csv actualizado")

    elapsed = (datetime.now() - start).seconds
    log.info("")
    log.info(f"✅ Actualización completada en {elapsed}s")
    log.info(f"   CSVs en: exports/csv/mundial_2026/")
    log.info(f"   Grupos en: exports/csv/grupos_mundial_2026.csv")
    log.info("=" * 55)


if __name__ == "__main__":
    main()
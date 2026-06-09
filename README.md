# ⚽ Mundial 2026 — Sports Analytics Pipeline

Pipeline de Data Engineering + Sports Analytics que extrae datos de SofaScore y alimenta dashboards Power BI para las 4 selecciones del Mundial 2026.

**Selecciones analizadas:** 🇨🇴 Colombia · 🇦🇷 Argentina · 🇪🇸 España · 🇲🇽 México

---

## 📊 Dashboard Power BI

El archivo `.pbix` incluye:
- Estadísticas por partido y por jugador
- Mapa de grupos del Mundial
- Comparativas de equipos (duelos, posesión, pases, xG)
- Fichas individuales con foto de jugador
- Temas personalizados por selección

---

## 🗂️ Estructura del proyecto

```
Mundial 2026/
├── actualizar_mundial.py              ← Script principal (extracción + transformación)
├── src/
│   └── transformation/
│       └── team_stats_pivot.py        ← Pivot de estadísticas de equipo
├── exports/
│   └── csv/
│       ├── mundial_2026/
│       │   ├── final_matches.csv              (partidos)
│       │   ├── final_player_per_match.csv     (jugadores por partido)
│       │   ├── final_player_master.csv        (resumen por jugador)
│       │   ├── final_team_stats.csv           (stats de equipo)
│       │   ├── final_events.csv               (goles, tarjetas, cambios)
│       │   └── final_lineups_all.csv          (lineups completos)
│       └── grupos_mundial_2026.csv
├── powerbi/
│   ├── Mundial2026.pbix               ← Dashboard Power BI
│   ├── tema_colombia.json
│   └── tema_argentina.json
├── requirements.txt
└── README.md
```

---

## ⚙️ Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/matiasnr96/mundial-2026.git
cd mundial-2026
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Obtener cookies de SofaScore

SofaScore requiere cookies reales del navegador para evitar bloqueos 403.

1. Abrí Chrome y navegá a [sofascore.com](https://www.sofascore.com)
2. Presioná `F12` → pestaña **Network**
3. Hacé clic en cualquier request a la API → **Copy as cURL**
4. Actualizá las variables `HEADERS` y `COOKIES` al inicio de `actualizar_mundial.py`

> ⚠️ El token `x-captcha` expira en minutos. Copiá y ejecutá inmediatamente.  
> Si obtenés error 403: esperá unos minutos, abrí Chrome en incógnito, y repetí el proceso.

### 4. Ejecutar el pipeline

```bash
python actualizar_mundial.py
```

El script descarga los datos, los transforma y actualiza todos los CSVs en `exports/csv/mundial_2026/`.

---

## 📁 CSVs incluidos

Los CSVs en `exports/csv/mundial_2026/` están listos para usar directamente en Power BI.

| Archivo | Filas | Columnas | Descripción |
|---|---|---|---|
| `final_matches.csv` | ~40 | 17 | Partidos disputados |
| `final_player_per_match.csv` | ~980 | 83 | Stats por jugador por partido |
| `final_player_master.csv` | ~196 | 50 | Resumen acumulado por jugador |
| `final_team_stats.csv` | ~40 | 122 | Stats de equipo por partido |
| `final_events.csv` | ~890 | 18 | Goles, tarjetas y cambios |
| `final_lineups_all.csv` | ~1925 | 83 | Lineups completos |

> ⚠️ **Separador decimal:** los CSVs usan **coma (,)** como separador decimal (configuración regional Argentina/España). Al abrir en Power BI, asegurate de tener la configuración regional correcta.

---

## 🔌 Power BI — Primeros pasos

1. Abrí `Mundial2026.pbix`
2. En **Transformar datos**, actualizá las rutas de los CSVs a tu carpeta local
3. Si los decimales no se ven bien: verificá que la configuración regional del archivo sea **Español (Argentina)**
4. Para las fotos de jugadores: seleccioná la columna `foto_url` → **Herramientas de columna** → **Categoría de datos** → **URL de imagen**

---

## 🏆 Teams & IDs (SofaScore)

| Selección | Team ID | Grupo | Tournament ID |
|---|---|---|---|
| Colombia | 4820 | K | 3964 |
| Argentina | 4819 | J | 3963 |
| España | 4698 | H | 3961 |
| México | 4781 | A | 3954 |

---

## 📦 Dependencias

| Librería | Uso |
|---|---|
| `curl_cffi` | Requests con impersonación de Chrome (evita bloqueos) |
| `pandas` | Transformación y exportación de datos |
| `numpy` | Cálculos numéricos |
| `tqdm` | Barras de progreso |

---

## ⚠️ Notas importantes

- El script solo enriquece jugadores de **nuestra selección** (no el rival) → ~14 requests por partido
- Los JSONs cacheados en `data/raw/` hacen que las corridas siguientes sean muy rápidas (~2 min)
- Los `PerformanceWarning` en los logs son normales y no afectan los datos
- A partir del **11/06/2026**, cambiar `SOLO_MUNDIAL = True` en el script para filtrar solo partidos del Mundial


---

## 👤 Autor

**Matias Rodriguez**  
📧 [rodriguez.matiasn2@gmail.com](mailto:rodriguez.matiasn2@gmail.com)  
💼 [linkedin.com/in/matias-rodriguez-mnr96](https://www.linkedin.com/in/matias-rodriguez-mnr96/)

---


## 📄 Licencia

MIT License — libre para uso personal y educativo.

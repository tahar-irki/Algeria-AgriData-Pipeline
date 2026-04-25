# ============================================================
# CROP RECOMMENDATION DASHBOARD — Streamlit
# Theme toggle button · Fixed legend backgrounds · Polished UI
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import reverse_geocoder as rg
import pycountry
import os
import sys

# ── Page config (must be FIRST Streamlit call) ───────────────
st.set_page_config(
    page_title="Crop Recommendation Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme state (toggled by button, persisted in session) ────
if "dark_mode" not in st.session_state:
    # Auto-detect on first load from Streamlit's config
    st.session_state.dark_mode = st.get_option("theme.base") == "dark"

is_dark = st.session_state.dark_mode

# ── Color palette ─────────────────────────────────────────────
ACCENT_GREEN  = "#639922"
ACCENT_AMBER  = "#BA7517"
ACCENT_TEAL   = "#1D9E75"
ACCENT_CORAL  = "#D85A30"
ACCENT_PURPLE = "#7F77DD"
ACCENT_PINK   = "#D4537E"
CROP_COLORS   = [ACCENT_GREEN, ACCENT_AMBER, ACCENT_TEAL,
                 ACCENT_CORAL, ACCENT_PURPLE, ACCENT_PINK, "#5DCAA5", "#FAC775"]

# ── Theme-derived tokens ─────────────────────────────────────
if is_dark:
    BG_PAGE         = "#101116"
    BG_SIDEBAR      = "#161B22"
    BG_CARD         = "#1A2416"
    BG_CHART        = "#1C211A" # Slightly lifted for better chart definition
    BG_LEGEND       = "rgba(26,36,22,0.95)"
    BORDER          = "#2A3D22"
    TEXT_PRIMARY    = "#E4F0D0"
    TEXT_MUTED      = "#8DA37E" # Lightened slightly for better readability
    GRID_COLOR      = "rgba(255,255,255,0.06)"
    HERO_COLOR      = "#C8E89A"
    INSIGHT_BG      = "#182414"
    INSIGHT_BORDER  = "#2A4A2E"
    INSIGHT_TEXT    = "#A7D98E" # Shifted from teal to lime-tinted for cohesion
    INSIGHT_STRONG  = "#C0DD97"
    PLOTLY_TPL      = "plotly_dark"
    MAP_STYLE       = "carto-darkmatter"
    TOGGLE_ICON     = "☀️"
    TOGGLE_LABEL    = "Switch to Light mode"
else:
    BG_PAGE        = "#f5f8f0"
    BG_SIDEBAR     = "#eef4e5"
    BG_CARD        = "#ffffff"
    BG_CHART       = "#ffffff"
    BG_LEGEND      = "rgba(255,255,255,0.95)"
    BORDER         = "#cde3a0"
    TEXT_PRIMARY   = "#1e3a0a"
    TEXT_MUTED     = "#6b8050"
    GRID_COLOR     = "rgba(0,0,0,0.06)"
    HERO_COLOR     = "#1e3a0a"
    INSIGHT_BG     = "#eaf3de"
    INSIGHT_BORDER = "#c0dd97"
    INSIGHT_TEXT   = "#27500a"
    INSIGHT_STRONG = "#3b6d11"
    PLOTLY_TPL     = "plotly_white"
    MAP_STYLE      = "carto-positron"
    TOGGLE_ICON    = "🌙"
    TOGGLE_LABEL   = "Switch to Dark mode"


# ── CSS injection ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

html, body, .stApp {{
    background-color: {BG_PAGE} !important;
}}

.main {{
    background-color: {BG_PAGE} !important;
}}

.block-container {{
    background-color: {BG_PAGE} !important;
}}
.main .block-container {{
    background-color: {BG_PAGE} !important;
}}
/* ── Sidebar ── */
[data-testid="stSidebar"] > div:first-child {{
    background-color: {BG_SIDEBAR} !important;
    border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] label {{
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: {TEXT_MUTED} !important;
}}

/* ── Theme toggle button ── */
[data-testid="stSidebar"] [data-testid="stButton"] > button {{
    background: {BG_CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 20px !important;
    color: {ACCENT_GREEN} !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 6px 14px !important;
    transition: all 0.2s ease;
}}
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover {{
    background: {ACCENT_GREEN} !important;
    color: white !important;
    border-color: {ACCENT_GREEN} !important;
}}

/* ── Metric cards ── */
[data-testid="metric-container"] {{
    background: {BG_CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    padding: 1rem 1.25rem !important;
}}
[data-testid="stMetricLabel"] p {{
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: {TEXT_MUTED} !important;
}}
[data-testid="stMetricValue"] {{
    font-family: 'DM Serif Display', serif !important;
    font-size: 2rem !important;
    color: {ACCENT_GREEN} !important;
}}

/* ── Section labels ── */
.section-label {{
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {TEXT_MUTED};
    margin: 0.25rem 0 0.5rem 0;
    border-left: 3px solid {ACCENT_GREEN};
    padding-left: 8px;
}}

/* ── Hero ── */
.hero-title {{
    font-family: 'DM Serif Display', serif;
    font-size: 2.4rem;
    line-height: 1.1;
    color: {HERO_COLOR};
    margin-bottom: 2px;
}}
.hero-title em {{ color: {ACCENT_GREEN}; font-style: italic; }}
.hero-sub {{
    font-size: 13px;
    color: {TEXT_MUTED};
    margin-bottom: 1rem;
}}

/* ── Insight box ── */
.insight-box {{
    background: {INSIGHT_BG};
    border: 1px solid {INSIGHT_BORDER};
    border-left: 4px solid {ACCENT_GREEN};
    border-radius: 10px;
    padding: 1rem 1.25rem;
    font-size: 14px;
    color: {INSIGHT_TEXT};
    line-height: 1.6;
}}
.insight-box strong {{ color: {INSIGHT_STRONG}; }}

/* ── Divider ── */
.divider {{
    border: none;
    border-top: 1px solid {BORDER};
    margin: 1rem 0;
}}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer{{ visibility: hidden; }}
header {{
    background: transparent !important;
}}
</style>
""", unsafe_allow_html=True)


# ── Plotly layout helper — legend background correctly themed ─
def apply_layout(fig, height=340, show_legend=True):
    legend_cfg = dict(
        bgcolor=BG_LEGEND,
        bordercolor=BORDER,
        borderwidth=1,
        font=dict(size=11, color=TEXT_PRIMARY),
    ) if show_legend else dict(visible=False)

    fig.update_layout(
        template=PLOTLY_TPL,
        paper_bgcolor=BG_CHART,
        plot_bgcolor=BG_CHART,
        height=height,
        margin=dict(l=12, r=12, t=12, b=12),
        font=dict(family="DM Sans", size=12, color=TEXT_MUTED),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR,
                   tickfont=dict(color=TEXT_MUTED)),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR,
                   tickfont=dict(color=TEXT_MUTED)),
        legend=legend_cfg,
        colorway=CROP_COLORS,
    )
    return fig


# ── Path helper ───────────────────────────────────────────────
def find__dir(start_path, filename):
    curr = os.path.abspath(start_path)
    while curr != os.path.dirname(curr):
        potential_data_path = os.path.join(curr, filename)
        if os.path.isdir(potential_data_path):
            return potential_data_path
        curr = os.path.dirname(curr)
    return None


# ── Geocoding helper ──────────────────────────────────────────
def get_country_name(code):
    try:
        return pycountry.countries.get(alpha_2=code).name
    except Exception:
        return None


def geocode_df(df):
    """Attach Country_Code, Country, and City columns via reverse geocoding."""
    coords = list(zip(df['Latitude'].values, df['Longitude'].values))
    results = rg.search(coords, mode=1)
    df['Country_Code'] = [res['cc'] for res in results]
    df['Country']      = [get_country_name(res['cc']) for res in results]
    df['City']         = [res['admin1'] for res in results]
    return df


# ── Data loading ──────────────────────────────────────────────
@st.cache_data
def load_data():
    DATA_DIR = find__dir(__file__, 'data')
    if DATA_DIR is None:
        st.error("Could not locate a 'data' directory. Please check your project structure.")
        st.stop()

    INPUT_FILE     = os.path.join(DATA_DIR, "north_algeria_crop_recommendations.csv")
    INPUT_FILE_MAP = os.path.join(DATA_DIR, "reduced_north_algeria_crop_recommendations.csv")

    # ── Map dataset (reduced, for performance) ────────────────
    try:
        map_df = pd.read_csv(INPUT_FILE_MAP)
    except FileNotFoundError:
        st.error(
            "Error: 'data/reduced_north_algeria_crop_recommendations.csv' not found. "
            "Please run trainingCode.py first to create the dataset."
        )
        st.stop()

    map_df = geocode_df(map_df)

    # ── Full dataset (for plots) ──────────────────────────────
    try:
        full_df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        st.error(
            "Error: 'data/north_algeria_crop_recommendations.csv' not found. "
            "Please run trainingCode.py first to create the dataset."
        )
        st.stop()

    full_df = geocode_df(full_df)

    return map_df, full_df


map_df, df = load_data()


# ════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        f"<div style='font-family:DM Serif Display,serif;font-size:1.35rem;"
        f"color:{ACCENT_GREEN};margin-bottom:2px'>🌱 Crop Intelligence</div>"
        f"<div style='font-size:11px;color:{TEXT_MUTED};margin-bottom:1.25rem'>"
        f"Soil · Climate · Agronomy</div>",
        unsafe_allow_html=True,
    )

    # ── Theme toggle ──────────────────────────────────────────
    if st.button(f"{TOGGLE_ICON}  {TOGGLE_LABEL}", key="theme_toggle",
                 use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-size:11px;font-weight:500;letter-spacing:.07em;"
        f"text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:.5rem'>"
        f"Filters</div>",
        unsafe_allow_html=True,
    )

    country     = st.selectbox("Country",
                               ["All"] + sorted(df["Country"].dropna().unique().tolist()))
    crop_filter = st.selectbox("Crop type",
                               ["All"] + sorted(df["recommended_crop"].dropna().unique().tolist()))
    soil_types  = st.multiselect("Soil type",
                                 options=sorted(df["Soil_Type"].dropna().unique().tolist()))
    temp_range  = st.slider("Temperature (°C)",
                            float(df["Temperature"].min()),
                            float(df["Temperature"].max()),
                            (float(df["Temperature"].min()), float(df["Temperature"].max())),
                            step=0.5)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-size:10px;color:{TEXT_MUTED};line-height:1.6'>"
        f"Active theme: {'🌙 Dark' if is_dark else '☀️ Light'}<br>"
        f"Total records: {len(df):,}</div>",
        unsafe_allow_html=True,
    )


# ── Apply filters to the full dataset (plots) ─────────────────
fdf = df.copy()
if country != "All":
    fdf = fdf[fdf["Country"] == country]
if crop_filter != "All":
    fdf = fdf[fdf["recommended_crop"] == crop_filter]
if soil_types:
    fdf = fdf[fdf["Soil_Type"].isin(soil_types)]
fdf = fdf[fdf["Temperature"].between(*temp_range)]

# ── Apply filters to the map dataset ─────────────────────────
mdf = map_df.copy()
if country != "All":
    mdf = mdf[mdf["Country"] == country]
if crop_filter != "All":
    mdf = mdf[mdf["recommended_crop"] == crop_filter]
if soil_types:
    mdf = mdf[mdf["Soil_Type"].isin(soil_types)]
mdf = mdf[mdf["Temperature"].between(*temp_range)]


# ════════════════════════════════════════════════════════════════
# HERO
# ════════════════════════════════════════════════════════════════
st.markdown(
    "<div class='hero-title'>Crop <em>Recommendation</em> Dashboard</div>"
    "<div class='hero-sub'>Agronomic intelligence · Soil &amp; climate analysis</div>",
    unsafe_allow_html=True,
)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# KPI METRICS
# ════════════════════════════════════════════════════════════════
top_crop = fdf["recommended_crop"].value_counts().idxmax() if not fdf.empty else "—"
top_pct  = int(fdf["recommended_crop"].value_counts(normalize=True).max() * 100) if not fdf.empty else 0
avg_temp = round(fdf["Temperature"].mean(), 1) if not fdf.empty else 0
avg_rain = int(fdf["Rainfall"].mean())         if not fdf.empty else 0
avg_ph   = round(fdf["Soil_pH"].mean(), 2)     if not fdf.empty else 0

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Records",      f"{len(fdf):,}",   f"{len(fdf)/len(df)*100:.0f}% of total")
m2.metric("Top crop",     top_crop,           f"{top_pct}% share")
m3.metric("Avg temp",     f"{avg_temp} °C",   None)
m4.metric("Avg rainfall", f"{avg_rain} mm",   None)
m5.metric("Avg soil pH",  str(avg_ph),        None)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# ROW 1 — Map + Bar
# ════════════════════════════════════════════════════════════════
col1, col2 = st.columns([1.6, 1], gap="medium")

with col1:
    st.markdown("<div class='section-label'>Geospatial distribution</div>", unsafe_allow_html=True)
    if not mdf.empty:
        fig_map = px.scatter_mapbox(
            mdf, lat="Latitude", lon="Longitude",
            color="recommended_crop", size="Rainfall",
            hover_data={"City": True, "Soil_Type": True, "Temperature": True,
                        "Latitude": False, "Longitude": False},
            zoom=1, height=380,
            color_discrete_sequence=CROP_COLORS,
        )
        fig_map.update_layout(
            mapbox_style=MAP_STYLE,
            paper_bgcolor=BG_CHART,
            margin=dict(l=0, r=0, t=0, b=0),
            height=380,
            legend=dict(
                bgcolor=BG_LEGEND,
                bordercolor=BORDER,
                borderwidth=1,
                font=dict(size=11, color=TEXT_PRIMARY),
            ),
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No data matches current filters.")

with col2:
    st.markdown("<div class='section-label'>Crop frequency</div>", unsafe_allow_html=True)
    if not fdf.empty:
        counts = fdf["recommended_crop"].value_counts().reset_index()
        counts.columns = ["Crop", "Count"]
        fig_bar = px.bar(
            counts, x="Count", y="Crop", orientation="h",
            color="Crop", color_discrete_sequence=CROP_COLORS,
        )
        fig_bar.update_traces(marker_line_width=0)
        fig_bar.update_layout(yaxis=dict(categoryorder="total ascending"))
        apply_layout(fig_bar, height=380, show_legend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# ROW 2 — Scatter + Box
# ════════════════════════════════════════════════════════════════
col3, col4 = st.columns(2, gap="medium")

with col3:
    st.markdown("<div class='section-label'>Climate envelope — temp vs humidity</div>",
                unsafe_allow_html=True)
    if not fdf.empty:
        fig_scatter = px.scatter(
            fdf, x="Temperature", y="Humidity",
            color="recommended_crop", opacity=0.7,
            labels={"Temperature": "Temperature (°C)", "Humidity": "Humidity (%)"},
            color_discrete_sequence=CROP_COLORS,
        )
        fig_scatter.update_traces(marker=dict(size=6))
        apply_layout(fig_scatter, height=320)
        st.plotly_chart(fig_scatter, use_container_width=True)

with col4:
    st.markdown("<div class='section-label'>Soil pH distribution by crop</div>",
                unsafe_allow_html=True)
    if not fdf.empty:
        fig_box = px.box(
            fdf, x="recommended_crop", y="Soil_pH",
            color="recommended_crop",
            labels={"recommended_crop": "Crop", "Soil_pH": "pH"},
            color_discrete_sequence=CROP_COLORS,
        )
        apply_layout(fig_box, height=320, show_legend=False)
        st.plotly_chart(fig_box, use_container_width=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# ROW 3 — Violin + Heatmap
# ════════════════════════════════════════════════════════════════
col5, col6 = st.columns([1, 1.4], gap="medium")

with col5:
    st.markdown("<div class='section-label'>Rainfall distribution by crop</div>",
                unsafe_allow_html=True)
    if not fdf.empty:
        fig_violin = px.violin(
            fdf, x="recommended_crop", y="Rainfall",
            color="recommended_crop", box=True, points=False,
            labels={"recommended_crop": "", "Rainfall": "Rainfall (mm)"},
            color_discrete_sequence=CROP_COLORS,
        )
        apply_layout(fig_violin, height=340, show_legend=False)
        st.plotly_chart(fig_violin, use_container_width=True)

with col6:
    st.markdown("<div class='section-label'>Correlation heatmap</div>", unsafe_allow_html=True)
    if not fdf.empty:
        numeric_cols = ["Temperature", "Humidity", "Rainfall", "Soil_pH",
                        "Nitrogen", "Phosphorus_est", "Potassium", "Organic_C"]
        corr = fdf[numeric_cols].corr().round(2)
        mid_color = "#1a1f18" if is_dark else "#ffffff"
        fig_heat = px.imshow(
            corr, text_auto=True, aspect="auto",
            color_continuous_scale=[
                [0.0, ACCENT_AMBER],
                [0.5, mid_color],
                [1.0, ACCENT_GREEN],
            ],
            zmin=-1, zmax=1,
        )
        fig_heat.update_traces(textfont=dict(size=10, color=TEXT_PRIMARY))
        fig_heat.update_layout(
            coloraxis_colorbar=dict(
                thickness=10, len=0.8,
                tickfont=dict(size=10, color=TEXT_MUTED),
                bgcolor=BG_LEGEND,
                bordercolor=BORDER,
                borderwidth=1,
            ),
        )
        apply_layout(fig_heat, height=340, show_legend=False)
        st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# ROW 4 — Nutrient radar
# ════════════════════════════════════════════════════════════════
st.markdown("<div class='section-label'>Nutrient profile by crop (N · P · K · Organic C)</div>",
            unsafe_allow_html=True)

if not fdf.empty:
    npk_cols  = ["Nitrogen", "Phosphorus_est", "Potassium", "Organic_C"]
    npk_means = fdf.groupby("recommended_crop")[npk_cols].mean().reset_index()
    def hex_to_rgba(hex_color, alpha=0.2):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'rgba({r},{g},{b},{alpha})'
    fig_radar = go.Figure()

    for i, row in npk_means.iterrows():
        vals = [row[c] for c in npk_cols] + [row[npk_cols[0]]]

        fig_radar.add_trace(go.Scatterpolar(
            r=vals,
            theta=npk_cols + [npk_cols[0]],
            name=row["recommended_crop"],
            fill="toself",
            fillcolor=hex_to_rgba(CROP_COLORS[i % len(CROP_COLORS)], 0.2),
            line=dict(color=CROP_COLORS[i % len(CROP_COLORS)], width=2),
        ))

    fig_radar.update_layout(
        polar=dict(
            bgcolor=BG_CHART,
            radialaxis=dict(visible=True, gridcolor=GRID_COLOR,
                            tickfont=dict(size=10, color=TEXT_MUTED)),
            angularaxis=dict(gridcolor=GRID_COLOR,
                             tickfont=dict(size=11, color=TEXT_MUTED)),
        ),
        paper_bgcolor=BG_CHART,
        height=380,
        margin=dict(l=60, r=60, t=20, b=20),
        font=dict(family="DM Sans", color=TEXT_MUTED),
        legend=dict(
            bgcolor=BG_LEGEND,
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(size=11, color=TEXT_PRIMARY),
        ),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# INSIGHT
# ════════════════════════════════════════════════════════════════
if not fdf.empty:
    top_soil = fdf["Soil_Type"].value_counts().idxmax()
    st.markdown(
        f"<div class='insight-box'>"
        f"💡 Under current filters, <strong>{top_crop}</strong> is the dominant recommendation "
        f"({top_pct}% of records). Conditions favor <strong>{top_soil}</strong> soils at "
        f"<strong>{avg_temp}°C</strong> avg temperature, "
        f"<strong>{avg_rain} mm/mo</strong> rainfall, "
        f"and soil pH <strong>{avg_ph}</strong>."
        f"</div>",
        unsafe_allow_html=True,
    )
else:
    st.warning("No data matches the selected filters. Adjust the sidebar filters.")

st.markdown("<br>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# DATA TABLE (collapsible)
# ════════════════════════════════════════════════════════════════
with st.expander("📄 Filtered data preview", expanded=False):
    st.dataframe(
        fdf.head(200).reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )


# ════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════
st.markdown(
    f"<div style='text-align:center;font-size:11px;color:{TEXT_MUTED};"
    f"padding:1rem 0 0.5rem;border-top:1px solid {BORDER};margin-top:1rem'>"
    f"Crop Intelligence Dashboard · Soil &amp; Climate Analysis</div>",
    unsafe_allow_html=True,
)
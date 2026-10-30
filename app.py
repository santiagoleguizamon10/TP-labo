import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuración de la página
st.set_page_config(
    page_title="Impacto de la Localía | Torneo Clausura",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado principal
st.markdown('<p class="main-header">⚽ Impacto de la Localía en el Fútbol Argentino</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Torneo Clausura – Producción Ofensiva, Disciplina y Validación Estadística</p>', unsafe_allow_html=True)

# 2. Carga y Procesamiento de Datos
@st.cache_data
def cargar_y_procesar_datos():
    df = pd.read_csv("data/Clausura26_tp_labo.csv")
    
    # Métricas por equipo como Local
    local_df = df.groupby("Local").agg(
        xG_Local=("Goles esperados (xG) (L)", "mean"),
        Tiros_Local=("Tiros al arco (L)", "mean"),
        Faltas_Local=("Faltas (L)", "mean"),
        Amarillas_Local=("Tarjetas amarillas (L)", "mean")
    ).reset_index().rename(columns={"Local": "Club"})
    
    # Métricas por equipo como Visitante
    visit_df = df.groupby("Visitante").agg(
        xG_Visitante=("Goles esperados (xG) (V)", "mean"),
        Tiros_Visitante=("Tiros al arco (V)", "mean"),
        Faltas_Visitante=("Faltas (V)", "mean"),
        Amarillas_Visitante=("Tarjetas amarillas (V)", "mean")
    ).reset_index().rename(columns={"Visitante": "Club"})
    
    # Consolidar resumen
    resumen = pd.merge(local_df, visit_df, on="Club")
    resumen["Caída xG"] = resumen["xG_Local"] - resumen["xG_Visitante"]
    resumen["Caída Tiros"] = resumen["Tiros_Local"] - resumen["Tiros_Visitante"]
    resumen["Dif Faltas"] = resumen["Faltas_Visitante"] - resumen["Faltas_Local"]
    resumen["Dif Amarillas"] = resumen["Amarillas_Visitante"] - resumen["Amarillas_Local"]
    
    # Columna auxiliar segura para el tamaño de las burbujas en Plotly
    resumen["Tamaño_Burbuja"] = resumen["Caída xG"].abs() + 0.1
    
    return df, resumen

df_partidos, df_resumen = cargar_y_procesar_datos()

# 3. Barra Lateral (Filtros)
st.sidebar.title("Panel de Control")
st.sidebar.markdown("---")

equipos = ["Todos los Clubes"] + sorted(df_resumen["Club"].dropna().unique().tolist())
equipo_sel = st.sidebar.selectbox("🎯 Filtrar por Club:", equipos)

if equipo_sel != "Todos los Clubes":
    df_filtrado = df_resumen[df_resumen["Club"] == equipo_sel]
else:
    df_filtrado = df_resumen

# 4. Tarjetas KPIs
top_caida_xg = df_resumen.sort_values("Caída xG", ascending=False).iloc[0]
top_caida_tiros = df_resumen.sort_values("Caída Tiros", ascending=False).iloc[0]
prom_caida_xg = df_resumen["Caída xG"].mean()

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric(
        label="🔴 Mayor Caída de xG (Visitante)",
        value=top_caida_xg["Club"],
        delta=f"-{top_caida_xg['Caída xG']:.2f} xG",
        delta_color="inverse"
    )
with kpi2:
    st.metric(
        label="🎯 Mayor Pérdida de Remates",
        value=top_caida_tiros["Club"],
        delta=f"-{top_caida_tiros['Caída Tiros']:.2f} Tiros",
        delta_color="inverse"
    )
with kpi3:
    st.metric(
        label="📊 Caída Promedio del Torneo",
        value=f"{prom_caida_xg:.2f} xG",
        delta="Brecha Local vs Visitante",
        delta_color="off"
    )

st.markdown("---")

# 5. Pestañas Principales
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Producción Ofensiva", 
    "🟨 Disciplina & Arbitraje", 
    "🔬 Validación Estadística", 
    "🔍 Ficha Individual"
])

# --- PESTAÑA 1: OF

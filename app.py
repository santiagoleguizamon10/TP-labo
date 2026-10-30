import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Impacto de la Localía - Torneo Clausura",
    page_icon="⚽",
    layout="wide"
)

# Título y encabezado principal
st.title("⚽ Análisis del Impacto de la Localía")
st.markdown("### Torneo Clausura – Análisis de Producción Ofensiva")
st.write("Esta aplicación evalúa el rendimiento de los equipos jugando de local versus visitante, analizando la caída en **Goles Esperados (xG)** y **Tiros al Arco**.")

# Carga de datos
@st.cache_data
def cargar_y_procesar_datos():
    df = pd.read_csv("data/Clausura26_tp_labo.csv")
    
    # Rendimiento de Local por equipo
    local_df = df.groupby("Local").agg(
        xG_Local=("Goles esperados (xG) (L)", "mean"),
        Tiros_Local=("Tiros al arco (L)", "mean")
    ).reset_index().rename(columns={"Local": "Club"})
    
    # Rendimiento de Visitante por equipo
    visit_df = df.groupby("Visitante").agg(
        xG_Visitante=("Goles esperados (xG) (V)", "mean"),
        Tiros_Visitante=("Tiros al arco (V)", "mean")
    ).reset_index().rename(columns={"Visitante": "Club"})
    
    # Unir métricas y calcular caídas (Local - Visitante)
    resumen = pd.merge(local_df, visit_df, on="Club")
    resumen["Caída xG"] = resumen["xG_Local"] - resumen["xG_Visitante"]
    resumen["Caída Tiros"] = resumen["Tiros_Local"] - resumen["Tiros_Visitante"]
    
    return resumen

df_resumen = cargar_y_procesar_datos()

# Filtros en la barra lateral
st.sidebar.header("Filtros")
equipos = ["Todos"] + sorted(df_resumen["Club"].dropna().unique().tolist())
equipo_sel = st.sidebar.selectbox("Seleccionar Club para Inspeccionar:", equipos)

if equipo_sel != "Todos":
    df_filtrado = df_resumen[df_resumen["Club"] == equipo_sel]
else:
    df_filtrado = df_resumen

# Métricas destacadas en tarjetas superiores
top_caida_xg = df_resumen.sort_values("Caída xG", ascending=False).iloc[0]
top_caida_tiros = df_resumen.sort_values("Caída Tiros", ascending=False).iloc[0]
prom_caida_xg = df_resumen["Caída xG"].mean()

col1, col2, col3 = st.columns(3)
col1.metric("Mayor Caída de xG", top_caida_xg["Club"], f"-{top_caida_xg['Caída xG']:.2f} xG")
col2.metric("Mayor Caída en Remates", top_caida_tiros["Club"], f"-{top_caida_tiros['Caída Tiros']:.2f} Tiros")
col3.metric("Promedio General Caída xG", f"{prom_caida_xg:.2f} xG", "Local vs Visitante")

st.markdown("---")
st.subheader("📊 Equipos Más Afectados al Jugar de Visitante")

col_left, col_right = st.columns(2)

with col_left:
    fig_xg = px.bar(
        df_filtrado.sort_values("Caída xG", ascending=True),
        x="Caída xG",
        y="Club",
        orientation="h",
        title="Caída Promedio de Goles Esperados (xG)",
        labels={"Caída xG": "Caída de xG (Local − Visitante)", "Club": "Club"},
        color="Caída xG",
        color_continuous_scale="Blues"
    )
    st.plotly_chart(fig_xg, use_container_width=True)

with col_right:
    fig_tiros = px.bar(
        df_filtrado.sort_values("Caída Tiros", ascending=True),
        x="Caída Tiros",
        y="Club",
        orientation="h",
        title="Caída Promedio de Tiros al Arco",
        labels={"Caída Tiros": "Caída de Remates al Arco", "Club": "Club"},
        color="Caída Tiros",
        color_continuous_scale="Oranges"
    )
    st.plotly_chart(fig_tiros, use_container_width=True)
    

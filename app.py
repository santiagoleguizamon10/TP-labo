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
st.markdown("### Torneo Clausura - Análisis de Producción Ofensiva")
st.write("Esta aplicación evalúa el rendimiento de los equipos jugando de local versus visitante, analizando la caída en **Goles Esperados (xG)** y **Tiros al Arco**.")

# Carga de datos de los top equipos
@st.cache_data
def cargar_datos():
    datos = [
        {"Club": "Independiente Rivadavia", "Caída xG": 1.32, "Caída Tiros": 1.40},
        {"Club": "Argentinos Juniors", "Caída xG": 1.04, "Caída Tiros": 3.22},
        {"Club": "Gimnasia y Esgrima", "Caída xG": 1.04, "Caída Tiros": 1.98},
        {"Club": "Huracán", "Caída xG": 0.91, "Caída Tiros": 2.17},
        {"Club": "Estudiantes de La Plata", "Caída xG": 0.80, "Caída Tiros": 2.43},
        {"Club": "Banfield", "Caída xG": 0.57, "Caída Tiros": 1.69},
        {"Club": "Vélez Sarsfield", "Caída xG": 0.50, "Caída Tiros": 1.20},
        {"Club": "Unión de Santa Fe", "Caída xG": 0.47, "Caída Tiros": 1.10},
        {"Club": "Central Córdoba", "Caída xG": 0.43, "Caída Tiros": 1.95},
        {"Club": "Gimnasia Mendoza", "Caída xG": 0.43, "Caída Tiros": 2.67}
    ]
    return pd.DataFrame(datos)

df_resumen = cargar_datos()

# Métricas destacadas en tarjetas superiores
col1, col2, col3 = st.columns(3)
col1.metric("Mayor Caída de xG", "Independiente Rivadavia", "-1.32 xG")
col2.metric("Mayor Caída en Remates", "Argentinos Juniors", "-3.22 Tiros")
col3.metric("Promedio General Caída xG", "0.75 xG", "Local vs Visitante")

st.markdown("---")

# Sección de Gráficos Interactivos con Plotly
st.subheader("📊 Equipos Más Afectados al Jugar de Visitante")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    fig_xg = px.bar(
        df_resumen.sort_values("Caída xG", ascending=True),
        x="Caída xG",
        y="Club",
        orientation='h',
        title="Caída Promedio de Goles Esperados (xG)",
        labels={"Caída xG": "Caída de xG (Local − Visitante)"},
        color="Caída xG",
        color_continuous_scale="Blues"
    )
    st.plotly_chart(fig_xg, use_container_width=True)

with col_chart2:
    fig_tiros = px.bar(
        df_resumen.sort_values("Caída Tiros", ascending=True),
        x="Caída Tiros",
        y="Club",
        orientation='h',
        title="Caída Promedio de Tiros al Arco",
        labels={"Caída Tiros": "Caída de Remates a Puerta"},
        color="Caída Tiros",
        color_continuous_scale="Oranges"
    )
    st.plotly_chart(fig_tiros, use_container_width=True)

# Filtro interactivo en la barra lateral
st.sidebar.header("🔍 Filtros")
club_seleccionado = st.sidebar.selectbox(
    "Seleccionar Club para Inspeccionar:", 
    ["Todos"] + list(df_resumen["Club"])
)

if club_seleccionado != "Todos":
    st.markdown(f"### Detalle de **{club_seleccionado}**")
    df_club = df_resumen[df_resumen["Club"] == club_seleccionado]
    st.dataframe(df_club, use_container_width=True)
else:
    st.markdown("### Tabla Completa de Resultados")
    st.dataframe(df_resumen, use_container_width=True)
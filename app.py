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
st.markdown("### Torneo Clausura – Análisis de Producción Ofensiva y Disciplina")
st.write("Esta aplicación evalúa el rendimiento de los equipos jugando de local versus visitante, analizando la caída en **Goles Esperados (xG)**, **Tiros al Arco** y el impacto en **Faltas y Tarjetas**.")

# Carga y procesamiento de datos
@st.cache_data
def cargar_y_procesar_datos():
    df = pd.read_csv("data/Clausura26_tp_labo.csv")
    
    # Metrics por equipo como Local
    local_df = df.groupby("Local").agg(
        xG_Local=("Goles esperados (xG) (L)", "mean"),
        Tiros_Local=("Tiros al arco (L)", "mean"),
        Faltas_Local=("Faltas (L)", "mean"),
        Amarillas_Local=("Tarjetas amarillas (L)", "mean")
    ).reset_index().rename(columns={"Local": "Club"})
    
    # Metrics por equipo como Visitante
    visit_df = df.groupby("Visitante").agg(
        xG_Visitante=("Goles esperados (xG) (V)", "mean"),
        Tiros_Visitante=("Tiros al arco (V)", "mean"),
        Faltas_Visitante=("Faltas (V)", "mean"),
        Amarillas_Visitante=("Tarjetas amarillas (V)", "mean")
    ).reset_index().rename(columns={"Visitante": "Club"})
    
    # Unir métricas y calcular brechas
    resumen = pd.merge(local_df, visit_df, on="Club")
    resumen["Caída xG"] = resumen["xG_Local"] - resumen["xG_Visitante"]
    resumen["Caída Tiros"] = resumen["Tiros_Local"] - resumen["Tiros_Visitante"]
    resumen["Dif Faltas"] = resumen["Faltas_Visitante"] - resumen["Faltas_Local"] # Faltas extra de visitante
    resumen["Dif Amarillas"] = resumen["Amarillas_Visitante"] - resumen["Amarillas_Local"]
    
    return df, resumen

df_partidos, df_resumen = cargar_y_procesar_datos()

# Filtros en la barra lateral
st.sidebar.header("Filtros")
equipos = ["Todos"] + sorted(df_resumen["Club"].dropna().unique().tolist())
equipo_sel = st.sidebar.selectbox("Seleccionar Club para Inspeccionar:", equipos)

if equipo_sel != "Todos":
    df_filtrado = df_resumen[df_resumen["Club"] == equipo_sel]
else:
    df_filtrado = df_resumen

# Tarjetas superiores destacadas
top_caida_xg = df_resumen.sort_values("Caída xG", ascending=False).iloc[0]
top_caida_tiros = df_resumen.sort_values("Caída Tiros", ascending=False).iloc[0]
prom_caida_xg = df_resumen["Caída xG"].mean()

col1, col2, col3 = st.columns(3)
col1.metric("Mayor Caída de xG", top_caida_xg["Club"], f"-{top_caida_xg['Caída xG']:.2f} xG")
col2.metric("Mayor Caída en Remates", top_caida_tiros["Club"], f"-{top_caida_tiros['Caída Tiros']:.2f} Tiros")
col3.metric("Promedio General Caída xG", f"{prom_caida_xg:.2f} xG", "Local vs Visitante")

st.markdown("---")

# Creación de Pestañas Organizadas
tab_ofensiva, tab_disciplina, tab_equipo = st.tabs([
    "📊 Producción Ofensiva", 
    "🟨 Disciplina y Faltas", 
    "🔍 Detalle por Club"
])

with tab_ofensiva:
    st.subheader("Equipos Más Afectados en Rendimiento Ofensivo")
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

with tab_disciplina:
    st.subheader("Impacto en Faltas y Tarjetas según la Localía")
    col_f, col_a = st.columns(2)

    with col_f:
        fig_faltas = px.bar(
            df_filtrado.sort_values("Dif Faltas", ascending=True),
            x="Dif Faltas",
            y="Club",
            orientation="h",
            title="Incremento de Faltas Cometidas al Jugar de Visitante",
            labels={"Dif Faltas": "Faltas Extra (Visitante − Local)", "Club": "Club"},
            color="Dif Faltas",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig_faltas, use_container_width=True)

    with col_a:
        fig_amarillas = px.bar(
            df_filtrado.sort_values("Dif Amarillas", ascending=True),
            x="Dif Amarillas",
            y="Club",
            orientation="h",
            title="Incremento de Tarjetas Amarillas de Visitante",
            labels={"Dif Amarillas": "Amarillas Extra (Visitante − Local)", "Club": "Club"},
            color="Dif Amarillas",
            color_continuous_scale="YlOrRd"
        )
        st.plotly_chart(fig_amarillas, use_container_width=True)

with tab_equipo:
    st.subheader(f"Inspección Individual de Métricas")
    if equipo_sel != "Todos":
        st.write(f"Mostrando métricas comparativas para **{equipo_sel}**:")
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.info("💡 Seleccioná un club específico en el menú de la izquierda para ver su desglose completo en la tabla.")
        st.dataframe(df_resumen, use_container_width=True)
    

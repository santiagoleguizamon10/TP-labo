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

# --- PESTAÑA 1: OFENSIVA ---
with tab1:
    st.subheader("Pérdida de Rendimiento Ofensivo al Jugar fuera de Casa")
    col_a, col_b = st.columns(2)
    
    with col_a:
        fig_xg = px.bar(
            df_filtrado.sort_values("Caída xG", ascending=True),
            x="Caída xG",
            y="Club",
            orientation="h",
            title="Caída en Goles Esperados (xG Local − xG Visitante)",
            color="Caída xG",
            color_continuous_scale="Viridis",
            text_auto=".2f"
        )
        st.plotly_chart(fig_xg, use_container_width=True)

    with col_b:
        fig_tiros = px.bar(
            df_filtrado.sort_values("Caída Tiros", ascending=True),
            x="Caída Tiros",
            y="Club",
            orientation="h",
            title="Pérdida de Tiros al Arco Promedio",
            color="Caída Tiros",
            color_continuous_scale="Plasma",
            text_auto=".2f"
        )
        st.plotly_chart(fig_tiros, use_container_width=True)

    st.markdown("#### ⚖️ Dispersión: xG Local vs xG Visitante")
    fig_scatter = px.scatter(
        df_resumen,
        x="xG_Visitante",
        y="xG_Local",
        text="Club",
        size="Tamaño_Burbuja",
        color="Caída xG",
        color_continuous_scale="RdBu_r",
        title="Comparativa xG (Puntos por encima de la línea indican fuerte dependencia de localía)",
        labels={"xG_Visitante": "xG Promedio Visitante", "xG_Local": "xG Promedio Local"}
    )
    max_val = max(df_resumen["xG_Local"].max(), df_resumen["xG_Visitante"].max()) + 0.2
    fig_scatter.add_shape(
        type="line", line=dict(dash="dash", color="red", width=2),
        x0=0, y0=0, x1=max_val, y1=max_val
    )
    fig_scatter.update_traces(textposition="top center", marker=dict(sizemin=8))
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- PESTAÑA 2: DISCIPLINA ---
with tab2:
    st.subheader("Efecto de la Localía en el Criterio Disciplinario")
    col_c, col_d = st.columns(2)
    
    with col_c:
        fig_faltas = px.bar(
            df_filtrado.sort_values("Dif Faltas", ascending=True),
            x="Dif Faltas",
            y="Club",
            orientation="h",
            title="Incremento de Faltas Cometidas de Visitante",
            color="Dif Faltas",
            color_continuous_scale="Reds",
            text_auto=".2f"
        )
        st.plotly_chart(fig_faltas, use_container_width=True)
        
    with col_d:
        fig_amarillas = px.bar(
            df_filtrado.sort_values("Dif Amarillas", ascending=True),
            x="Dif Amarillas",
            y="Club",
            orientation="h",
            title="Tarjetas Amarillas Extra de Visitante",
            color="Dif Amarillas",
            color_continuous_scale="YlOrBr",
            text_auto=".2f"
        )
        st.plotly_chart(fig_amarillas, use_container_width=True)

# --- PESTAÑA 3: VALIDACIÓN ESTADÍSTICA ---
with tab3:
    st.subheader("🧪 Análisis de Significancia Estadística")
    st.write("Evaluación de la brecha de localía sobre los partidos del torneo:")
    
    diferencias = df_partidos["Goles esperados (xG) (L)"] - df_partidos["Goles esperados (xG) (V)"]
    diferencias = diferencias.dropna()
    
    media_diff = np.mean(diferencias)
    std_diff = np.std(diferencias, ddof=1)
    n = len(diferencias)
    t_stat = media_diff / (std_diff / np.sqrt(n))
    
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.info(f"**Estadístico t (Emparejado):** {t_stat:.4f}")
    with col_stat2:
        st.success(f"**Diferencia Media de xG:** +{media_diff:.3f} xG a favor del Local (N = {n} partidos)")

    st.markdown("---")
    st.subheader("🔥 Matriz de Correlación de Métricas de Juego")
    
    cols_interes = [
        "Goles esperados (xG) (L)", "Goles esperados (xG) (V)",
        "Faltas (L)", "Faltas (V)",
        "Tarjetas amarillas (L)", "Tarjetas amarillas (V)"
    ]
    df_corr = df_partidos[cols_interes].corr()
    
    fig_corr = px.imshow(
        df_corr,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="Blues",
        title="Correlación Lineal (Pearson) entre Variables"
    )
    st.plotly_chart(fig_corr, use_container_width=True)

# --- PESTAÑA 4: DETALLE INDIVIDUAL ---
with tab4:
    st.subheader("🔍 Desglose Completo por Club")
    if equipo_sel != "Todos los Clubes":
        st.write(f"Métricas consolidadas para **{equipo_sel}**:")
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.info("💡 Seleccioná un club específico en la barra lateral para filtrarlo en la tabla.")
        st.dataframe(df_resumen, use_container_width=True)

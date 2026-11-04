"""
Influencia de la localía en el fútbol argentino · Torneo Clausura 2026
TP Grupal · Laboratorio de Métodos Cuantitativos · FCE UBA · 2C 2026
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

st.set_page_config(page_title="Localía en el fútbol argentino", page_icon="⚽", layout="wide")

CLR = {"Local": "#2563EB", "Visitante": "#EA580C"}
GRANDES = ["Boca Juniors", "River Plate", "Racing Club", "CA Independiente", "San Lorenzo"]
RESALTE = "#F5B301"

st.markdown("""<style>
.block-container{padding-top:1.6rem}
.big{font-size:2.1rem;font-weight:800;color:#1E3A8A;line-height:1.15;margin:0}
.sub{color:#4B5563;margin:4px 0 14px 0}
.box{color:#0F172A;background:#F1F5F9;border-left:5px solid #2563EB;padding:12px 16px;border-radius:6px;margin:8px 0}
</style>""", unsafe_allow_html=True)


# ───────────────────────── Datos ─────────────────────────
@st.cache_data
def cargar():
    df = pd.read_csv("data/Clausura26_tp_labo.csv")
    
    # Vectorización de limpieza sin bucles
    cols_amarillas = ["Tarjetas amarillas (L)", "Tarjetas amarillas (V)"]
    df[cols_amarillas] = df[cols_amarillas].fillna(0)
    
    cols_pos = ["Posesión de balón (L)", "Posesión de balón (V)"]
    df[cols_pos] = df[cols_pos].replace({"%": ""}, regex=True).astype(float)
    
    df["Tarj (L)"] = df["Tarjetas amarillas (L)"] + df["Tarjetas rojas (L)"]
    df["Tarj (V)"] = df["Tarjetas amarillas (V)"] + df["Tarjetas rojas (V)"]
    
    # Uso de np.select para evitar np.where anidados
    cond_L = [df["Resultado (L)"] > df["Resultado (V)"], df["Resultado (L)"] == df["Resultado (V)"]]
    cond_V = [df["Resultado (V)"] > df["Resultado (L)"], df["Resultado (V)"] == df["Resultado (L)"]]
    df["Puntos (L)"] = np.select(cond_L, [3, 1], default=0)
    df["Puntos (V)"] = np.select(cond_V, [3, 1], default=0)
    
    df["Faltas totales"] = df["Faltas (L)"] + df["Faltas (V)"]
    df["Intensidad"] = pd.qcut(df["Faltas totales"], 3, labels=["Limpio", "Intensidad media", "Picado"])

    filas = []
    for s, o, cond in [("L", "V", "Local"), ("V", "L", "Visitante")]:
        t = pd.DataFrame({
            "Club": df["Local" if s == "L" else "Visitante"], 
            "Condición": cond, 
            "Intensidad": df["Intensidad"],
            "Puntos": df[f"Puntos ({s})"], 
            "GF": df[f"Resultado ({s})"], 
            "GC": df[f"Resultado ({o})"],
            "xG": df[f"Goles esperados (xG) ({s})"], 
            "xG en contra": df[f"Goles esperados (xG) ({o})"],
            "Tiros al arco": df[f"Tiros al arco ({s})"], 
            "Tiros al arco en contra": df[f"Tiros al arco ({o})"],
            "Tiros totales en contra": df[f"Tiros totales ({o})"],
            "Posesión": df[f"Posesión de balón ({s})"], 
            "Faltas": df[f"Faltas ({s})"], 
            "Tarjetas": df[f"Tarj ({s})"]
        })
        t["Severidad"] = t["Tarjetas"] / t["Faltas"].replace(0, np.nan) * 10
        filas.append(t)
        
    largo = pd.concat(filas, ignore_index=True)
    largo["Jerarquía"] = np.where(largo["Club"].isin(GRANDES), "Grande", "Resto")

    # Optimización del agrupamiento
    metricas = ["GF", "GC", "xG", "xG en contra", "Tiros al arco", "Posesión", "Faltas", "Tarjetas", "Severidad"]
    agg_dict = {"Puntos": ["size", "sum"]}
    agg_dict.update({m: ["mean"] for m in metricas})
    
    g = largo.groupby(["Club", "Condición"]).agg(agg_dict).unstack("Condición")
    g.columns = [f"{col[0]}|{col[2]}" if col[0] != "Puntos" else f"{'PJ' if col[1]=='size' else 'Pts'}|{col[2]}" for col in g.columns]
    
    r = pd.DataFrame(index=g.index)
    r["Efectividad L"] = g["Pts|Local"] / (g["PJ|Local"] * 3) * 100
    r["Efectividad V"] = g["Pts|Visitante"] / (g["PJ|Visitante"] * 3) * 100
    r["Δ Efectividad (pp)"] = r["Efectividad L"] - r["Efectividad V"]
    
    for m in ["xG", "Tiros al arco", "Posesión", "GF"]:
        r[f"{m} L"], r[f"{m} V"] = g[f"{m}|Local"], g[f"{m}|Visitante"]
        r[f"Δ {m}"] = r[f"{m} L"] - r[f"{m} V"]
        
    r["Δ Faltas (V−L)"] = g["Faltas|Visitante"] - g["Faltas|Local"]
    r["Δ Tarjetas (V−L)"] = g["Tarjetas|Visitante"] - g["Tarjetas|Local"]
    r["Solidez (GC V − GC L)"] = g["GC|Visitante"] - g["GC|Local"]
    
    return df, largo, r.dropna().reset_index()

df, largo, club = cargar()
N = len(df)

# ───────────────────────── Sidebar ─────────────────────────
st.sidebar.title("⚽ Panel")
opciones_club = ["— ninguno —"] + sorted(club["Club"])
idx_defecto = opciones_club.index("River Plate") if "River Plate" in opciones_club else 0

sel = st.sidebar.selectbox("Resaltar un club en los gráficos", opciones_club, index=idx_defecto)
sel = None if sel.startswith("—") else sel

st.sidebar.caption(f"Dataset: {N} partidos · {df['Fecha'].nunique()} fechas · Torneo Clausura 2026. "
                   "Fuente: estadísticas de partido (CSV del repositorio del grupo).")
st.sidebar.markdown("**Cómo leer los gráficos:** azul = local, naranja = visitante; "
                    "el club elegido se resalta en dorado.")

def barras_dif(col, titulo, xlab, sentido=1, dec=2, escala=None):
    d = club.sort_values(col)
    cols = [RESALTE if c == sel else (CLR["Local"] if v * sentido >= 0 else CLR["Visitante"]) for c, v in zip(d["Club"], d[col])]
    
    marcador = dict(color=cols)
    if escala:
        marcador = dict(
            color=d[col], colorscale=escala, cmid=0, 
            line=dict(
                color=[RESALTE if c == sel else "rgba(0,0,0,0)" for c in d["Club"]], 
                width=[4 if c == sel else 0 for c in d["Club"]]
            )
        )
        
    f = go.Figure(go.Bar(
        x=d[col], y=d["Club"], orientation="h", 
        marker=marcador, text=d[col].round(dec), textposition="outside"
    ))
    f.add_vline(x=0, line_color="black")
    f.update_layout(title=titulo, xaxis_title=xlab, yaxis_title="Club", height=760, margin=dict(l=10, r=30, t=50, b=10))
    return f

def tabla_test(pares):
    out = []
    for nombre, a, b in pares:
        t, p = stats.ttest_rel(df[a], df[b])
        out.append({
            "Métrica": nombre, "Local": df[a].mean(), "Visitante": df[b].mean(), 
            "Diferencia (L−V)": df[a].mean() - df[b].mean(),
            "t": t, "p-valor": p, "¿Significativa (5%)?": "Sí" if p < 0.05 else "No"
        })
    return pd.DataFrame(out)

tests = tabla_test([
    ("Goles", "Resultado (L)", "Resultado (V)"),
    ("xG", "Goles esperados (xG) (L)", "Goles esperados (xG) (V)"),
    ("Tiros al arco", "Tiros al arco (L)", "Tiros al arco (V)"),
    ("Tiros totales", "Tiros totales (L)", "Tiros totales (V)"),
    ("Posesión (%)", "Posesión de balón (L)", "Posesión de balón (V)"),
    ("Faltas", "Faltas (L)", "Faltas (V)"),
    ("Tarjetas (am.+roj.)", "Tarj (L)", "Tarj (V)"),
    ("Puntos", "Puntos (L)", "Puntos (V)")
]).set_index("Métrica")

def _delta(r, signo=1):
    return f"{signo * r['Diferencia (L−V)']:+.2f} · p = {r['p-valor']:.3f} ({'significativa' if r['p-valor'] < .05 else 'no significativa'})"

def kpi(col, metrica, label, fmt=".2f", suf=""):
    r = tests.loc[metrica]
    col.metric(f"{label} · local vs visitante", f"{r['Local']:{fmt}}{suf} vs {r['Visitante']:{fmt}}{suf}", _delta(r), delta_color="off")

def kpi_def(col, metrica, label):
    r = tests.loc[metrica]
    col.metric(f"{label} concedidos · local vs visitante", f"{r['Visitante']:.2f} vs {r['Local']:.2f}", _delta(r, -1), delta_color="off")

gl = (df["Puntos (L)"] == 3).sum()
emp = (df["Puntos (L)"] == 1).sum()
gv = (df["Puntos (V)"] == 3).sum()
ef_L = df["Puntos (L)"].sum() / (N * 3) * 100
ef_V = df["Puntos (V)"].sum() / (N * 3) * 100
sev = largo.groupby("Condición")["Severidad"].mean()

# ───────────────────────── Encabezado ─────────────────────────
st.markdown('<p class="big">⚽ ¿Cuánto vale jugar de local en el fútbol argentino?</p>', unsafe_allow_html=True)
st.markdown('<p class="sub">Torneo Clausura 2026 · TP Grupal · Laboratorio de Métodos Cuantitativos · FCE UBA</p>', unsafe_allow_html=True)

tabs = st.tabs(["🎯 Pregunta", "🏆 Puntos", "⚔️ Ataque", "🎮 Posesión", "🟨 Disciplina", "🛡️ Defensa", "🔍 Ficha del club", "✅ Conclusiones"])

# ── 1. Pregunta ──
with tabs[0]:
    st.markdown('<div class="box"><b>Pregunta de investigación.</b><br>¿Cómo varía el rendimiento de los equipos argentinos cuando juegan de local respecto de su desempeño como visitante durante el Torneo Clausura 2026?</div>', unsafe_allow_html=True)
    st.markdown('<div class="box" style="border-left-color:#EA580C"><b>Cinco preguntas para responderla</b><ol style="margin:8px 0 0 0"><li>🏆 <b>Puntos:</b> ¿cuántos puntos más se suman en casa y todos los clubes se benefician por igual?</li><li>⚔️ <b>Ataque:</b> ¿cuánto depende la localía de la forma de atacar? ¿Se genera menos peligro (xG, tiros al arco) al salir?</li><li>🎮 <b>Posesión:</b> ¿jugar en casa da el protagonismo con la pelota o pesa más el estilo de cada club?</li><li>🟨 <b>Disciplina:</b> ¿el visitante recibe más tarjetas por la misma cantidad de faltas?</li><li>🛡️ <b>Defensa:</b> ¿se defiende peor de visitante? ¿Los cinco grandes están a salvo?</li></ol></div>', unsafe_allow_html=True)
    st.markdown('<div class="box" style="border-left-color:#16A34A"><b>💬 La teoría de todos los futboleros: “la localía la gana la gente”.</b><br>Se dice que la cancha llena empuja al local, aprieta al árbitro y le pone los nervios al visitante. El dataset no mide la hinchada (no tiene asistencia ni ambiente), pero sí las huellas que dejaría: más ataque, más tarjetas para el visitante y defensas más frágiles afuera. ¿Alcanzan los datos para respaldar el relato o es puro folklore?</div>', unsafe_allow_html=True)

# ── 2. Puntos ──
with tabs[1]:
    st.subheader("Efectividad: puntos obtenidos sobre puntos posibles")
    c = st.columns(4)
    c[0].metric("Efectividad local", f"{ef_L:.1f}%")
    c[1].metric("Efectividad visitante", f"{ef_V:.1f}%")
    c[2].metric("Ventaja de localía", f"{ef_L - ef_V:+.1f} pp")
    kpi(c[3], "Puntos", "Puntos por partido")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        f = go.Figure(go.Bar(
            x=["Local", "Visitante"], y=[ef_L, ef_V], marker_color=list(CLR.values()),
            text=[f"{ef_L:.1f}%", f"{ef_V:.1f}%"], textposition="outside"
        ))
        f.update_layout(title="Efectividad global", xaxis_title="Condición", yaxis_title="% de puntos posibles", yaxis_range=[0, 70], height=380)
        st.plotly_chart(f, use_container_width=True)
        
        g = go.Figure()
        for nombre, v, col in [("Gana local", gl, CLR["Local"]), ("Empate", emp, "#9CA3AF"), ("Gana visitante", gv, CLR["Visitante"])]:
            g.add_bar(name=nombre, x=[v], y=["Resultados"], orientation="h", marker_color=col, text=f"{v / N * 100:.0f}%", textposition="inside")
        g.update_layout(barmode="stack", title="Resultados de los partidos", xaxis_title="Cantidad de partidos", height=230, legend=dict(orientation="h", y=-0.5))
        st.plotly_chart(g, use_container_width=True)
        st.caption(f"**¿Por qué {ef_L:.1f}% + {ef_V:.1f}% no suma 100%?** Cada condición se mide contra sus propios {N * 3} puntos posibles, y en un empate se reparten 2 puntos en vez de 3. Con {emp} empates ({emp / N * 100:.0f}%) se “pierden” {emp / (3 * N) * 100:.1f} pp.")
    
    with c2:
        st.plotly_chart(barras_dif("Δ Efectividad (pp)", "Ventaja de localía por club: efectividad local − visitante", "Diferencia en puntos porcentuales (pp)"), use_container_width=True)
        
    top, bot = club.nlargest(3, "Δ Efectividad (pp)"), club.nsmallest(3, "Δ Efectividad (pp)")
    st.info(f"**Interpretación:** mayor ventaja en {', '.join(top['Club'])}. Sacan **mejor** resultado de visitante que de local: {', '.join(club[club['Δ Efectividad (pp)'] < 0]['Club']) or 'ningún club'}. La localía ayuda en promedio, pero no a todos por igual y no es causa única del resultado.")

# ── 3. Ataque ──
with tabs[2]:
    st.subheader("Producción ofensiva: xG y tiros al arco")
    c = st.columns(3)
    kpi(c[0], "xG", "xG por partido")
    kpi(c[1], "Tiros al arco", "Tiros al arco por partido")
    kpi(c[2], "Goles", "Goles por partido")
    
    m = max(club["xG L"].max(), club["xG V"].max()) + .15
    f = px.scatter(
        club, x="xG V", y="xG L", text="Club", color="Δ xG", 
        color_continuous_scale="RdYlGn_r", color_continuous_midpoint=0,
        title="xG promedio como local vs. como visitante (cada punto es un club)",
        labels={"xG V": "xG promedio de visitante", "xG L": "xG promedio de local", "Δ xG": "Caída de xG"}, height=580
    )
    f.add_shape(type="line", x0=0, y0=0, x1=m, y1=m, line=dict(dash="dash", color="gray"))
    f.update_traces(textposition="top center", marker=dict(size=12, line=dict(width=1, color="#333")))
    
    if sel:
        r = club[club["Club"] == sel]
        f.add_trace(go.Scatter(
            x=r["xG V"], y=r["xG L"], mode="markers", 
            marker=dict(size=24, color="rgba(0,0,0,0)", line=dict(width=4, color=RESALTE)), 
            showlegend=False, hoverinfo="skip"
        ))
    st.plotly_chart(f, use_container_width=True)
    
    arriba = (club["xG L"] > club["xG V"]).sum()
    st.info(f"**Interpretación:** la diagonal marca igual producción en ambas condiciones. {arriba} de {len(club)} clubes quedan por encima (generan más peligro en casa); {len(club) - arriba} están por debajo. **Color:** rojo = cae al salir, verde = mejora de visitante.")
    
    c1, c2 = st.columns(2)
    c1.plotly_chart(barras_dif("Δ xG", "Caída de xG al salir (local − visitante)", "Diferencia de xG por partido", escala="RdYlGn_r"), use_container_width=True)
    c2.plotly_chart(barras_dif("Δ Tiros al arco", "Caída de tiros al arco al salir (local − visitante)", "Diferencia de tiros al arco por partido", escala="RdYlGn_r"), use_container_width=True)

# ── 4. Posesión ──
with tabs[3]:
    st.subheader("¿La localía da el protagonismo con la pelota?")
    c = st.columns(2)
    kpi(c[0], "Posesión (%)", "Posesión", ".1f", "%")
    c[1].metric("Partidos con local > 50% de posesión", f"{(df['Posesión de balón (L)'] > 50).mean() * 100:.1f}%")
    
    pos = pd.concat([
        pd.DataFrame({"Condición": "Local", "Posesión (%)": df["Posesión de balón (L)"]}),
        pd.DataFrame({"Condición": "Visitante", "Posesión (%)": df["Posesión de balón (V)"]})
    ])
    f = px.box(
        pos, x="Condición", y="Posesión (%)", color="Condición", color_discrete_map=CLR, points="all",
        title="Distribución de la posesión según condición", height=480
    )
    f.add_hline(y=50, line_dash="dash", line_color="gray").update_layout(showlegend=False, xaxis_title="Condición de juego", yaxis_title="Posesión de balón (%)")
    
    c1, c2 = st.columns([1, 1])
    c1.plotly_chart(f, use_container_width=True)
    p = tests.loc["Posesión (%)"]
    c1.info(f"**Interpretación:** el local promedia {p['Local']:.1f}% (+{p['Diferencia (L−V)']:.1f} pp), pero las cajas se superponen: con p = {p['p-valor']:.3f} la diferencia no es estadísticamente distinguible de cero.")
    c2.plotly_chart(barras_dif("Δ Posesión", "“Efecto empuje”: posesión local − visitante por club", "Diferencia de posesión (pp)"), use_container_width=True)

# ── 5. Disciplina ──
with tabs[4]:
    st.subheader("Faltas, tarjetas y severidad del arbitraje")
    _rl = df["Tarj (L)"] / df["Faltas (L)"].replace(0, np.nan) * 10
    _rv = df["Tarj (V)"] / df["Faltas (V)"].replace(0, np.nan) * 10
    _ok = _rl.notna() & _rv.notna()
    p_sev = stats.ttest_rel(_rl[_ok], _rv[_ok])[1]
    
    c = st.columns(3)
    kpi(c[0], "Faltas", "Faltas por partido")
    kpi(c[1], "Tarjetas (am.+roj.)", "Tarjetas por partido")
    c[2].metric("Tarjetas cada 10 faltas · local vs visitante", f"{sev['Local']:.2f} vs {sev['Visitante']:.2f}", f"{sev['Local'] - sev['Visitante']:+.2f} · p = {p_sev:.3f} ({'significativa' if p_sev < .05 else 'no significativa'})", delta_color="off")
    
    met = largo.groupby("Condición")[["Faltas", "Tarjetas", "Severidad"]].mean()
    f = go.Figure()
    for cond in ["Local", "Visitante"]:
        f.add_bar(
            name=cond, x=["Faltas por partido", "Tarjetas por partido", "Tarjetas cada 10 faltas"], 
            y=met.loc[cond].values, marker_color=CLR[cond], text=met.loc[cond].round(2).values, textposition="outside"
        )
    f.update_layout(barmode="group", title="Comparativa disciplinaria: local vs. visitante", xaxis_title="Métrica", yaxis_title="Promedio por partido", height=430)
    
    c1, c2 = st.columns(2)
    c1.plotly_chart(f, use_container_width=True)
    
    inten = largo.groupby(["Intensidad", "Condición"], observed=True)["Severidad"].mean().unstack()
    inten["Brecha"] = inten["Visitante"] - inten["Local"]
    f2 = go.Figure(go.Bar(
        x=inten.index.astype(str), y=inten["Brecha"], 
        marker_color=["#2CA02C", "#FF7F0E", "#D62728"], text=inten["Brecha"].round(2), textposition="outside"
    ))
    f2.update_layout(title="Brecha de severidad (visitante − local) según intensidad del partido", xaxis_title="Intensidad (tercios de faltas totales)", yaxis_title="Tarjetas extra cada 10 faltas", height=430)
    c2.plotly_chart(f2, use_container_width=True)
    
    pf, pt = tests.loc["Faltas", "p-valor"], tests.loc["Tarjetas (am.+roj.)", "p-valor"]
    st.info(f"**Interpretación:** el visitante recibe más tarjetas ({met.loc['Visitante','Tarjetas']:.2f} vs {met.loc['Local','Tarjetas']:.2f}; p = {pt:.3f}) y {sev['Visitante']:.2f} cada 10 faltas contra {sev['Local']:.2f}. Es una **asimetría disciplinaria** consistente con la localía.")
    
    st.plotly_chart(barras_dif("Δ Tarjetas (V−L)", "Tarjetas extra del club como visitante (visitante − local)", "Tarjetas por partido", sentido=-1), use_container_width=True)

# ── 6. Defensa ──
with tabs[5]:
    st.subheader("¿Se defiende peor de visitante?")
    c = st.columns(3)
    kpi_def(c[0], "Tiros totales", "Tiros totales")
    kpi_def(c[1], "Tiros al arco", "Tiros al arco")
    kpi_def(c[2], "xG", "xG")
    
    vars_ = [("Tiros totales en contra", "Tiros totales recibidos"), ("Tiros al arco en contra", "Tiros al arco recibidos"), ("xG en contra", "xG concedido")]
    cols = st.columns(3)
    for (v, tit), c_ in zip(vars_, cols):
        f = px.box(largo, x="Condición", y=v, color="Condición", color_discrete_map=CLR, title=tit, labels={v: tit})
        f.update_layout(showlegend=False, height=380, xaxis_title="Condición")
        c_.plotly_chart(f, use_container_width=True)
        
    med = largo.groupby("Condición")[["Tiros totales en contra", "Tiros al arco en contra", "xG en contra"]].median()
    st.info(f"**Interpretación (medianas):** de visitante se reciben {med.loc['Visitante','Tiros totales en contra']:.0f} tiros totales (local: {med.loc['Local','Tiros totales en contra']:.0f}), {med.loc['Visitante','Tiros al arco en contra']:.1f} al arco y {med.loc['Visitante','xG en contra']:.2f} xG.")
    
    st.markdown("##### Grandes vs. resto")
    jer = largo.groupby(["Jerarquía", "Condición"])[[v for v, _ in vars_]].mean().reset_index()
    cols = st.columns(3)
    for (v, tit), c_ in zip(vars_, cols):
        f = px.bar(
            jer, x="Jerarquía", y=v, color="Condición", barmode="group", color_discrete_map=CLR, text_auto=".2f",
            category_orders={"Jerarquía": ["Resto", "Grande"]}, title=tit, labels={v: "Promedio por partido"}
        )
        f.update_layout(height=380)
        c_.plotly_chart(f, use_container_width=True)
    st.caption("Los cinco grandes: " + ", ".join(GRANDES) + ". La brecha entre grandes y resto se concentra en condición de local; de visitante se achica.")

    st.markdown("##### Los 5 grandes entre sí")
    gg = largo[largo["Club"].isin(GRANDES)].groupby(["Club", "Condición"])[[v for v, _ in vars_]].mean().unstack()
    cols = st.columns(3)
    arriba5 = []
    for (v, tit), c_ in zip(vars_, cols):
        x, y = gg[(v, "Local")], gg[(v, "Visitante")]
        arriba5.append(int((y > x).sum()))
        lo, hi = min(x.min(), y.min()) * .85, max(x.max(), y.max()) * 1.15
        
        f = go.Figure()
        f.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", line=dict(dash="dash", color="red"), name="Rendimiento igual (X = Y)"))
        f.add_trace(go.Scatter(
            x=x, y=y, mode="markers+text", text=gg.index, textposition="top center", showlegend=False,
            marker=dict(size=14, color=[RESALTE if k == sel else CLR["Local"] for k in gg.index], line=dict(width=1, color="black"))
        ))
        f.update_layout(title=tit, xaxis_title="Promedio como local", yaxis_title="Promedio como visitante", height=400, legend=dict(orientation="h", y=-0.25))
        c_.plotly_chart(f, use_container_width=True)
    st.info(f"**Interpretación:** por encima de la diagonal, el club concede más de visitante que de local. Tiros totales: {arriba5[0]} de 5; tiros al arco: {arriba5[1]} de 5; xG: {arriba5[2]} de 5.")

    st.plotly_chart(barras_dif("Solidez (GC V − GC L)", "Solidez defensiva: goles recibidos de visitante − goles recibidos de local", "Goles en contra por partido (positivo = defiende mejor en casa)"), use_container_width=True)

# ── 7. Ficha del club ──
with tabs[6]:
    elegido = st.selectbox("Club", sorted(club["Club"]), index=sorted(club["Club"]).index(sel) if sel else 0, key="ficha")
    f_ = club[club["Club"] == elegido].iloc[0]
    filas = [
        ("Efectividad (%)", "Efectividad L", "Efectividad V"), 
        ("Goles a favor", "GF L", "GF V"), ("xG", "xG L", "xG V"),
        ("Tiros al arco", "Tiros al arco L", "Tiros al arco V"), 
        ("Posesión (%)", "Posesión L", "Posesión V")
    ]
    t = pd.DataFrame([{"Métrica": n, "Local": f_[a], "Visitante": f_[b], "Local − Visitante": f_[a] - f_[b]} for n, a, b in filas]).set_index("Métrica")
    st.dataframe(t.style.format("{:.2f}"), use_container_width=True)
    
    d = df[(df["Local"] == elegido) | (df["Visitante"] == elegido)][["Fecha", "Local", "Resultado (L)", "Resultado (V)", "Visitante"]]
    st.markdown("**Partidos del torneo**")
    st.dataframe(d, use_container_width=True, hide_index=True)

# ── 8. Conclusiones ──
with tabs[7]:
    xg, ta = tests.loc["xG"], tests.loc["Tiros al arco"]
    st.subheader("Respuesta a la pregunta de investigación")
    st.markdown(f"""
1. **Resultados:** los locales obtuvieron {ef_L:.1f}% de los puntos posibles contra {ef_V:.1f}% de los visitantes (+{ef_L - ef_V:.1f} pp).
2. **Ataque y defensa:** de local se generan más ocasiones (xG {xg['Local']:.2f} vs {xg['Visitante']:.2f}; tiros al arco {ta['Local']:.2f} vs {ta['Visitante']:.2f}) y se conceden menos. La ventaja es estructural, no solo de resultado.
3. **Posesión:** la diferencia ({tests.loc['Posesión (%)','Diferencia (L−V)']:+.1f} pp) **no** es significativa: la localía no “regala” la pelota.
4. **Disciplina:** el visitante recibe más tarjetas con un nivel de faltas parecido ({sev['Visitante']:.2f} vs {sev['Local']:.2f} cada 10 faltas).
5. **Heterogeneidad:** la ventaja varía mucho entre clubes; varios rinden igual o mejor de visitante (ver pestañas Puntos y Ataque).
""")
    st.subheader("Limitaciones")
    st.markdown(f"""
- Muestra corta: {N} partidos en {df['Fecha'].nunique()} fechas (falta al menos un partido del fixture), y cada club tiene unos 6–7 partidos por condición; los promedios por club son inestables.
- Los clubes no juegan contra los mismos rivales de local y de visitante (fixture parcial): parte de la brecha puede deberse a la calidad del rival.
- Resultados descriptivos y pruebas pareadas por partido; no se aísla el efecto causal de la localía ni se controla el marcador en el análisis disciplinario.
""")
    st.caption("Código y notebook: repositorio de GitHub del grupo.")
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Entrega Efectiva — C07-26", layout="wide")

GOOD = "#2F6E5C"
BAD = "#A33D3F"
NEUTRAL = "#6B7280"
ACCENT = "#B5661C"

EVALUABLES = ["Entrega Efectiva", "Entrega No Efectiva"]

RETRASO_BINS = [0, 1, 2, 3, 5, 7, 10, 9999]
RETRASO_LABELS = ["1 día", "2 días", "3 días", "4-5 días", "6-7 días", "8-10 días", "11+ días"]

CLICK_KEYS = ["chart_region", "chart_cd", "chart_retraso", "chart_clasif"]


@st.cache_data
def load_data():
    df = pd.read_csv(
        "dashboard_data.csv",
        parse_dates=["FechaPedido", "Fecha_Maxima", "Ultima_Hora_Entrega"],
    )
    df["Rango_Retraso"] = pd.cut(df["Dias_Retraso"], bins=RETRASO_BINS, labels=RETRASO_LABELS, right=True)
    return df


df = load_data()


def get_click(key, axis):
    """Lee la selección de clic (si existe) guardada por Streamlit para un gráfico."""
    state = st.session_state.get(key)
    if not state:
        return None
    points = state.get("selection", {}).get("points", [])
    if not points:
        return None
    return points[0].get(axis)


# ---------------- Sidebar: filtros ----------------
st.sidebar.title("Filtros")

regiones = sorted(df["Region"].dropna().unique().tolist())
sel_regiones = st.sidebar.multiselect("Región", regiones, default=regiones)

df_region = df[df["Region"].isin(sel_regiones)] if sel_regiones else df.iloc[0:0]

cds = sorted(df_region["CD Final"].dropna().unique().tolist())
sel_cds = st.sidebar.multiselect("CD Final", cds, default=cds)

fecha_min, fecha_max = df["FechaPedido"].min().date(), df["FechaPedido"].max().date()
rango_fechas = st.sidebar.date_input(
    "Rango de FechaPedido", value=(fecha_min, fecha_max), min_value=fecha_min, max_value=fecha_max
)
if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    f_ini, f_fin = rango_fechas
else:
    f_ini, f_fin = fecha_min, fecha_max

sidebar_mask = (
    df["Region"].isin(sel_regiones)
    & df["CD Final"].isin(sel_cds)
    & (df["FechaPedido"].dt.date >= f_ini)
    & (df["FechaPedido"].dt.date <= f_fin)
)
df_sidebar = df[sidebar_mask].copy()

# ---------------- Cross-filter por clic (estilo Power BI) ----------------
click_region = get_click("chart_region", "y")
click_cd = get_click("chart_cd", "y")
click_retraso = get_click("chart_retraso", "x")
click_clasif = get_click("chart_clasif", "x")


def build_filtered(base_df, exclude=None):
    d = base_df
    if click_region is not None and exclude != "region":
        d = d[d["Region"] == click_region]
    if click_cd is not None and exclude != "cd":
        d = d[d["CD Final"] == click_cd]
    if click_retraso is not None and exclude != "retraso":
        d = d[d["Rango_Retraso"] == click_retraso]
    if click_clasif is not None and exclude != "clasif":
        d = d[d["Clasificacion"] == click_clasif]
    return d


if sel_regiones and sel_cds:
    dff_full = build_filtered(df_sidebar)
else:
    dff_full = df_sidebar.iloc[0:0]

st.sidebar.caption(f"{len(dff_full):,} pedidos en el filtro actual (de {len(df):,} totales)")

if st.sidebar.button("✕ Quitar selección de clic"):
    for k in CLICK_KEYS:
        st.session_state.pop(k, None)
    st.rerun()

# ---------------- Header ----------------
st.title("KPI de Entrega Efectiva — Campaña C07-26 (CENTRUM)")
st.caption("Fuente: In Puts EE (CENTRUM) Final S1_LISTO_KPI.xlsx · Fecha de referencia del cálculo: 26/08/2026")

active_clicks = []
if click_region is not None:
    active_clicks.append(f"Región = **{click_region}**")
if click_cd is not None:
    active_clicks.append(f"CD Final = **{click_cd}**")
if click_retraso is not None:
    active_clicks.append(f"Días de retraso = **{click_retraso}**")
if click_clasif is not None:
    active_clicks.append(f"Clasificación = **{click_clasif}**")
if active_clicks:
    st.info(
        "🔎 Filtro por clic activo (haz clic de nuevo sobre la misma barra, o usa el botón de la barra "
        "lateral, para quitarlo): " + " · ".join(active_clicks)
    )

evaluados = dff_full[dff_full["Clasificacion"].isin(EVALUABLES)]
n_eval = len(evaluados)
n_total = len(dff_full)
n_efectiva = (evaluados["Clasificacion"] == "Entrega Efectiva").sum()
kpi_evaluados = (n_efectiva / n_eval * 100) if n_eval else 0
kpi_total = (n_efectiva / n_total * 100) if n_total else 0
n_pendiente = (dff_full["Clasificacion"] == "Pendiente fuera de tiempo").sum()
n_excluido = (dff_full["Clasificacion"] == "Excluido - sin Lead Time disponible").sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("% Entrega Efectiva (sobre evaluados)", f"{kpi_evaluados:.2f}%")
c2.metric("% Entrega Efectiva (sobre total)", f"{kpi_total:.2f}%")
c3.metric("Pedidos evaluados", f"{n_eval:,}")
c4.metric("Pendientes fuera de tiempo", f"{n_pendiente:,}")
c5.metric("Excluidos (sin Lead Time)", f"{n_excluido:,}")

st.divider()

# ---------------- Región y CD Final ----------------
col_izq, col_der = st.columns(2)


def resumen_por(df_eval, col):
    g = df_eval.groupby(col, observed=True).agg(
        Pedidos=("Clasificacion", "size"),
        Efectivos=("Clasificacion", lambda s: (s == "Entrega Efectiva").sum()),
    )
    g["%_EE"] = (g["Efectivos"] / g["Pedidos"] * 100).round(2)
    return g.reset_index().sort_values("%_EE")


dff_excl_region = build_filtered(df_sidebar, exclude="region") if sel_regiones and sel_cds else df_sidebar.iloc[0:0]
dff_excl_cd = build_filtered(df_sidebar, exclude="cd") if sel_regiones and sel_cds else df_sidebar.iloc[0:0]

with col_izq:
    st.subheader("% Entrega Efectiva por Región")
    st.caption("Haz clic en una barra para filtrar todo el dashboard por esa región.")
    r = resumen_por(dff_excl_region[dff_excl_region["Clasificacion"].isin(EVALUABLES)], "Region")
    if len(r):
        fig = px.bar(
            r, x="%_EE", y="Region", orientation="h", text="%_EE",
            color="%_EE", color_continuous_scale=[BAD, "#E8C468", GOOD],
            range_color=[max(0, r["%_EE"].min() - 5), 100],
            hover_data={"Pedidos": True, "Efectivos": True},
        )
        fig.add_vline(x=kpi_evaluados, line_dash="dash", line_color=NEUTRAL,
                       annotation_text=f"KPI general {kpi_evaluados:.1f}%")
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(coloraxis_showscale=False, xaxis_title="% Entrega Efectiva",
                           yaxis_title="", height=280, margin=dict(l=0, r=10, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True, on_select="rerun",
                         selection_mode="points", key="chart_region")
        st.dataframe(r.rename(columns={"%_EE": "% EE"}), use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos con los filtros actuales.")

with col_der:
    st.subheader("% Entrega Efectiva por CD Final (peor a mejor)")
    st.caption("Haz clic en una barra para filtrar todo el dashboard por ese CD Final.")
    c = resumen_por(dff_excl_cd[dff_excl_cd["Clasificacion"].isin(EVALUABLES)], "CD Final")
    if len(c):
        n_show = st.slider("Mostrar los N CD más débiles", 5, min(40, len(c)), 15, key="n_cd")
        peor = c.head(n_show)
        fig2 = px.bar(
            peor.sort_values("%_EE", ascending=False), x="%_EE", y="CD Final", orientation="h", text="%_EE",
            color="%_EE", color_continuous_scale=[BAD, "#E8C468", GOOD],
            range_color=[max(0, c["%_EE"].min() - 5), 100],
            hover_data={"Pedidos": True, "Efectivos": True},
        )
        fig2.add_vline(x=kpi_evaluados, line_dash="dash", line_color=NEUTRAL,
                        annotation_text=f"KPI general {kpi_evaluados:.1f}%")
        fig2.update_traces(texttemplate="%{text}%", textposition="outside")
        fig2.update_layout(coloraxis_showscale=False, xaxis_title="% Entrega Efectiva",
                            yaxis_title="", height=max(280, n_show * 22), margin=dict(l=0, r=10, t=10, b=0))
        st.plotly_chart(fig2, use_container_width=True, on_select="rerun",
                         selection_mode="points", key="chart_cd")
        with st.expander(f"Ver los {len(c)} CD completos"):
            st.dataframe(c.rename(columns={"%_EE": "% EE"}), use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos con los filtros actuales.")

pond_region = (r["Efectivos"].sum() / r["Pedidos"].sum() * 100) if len(r) and r["Pedidos"].sum() else 0
st.caption(
    f"Promedio ponderado por Región: **{pond_region:.2f}%** — "
    + ("coincide con el KPI general." if round(pond_region, 2) == round(kpi_evaluados, 2)
       else f"difiere {pond_region - kpi_evaluados:+.2f} pp del KPI general (por el filtro aplicado).")
)

st.divider()

# ---------------- Causas raíz ----------------
st.subheader("Causas raíz de la Entrega No Efectiva")

dff_excl_retraso = build_filtered(df_sidebar, exclude="retraso") if sel_regiones and sel_cds else df_sidebar.iloc[0:0]
dff_excl_clasif = build_filtered(df_sidebar, exclude="clasif") if sel_regiones and sel_cds else df_sidebar.iloc[0:0]

no_ef_retraso = dff_excl_retraso[dff_excl_retraso["Clasificacion"] == "Entrega No Efectiva"].copy()
no_ef = dff_full[dff_full["Clasificacion"] == "Entrega No Efectiva"].copy()
ef_clasif = dff_excl_clasif[dff_excl_clasif["Clasificacion"] == "Entrega Efectiva"].copy()
no_ef_clasif = dff_excl_clasif[dff_excl_clasif["Clasificacion"] == "Entrega No Efectiva"].copy()

if len(no_ef_retraso) or len(no_ef_clasif):
    cr1, cr2, cr3 = st.columns(3)

    with cr1:
        st.markdown("**Días de retraso vs. fecha máxima**")
        st.caption("Clic en una barra para filtrar por ese rango de retraso.")
        dist = no_ef_retraso["Rango_Retraso"].value_counts().reindex(RETRASO_LABELS).reset_index()
        dist.columns = ["Rango", "Pedidos"]
        fig3 = px.bar(dist, x="Rango", y="Pedidos", color_discrete_sequence=[ACCENT])
        fig3.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig3, use_container_width=True, on_select="rerun",
                         selection_mode="points", key="chart_retraso")

    with cr2:
        st.markdown("**N° de intentos de entrega promedio**")
        st.caption("Clic en una barra para filtrar por Efectiva / No Efectiva.")
        intentos_cmp = pd.DataFrame({
            "Clasificación": ["Entrega Efectiva", "Entrega No Efectiva"],
            "Promedio intentos": [
                round(ef_clasif["Total_Intentos"].mean(), 2) if len(ef_clasif) else 0,
                round(no_ef_clasif["Total_Intentos"].mean(), 2) if len(no_ef_clasif) else 0,
            ],
        })
        fig4 = px.bar(intentos_cmp, x="Clasificación", y="Promedio intentos",
                       color="Clasificación", color_discrete_map={
                           "Entrega Efectiva": GOOD, "Entrega No Efectiva": BAD})
        fig4.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        st.plotly_chart(fig4, use_container_width=True, on_select="rerun",
                         selection_mode="points", key="chart_clasif")
        st.caption("Un pedido No Efectiva requiere en promedio el doble de intentos que uno Efectivo: el cuello de botella es operativo (última milla), no de plazo.")

    with cr3:
        st.markdown("**Concentración de la No Efectiva por CD**")
        if len(no_ef):
            top_cd = no_ef["CD Final"].value_counts().head(8).reset_index()
            top_cd.columns = ["CD Final", "Pedidos No Efectiva"]
            top_cd["% del total No Efectiva"] = (top_cd["Pedidos No Efectiva"] / len(no_ef) * 100).round(1)
            fig5 = px.bar(top_cd.sort_values("Pedidos No Efectiva"), x="Pedidos No Efectiva", y="CD Final",
                           orientation="h", color_discrete_sequence=[BAD])
            fig5.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="")
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("No hay pedidos No Efectiva en el filtro actual.")

    pend = dff_full[dff_full["Clasificacion"] == "Pendiente fuera de tiempo"]
    if len(pend):
        nunca = int((pend["Tiene_Preliquidacion"] == False).sum())
        con_intento = len(pend) - nunca
        st.caption(
            f"Pendientes fuera de tiempo en el filtro actual: **{len(pend):,}** "
            f"({nunca:,} nunca tuvieron un intento de entrega registrado / {con_intento:,} sí tuvieron intento(s) sin cierre válido) "
            "— causa distinta a la No Efectiva, no ligada a última milla."
        )
else:
    st.info("No hay pedidos No Efectiva en el filtro actual.")

st.divider()

# ---------------- Tabla de excepciones ----------------
st.subheader("Tabla de excepciones (auditoría)")
tipo_exc = st.multiselect(
    "Clasificación a revisar",
    sorted(dff_full["Clasificacion"].dropna().unique().tolist()),
    default=[v for v in ["Entrega No Efectiva"] if v in dff_full["Clasificacion"].unique()],
)
cols_show = ["NroOrden", "FechaPedido", "ZIP", "Region", "CD Final", "LeadTimeDias",
             "Fecha_Maxima", "Ultima_Hora_Entrega", "Dias_Retraso", "Total_Intentos",
             "Motivo_Ultimo", "Clasificacion"]
exc = dff_full[dff_full["Clasificacion"].isin(tipo_exc)][cols_show].sort_values("Dias_Retraso", ascending=False)
st.dataframe(exc, use_container_width=True, hide_index=True, height=360)
st.download_button("Descargar excepciones (CSV)", exc.to_csv(index=False).encode("utf-8-sig"),
                    file_name="excepciones_entrega_efectiva.csv", mime="text/csv")

st.caption("Taller Entrega Efectiva · CENTRUM · Semana 03")

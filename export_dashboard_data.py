"""Exporta la data consolidada del Excel a CSV para que el dashboard de Streamlit cargue rapido.
Correr de nuevo si el Excel de KPI cambia."""
import pandas as pd

f = "In Puts EE (CENTRUM) Final S1_LISTO_KPI.xlsx"

pc = pd.read_excel(f, sheet_name="Pedidos_Clasificados",
                    parse_dates=["FechaPedido", "Fecha_Maxima", "Ultima_Hora_Entrega"])
idz = pd.read_excel(f, sheet_name="IDZones 26")[
    ["Cod Postal", "DEPARTAMENTO", "PROVINCIA", "DISTRITO", "Region", "Zona", "CD Final", "Latitud", "Longitud"]
]
uli = pd.read_excel(f, sheet_name="Preliquidacion_UltimoIntento")
uli["Orden_Base"] = uli["Orden_Base"].astype("Int64")
intentos = uli.groupby("Orden_Base")["Total_Intentos"].max().reset_index()

m = pc.merge(idz, left_on="ZIP", right_on="Cod Postal", how="left")
m = m.merge(intentos, left_on="NroOrden", right_on="Orden_Base", how="left")
m = m.drop(columns=["Cod Postal", "Orden_Base"])

m["Dias_Retraso"] = (m["Ultima_Hora_Entrega"].dt.normalize() - m["Fecha_Maxima"].dt.normalize()).dt.days
m["Semana"] = m["FechaPedido"].dt.isocalendar().week

m.to_csv("dashboard_data.csv", index=False, encoding="utf-8-sig")
print("Exportado:", len(m), "filas ->", "dashboard_data.csv")
print(m["Clasificacion"].value_counts())

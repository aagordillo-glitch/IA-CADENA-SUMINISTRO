# Bitácora del proyecto — Taller Entrega Efectiva (CENTRUM)

Registro de avances del taller de KPI de Entrega Efectiva (campaña C07-26).
Se actualiza al final de cada día de trabajo con lo avanzado, decisiones tomadas y lo pendiente para la próxima sesión.

---

## 2026-08-26 — Cálculo del KPI (pasos a–c del taller)

**Archivo de trabajo:** `In Puts EE (CENTRUM) Final S1_LISTO_KPI.xlsx`

- Auditoría de consistencia de las 5 hojas fuente (formato de código postal, rangos de fecha, duplicados) → hoja `Notas_Calidad_Datos`.
- Cruce de `Seg Ped C07-26` con `Preliquidacion_Limpia` (último intento por código de orden) y con `IDZones` / `LT C07-Acido` por código postal → hojas `Pedido_Entrega_Join`, `Preliquidacion_UltimoIntento`, `Preliquidacion_Sin_Pedido`.
- Clasificación de cada pedido según el diagrama de negocio (Efectiva / No Efectiva / Pendiente) → hoja `Pedidos_Clasificados`, con supuestos documentados en `Supuestos_Clasificacion` (mapeo de código postal LT↔IDZones, criterio de último intento, motivos válidos de recepción, fecha de referencia "hoy", pedidos excluidos por falta de lead time).
- 84 pedidos excluidos por no tener lead time disponible para su ZIP+fecha → hoja `Excluidos_Detalle`.

**Resultado (hoja `Resumen_KPI`):**
- Total de pedidos: 27,077
- % Entrega Efectiva sobre pedidos evaluados (Efectiva + No Efectiva, 26,471 pedidos): **94.07%**
- % Entrega Efectiva sobre el total de pedidos: **91.96%**

**Pendiente para la siguiente sesión:** desagregación por Región/CD Final (paso d), causas raíz (paso e), recomendaciones (paso f), dashboard Streamlit (paso g).

---

## 2026-08-28 — Desagregación por Región y CD Final (paso d)

- Se cruzó `Pedidos_Clasificados` con `IDZones 26` por ZIP (match perfecto, 0 pedidos sin Región/CD Final) y se calculó el % de Entrega Efectiva por Región y por CD Final sobre los pedidos evaluados (Efectiva + No Efectiva), ordenado de peor a mejor.
- Resultados guardados como nuevas hojas en `In Puts EE (CENTRUM) Final S1_LISTO_KPI.xlsx`: `EE_por_Region` y `EE_por_CD_Final`.

**Por Región (peor a mejor):**
| Región | Pedidos | % EE |
|---|---|---|
| SUR | 7,817 | 90.10% |
| CENTRO O. | 6,088 | 95.15% |
| NORTE | 12,566 | 96.01% |

**Por CD Final:** rango completo entre **CD Juliaca (68.92%, 1,496 pedidos)** —el más rezagado por lejos— y varios CD pequeños en 100% (Chala, Chilca, PIC Chinchao/Cajamarquilla/Ambo/Huariaca/La Oroya, todos con muy pocos pedidos). Otros focos débiles: CD Sicuani (76.60%), CD MDD (84.60%), CD Puno (85.16%), CD 5 Tarapoto (89.38%).

**Consistencia con el KPI general:** el promedio ponderado por número de pedidos, tanto por Región como por CD Final, da **94.07%** — coincide exactamente con el KPI general sobre evaluados (`Resumen_KPI`). No hay pedidos huérfanos en el corte.

**Se estableció como preferencia del usuario:** mantener esta bitácora actualizada, guardando los cambios al final de cada día de trabajo en el proyecto.

### Causas raíz de la Entrega No Efectiva (paso e)

Nueva hoja `Causas_Raiz` agregada al workbook con el detalle. Hallazgo principal: **la No Efectiva es un problema de ejecución (última milla), no de planeación/lead time.**

- Los 1,571 pedidos No Efectiva SÍ fueron aprobados con motivo válido (recibió titular/tercero) y SÍ tenían Lead Time asignado — de hecho su Lead Time promedio (5.80 días) es igual o mayor al de los Efectivos (5.47 días). Simplemente llegaron después de la fecha máxima.
- 61% de los No Efectiva se resolvió con solo 1 día de retraso; 21% tomó 4+ días (cola larga).
- Fuerte correlación con reintentos: un pedido No Efectiva necesitó en promedio el doble de intentos de entrega que uno Efectivo (2.53 vs 1.26) — señal de cuello de botella operativo de última milla, no de plazo mal calculado.
- **CD Juliaca concentra 29.6% de toda la No Efectiva nacional** (465 de 1,571 pedidos) siendo solo ~5.6% del volumen evaluado, con reintentos aún peores (2.77 en promedio). 4 de los 5 CD más débiles (Juliaca, Sicuani, MDD, Puno) son de la Región SUR — explica por qué SUR es la región más débil.
- Los 522 "Pendiente fuera de tiempo" tienen una causa distinta: 289 nunca tuvieron ni un intento de entrega registrado (nunca se despacharon), concentrados en CD AGENCIAS y CD YANBAL (no en Juliaca) — sugiere un problema de canal/proceso separado, no geográfico de última milla.

### Dashboard Streamlit (paso g, adelantado a pedido del usuario)

Se construyó `dashboard_ee.py`, un dashboard interactivo (no solo el esqueleto del taller) para tomar decisiones y presentar hallazgos:

- `export_dashboard_data.py`: exporta la data ya clasificada y cruzada (Pedidos_Clasificados + IDZones + N° de intentos) a `dashboard_data.csv`, para que el dashboard cargue rápido sin leer el Excel completo. Volver a correrlo si el Excel de KPI cambia.
- El dashboard incluye: filtros (Región, CD Final, rango de fecha de pedido), tarjetas de KPI general (sobre evaluados y sobre total), gráfico de % EE por Región y por CD Final (ordenado de peor a mejor, con línea de referencia del KPI general), sección de causas raíz (distribución de días de retraso, comparación de N° de intentos de entrega Efectiva vs No Efectiva, concentración por CD), y una tabla de excepciones descargable en CSV.
- Probado en navegador (Chrome vía la extensión) corriendo con `streamlit run dashboard_ee.py`: KPI general, cortes por Región/CD y gráficos de causas raíz se ven correctos y consistentes con `Resumen_KPI`, `EE_por_Region`, `EE_por_CD_Final` y `Causas_Raiz` del Excel.
- Para correrlo: `streamlit run dashboard_ee.py` (por defecto abre en http://localhost:8501).

**Pendiente para la siguiente sesión:** recomendaciones priorizadas y etiquetadas ESOAM (paso f, aún no hecho).

---

## 2026-09-02 — Cross-filtering estilo Power BI en el dashboard

A pedido del usuario, se agregó interactividad de "clic para filtrar" en `dashboard_ee.py`: al hacer clic en una barra de cualquiera de los 4 gráficos principales, todo el dashboard (tarjetas de KPI, los demás gráficos y la tabla de excepciones) se filtra por ese dato, igual que en Power BI. Se implementó con `st.plotly_chart(..., on_select="rerun", selection_mode="points", key=...)`, disponible desde Streamlit 1.35 (el entorno tiene 1.62 instalado).

- Gráficos clicables y campo que filtran: % EE por Región → `Region`; % EE por CD Final → `CD Final`; Días de retraso → `Rango_Retraso`; N° de intentos promedio (Efectiva vs No Efectiva) → `Clasificacion`. La tarjeta "Concentración de No Efectiva por CD" no es clicable (solo informativa), pero sí refleja los filtros activos.
- Los 4 filtros de clic se combinan entre sí y con los filtros de la barra lateral (Región/CD Final/rango de fechas) con lógica AND.
- Cada gráfico se calcula excluyendo su propio filtro de clic (self-filter exclusion, como en Power BI): así el gráfico de Región sigue mostrando las 3 regiones aunque ya se haya hecho clic en una, permitiendo cambiar de selección sin quedar "atascado".
- Se agregó un aviso ("🔎 Filtro por clic activo…") con el detalle de la selección activa, y un botón "✕ Quitar selección de clic" en la barra lateral para limpiar los 4 filtros a la vez (además del comportamiento nativo de Plotly: volver a hacer clic en la misma barra la deselecciona).
- `requirements.txt` actualizado a `streamlit>=1.35` (versión mínima que soporta `on_select` en `st.plotly_chart`).
- Verificado con `streamlit.testing.v1.AppTest` (sin necesidad del navegador, ya que la extensión de Chrome no estaba conectada en esta sesión): sin excepciones en la carga inicial (KPI 94.07%/91.96%, igual que `Resumen_KPI`) y, simulando un clic en la barra "SUR", las tarjetas recalculan correctamente a 90.10% / 7,817 pedidos evaluados — coincide exactamente con `EE_por_Region` del Excel.

**Pendiente para la siguiente sesión:** probar el cross-filtering en el navegador real (la extensión de Chrome no estaba conectada esta sesión) y recomendaciones priorizadas y etiquetadas ESOAM (paso f, aún no hecho).

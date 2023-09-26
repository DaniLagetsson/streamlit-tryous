# streamlit run .\calculadora_hipoteca.py --server.port 8080
# 
import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.express as px
import os
import warnings
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import time

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Calculadora hipoteca", page_icon=":house_buildings:", layout="wide") #Para la pestaña del navegador

st.title(" :house_buildings: Calculadora hipotecaria :bank: ") #El título de la página
st.markdown('<style>div.block-containe{pagging-top;1rem;}</style>',unsafe_allow_html = True)

hoy = date.today()

st.sidebar.header("Rellena las características de tu hipoteca: ")
precioCasa = st.sidebar.number_input("¿Cuánto cuesta la casa? Ej: 100000")
interes = st.sidebar.number_input("¿Qué interés tiene el préstamo? Ej: 2.5")
inmobiliaria = st.sidebar.number_input("¿Qué porcentaje se lleva la inmobiliaria? Ej: 3")
gastosTasacion = st.sidebar.number_input("¿Cuánto te cuesta la tasación? Ej: 400")
fechaIni = st.sidebar.date_input(f"¿Cuándo quieres comprarla? Por defecto {hoy}")
anyosHipoteca = st.sidebar.selectbox("¿En cuántos años quieres pagarla?", [5,10,15,20,25,30,35,40])
ahorros = st.sidebar.number_input("¿Cuántos ahorros tienes? Ej: 30000")
gastos = st.sidebar.number_input("¿Cuántos gastos tienes al mes de préstamos, facturas, ocio, comida, comunidad...? Ej: 500")
ingresos = st.sidebar.number_input("¿Cuántos ingresos tienes al mes? Ej: 1500")


fechaFin = fechaIni + relativedelta(years=anyosHipoteca)

gastosRegistro = 0.08*precioCasa + gastosTasacion
gastosInmobiliaria = inmobiliaria/100 * precioCasa  #400 de la tasación
hipoteca = precioCasa+gastosInmobiliaria+gastosRegistro-ahorros
interes = interes/100
cuota = round(npf.pmt(interes/12,anyosHipoteca*12,hipoteca)*(-1),2)

if hipoteca == 0:
    st.subheader(f"*¡Introduce las variables en el menú de la izquierda para ver tu caso!* ")
    st.write(f"Ejemplo para una hipoteca de 75.000€ a 30 años al 2.65% con unos ingresos de 1500€ y unos gastos de 500€ ")
    interes = 0.0265
    hipoteca = 75000
    anyosHipoteca = 30
    anyoIni = 2023
    ingresos = 1500
    gastos = 500
    cuota = round(npf.pmt(interes/12,anyosHipoteca*12,hipoteca)*(-1),2)
    fechaFin = fechaIni + relativedelta(years=anyosHipoteca)
    amort_type = "Ninguna"
df = pd.DataFrame(columns=["Año"])
anyoIni = fechaIni.year

with st.spinner('Cociendo resultados...'):
    time.sleep(2)
st.success('¡Resultados recién salidos del horno! :cookie:')

for i in range(anyosHipoteca):
    df.loc[i,"Año"]=anyoIni+i

df["Cuota"] = cuota*12
for i in range(anyosHipoteca):
    if i == 0:
        df.loc[0,"Intereses Pagados"] = round(interes*hipoteca,2)
        df.loc[0,"Amortizacion Anual"] = round(df.loc[0,"Cuota"]-df.loc[0,"Intereses Pagados"],2)
        df.loc[0,"Amortizacion Total"] = df.loc[0,"Amortizacion Anual"]
        df.loc[0,"Capital Pendiente"] = round(hipoteca - df.loc[0,"Amortizacion Anual"],2)
        df.loc[0,"Ahorros Acumulados"] = round(ingresos*12 - gastos*12 - cuota*12,2)
    else:
        df.loc[i,"Intereses Pagados"] = round(interes*df.loc[i-1,"Capital Pendiente"],2)
        df.loc[i,"Amortizacion Anual"] = round(df.loc[i,"Cuota"]-df.loc[i,"Intereses Pagados"],2)
        df.loc[i,"Amortizacion Total"] = df.loc[i,"Amortizacion Anual"]+df.loc[i-1,"Amortizacion Total"]
        df.loc[i,"Capital Pendiente"] = round(df.loc[i-1,"Capital Pendiente"] - df.loc[i,"Amortizacion Anual"],2)
        df.loc[i,"Ahorros Acumulados"] = round(df.loc[i-1,"Ahorros Acumulados"] + ingresos*12 - gastos*12 - cuota*12,2)

pagado = df[df["Ahorros Acumulados"]>df["Capital Pendiente"]].reset_index(drop=True)
if pagado.shape[0]>0:
    anyoPagado = pagado.loc[0,"Año"]

st.write(f"El período para pagar la hipoteca es del {fechaIni} al {fechaFin}")
st.write(f"El importe de la hipoteca será de {hipoteca} €")
st.write(f"La cuota mensual será de {cuota} € :euro:")
if pagado.shape[0]>0:
    st.markdown(f"En el año {anyoPagado} tendrás suficientes ahorros para amortizar la hipoteca. ¡Enhorabuena! :confetti_ball: ")

amort_type = st.radio("¿Vas a hacer alguna amortización parcial en cuota o en tiempo?", ["Ninguna","Cuota","Tiempo"])
if amort_type != "Ninguna":
    amortizacion = st.number_input("¿Cuánto dinero vas a amortizar?")
    anyo_amort = st.number_input("¿En qué año vas a amortizar?", fechaIni.year + 1 ,fechaFin.year)
    tasa_amort = st.number_input("¿Hay un porcentaje de penalización por amortización? Debe estar por ley entre el 0 y el 2",0,2)
    if tasa_amort != 0:
        tasa_amort = tasa_amort/100


if amort_type == "Cuota":
    for i in range(anyosHipoteca):
        if i == 0:
            df.loc[0,"Intereses Pagados"] = round(interes*hipoteca,2)
            df.loc[0,"Amortizacion Anual"] = round(df.loc[0,"Cuota"]-df.loc[0,"Intereses Pagados"],2)
            df.loc[0,"Amortizacion Total"] = df.loc[0,"Amortizacion Anual"]
            df.loc[0,"Capital Pendiente"] = round(hipoteca - df.loc[0,"Amortizacion Anual"],2)
            df.loc[0,"Ahorros Acumulados"] = round(ingresos*12 - gastos*12 - cuota*12,2)
        elif df.loc[i,"Año"]<anyo_amort:
            df.loc[i,"Intereses Pagados"] = round(interes*df.loc[i-1,"Capital Pendiente"],2)
            df.loc[i,"Amortizacion Anual"] = round(df.loc[i,"Cuota"]-df.loc[i,"Intereses Pagados"],2)
            df.loc[i,"Amortizacion Total"] = df.loc[i,"Amortizacion Anual"]+df.loc[i-1,"Amortizacion Total"]
            df.loc[i,"Capital Pendiente"] = round(df.loc[i-1,"Capital Pendiente"] - df.loc[i,"Amortizacion Anual"],2)
            df.loc[i,"Ahorros Acumulados"] = round(df.loc[i-1,"Ahorros Acumulados"] + ingresos*12 - gastos*12 - cuota*12,2)
        elif df.loc[i,"Año"]==anyo_amort:
            anyosHipoteNew = fechaFin.year - anyo_amort
            nuevaCuota = round(npf.pmt(interes/12,anyosHipoteNew*12,df.loc[i-1,"Capital Pendiente"]-amortizacion)*(-1),2)
            amortizacion = amortizacion - tasa_amort*df.loc[i-1,"Capital Pendiente"]
            df.loc[i,"Cuota"] = nuevaCuota*12
            df.loc[i,"Intereses Pagados"] = round(interes*df.loc[i-1,"Capital Pendiente"],2)
            df.loc[i,"Amortizacion Anual"] = round(df.loc[i,"Cuota"]-df.loc[i,"Intereses Pagados"]+amortizacion,2)
            df.loc[i,"Amortizacion Total"] = df.loc[i,"Amortizacion Anual"]+df.loc[i-1,"Amortizacion Total"] 
            df.loc[i,"Capital Pendiente"] = round(df.loc[i-1,"Capital Pendiente"] - df.loc[i,"Amortizacion Anual"],2)
            df.loc[i,"Ahorros Acumulados"] = round(df.loc[i-1,"Ahorros Acumulados"] + ingresos*12 - gastos*12 - cuota*12 - amortizacion,2)
        elif df.loc[i,"Año"]>anyo_amort:
            df.loc[i,"Cuota"] = nuevaCuota*12
            df.loc[i,"Intereses Pagados"] = round(interes*df.loc[i-1,"Capital Pendiente"],2)
            df.loc[i,"Amortizacion Anual"] = round(df.loc[i,"Cuota"]-df.loc[i,"Intereses Pagados"],2)
            df.loc[i,"Amortizacion Total"] = df.loc[i,"Amortizacion Anual"]+df.loc[i-1,"Amortizacion Total"]
            df.loc[i,"Capital Pendiente"] = round(df.loc[i-1,"Capital Pendiente"] - df.loc[i,"Amortizacion Anual"],2)
            df.loc[i,"Ahorros Acumulados"] = round(df.loc[i-1,"Ahorros Acumulados"] + ingresos*12 - gastos*12 - cuota*12,2)
    st.markdown(f"La cuota mensual a partir de {anyo_amort} será de {nuevaCuota} € :euro: :tada:")    

if amort_type == "Tiempo":
    for i in range(anyosHipoteca):
        if i == 0:
            df.loc[0,"Intereses Pagados"] = round(interes*hipoteca,2)
            df.loc[0,"Amortizacion Anual"] = round(df.loc[0,"Cuota"]-df.loc[0,"Intereses Pagados"],2)
            df.loc[0,"Amortizacion Total"] = df.loc[0,"Amortizacion Anual"]
            df.loc[0,"Capital Pendiente"] = round(hipoteca - df.loc[0,"Amortizacion Anual"],2)
            df.loc[0,"Ahorros Acumulados"] = round(ingresos*12 - gastos*12 - cuota*12,2)
        elif df.loc[i,"Año"]<anyo_amort:
            df.loc[i,"Intereses Pagados"] = round(interes*df.loc[i-1,"Capital Pendiente"],2)
            df.loc[i,"Amortizacion Anual"] = round(df.loc[i,"Cuota"]-df.loc[i,"Intereses Pagados"],2)
            df.loc[i,"Amortizacion Total"] = df.loc[i,"Amortizacion Anual"]+df.loc[i-1,"Amortizacion Total"]
            df.loc[i,"Capital Pendiente"] = round(df.loc[i-1,"Capital Pendiente"] - df.loc[i,"Amortizacion Anual"],2)
            df.loc[i,"Ahorros Acumulados"] = round(df.loc[i-1,"Ahorros Acumulados"] + ingresos*12 - gastos*12 - cuota*12,2)
        elif df.loc[i,"Año"]==anyo_amort:
            amortizacion = amortizacion - tasa_amort*df.loc[i-1,"Capital Pendiente"]
            df.loc[i,"Intereses Pagados"] = round(interes*df.loc[i-1,"Capital Pendiente"],2)
            df.loc[i,"Amortizacion Anual"] = round(df.loc[i,"Cuota"]-df.loc[i,"Intereses Pagados"]+amortizacion,2)
            df.loc[i,"Amortizacion Total"] = df.loc[i,"Amortizacion Anual"]+df.loc[i-1,"Amortizacion Total"] 
            df.loc[i,"Capital Pendiente"] = round(df.loc[i-1,"Capital Pendiente"] - df.loc[i,"Amortizacion Anual"],2)
            df.loc[i,"Ahorros Acumulados"] = round(df.loc[i-1,"Ahorros Acumulados"] + ingresos*12 - gastos*12 - cuota*12 - amortizacion,2)
        elif df.loc[i,"Año"]>anyo_amort:
            df.loc[i,"Intereses Pagados"] = round(interes*df.loc[i-1,"Capital Pendiente"],2)
            df.loc[i,"Amortizacion Anual"] = round(df.loc[i,"Cuota"]-df.loc[i,"Intereses Pagados"],2)
            df.loc[i,"Amortizacion Total"] = df.loc[i,"Amortizacion Anual"]+df.loc[i-1,"Amortizacion Total"]
            df.loc[i,"Capital Pendiente"] = round(df.loc[i-1,"Capital Pendiente"] - df.loc[i,"Amortizacion Anual"],2)
            df.loc[i,"Ahorros Acumulados"] = round(df.loc[i-1,"Ahorros Acumulados"] + ingresos*12 - gastos*12 - cuota*12,2)
    df = df[df["Capital Pendiente"]>0]
    reduccion = df.loc[df.shape[0]-1,"Año"]
    st.markdown(f"El período hipotecario se reducirá al año {reduccion} :calendar: :tada:")    

with st.expander("Desplegar la tabla de amortización"):
    st.write(df.style.background_gradient(cmap="Blues"))
    csv = df.to_csv(index=False, sep=";").encode('ISO-8859-1')
    st.download_button("Descargar tabla en csv", data=csv, file_name = f"Tabla de amortización_{hoy}.csv", mime = "text/csv",
        help = "Pincha aquí para descargar la tabla de amortización anual")

col1, col2 = st.tabs(["Amortización","Intereses"])
with col1:
    st.subheader("Gráfica de amortización")
    fig = px.line(df, x="Año",y=["Amortizacion Total","Capital Pendiente", "Ahorros Acumulados"], template="seaborn")
    st.plotly_chart(fig,use_container_width=True, height = 200)

with col2:
    st.subheader("Gráfica de intereses")
    fig2 = px.line(df, x="Año",y=["Intereses Pagados","Amortizacion Anual"], template="seaborn")
    st.plotly_chart(fig2,use_container_width=True, height = 200)

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
mesesHipoteca = anyosHipoteca*12

if hipoteca == 0:
    st.subheader(f"*¡Introduce las variables en el menú de la izquierda para ver tu caso!* ")
    st.write(f"Ejemplo para una hipoteca de 50.000€ a 30 años al 3.7% con unos ingresos de 3500€ y unos gastos de 600€ ")
    interes = 0.037
    hipoteca = 50000
    anyosHipoteca = 30
    anyoIni = 2023
    ingresos = 3500
    gastos = 600
    cuota = round(npf.pmt(interes/12,anyosHipoteca*12,hipoteca)*(-1),2)
    fechaFin = fechaIni + relativedelta(years=anyosHipoteca)
    amort_type = "Ninguna"
df = pd.DataFrame(columns=["Mes"])
anyoIni = fechaIni.year

with st.spinner('Cociendo resultados...'):
    time.sleep(2)
st.success('¡Resultados recién salidos del horno! :cookie:')

for i in range(mesesHipoteca):
    df.loc[i,"Mes"]=fechaIni + relativedelta(months=i)

df["Cuota"] = cuota
for i in range(mesesHipoteca):
    if i == 0:
        df.loc[0,"Intereses Pagados"] = round(interes*hipoteca/12,2)
        df.loc[0,"Amortizacion Mensual"] = round(df.loc[0,"Cuota"]-df.loc[0,"Intereses Pagados"],2)
        df.loc[0,"Amortizacion Total"] = df.loc[0,"Amortizacion Mensual"]
        df.loc[0,"Capital Pendiente"] = round(hipoteca - df.loc[0,"Amortizacion Mensual"],2)
        df.loc[0,"Ahorros Acumulados"] = round(ingresos - gastos - cuota,2)
    else:
        df.loc[i,"Intereses Pagados"] = round(interes*df.loc[i-1,"Capital Pendiente"]/12,2)
        df.loc[i,"Amortizacion Mensual"] = round(df.loc[i,"Cuota"]-df.loc[i,"Intereses Pagados"],2)
        df.loc[i,"Amortizacion Total"] = df.loc[i,"Amortizacion Mensual"]+df.loc[i-1,"Amortizacion Total"]
        df.loc[i,"Capital Pendiente"] = round(df.loc[i-1,"Capital Pendiente"] - df.loc[i,"Amortizacion Mensual"],2)
        df.loc[i,"Ahorros Acumulados"] = round(df.loc[i-1,"Ahorros Acumulados"] + ingresos - gastos - cuota,2)

pagado = df[df["Ahorros Acumulados"]>df["Capital Pendiente"]].reset_index(drop=True)
if pagado.shape[0]>0:
    anyoPagado = pagado.loc[0,"Mes"]

st.write(f"El período para pagar la hipoteca es del {fechaIni} al {fechaFin}")
st.write(f"El importe de la hipoteca será de {hipoteca} €")
st.write(f"La cuota mensual será de {cuota} € :euro:")
if pagado.shape[0]>0:
    st.markdown(f"En la fecha {anyoPagado} tendrás suficientes ahorros para amortizar la hipoteca. ¡Enhorabuena! :confetti_ball: ")

anyo_amort = fechaIni + relativedelta(years=1)

amort_type = st.radio("¿Vas a hacer alguna amortización parcial en cuota o en tiempo?", ["No","Sí"])
if amort_type != "No":
    amortizacion = st.number_input("¿Cuánto dinero vas a amortizar?")
    anyo_amort = st.date_input("¿En qué fecha vas a amortizar?")
    anyo_amort = anyo_amort.replace(day=fechaIni.day) 
    tasa_amort = st.number_input("¿Hay un porcentaje de penalización por amortización? Debe estar por ley entre el 0 y el 2",0,2)
    amort_gratis = st.number_input("¿Hay un porcentaje de amortización gratuita anual?",0,100)
    if amort_gratis > 0:
        df_pendiente = df[df["Mes"]==anyo_amort][["Capital Pendiente"]].reset_index(drop=True)
        pendiente = df_pendiente.loc[0,"Capital Pendiente"]
        amort_gratis = amort_gratis/100
        max_amort_gratis = pendiente*amort_gratis
        if max_amort_gratis > amortizacion:
            amort_gravada = 0
        else:
            amort_gravada = amortizacion-max_amort_gratis
    else:
        amort_gravada = amortizacion
    if tasa_amort > 0:
        tasa_amort = tasa_amort/100


if (amort_type != "No") & (anyo_amort > fechaIni):
    for i in range(mesesHipoteca):
        if i == 0:
            df.loc[i,"Cuota Reducida"] = cuota
            df.loc[0,"Intereses Pagados"] = round(interes*hipoteca/12,2)
            df.loc[0,"Amortizacion Mensual"] = round(df.loc[0,"Cuota"]-df.loc[0,"Intereses Pagados"],2)
            df.loc[0,"Amortizacion Total"] = df.loc[0,"Amortizacion Mensual"]
            df.loc[0,"Capital Pendiente"] = round(hipoteca - df.loc[0,"Amortizacion Mensual"],2)
            df.loc[0,"Ahorros Acumulados"] = round(ingresos - gastos - cuota,2)
            df.loc[0,"Intereses Pagados Red Cuota"] = df.loc[0,"Intereses Pagados"]
            df.loc[0,"Amortizacion Mensual Red Cuota"] = df.loc[0,"Amortizacion Mensual"]
            df.loc[0,"Amortizacion Total Red Cuota"] = df.loc[0,"Amortizacion Total"]
            df.loc[0,"Capital Pendiente Red Cuota"] = df.loc[0,"Capital Pendiente"]
            df.loc[0,"Ahorros Acumulados Red Cuota"] = df.loc[0,"Ahorros Acumulados"]
            df.loc[0,"Intereses Pagados Red Tiempo"] = df.loc[0,"Intereses Pagados"]
            df.loc[0,"Amortizacion Mensual Red Tiempo"] = df.loc[0,"Amortizacion Mensual"]
            df.loc[0,"Amortizacion Total Red Tiempo"] = df.loc[0,"Amortizacion Total"]
            df.loc[0,"Capital Pendiente Red Tiempo"] = df.loc[0,"Capital Pendiente"]
            df.loc[0,"Ahorros Acumulados Red Tiempo"] = df.loc[0,"Ahorros Acumulados"]
        elif df.loc[i,"Mes"]<anyo_amort:
            df.loc[i,"Cuota Reducida"] = cuota
            df.loc[i,"Intereses Pagados"] = round(interes*df.loc[i-1,"Capital Pendiente"]/12,2)
            df.loc[i,"Amortizacion Mensual"] = round(df.loc[i,"Cuota"]-df.loc[i,"Intereses Pagados"],2)
            df.loc[i,"Amortizacion Total"] = df.loc[i,"Amortizacion Mensual"]+df.loc[i-1,"Amortizacion Total"]
            df.loc[i,"Capital Pendiente"] = round(df.loc[i-1,"Capital Pendiente"] - df.loc[i,"Amortizacion Mensual"],2)
            df.loc[i,"Ahorros Acumulados"] = round(df.loc[i-1,"Ahorros Acumulados"] + ingresos - gastos - cuota,2)            
            df.loc[i,"Intereses Pagados Red Cuota"] = df.loc[i,"Intereses Pagados"]
            df.loc[i,"Amortizacion Mensual Red Cuota"] = df.loc[i,"Amortizacion Mensual"]
            df.loc[i,"Amortizacion Total Red Cuota"] = df.loc[i,"Amortizacion Total"]
            df.loc[i,"Capital Pendiente Red Cuota"] = df.loc[i,"Capital Pendiente"]
            df.loc[i,"Ahorros Acumulados Red Cuota"] = df.loc[i,"Ahorros Acumulados"]
            df.loc[i,"Intereses Pagados Red Tiempo"] = df.loc[i,"Intereses Pagados"]
            df.loc[i,"Amortizacion Mensual Red Tiempo"] = df.loc[i,"Amortizacion Mensual"]
            df.loc[i,"Amortizacion Total Red Tiempo"] = df.loc[i,"Amortizacion Total"]
            df.loc[i,"Capital Pendiente Red Tiempo"] = df.loc[i,"Capital Pendiente"]
            df.loc[i,"Ahorros Acumulados Red Tiempo"] = df.loc[i,"Ahorros Acumulados"]
        elif df.loc[i,"Mes"]==anyo_amort:
            mesesHipoteNew = int(((fechaFin - anyo_amort).days)/30.5)
            amortizacion = float(amortizacion - tasa_amort*amort_gravada)
            nuevaCuota = round(npf.pmt(interes/12,mesesHipoteNew,df.loc[i-1,"Capital Pendiente"]-amortizacion)*(-1),2)
            df.loc[i,"Cuota Reducida"] = nuevaCuota
            df.loc[i,"Intereses Pagados"] = round(interes*df.loc[i-1,"Capital Pendiente"]/12,2)
            df.loc[i,"Amortizacion Mensual"] = round(df.loc[i,"Cuota"]-df.loc[i,"Intereses Pagados"],2)
            df.loc[i,"Amortizacion Total"] = df.loc[i,"Amortizacion Mensual"]+df.loc[i-1,"Amortizacion Total"]
            df.loc[i,"Capital Pendiente"] = round(df.loc[i-1,"Capital Pendiente"] - df.loc[i,"Amortizacion Mensual"],2)
            df.loc[i,"Ahorros Acumulados"] = round(df.loc[i-1,"Ahorros Acumulados"] + ingresos - gastos - cuota,2)
            df.loc[i,"Intereses Pagados Red Cuota"] = df.loc[i,"Intereses Pagados"]
            df.loc[i,"Amortizacion Mensual Red Cuota"] = round(df.loc[i,"Cuota Reducida"]-df.loc[i,"Intereses Pagados Red Cuota"]+amortizacion,2)
            df.loc[i,"Amortizacion Total Red Cuota"] = df.loc[i,"Amortizacion Mensual Red Cuota"]+df.loc[i-1,"Amortizacion Total Red Cuota"] 
            df.loc[i,"Capital Pendiente Red Cuota"] = round(df.loc[i-1,"Capital Pendiente Red Cuota"] - df.loc[i,"Amortizacion Mensual Red Cuota"],2)
            df.loc[i,"Ahorros Acumulados Red Cuota"] = round(df.loc[i-1,"Ahorros Acumulados Red Cuota"] + ingresos - gastos - cuota - amortizacion,2)
            df.loc[i,"Intereses Pagados Red Tiempo"] = df.loc[i,"Intereses Pagados"]
            df.loc[i,"Amortizacion Mensual Red Tiempo"] = round(df.loc[i,"Cuota"]-df.loc[i,"Intereses Pagados Red Tiempo"]+amortizacion,2)
            df.loc[i,"Amortizacion Total Red Tiempo"] = df.loc[i,"Amortizacion Mensual Red Tiempo"]+df.loc[i-1,"Amortizacion Total Red Tiempo"] 
            df.loc[i,"Capital Pendiente Red Tiempo"] = round(df.loc[i-1,"Capital Pendiente Red Tiempo"] - df.loc[i,"Amortizacion Mensual Red Tiempo"],2)
            df.loc[i,"Ahorros Acumulados Red Tiempo"] = round(df.loc[i-1,"Ahorros Acumulados Red Tiempo"] + ingresos - gastos - cuota - amortizacion,2)
        elif df.loc[i,"Mes"]>anyo_amort:
            df.loc[i,"Cuota Reducida"] = nuevaCuota
            df.loc[i,"Intereses Pagados"] = round(interes*df.loc[i-1,"Capital Pendiente"]/12,2)
            df.loc[i,"Amortizacion Mensual"] = round(df.loc[i,"Cuota"]-df.loc[i,"Intereses Pagados"],2)
            df.loc[i,"Amortizacion Total"] = df.loc[i,"Amortizacion Mensual"]+df.loc[i-1,"Amortizacion Total"]
            df.loc[i,"Capital Pendiente"] = round(df.loc[i-1,"Capital Pendiente"] - df.loc[i,"Amortizacion Mensual"],2)
            df.loc[i,"Ahorros Acumulados"] = round(df.loc[i-1,"Ahorros Acumulados"] + ingresos - gastos - cuota,2)            
            df.loc[i,"Intereses Pagados Red Cuota"] = round(interes*df.loc[i-1,"Capital Pendiente Red Cuota"]/12,2)
            df.loc[i,"Amortizacion Mensual Red Cuota"] = round(df.loc[i,"Cuota Reducida"]-df.loc[i,"Intereses Pagados Red Cuota"],2)
            df.loc[i,"Amortizacion Total Red Cuota"] = df.loc[i,"Amortizacion Mensual Red Cuota"]+df.loc[i-1,"Amortizacion Total Red Cuota"] 
            df.loc[i,"Capital Pendiente Red Cuota"] = round(df.loc[i-1,"Capital Pendiente Red Cuota"] - df.loc[i,"Amortizacion Mensual Red Cuota"],2)
            df.loc[i,"Ahorros Acumulados Red Cuota"] = round(df.loc[i-1,"Ahorros Acumulados Red Cuota"] + ingresos - gastos - cuota,2)
            df.loc[i,"Intereses Pagados Red Tiempo"] = round(interes*df.loc[i-1,"Capital Pendiente Red Tiempo"]/12,2)
            df.loc[i,"Amortizacion Mensual Red Tiempo"] = round(df.loc[i,"Cuota"]-df.loc[i,"Intereses Pagados Red Tiempo"],2)
            df.loc[i,"Amortizacion Total Red Tiempo"] = df.loc[i,"Amortizacion Mensual Red Tiempo"]+df.loc[i-1,"Amortizacion Total Red Tiempo"] 
            df.loc[i,"Capital Pendiente Red Tiempo"] = round(df.loc[i-1,"Capital Pendiente Red Tiempo"] - df.loc[i,"Amortizacion Mensual Red Tiempo"],2)
            df.loc[i,"Ahorros Acumulados Red Tiempo"] = round(df.loc[i-1,"Ahorros Acumulados Red Tiempo"] + ingresos - gastos - cuota,2)
    st.markdown(f"Si decides reducir cuota, la nueva cuota mensual a partir de {anyo_amort} será de {nuevaCuota} € :euro: :tada:")    
    df_temp = df[df["Capital Pendiente Red Tiempo"]>0]
    reduccion = df_temp.loc[df_temp.shape[0]-1,"Mes"]
    st.markdown(f"Si decides reducir tiempo, el período hipotecario se reducirá a la fecha {reduccion} :calendar: :tada:")    

  

with st.expander("Desplegar la tabla de amortización"):
    st.write(df.style.background_gradient(cmap="Blues"))
    csv = df.to_csv(index=False, sep=";").encode('ISO-8859-1')
    st.download_button("Descargar tabla en csv", data=csv, file_name = f"Tabla de amortización_{hoy}.csv", mime = "text/csv",
        help = "Pincha aquí para descargar la tabla de amortización anual")

col1, col2 = st.tabs(["Amortización","Intereses"])
with col1:
    st.subheader("Gráfica de amortización")
    fig = px.line(df, x="Mes",y=["Amortizacion Total","Capital Pendiente", "Ahorros Acumulados"], template="seaborn")
    st.plotly_chart(fig,use_container_width=True, height = 200)

with col2:
    st.subheader("Gráfica de intereses")
    fig2 = px.line(df, x="Mes",y=["Intereses Pagados","Amortizacion Mensual"], template="seaborn")
    st.plotly_chart(fig2,use_container_width=True, height = 200)

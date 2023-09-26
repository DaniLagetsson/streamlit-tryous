# Correr la siguiente línea en la terminal para lanzar la app
# streamlit run .\streamlit_app.py --server.port 8888

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import warnings
import glob
warnings.filterwarnings('ignore')

fileGit = "https://raw.githubusercontent.com/DaniLagetsson/streamlit-tryous/main/consumo_periodo_23-08-2023_22-09-2023.csv"

# ruta = 'C:/Users/u1129253/Downloads/'
# list_of_files = glob.glob(ruta+"consumo_periodo*.csv") # * means all if need specific format then *.csv
# latest_file = max(list_of_files, key=os.path.getctime)

st.set_page_config(page_title="Factura de la luz", page_icon=":memo:", layout="wide") #Para la pestaña del navegador

st.title(" :memo: Factura de la luz") #El título de la página
st.markdown('<style>div.block-containe{pagging-top;1rem;}</style>',unsafe_allow_html = True)

fl = st.file_uploader(":file_folder: Upload a file", type=(["csv"]))
if fl is not None:
    filename = fl.name
    st.write(filename)
    df = pd.read_csv(fl, sep=";")
else:
    # os.chdir("C:/Users/u1129253/Downloads")
    df = pd.read_csv(fileGit, sep=";")

col1, col2 = st.columns((2))

df["Fecha"] = pd.to_datetime(pd.to_datetime(df["Fecha"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d'))
df["Consumo_kWh"] = df["Consumo_kWh"].str.replace(",",".")
df["Consumo_kWh"] = df["Consumo_kWh"].astype(float)
df["Hora"] = df["Hora"]-1
# df["Hora"] = np.where(df["Hora"]==0,24,df["Hora"])

startDate = pd.to_datetime(df["Fecha"]).min()
endDate = pd.to_datetime(df["Fecha"]).max()

with col1:
    date1 = pd.to_datetime(st.date_input("Start Date",startDate))

with col2:
    date2 = pd.to_datetime(st.date_input("End Date",endDate))

df = df[(df["Fecha"]>=date1)&(df["Fecha"]<=date2)].copy()

fechas = pd.DatetimeIndex(df['Fecha'].unique())

st.sidebar.header("Rellena las características de tu contrato: ")
coste_kwh = st.sidebar.text_input("¿Cuál es el coste del kwH en €? Por defecto 0.1299")
coste_pot = st.sidebar.text_input("¿Cuál es el coste de la potencia total en €? Por defecto 0.122308")
pot_contr = st.sidebar.text_input("¿Cuál es tu potencia contratada en Kw? Por defecto 3")
IVA = st.sidebar.selectbox("¿Cuál es el IVA vigente para la electricidad?", ["0%","4%","5%","10%","21%"])


# hour = st.sidebar.multiselect("Selecciona una hora", df["Hora"].unique())

# Cálculo de la factura

if not coste_kwh:
    coste_kwh = 0.1299
else:
    coste_kwh = coste_kwh.replace(",",".")
    coste_kwh = float(coste_kwh)
if not coste_pot:
    coste_pot = 0.122308
else:
    coste_pot = coste_pot.replace(",",".")
    coste_pot = float(coste_pot)
if not pot_contr:
    pot_contr = 3
else:
    pot_contr = pot_contr.replace(",",".")
    pot_contr = float(pot_contr)
alq_equipo = 0.02688
cargo_bono_social = 0.03846
imp_elec = 0.005
if not IVA:
    IVA = 0.05
else:
    IVA = IVA.replace(",",".")
    IVA = IVA.replace("%","")
    IVA = float(IVA)
    IVA = IVA/100
dias = len(df.Fecha.unique())
energia_cons_libre = df["Consumo_kWh"].sum()*coste_kwh
potencia_cons_libre = dias*pot_contr*coste_pot
financ_bs = dias*cargo_bono_social
total_energia_libre = (energia_cons_libre+potencia_cons_libre+financ_bs)*(1+imp_elec)
coste_equipo = alq_equipo*dias
total_factura_libre = round((total_energia_libre+coste_equipo)*(1+IVA),2)

st.write(f" :euro: La factura para el período seleccionado es de {total_factura_libre} € :euro:")

consumo_df = df.groupby(by = ["Fecha"],as_index=False)["Consumo_kWh"].sum()

cl1, cl2 = st.columns((2))

with cl1:
    st.subheader("Consumo por fecha")
    fig = px.bar(consumo_df, x="Fecha",y="Consumo_kWh", template="seaborn")
    st.plotly_chart(fig,use_container_width=True, height = 200)

with cl2:
    with st.expander("Datos consumo"):
        st.write(consumo_df.style.background_gradient(cmap="Blues"))
        csv = consumo_df.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar datos", data=csv, file_name = "Consumo.csv", mime = "text/csv",
            help = "Pincha aquí para descargar el fichero")

# st.table(consumo_df.head())


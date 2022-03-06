#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 18:46:34 2022

@author: javiroman
"""

import pandas as pd
from os import path
inputs = "/Users/javiroman/RGV Soluciones Dropbox/Javier Román Bautista/Contenido Marketing/Inputs"


# Cargamos la base de datos viales
datos_viales = pd.read_csv(path.join(inputs, 'datos_viales.csv'))
# La exploramos
datos_viales.head()
columnas = list(datos_viales.columns)
columnas
# Quitamos las columnas con na values
datos_viales_simple = datos_viales.dropna(axis=1,how='all')
# Vemos un poco la base de datos
columnas = list(datos_viales_simple.columns)
columnas
sample = datos_viales_simple.sample(2000)
sample
sample = datos_viales_simple.head(2000)
sample
# Reducimos la base a solo las filas que contengan datos del tránsito diario promedio anual 
datos_viales_simple_2=datos_viales_simple.dropna(subset =  ['TDPA'])
datos_viales_simple_2["TDPA"]=datos_viales_simple_2["TDPA"].str.replace(',', '')
datos_viales_simple_2['TDPA'] = pd.to_numeric(datos_viales_simple_2['TDPA'])
datos_viales_simple_2["TDPA"].sum()
# Obteneos el TDPA por entidad federativa
resumen_datos_viajes = (datos_viales_simple_2
                       .groupby(['Estado','Carretera'])
                       .agg(TDPA_promedio_carretera = ('TDPA', 'mean')))
resumen_datos_viajes_final = (resumen_datos_viajes
                              .groupby('Estado')
                              .agg(TDPA_entidad = ('TDPA_promedio_carretera', 'sum')))
resumen_datos_viajes_final['TDPA_entidad'].sum()
# Guardamos los resultados
resumen_datos_viajes_final.to_csv(path.join(inputs, 'resultados_carreteras.csv'))


# Cargamos los datos de caminos a nivel nacional
caminos = pd.read_csv(path.join(inputs, 'red_vial.csv'))
# Nos quedamos solo con las carreteras
caminos.columns
pd.unique(caminos['TIPO_VIAL'])
carreteras = caminos.query('TIPO_VIAL == "Carretera"')
# Nos quedamos solo con las carreteras estatales
carreteras_estatales = carreteras.query('ADMINISTRA=="Estatal"')
pd.unique(carreteras_estatales['JURISDI'])
carreteras_estatales = carreteras_estatales.set_index("JURISDI")
carreteras_estatales = carreteras_estatales.drop(labels = ['Fed.', 'N/D'], axis=0)
carreteras_estatales = carreteras_estatales.reset_index()
carreteras_estatales = carreteras_estatales.set_index("ID_RED")
carreteras_estatales = carreteras_estatales.dropna(subset =  ['JURISDI'])
# Obtenemos la longitud de las carreteras por estado
carreteras_estatales['LONGITUD'] = carreteras_estatales['LONGITUD'].str.replace(',', '')
carreteras_estatales['LONGITUD'] = pd.to_numeric(carreteras_estatales['LONGITUD'])
carreteras_estatales['LONGITUD'].sum()
resumen_carreteras_estatales = (carreteras_estatales
                       .groupby('JURISDI')
                       .agg(metros_total = ('LONGITUD', 'sum')))
resumen_carreteras_estatales['long_kilometros'] = resumen_carreteras_estatales['metros_total']/1000
resumen_carreteras_estatales['long_kilometros'].sum()
resumen_carreteras_estatales['cve_ent'] = [1,2,3,4,8,7,5,6,9,10,12,11,13,14,15,16,17,19,18,20,21,23,22,24,25,26,27,28,29,30,31,32]
# Guardamos los resultados
resumen_carreteras_estatales.to_csv(path.join(inputs, 'resultados_carreteras_estatales.csv'))

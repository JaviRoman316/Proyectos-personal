# -*- coding: utf-8 -*-
"""
Created on Tue Jul  4 11:13:01 2023

@author: Javier Roman
"""

###############
####LIBRERIAS
###############
# import requests
# import json
import numpy as np
import pandas as pd
import os
import googlemaps

##########
#INPUTS
##########
path_carpeta = r'ubicacion archivos'
path_inputs = os.path.join(path_carpeta, 'Inputs')
path_outputs = os.path.join(path_carpeta, 'Outputs')

encoding = 'latin-1'
df_ubicaciones = pd.read_csv(os.path.join(path_inputs, 'ubicaciones.csv'), encoding=encoding)

df_ubicaciones['ubicaciones'] = df_ubicaciones['latitud'].astype(str) + ',' + df_ubicaciones['longitud'].astype(str)

ubicaciones = {}
ubicaciones = dict(zip(df_ubicaciones['id_punto'], df_ubicaciones['ubicaciones']))

nombres_ubicaciones = list(ubicaciones.keys())
longitudes_latitudes = list(ubicaciones.values())

batch_size = 25
location_batches = [longitudes_latitudes[i:i + batch_size] for i in range(0, len(longitudes_latitudes), batch_size)]

api_key = 'API_KEY'

##########
#MODELO
##########

distance_matrix = []
time_matrix = []
time_traffic_matrix = []

for origen in longitudes_latitudes:
    gmaps = googlemaps.Client(key = api_key)
    renglon_distancias = []
    renglon_tiempos = []
    renglon_tiempos_trafico = []
    for batch in range(len(location_batches)):
        destinos = location_batches[batch]
        result = gmaps.distance_matrix(origins = origen, destinations = destinos, departure_time = 1689001200, traffic_model='pessimistic', mode = 'driving')
        resultados = result['rows'][0]["elements"]
        for i in range(len(resultados)):
            valor = resultados[i]['distance']['value']
            renglon_distancias.append(valor)
            valor = resultados[i]['duration']['value']
            renglon_tiempos.append(valor)
            valor = resultados[i]['duration_in_traffic']['value']
            renglon_tiempos_trafico.append(valor)
    distance_matrix.append(renglon_distancias)
    time_matrix.append(renglon_tiempos)
    time_traffic_matrix.append(renglon_tiempos_trafico)

matriz_distancias = np.array(distance_matrix)

matriz_tiempos = np.array(time_matrix)
matriz_tiempos = matriz_tiempos / 60

matriz_tiempos_trafico = np.array(time_traffic_matrix)
matriz_tiempos_trafico = matriz_tiempos_trafico / 60

df_final_distancias = pd.DataFrame(matriz_distancias,columns=nombres_ubicaciones)
df_final_distancias.index = nombres_ubicaciones

df_final_tiempos = pd.DataFrame(matriz_tiempos,columns=nombres_ubicaciones)
df_final_tiempos.index = nombres_ubicaciones

df_final_tiempos_trafico = pd.DataFrame(matriz_tiempos_trafico,columns=nombres_ubicaciones)
df_final_tiempos_trafico.index = nombres_ubicaciones

##########
# OUTPUT
##########
file_name = 'matriz_tiempos_trafico.csv'
df_final_tiempos_trafico.to_csv(os.path.join(path_outputs,file_name),encoding='utf-8-sig')

file_name = 'matriz_tiempos_normal.csv'
df_final_tiempos.to_csv(os.path.join(path_outputs,file_name),encoding='utf-8-sig')

file_name = 'matriz_distancias.csv'
df_final_distancias.to_csv(os.path.join(path_outputs,file_name),encoding='utf-8-sig')

##########
# OLD WAY. SIRVE PERFECTO PARA MATRICES INFERIORES A 100 UBICACIONES
##########
# 
# def send_request(origin_addresses, dest_addresses, API_key):
#   """ Build and send request for the given origin and destination addresses."""
#   def build_address_str(addresses):
#     # Build a pipe-separated string of addresses
#     address_str = ''
#     for i in range(len(addresses) - 1):
#       address_str += addresses[i] + '|'
#     address_str += addresses[-1]
#     return address_str

#   url = 'https://maps.googleapis.com/maps/api/distancematrix/json?departure_time=1688580000&traffic_model=pessimistic' # departure time es en unix time y modelo de trafico es que tan cargado puede estar este
#   origin_address_str = build_address_str(origin_addresses)
#   dest_address_str = build_address_str(dest_addresses)
#   request_info = url + '&origins=' + origin_address_str + '&destinations=' + \
#                        dest_address_str + '&key=' + API_key
#   payload={}
#   headers = {}
#   response = requests.request("GET", request_info, headers=headers, data=payload)
#   db = json.loads(response.content)
#   return db

# def build_distance_matrix(response):
#   distance_matrix = []
#   for row in response['rows']:
#     row_list = [row['elements'][j]['duration_in_traffic']['value'] for j in range(len(row['elements']))]
#     distance_matrix.append(row_list)
#   return distance_matrix

# def create_distance_matrix(data):
#   addresses = data["addresses"]
#   API_key = data["API_key"]
#   # Distance Matrix API only accepts 100 elements per request, so get rows in multiple requests.
#   max_elements = 100
#   num_addresses = len(addresses)
#   # Maximum number of rows that can be computed per request.
#   max_rows = max_elements // num_addresses
#   # num_addresses = q * max_rows + r.
#   q, r = divmod(num_addresses, max_rows)
#   dest_addresses = addresses
#   distance_matrix = []
#   # Send q requests, returning max_rows rows per request.
#   for i in range(q):
#     origin_addresses = addresses[i * max_rows: (i + 1) * max_rows]
#     response = send_request(origin_addresses, dest_addresses, API_key)
#     distance_matrix += build_distance_matrix(response)

#   # Get the remaining remaining r rows, if necessary.
#   if r > 0:
#     origin_addresses = addresses[q * max_rows: q * max_rows + r]
#     response = send_request(origin_addresses, dest_addresses, API_key)
#     distance_matrix += build_distance_matrix(response)
#   return distance_matrix

# def create_data():
#   """Creates the data."""
#   data = {}
#   data['API_key'] = 'API_KEY'
#   data['addresses'] = []
#   return data

# ########
# # Main 
# ########
# def main():
#   """Entry point of the program"""
#   # Create the data.
#   data = create_data()
#   addresses = data['addresses']
#   API_key = data['API_key']
#   distance_matrix = create_distance_matrix(data)
#   print(distance_matrix)
#   return distance_matrix

# if __name__ == '__main__':
#   resultado = main()




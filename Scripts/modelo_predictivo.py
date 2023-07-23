# -*- coding: utf-8 -*-
"""
Created on Thu Feb 16 20:02:32 2023

_Descripcion: Genera modelo predictivo de machine learning para el consumo de algunas claves.

@author: Javier Roman
"""

##########
#LIBRERIAS
##########
import boto3 # Conexion con athena
import pandas as pd # Manipulacion de bases de datos
from os import path # Manejo de rutas
from sklearn.ensemble import RandomForestRegressor # Modelos de Random Forest
from skforecast.ForecasterAutoreg import ForecasterAutoreg # Modelos autoregresivos de ML
import numpy as np # Calculos
from scipy import stats # Estadistica
import time
#from IPython import get_ipython # Para remover todas las variables del kernel

#get_ipython().magic('reset -sf')

##########
#DIRECTORIO DONDE GUARDAREMOS LOS RESULTADOS FINALES DEL ANALISIS
##########
outputs = "ubicacion outputs"

##########
#VARIABLES
##########
aws_access_key = 'ACCESS KEY'
aws_secret_key = 'SECRET KEY'
aws_region = 'REGION'
s3_staging_dir = 'S3 DIR'
database = 'DATABASE'

##########
#CONECTAR A AWS ATHENA
##########
athena_client = boto3.client(
    "athena",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=aws_region,
)

##########
#FUNCION PARA GENERAR LA TABLA
##########
def run_query(sql_query,database):
    query_response = athena_client.start_query_execution(
        QueryString=sql_query,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={
            "OutputLocation": s3_staging_dir,
            "EncryptionConfiguration": {"EncryptionOption": "SSE_S3"},
        }
    )
    return query_response["QueryExecutionId"]

##########
#GENERACIÓN DE LA TABLA Y GUARDARLA EN S3
##########
sql_query="""
QUERY PARA OBTENER INFORMACION A NIVEL CLAVE-UNIDAD MEDICA
"""

execution_id = run_query(sql_query,database)

##########
#OBTENER LA TABLA DE S3 Y CARGARLA EN PYTHON
##########
file = 'UBIC' + execution_id + '.csv'

s3_client = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=aws_region
)

temp_file_location: str = "athena_query_results.csv"

time.sleep(60)

resultados = s3_client.download_file(
        'sql-queries',
        file,
        temp_file_location
    )

data = pd.read_csv(temp_file_location)

########
# ANALISIS
########

# Comenzamos el analisis cambiando la columna semana a date type
base = data
base['semana'] = pd.to_datetime(base['semana'])

# Obtenemos las distintas claves oracle y unidades medicas que se analizaran
claves = base['clave_oracle'].unique().tolist()
unidades = base['unidad_medica'].unique().tolist()
# Generamos la tabla donde se guardaran los resultados
tabla_final = pd.DataFrame()

# Realizamos un modelo para cada clave-unidad medica
for i in range(len(claves)-1):
    for j in range(len(unidades)-1):
        # Obtenemos la clave y unidad medica que vamos a analizar
        clave = claves[i]
        unidad = unidades[j]
        # Filtramos la base
        base_final = base.query('clave_oracle == @clave')
        base_final = base_final.query('unidad_medica == @unidad')
        base_final = base_final.sort_values(by=['semana'], ascending=True)
        # Vemos si hay suficiente informacion para llevar a cabo el analisis
        if base_final.empty | len(base_final['clave_oracle']) < 24:
            print('DataFrame is empty!')
        else:
            # Removemos la columna de descripcion que no usaremos en primera instancia
            descripcion = base_final['descripcion'].iloc[0]
            base_final = base_final.drop(['descripcion'],axis=1)
            # Removeremos los outliers
            base_final = base_final[(np.abs(stats.zscore(base_final['cantidad_indicada_semanal'])) < 3)]
            # Fijamos a la semana como index y establecemos su frecuencia (semana que empeiza en lunes)
            base_final = base_final.set_index('semana')
            base_final = base_final.asfreq('W-Mon')
            # Rellenamos los valores para las semanas que no tenemos
            median_value=base_final['cantidad_indicada_semanal'].median()
            base_final['cantidad_indicada_semanal'].fillna(value=median_value, inplace=True)
            base_final['clave_oracle'].fillna(value=clave, inplace=True)
            base_final['unidad_medica'].fillna(value=unidad, inplace=True)
            base_final['descripcion']=descripcion
            # Corremos el modelo de random forest con 12 observaciones de test y el resto de training
            steps = 12
            data_train = base_final[:-steps]
            data_test  = base_final[-steps:]
            # Establecemos que la variable se explica hasta con 6 lags (este parametro se puede tunear para modelos mas robustos)
            forecaster = ForecasterAutoreg(
                            regressor = RandomForestRegressor(random_state=123),
                            lags      = 6
                         )
            # Corremos el modelo y generamos las predicciones
            forecaster.fit(y=data_train['cantidad_indicada_semanal'])
            predictions = forecaster.predict(steps=steps)
            # Vamos guardando los resultados
            tabla_semifinal = base_final.merge(predictions, how='left',left_index=True, right_index=True)
            tabla_semifinal = tabla_semifinal.reset_index()
            tabla_final = tabla_final.append(tabla_semifinal,ignore_index = True)

# Removemos las comas de los resultados para evitar errores al cargar la tabla en Athena
x2 = tabla_final.select_dtypes(include=['object'])
nombres = list(x2.columns)
for i in range(0,len(x2.axes[1])-1):
    tabla_final[nombres[i]] = tabla_final[nombres[i]].str.replace(',',' ')

########
# GUARDAMOS LOS RESULTADOS
########

# Guardamos los resultados de forma local

tabla_final.to_csv(path.join(outputs, 'resultados_modelo_predictivo.csv'),sep=',',index=False)

# Guardamos los resultados en el s3
s3 = boto3.resource('s3',aws_access_key_id=aws_access_key,aws_secret_access_key=aws_secret_key)
s3.Bucket('bucket name').upload_file(path.join(outputs, 'resultados_modelo_predictivo.csv'), 'ubicacion_en_s3/resultados_modelo.csv', )



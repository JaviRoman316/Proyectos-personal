# -*- coding: utf-8 -*-
"""
Created on Thursday Jun 29 12:15:46 2023

@author: Javier Roman
"""

# Librerías
import os

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

import pandas as pd
import numpy as np

# Paths
path_carpeta = r'ubicacion archivos'
path_inputs = os.path.join(path_carpeta, 'Inputs')
path_outputs = os.path.join(path_carpeta, 'Outputs')

# Carga de las bases de datos
encoding = 'latin-1'

matriz_distancias = pd.read_csv(os.path.join(path_inputs, 'matriz_distancias.csv'), encoding=encoding,index_col=0)
matriz_tiempos = pd.read_csv(os.path.join(path_inputs, 'matriz_tiempos_normal.csv'), encoding=encoding, index_col=0)
matriz_tiempos_trafico = pd.read_csv(os.path.join(path_inputs, 'matriz_tiempos_trafico.csv'), encoding=encoding, index_col=0)

# Creacion de los inputs del modelo
distancias = matriz_distancias.to_numpy()
tiempos_normal = matriz_tiempos.to_numpy()
tiempos = matriz_tiempos_trafico.to_numpy()
tiempos = tiempos/60

# Tenemos que transformar los minutos en enteros para que jale el modelo, ya que la optimizacion la hace sobre numeros enteros
tiempos = np.ceil(tiempos)
tiempos = tiempos.astype(int)

# Le agregamos el service time que es fijo
tiempos_final = tiempos + 30

# Creacion de las ventanas de tiempo, es decir, de que momento a que momento se puede recibir mercancia en cada punto
# En este caso las ventanas de tiempo son iguales para todos los puntos
n = len(distancias) - 1  # Numero de puntos
maximo = max(tiempos_final[0])
maximo = int(maximo)
value1 = maximo  # Inicio de la ventana
value2 = maximo + 255  # Fin de la ventana

ventanas_tiempo = [(0,3000)]
resultado = [(value1, value2) for i in range(n)]
ventanas_tiempo = ventanas_tiempo + resultado

# Funcion que nos ayudara a introducir los inputs al modelo
def create_data_model():
    """Creates the data model."""
    data = {}
    # Matriz de tiempo entre las ubicaciones en minutos
    data['time_matrix'] = tiempos_final.tolist()
    # Agregamos las ventanas de tiempo para cada ubicacion 
    data['time_windows'] = ventanas_tiempo
    # La capacidad del vehiculo
    data['vehicle_capacity'] = 10000
    # Numero de vehiculos
    data['num_vehicles'] = 42
    # Ubicacion del CEDIS
    data['depot'] = 0
    return data

# Funcion que nos imprimira las rutas finales
def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    print(f'Objective: {solution.ObjectiveValue()}')
    time_dimension = routing.GetDimensionOrDie('Time')
    total_time = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)
            plan_output += '{0} Time({1},{2}) -> '.format(
                manager.IndexToNode(index), solution.Min(time_var),
                solution.Max(time_var))
            index = solution.Value(routing.NextVar(index))
        time_var = time_dimension.CumulVar(index)
        plan_output += '{0} Time({1},{2})\n'.format(manager.IndexToNode(index),
                                                    solution.Min(time_var),
                                                    solution.Max(time_var))
        plan_output += 'Time of the route: {}min\n'.format(
            solution.Min(time_var))
        print(plan_output)
        total_time += solution.Min(time_var)
    print('Total time of all routes: {}min'.format(total_time))

# Funcion que nos permitira obtener las rutas
def get_routes(solution, routing, manager):
  """Get vehicle routes from a solution and store them in an array."""
  # Get vehicle routes and store them in a two dimensional array whose
  # i,j entry is the jth location visited by vehicle i along its route.
  routes = []
  for route_nbr in range(routing.vehicles()):
    index = routing.Start(route_nbr)
    route = [manager.IndexToNode(index)]
    while not routing.IsEnd(index):
      index = solution.Value(routing.NextVar(index))
      route.append(manager.IndexToNode(index))
    routes.append(route)
  return routes

# Funciones que resuelve el modelo
def main():
    """Resuelve el VRP con ventanas de tiempo"""
    # Instanciamos los datos del problema
    data = create_data_model()

    # Generamos el routing index manager
    manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']),
                                            data['num_vehicles'], data['depot'])

    # Generamos el Routing Model
    routing = pywrapcp.RoutingModel(manager)

    # Registramos el time callback
    # Simplemente es una funciona que te regresa los tiempos entre 2 puntos, entonces es una llamada a la matriz de tiempos que introducimos como input
    def time_callback(from_index, to_index):
        """Returns the travel time between the two nodes."""
        # Convert from routing variable Index to time matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['time_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Aqui definimso el costo de cada edge o arc como le llaman
    # En este caso el costo simplemente es la distancia de tiempo, pero esto se podria modificar para complicar el problema
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Agregamos las restricciones de ventanas de tiempo
    time = 'Time'
    routing.AddDimension(
        transit_callback_index,
        500,  # Allow waiting time
        3000,  # Maximum time per vehicle
        False,  # Don't force start cumul to zero.
        time)
    time_dimension = routing.GetDimensionOrDie(time)
   
    # Agregamos las restricciones de ventanas de tiempo para cada ubicacion excepto el cedis 
    for location_idx, time_window in enumerate(data['time_windows']):
        if location_idx == data['depot']:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
    
    # Agregamos las restricciones de ventanas de tiempo por cada inicio de ruta
    depot_idx = data['depot']
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        time_dimension.CumulVar(index).SetRange(
            data['time_windows'][depot_idx][0],
            data['time_windows'][depot_idx][1])

    # Instanciamos los tiempos de inicio y fin para producir tiempos factibles
    for i in range(data['num_vehicles']):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(i)))
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.End(i)))

    # Configurando la solucion inicial
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = ( 
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    # search_parameters.solution_limit = 100
    # search_parameters.time_limit.seconds = 10000

    # Resolvemos el problema
    solution = routing.SolveWithParameters(search_parameters)

    # Imprimimos la solucion en la consola 
    if solution:
        print_solution(data, manager, routing, solution)
        routes = get_routes(solution, routing, manager)
        # Desplegamos las rutas
        for i, route in enumerate(routes):
          print('Route', i, route)
    return routes

if __name__ == '__main__':
    rutas_final = main()

auxiliar = matriz_tiempos_trafico.columns.tolist()
auxiliar[0] = 'PE000'
auxiliar_2 = range(0,199)
rutas_nombres = dict(zip(auxiliar_2,auxiliar)) 

rutas_finales = rutas_final

for i in range(0,199):    
    rutas_finales = [[rutas_nombres[i] if x == i else x for x in sublist] for sublist in rutas_finales]

df_rutas_finales = pd.DataFrame(rutas_finales)

######
# GUARDAMOS LOS RESULTADOS
######
file_name = 'rutas_optimas.csv'
df_rutas_finales.to_csv(os.path.join(path_outputs,file_name),encoding='utf-8-sig')


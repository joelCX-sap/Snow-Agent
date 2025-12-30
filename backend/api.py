#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime

def obtener_clima(ciudad, fecha):
    """
    Obtiene el clima actual de una estación meteorológica de Weather Underground.
    
    Args:
        ciudad (str): ID de la estación (ej: 'IROGRA6' para Río Grande)
        fecha (str): Fecha en formato YYYY-MM-DD (no utilizada en esta API, pero mantenida para compatibilidad)
    
    Returns:
        dict: Respuesta JSON de la API o None si hay error
    """
    
    # Mapeo de ciudades a IDs de estaciones de Weather Underground
    # Puedes expandir este diccionario con más estaciones
    estaciones = {
        'rio grande': 'IROGRA6',
        'riogrande': 'IROGRA6',
        'ushuaia': 'IUSHUA2',  # Ejemplo, ajustar según estaciones disponibles
        'bariloche': 'IBARIL1',  # Ejemplo, ajustar según estaciones disponibles
    }
    
    # Convertir ciudad a minúsculas para búsqueda
    ciudad_lower = ciudad.lower().strip()
    
    # Obtener el ID de estación
    station_id = estaciones.get(ciudad_lower, ciudad)
    
    # URL de la API de Weather Underground
    # Nota: Esta es una API de ejemplo. Necesitarás obtener una API key real de Weather Underground
    base_url = "https://api.weather.com/v2/pws/observations/current"
    api_key = "857331eb9cea4e60b331eb9cea9e60d7"  # Reemplazar con tu API key real
    
    # Parámetros de la petición
    params = {
        'stationId': station_id,
        'format': 'json',
        'units': 'm',  # m para métrico, e para imperial
        'apiKey': api_key
    }
    
    try:
        # Realizar la petición HTTP
        print(f"Consultando clima para estación: {station_id}")
        print(f"URL: {base_url}")
        print("-" * 60)
        
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Lanza excepción si hay error HTTP
        
        # Parsear la respuesta
        datos = response.json()
        
        # Formatear la respuesta para que sea similar al formato original
        if 'observations' in datos and len(datos['observations']) > 0:
            obs = datos['observations'][0]
            
            # Crear estructura similar a la API anterior para mantener compatibilidad
            clima_formateado = {
                'location': {
                    'name': obs.get('neighborhood', 'Desconocido'),
                    'country': obs.get('country', 'AR'),
                    'lat': obs.get('lat', 0),
                    'lon': obs.get('lon', 0)
                },
                'current': {
                    'last_updated': obs.get('obsTimeLocal', ''),
                    'temp_c': obs.get('metric', {}).get('temp', 0),
                    'condition': {
                        'text': 'Datos de estación meteorológica',
                        'icon': ''
                    },
                    'wind_kph': obs.get('metric', {}).get('windSpeed', 0),
                    'wind_degree': obs.get('winddir', 0),
                    'pressure_mb': obs.get('metric', {}).get('pressure', 0),
                    'precip_mm': obs.get('metric', {}).get('precipTotal', 0),
                    'humidity': obs.get('humidity', 0),
                    'feelslike_c': obs.get('metric', {}).get('heatIndex', 0),
                    'uv': obs.get('uv', 0),
                    'gust_kph': obs.get('metric', {}).get('windGust', 0),
                    'dewpoint_c': obs.get('metric', {}).get('dewpt', 0),
                    'solar_radiation': obs.get('solarRadiation', 0)
                },
                'raw_data': obs  # Incluir datos originales por si se necesitan
            }
            
            return clima_formateado
        else:
            print("No se encontraron observaciones en la respuesta")
            return datos
        
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la petición: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None

def obtener_clima_simulado(ciudad, fecha):
    """
    Función de ejemplo que simula una respuesta de la API usando datos de ejemplo.
    Útil para pruebas sin necesidad de API key.
    
    Args:
        ciudad (str): Nombre de la ciudad
        fecha (str): Fecha en formato YYYY-MM-DD
    
    Returns:
        dict: Respuesta simulada con formato compatible
    """
    
    # Datos de ejemplo basados en tu muestra
    datos_ejemplo = {
        'location': {
            'name': 'Río Grande',
            'country': 'AR',
            'lat': -53.78096,
            'lon': -67.753105
        },
        'current': {
            'last_updated': '2025-11-25 16:53:33',
            'temp_c': 13,
            'condition': {
                'text': 'Datos de estación meteorológica',
                'icon': ''
            },
            'wind_kph': 18,
            'wind_degree': 359,
            'pressure_mb': 1008.33,
            'precip_mm': 0.0,
            'humidity': 50,
            'feelslike_c': 13,
            'uv': 2.0,
            'gust_kph': 20,
            'dewpoint_c': 3,
            'solar_radiation': 228.3
        }
    }
    
    print(f"Retornando datos simulados para {ciudad}")
    return datos_ejemplo

def validar_fecha(fecha_str):
    """
    Valida que la fecha tenga el formato correcto YYYY-MM-DD.
    
    Args:
        fecha_str (str): Fecha a validar
    
    Returns:
        bool: True si la fecha es válida, False en caso contrario
    """
    try:
        datetime.strptime(fecha_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def main():
    """
    Función principal que solicita la ciudad y fecha al usuario y muestra el clima.
    """
    print("=== CONSULTA DE CLIMA - Weather Underground ===")
    print()
    print("Ciudades disponibles: Rio Grande, Ushuaia, Bariloche")
    print("O ingresa el ID de estación directamente (ej: IROGRA6)")
    print()
    
    # Solicitar ciudad
    ciudad = input("Ingrese el nombre de la ciudad o ID de estación: ").strip()
    while not ciudad:
        print("Por favor, ingrese un nombre de ciudad válido.")
        ciudad = input("Ingrese el nombre de la ciudad o ID de estación: ").strip()
    
    # Solicitar fecha
    while True:
        fecha = input("Ingrese la fecha (formato YYYY-MM-DD): ").strip()
        
        if validar_fecha(fecha):
            break
        else:
            print("Formato de fecha incorrecto. Use el formato YYYY-MM-DD (ejemplo: 2025-11-05)")
            print()
    
    # Preguntar si usar datos simulados o API real
    usar_simulado = input("\n¿Usar datos simulados? (s/n): ").strip().lower()
    
    if usar_simulado == 's':
        # Usar datos simulados
        datos_clima = obtener_clima_simulado(ciudad, fecha)
    else:
        # Obtener clima de la API real
        datos_clima = obtener_clima(ciudad, fecha)
    
    if datos_clima:
        print("\nRESPUESTA JSON:")
        print("=" * 60)
        print(json.dumps(datos_clima, indent=2, ensure_ascii=False))
        
        # Mostrar resumen del clima
        if 'current' in datos_clima:
            print("\n" + "=" * 60)
            print("RESUMEN DEL CLIMA:")
            print("=" * 60)
            current = datos_clima['current']
            print(f"Temperatura: {current.get('temp_c', 'N/A')}°C")
            print(f"Sensación térmica: {current.get('feelslike_c', 'N/A')}°C")
            print(f"Humedad: {current.get('humidity', 'N/A')}%")
            print(f"Viento: {current.get('wind_kph', 'N/A')} km/h")
            print(f"Ráfagas: {current.get('gust_kph', 'N/A')} km/h")
            print(f"Presión: {current.get('pressure_mb', 'N/A')} mb")
            print(f"Precipitación: {current.get('precip_mm', 'N/A')} mm")
            print(f"UV: {current.get('uv', 'N/A')}")
            print(f"Radiación solar: {current.get('solar_radiation', 'N/A')} W/m²")
    else:
        print("No se pudo obtener información del clima.")

if __name__ == "__main__":
    main()

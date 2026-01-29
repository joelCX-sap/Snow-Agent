#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de clima usando Open-Meteo API
Reemplaza la API de Weather Underground por Open-Meteo (gratuita y sin API key)
"""

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
import pytz

logger = logging.getLogger(__name__)

# Configuración de coordenadas para cada ubicación
UBICACIONES = {
    "rio grande": {
        "nombre": "Río Grande",
        "latitude": -53.7877,
        "longitude": -67.7097,
        "timezone": "America/Argentina/Ushuaia",
        "country": "AR"
    },
    "riogrande": {
        "nombre": "Río Grande",
        "latitude": -53.7877,
        "longitude": -67.7097,
        "timezone": "America/Argentina/Ushuaia",
        "country": "AR"
    },
    "amsterdam": {
        "nombre": "Amsterdam Schiphol",
        "latitude": 52.374,
        "longitude": 4.8897,
        "timezone": "Europe/Amsterdam",
        "country": "NL"
    },
    "bariloche": {
        "nombre": "San Carlos de Bariloche",
        "latitude": -41.1335,
        "longitude": -71.3103,
        "timezone": "America/Argentina/Salta",
        "country": "AR"
    },
    "nyc": {
        "nombre": "New York City (JFK)",
        "latitude": 40.6413,
        "longitude": -73.7781,
        "timezone": "America/New_York",
        "country": "US"
    },
    "new york": {
        "nombre": "New York City (JFK)",
        "latitude": 40.6413,
        "longitude": -73.7781,
        "timezone": "America/New_York",
        "country": "US"
    },
    "newyork": {
        "nombre": "New York City (JFK)",
        "latitude": 40.6413,
        "longitude": -73.7781,
        "timezone": "America/New_York",
        "country": "US"
    }
}

class OpenMeteoService:
    """Servicio para obtener datos meteorológicos de Open-Meteo"""
    
    def __init__(self):
        # Setup del cliente Open-Meteo con cache y retry
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=retry_session)
        self.url = "https://api.open-meteo.com/v1/forecast"
    
    def obtener_clima(self, ciudad: str, fecha: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el clima de una ubicación usando Open-Meteo.
        
        Args:
            ciudad: Nombre de la ciudad (rio grande, amsterdam, bariloche)
            fecha: Fecha en formato YYYY-MM-DD (usada para contexto, el forecast es actual)
        
        Returns:
            Dict con datos del clima formateados o None si hay error
        """
        try:
            # Obtener configuración de la ubicación
            ciudad_lower = ciudad.lower().strip()
            ubicacion = UBICACIONES.get(ciudad_lower)
            
            if not ubicacion:
                logger.warning(f"Ciudad no encontrada: {ciudad}. Usando Río Grande por defecto.")
                ubicacion = UBICACIONES["rio grande"]
            
            # Parámetros para la API
            params = {
                "latitude": ubicacion["latitude"],
                "longitude": ubicacion["longitude"],
                "hourly": [
                    "temperature_2m", 
                    "relative_humidity_2m", 
                    "precipitation", 
                    "rain", 
                    "snowfall", 
                    "cloud_cover", 
                    "cloud_cover_low", 
                    "cloud_cover_mid", 
                    "visibility", 
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "snow_depth"
                ],
                "current": [
                    "temperature_2m", 
                    "precipitation", 
                    "rain", 
                    "relative_humidity_2m", 
                    "cloud_cover", 
                    "wind_speed_10m", 
                    "wind_direction_10m", 
                    "showers", 
                    "snowfall"
                ],
                "timezone": ubicacion["timezone"],
                "forecast_days": 2,  # 2 días para tener margen
            }
            
            logger.info(f"Consultando Open-Meteo para {ubicacion['nombre']} ({ubicacion['latitude']}, {ubicacion['longitude']})")
            
            # Realizar la consulta
            responses = self.client.weather_api(self.url, params=params)
            response = responses[0]
            
            # Procesar datos actuales
            current = response.Current()
            current_data = {
                "temperature_2m": current.Variables(0).Value(),
                "precipitation": current.Variables(1).Value(),
                "rain": current.Variables(2).Value(),
                "relative_humidity_2m": current.Variables(3).Value(),
                "cloud_cover": current.Variables(4).Value(),
                "wind_speed_10m": current.Variables(5).Value(),
                "wind_direction_10m": current.Variables(6).Value(),
                "showers": current.Variables(7).Value(),
                "snowfall": current.Variables(8).Value(),
                "time": current.Time()
            }
            
            # Procesar datos horarios
            hourly = response.Hourly()
            hourly_data = self._procesar_datos_horarios(hourly, response.UtcOffsetSeconds(), ubicacion["timezone"])
            
            # Obtener forecast para las próximas horas (hora actual + 3 horas)
            forecast_horas = self._obtener_forecast_proximas_horas(hourly_data, 4, ubicacion["timezone"])  # hora actual + 3 = 4 horas
            
            # Formatear respuesta compatible con el sistema existente
            clima_formateado = self._formatear_respuesta(
                ubicacion=ubicacion,
                current_data=current_data,
                hourly_data=hourly_data,
                forecast_horas=forecast_horas,
                response=response
            )
            
            return clima_formateado
            
        except Exception as e:
            logger.error(f"Error obteniendo clima de Open-Meteo: {e}")
            return None
    
    def _procesar_datos_horarios(self, hourly, utc_offset: int, timezone_str: str) -> pd.DataFrame:
        """Procesa los datos horarios del response de Open-Meteo"""
        
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
        hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
        hourly_rain = hourly.Variables(3).ValuesAsNumpy()
        hourly_snowfall = hourly.Variables(4).ValuesAsNumpy()
        hourly_cloud_cover = hourly.Variables(5).ValuesAsNumpy()
        hourly_cloud_cover_low = hourly.Variables(6).ValuesAsNumpy()
        hourly_cloud_cover_mid = hourly.Variables(7).ValuesAsNumpy()
        hourly_visibility = hourly.Variables(8).ValuesAsNumpy()
        hourly_wind_speed_10m = hourly.Variables(9).ValuesAsNumpy()
        hourly_wind_direction_10m = hourly.Variables(10).ValuesAsNumpy()
        hourly_snow_depth = hourly.Variables(11).ValuesAsNumpy()
        
        # Crear el date_range en UTC (sin sumar el offset, ya que los timestamps vienen en UTC)
        # Luego convertir a la zona horaria local
        dates_utc = pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        )
        
        # Convertir a la zona horaria local
        try:
            tz = pytz.timezone(timezone_str)
            dates_local = dates_utc.tz_convert(tz)
        except Exception as e:
            logger.warning(f"Error convirtiendo timezone {timezone_str}: {e}. Usando UTC.")
            dates_local = dates_utc
        
        hourly_data = {
            "date": dates_local,
            "temperature_2m": hourly_temperature_2m,
            "relative_humidity_2m": hourly_relative_humidity_2m,
            "precipitation": hourly_precipitation,
            "rain": hourly_rain,
            "snowfall": hourly_snowfall,
            "cloud_cover": hourly_cloud_cover,
            "cloud_cover_low": hourly_cloud_cover_low,
            "cloud_cover_mid": hourly_cloud_cover_mid,
            "visibility": hourly_visibility,
            "wind_speed_10m": hourly_wind_speed_10m,
            "wind_direction_10m": hourly_wind_direction_10m,
            "snow_depth": hourly_snow_depth
        }
        
        return pd.DataFrame(data=hourly_data)
    
    def _obtener_forecast_proximas_horas(self, hourly_df: pd.DataFrame, num_horas: int = 4, timezone_str: str = "UTC") -> List[Dict[str, Any]]:
        """
        Obtiene el forecast para las próximas N horas.
        Por ejemplo: si son las 18:30, retorna forecast de 18:00, 19:00, 20:00, 21:00
        
        Args:
            hourly_df: DataFrame con datos horarios (ya en timezone local)
            num_horas: Número de horas a incluir (hora actual + 3 = 4)
            timezone_str: Zona horaria de la ubicación
        
        Returns:
            Lista de diccionarios con el forecast por hora
        """
        # Obtener la hora actual en la zona horaria de la ubicación
        try:
            tz = pytz.timezone(timezone_str)
            now_local = datetime.now(tz)
        except Exception as e:
            logger.warning(f"Error con timezone {timezone_str}: {e}. Usando hora local del sistema.")
            now_local = datetime.now()
        
        # Redondear a la hora actual (sin minutos)
        current_hour = now_local.replace(minute=0, second=0, microsecond=0)
        
        logger.info(f"Hora actual en {timezone_str}: {now_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"Buscando forecast desde: {current_hour.strftime('%Y-%m-%d %H:%M')}")
        
        forecast_horas = []
        
        for i in range(num_horas):
            target_hour = current_hour + timedelta(hours=i)
            
            # Buscar en el DataFrame la hora correspondiente
            # El DataFrame ya tiene las fechas convertidas a la zona horaria local
            for idx, row in hourly_df.iterrows():
                row_date = row['date']
                
                # Convertir ambas fechas a timestamps para comparación más precisa
                # Esto evita problemas con la comparación de timezones
                row_ts = pd.Timestamp(row_date)
                target_ts = pd.Timestamp(target_hour)
                
                # Comparar año, mes, día y hora
                if (row_ts.year == target_ts.year and 
                    row_ts.month == target_ts.month and 
                    row_ts.day == target_ts.day and 
                    row_ts.hour == target_ts.hour):
                    
                    forecast_horas.append({
                        "hora": target_hour.strftime("%H:%M"),
                        "fecha": target_hour.strftime("%Y-%m-%d"),
                        "temperature_2m": round(float(row['temperature_2m']), 1),
                        "relative_humidity_2m": int(row['relative_humidity_2m']),
                        "precipitation": round(float(row['precipitation']), 2),
                        "rain": round(float(row['rain']), 2),
                        "snowfall": round(float(row['snowfall']), 2),
                        "cloud_cover": int(row['cloud_cover']),
                        "visibility": round(float(row['visibility']), 0),
                        "wind_speed_10m": round(float(row['wind_speed_10m']), 1),
                        "wind_direction_10m": int(row['wind_direction_10m']),
                        "snow_depth": round(float(row['snow_depth']), 2) if pd.notna(row['snow_depth']) else 0
                    })
                    logger.debug(f"Encontrado forecast para {target_hour.strftime('%H:%M')}: {row['temperature_2m']:.1f}°C")
                    break
        
        logger.info(f"Forecast encontrado para {len(forecast_horas)} horas")
        return forecast_horas
    
    def _formatear_respuesta(
        self, 
        ubicacion: Dict[str, Any],
        current_data: Dict[str, Any],
        hourly_data: pd.DataFrame,
        forecast_horas: List[Dict[str, Any]],
        response
    ) -> Dict[str, Any]:
        """Formatea la respuesta para ser compatible con el sistema existente"""
        
        # Calcular probabilidades basadas en los datos
        prob_lluvia = self._calcular_probabilidad_lluvia(forecast_horas)
        prob_nieve = self._calcular_probabilidad_nieve(forecast_horas)
        
        # Calcular máximos y mínimos del día
        today = datetime.now().date()
        hourly_today = hourly_data[hourly_data['date'].dt.date == today]
        
        if len(hourly_today) > 0:
            temp_max = round(float(hourly_today['temperature_2m'].max()), 1)
            temp_min = round(float(hourly_today['temperature_2m'].min()), 1)
            viento_max = round(float(hourly_today['wind_speed_10m'].max()), 1)
            precip_total = round(float(hourly_today['precipitation'].sum()), 2)
        else:
            temp_max = round(float(current_data['temperature_2m']), 1)
            temp_min = round(float(current_data['temperature_2m']), 1)
            viento_max = round(float(current_data['wind_speed_10m']), 1)
            precip_total = round(float(current_data['precipitation']), 2)
        
        # Determinar condición del clima
        condicion = self._determinar_condicion(current_data, forecast_horas)
        
        # Calcular visibilidad en km (Open-Meteo devuelve en metros)
        visibilidad_km = round(float(current_data.get('cloud_cover', 24140)) / 1000, 1) if forecast_horas else None
        if forecast_horas and len(forecast_horas) > 0:
            visibilidad_km = round(float(forecast_horas[0].get('visibility', 24140)) / 1000, 1)
        
        clima_formateado = {
            'location': {
                'name': ubicacion['nombre'],
                'country': ubicacion['country'],
                'lat': ubicacion['latitude'],
                'lon': ubicacion['longitude'],
                'localtime': datetime.now().strftime('%Y-%m-%d %H:%M')
            },
            'current': {
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'temp_c': round(float(current_data['temperature_2m']), 1),
                'condition': {
                    'text': condicion,
                    'icon': ''
                },
                'wind_kph': round(float(current_data['wind_speed_10m']), 1),
                'wind_degree': int(current_data['wind_direction_10m']),
                'pressure_mb': 1013,  # Open-Meteo no provee presión en forecast básico
                'precip_mm': round(float(current_data['precipitation']), 2),
                'humidity': int(current_data['relative_humidity_2m']),
                'feelslike_c': round(float(current_data['temperature_2m']), 1),  # Aproximación
                'uv': 0,  # Open-Meteo no provee UV en forecast básico
                'gust_kph': round(float(current_data['wind_speed_10m']) * 1.3, 1),  # Aproximación
                'dewpoint_c': 0,  # Se podría calcular
                'cloud_cover': int(current_data['cloud_cover']),
                'snowfall': round(float(current_data['snowfall']), 2),
                'vis_km': visibilidad_km
            },
            'forecast': {
                'forecastday': [{
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'day': {
                        'maxtemp_c': temp_max,
                        'mintemp_c': temp_min,
                        'daily_chance_of_rain': prob_lluvia,
                        'daily_chance_of_snow': prob_nieve,
                        'totalprecip_mm': precip_total,
                        'maxwind_kph': viento_max
                    }
                }]
            },
            'forecast_proximas_horas': forecast_horas,
            'openmeteo_metadata': {
                'coordinates': f"{response.Latitude()}°N {response.Longitude()}°E",
                'elevation': response.Elevation(),
                'timezone': str(response.Timezone()),
                'utc_offset_seconds': response.UtcOffsetSeconds()
            }
        }
        
        return clima_formateado
    
    def _calcular_probabilidad_lluvia(self, forecast_horas: List[Dict[str, Any]]) -> int:
        """Calcula probabilidad de lluvia basada en las próximas horas"""
        if not forecast_horas:
            return 0
        
        horas_con_lluvia = sum(1 for h in forecast_horas if h.get('rain', 0) > 0 or h.get('precipitation', 0) > 0.1)
        return min(int((horas_con_lluvia / len(forecast_horas)) * 100), 100)
    
    def _calcular_probabilidad_nieve(self, forecast_horas: List[Dict[str, Any]]) -> int:
        """Calcula probabilidad de nieve basada en las próximas horas"""
        if not forecast_horas:
            return 0
        
        horas_con_nieve = sum(1 for h in forecast_horas if h.get('snowfall', 0) > 0)
        # También considerar temperatura bajo cero como factor
        horas_frias = sum(1 for h in forecast_horas if h.get('temperature_2m', 10) < 2)
        
        prob_nieve = int((horas_con_nieve / len(forecast_horas)) * 100)
        if horas_frias > len(forecast_horas) / 2:
            prob_nieve = max(prob_nieve, 30)  # Mínimo 30% si hace frío
        
        return min(prob_nieve, 100)
    
    def _determinar_condicion(self, current_data: Dict[str, Any], forecast_horas: List[Dict[str, Any]]) -> str:
        """Determina la condición climática actual en texto"""
        
        temp = current_data.get('temperature_2m', 20)
        cloud_cover = current_data.get('cloud_cover', 0)
        precipitation = current_data.get('precipitation', 0)
        snowfall = current_data.get('snowfall', 0)
        rain = current_data.get('rain', 0)
        
        if snowfall > 0:
            return "Nevando"
        elif rain > 0 or precipitation > 0:
            return "Lluvia"
        elif cloud_cover >= 80:
            return "Muy nublado"
        elif cloud_cover >= 50:
            return "Parcialmente nublado"
        elif cloud_cover >= 20:
            return "Algunas nubes"
        else:
            return "Despejado"


# Función principal para compatibilidad con el código existente
def obtener_clima(ciudad: str, fecha: str) -> Optional[Dict[str, Any]]:
    """
    Función wrapper para mantener compatibilidad con api.py existente
    
    Args:
        ciudad: Nombre de la ciudad
        fecha: Fecha en formato YYYY-MM-DD
    
    Returns:
        Dict con datos del clima o None si hay error
    """
    service = OpenMeteoService()
    return service.obtener_clima(ciudad, fecha)


def validar_fecha(fecha_str: str) -> bool:
    """
    Valida que la fecha tenga el formato correcto YYYY-MM-DD.
    
    Args:
        fecha_str: Fecha a validar
    
    Returns:
        bool: True si la fecha es válida, False en caso contrario
    """
    try:
        datetime.strptime(fecha_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    # Test del módulo
    print("=== Test Open-Meteo Weather Service ===\n")
    
    service = OpenMeteoService()
    
    # Test Río Grande
    print("1. Consultando Río Grande...")
    clima_rg = service.obtener_clima("rio grande", "2026-01-26")
    if clima_rg:
        print(f"   Temperatura: {clima_rg['current']['temp_c']}°C")
        print(f"   Condición: {clima_rg['current']['condition']['text']}")
        print(f"   Viento: {clima_rg['current']['wind_kph']} km/h")
        print(f"   Humedad: {clima_rg['current']['humidity']}%")
        if clima_rg.get('forecast_proximas_horas'):
            print(f"   Forecast próximas {len(clima_rg['forecast_proximas_horas'])} horas:")
            for h in clima_rg['forecast_proximas_horas']:
                print(f"      {h['hora']}: {h['temperature_2m']}°C, {h['wind_speed_10m']} km/h")
    
    print("\n2. Consultando Amsterdam...")
    clima_ams = service.obtener_clima("amsterdam", "2026-01-26")
    if clima_ams:
        print(f"   Temperatura: {clima_ams['current']['temp_c']}°C")
        print(f"   Condición: {clima_ams['current']['condition']['text']}")
        print(f"   Viento: {clima_ams['current']['wind_kph']} km/h")
        if clima_ams.get('forecast_proximas_horas'):
            print(f"   Forecast próximas {len(clima_ams['forecast_proximas_horas'])} horas:")
            for h in clima_ams['forecast_proximas_horas']:
                print(f"      {h['hora']}: {h['temperature_2m']}°C, {h['wind_speed_10m']} km/h")
    
    print("\n=== Test completado ===")
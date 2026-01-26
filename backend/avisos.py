#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de Generación de Avisos - MVP1 SNOW
Procesa condiciones meteorológicas y genera avisos según procedimiento establecido
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definición de tipos de avisos según MVP1 SNOW con códigos SAP
AVISOS_CONFIG = {
    'AVISO_0': {
        'nombre': 'Temperatura Bajo Cero - Riesgo Crítico de Hielo',
        'clase': 'CRITICO',
        'QMART': 'O1',  # Clase de aviso
        'QMTXT': 'Temperatura Bajo Cero - Riesgo Crítico de Hielo',  # Descripción
        'TPLNR': 'RGA-INF-PAVIM',  # Ubicación técnica
        'SWERK': 'RGA',  # Centro de emplazamiento
        'INGRP': 'OPE',  # Grupo planificador
        'GEWRK': 'ADM_AD',  # Puesto de trabajo
        'PRIOK': '1',  # Prioridad MÁXIMA
        'QMGRP': 'YB-DERR1',  # Grupo modo de fallo
        'QMCOD': 'Y116',  # Modo de fallo - Nuevo código para bajo cero
        'nota': 'Aviso crítico cuando la temperatura está bajo 0°C - Alto riesgo de formación de hielo',
        'condiciones': {
            'temp_ambiente_max': 0,  # Temperatura menor a 0°C
            'viento_max': 100  # Sin límite efectivo de viento
        }
    },
    'AVISO_1': {
        'nombre': 'Umbral de Alerta',
        'clase': 'ALERTA',
        'QMART': 'O1',  # Clase de aviso
        'QMTXT': 'Umbral de Alerta',  # Descripción
        'TPLNR': 'RGA-INF-PAVIM',  # Ubicación técnica
        'SWERK': 'RGA',  # Centro de emplazamiento
        'INGRP': 'OPE',  # Grupo planificador
        'GEWRK': 'ADM_AD',  # Puesto de trabajo
        'PRIOK': '2',  # Prioridad
        'QMGRP': 'YB-DERR1',  # Grupo modo de fallo
        'QMCOD': 'Y110',  # Modo de fallo
        'condiciones': {
            'temp_ambiente_min': 3,
            'temp_ambiente_max': 6,
            'temp_rocio_diferencia': -3,
            'temp_pista_max': 0,
            'humedad_min': 56,
            'viento_max': 36
        }
    },
    'AVISO_2': {
        'nombre': 'Umbral de Contingencia',
        'clase': 'CONTINGENCIA',
        'QMART': 'O1',
        'QMTXT': 'Umbral de Contingencia',
        'TPLNR': 'RGA-INF-PAVIM',
        'SWERK': 'RGA',
        'INGRP': 'OPE',
        'GEWRK': 'ADM_AD',
        'PRIOK': '1',
        'QMGRP': 'YB-DERR1',
        'QMCOD': 'Y111',
        'nota': 'A futuro este aviso se convertirá en Incidencia',
        'condiciones': {
            'temp_ambiente_min': -50,  # Extendido para incluir bajo cero
            'temp_ambiente_max': 3,
            'temp_rocio_diferencia': -1,
            'temp_pista_max': 0,
            'humedad_min': 40,  # Reducido para ser más inclusivo
            'viento_max': 50  # Aumentado para ser más inclusivo
        }
    },
    'AVISO_3': {
        'nombre': 'Alerta de cambio de condiciones meteorológicas',
        'QMART': 'O1',
        'QMTXT': 'Alerta de cambio de condiciones meteorológicas',
        'TPLNR': 'RGA-INF-PAVIM',
        'SWERK': 'RGA',
        'INGRP': 'OPE',
        'GEWRK': 'ADM_AD',
        'PRIOK': '2',
        'QMGRP': 'YB-DERR1',
        'QMCOD': 'Y112',
        'nota': 'Genera automáticamente OT de Monitoreo de condiciones de superficies pavimentadas utilizando Marwis',
        'condiciones': {
            'temp_ambiente_max': 0,
            'temp_rocio_diferencia': -1,
            'temp_pista_max': 0,
            'humedad_min': 63,
            'viento_max': 33,
            'sin_lectura_marwis_2h': True
        }
    },
    'AVISO_4': {
        'nombre': 'Alerta de hielo',
        'QMART': 'O1',
        'QMTXT': 'Alerta de hielo',
        'TPLNR': 'RGA-INF-PAVIM',
        'SWERK': 'RGA',
        'INGRP': 'OPE',
        'GEWRK': 'ADM_AD',
        'PRIOK': '1',
        'QMGRP': 'YB-DERR1',
        'QMCOD': 'Y113',
        'condiciones': {
            'temp_ambiente_max': 0,
            'temp_rocio_diferencia': -1,
            'temp_pista_max': 0,
            'humedad_min': 63,
            'viento_max': 33,
            'surface_condition': ['WET', 'DAMP'],
            'marwis_ultimos_15min': True
        }
    },
    'AVISO_5': {
        'nombre': 'Alerta de lluvia',
        'QMART': 'O1',
        'QMTXT': 'Alerta de lluvia',
        'TPLNR': 'RGA-INF-PAVIM',
        'SWERK': 'RGA',
        'INGRP': 'OPE',
        'GEWRK': 'ADM_AD',
        'PRIOK': '2',
        'QMGRP': 'YB-DERR1',
        'QMCOD': 'Y114',
        'condiciones': {
            'temp_ambiente_max': 0,
            'temp_rocio_diferencia': -1,
            'temp_pista_max': 0,
            'humedad_min': 63,
            'viento_max': 33,
            'pronostico_lluvia_2h': True
        }
    },
    'AVISO_6': {
        'nombre': 'Alerta de nieve',
        'QMART': 'O1',
        'QMTXT': 'Alerta de nieve',
        'TPLNR': 'RGA-INF-PAVIM',
        'SWERK': 'RGA',
        'INGRP': 'OPE',
        'GEWRK': 'ADM_AD',
        'PRIOK': '1',
        'QMGRP': 'YB-DERR1',
        'QMCOD': 'Y115',
        'condiciones': {
            'temp_ambiente_max': 0,
            'temp_rocio_diferencia': -1,
            'temp_pista_max': 0,
            'humedad_min': 63,
            'viento_max': 33,
            'pronostico_nieve_3h': True
        }
    }
}

def evaluar_condiciones_aviso_0(condiciones_clima: Dict[str, Any]) -> bool:
    """
    Evaluar si se cumplen condiciones para Aviso 0 (Temperatura Bajo Cero - Crítico)
    Este aviso se genera cuando la temperatura está bajo 0°C
    """
    try:
        config = AVISOS_CONFIG['AVISO_0']['condiciones']
        
        temp_amb = condiciones_clima.get('temperatura_actual', 999)
        viento = condiciones_clima.get('viento', 0)
        
        # Si viento viene como string 'N/A', usar 0
        if isinstance(viento, str):
            viento = 0
        
        # Condición principal: temperatura bajo cero
        cumple = (
            temp_amb < config['temp_ambiente_max'] and  # temp < 0°C
            viento < config['viento_max']  # Sin límite efectivo
        )
        
        logger.info(f"Evaluando AVISO_0: temp_amb={temp_amb}, cumple={cumple}")
        return cumple
    except Exception as e:
        logger.error(f"Error evaluando Aviso 0: {e}")
        return False

def evaluar_condiciones_aviso_1(condiciones_clima: Dict[str, Any]) -> bool:
    """Evaluar si se cumplen condiciones para Aviso 1 (Umbral de Alerta)"""
    try:
        config = AVISOS_CONFIG['AVISO_1']['condiciones']
        
        temp_amb = condiciones_clima.get('temperatura_actual', 999)
        temp_rocio = condiciones_clima.get('punto_rocio', 999)
        temp_pista = condiciones_clima.get('temperatura_pista', 999)
        humedad = condiciones_clima.get('humedad', 0)
        viento = condiciones_clima.get('viento', 999)
        
        # Verificar todas las condiciones
        cumple = (
            config['temp_ambiente_min'] < temp_amb <= config['temp_ambiente_max'] and
            temp_rocio >= (temp_amb + config['temp_rocio_diferencia']) and
            temp_pista < config['temp_pista_max'] and
            humedad >= config['humedad_min'] and
            viento < config['viento_max']
        )
        
        return cumple
    except Exception as e:
        logger.error(f"Error evaluando Aviso 1: {e}")
        return False

def evaluar_condiciones_aviso_2(condiciones_clima: Dict[str, Any]) -> bool:
    """Evaluar si se cumplen condiciones para Aviso 2 (Umbral de Contingencia)"""
    try:
        config = AVISOS_CONFIG['AVISO_2']['condiciones']
        
        temp_amb = condiciones_clima.get('temperatura_actual', 999)
        temp_rocio = condiciones_clima.get('punto_rocio', 999)
        temp_pista = condiciones_clima.get('temperatura_pista', 999)
        humedad = condiciones_clima.get('humedad', 0)
        viento = condiciones_clima.get('viento', 999)
        
        cumple = (
            config['temp_ambiente_min'] <= temp_amb <= config['temp_ambiente_max'] and
            temp_rocio >= (temp_amb + config['temp_rocio_diferencia']) and
            temp_pista < config['temp_pista_max'] and
            humedad >= config['humedad_min'] and
            viento < config['viento_max']
        )
        
        return cumple
    except Exception as e:
        logger.error(f"Error evaluando Aviso 2: {e}")
        return False

def evaluar_condiciones_aviso_3(condiciones_clima: Dict[str, Any], marwis_data: Optional[Dict] = None) -> bool:
    """Evaluar si se cumplen condiciones para Aviso 3 (Alerta de cambio de condiciones)"""
    try:
        config = AVISOS_CONFIG['AVISO_3']['condiciones']
        
        temp_amb = condiciones_clima.get('temperatura_actual', 999)
        temp_rocio = condiciones_clima.get('punto_rocio', 999)
        temp_pista = condiciones_clima.get('temperatura_pista', 999)
        humedad = condiciones_clima.get('humedad', 0)
        viento = condiciones_clima.get('viento', 999)
        
        # Verificar si no hay lectura de MARWIS en las últimas 2 horas
        sin_lectura_marwis = marwis_data is None or not marwis_data.get('measurements')
        
        cumple = (
            temp_amb <= config['temp_ambiente_max'] and
            temp_rocio >= (temp_amb + config['temp_rocio_diferencia']) and
            temp_pista < config['temp_pista_max'] and
            humedad >= config['humedad_min'] and
            viento < config['viento_max'] and
            sin_lectura_marwis
        )
        
        return cumple
    except Exception as e:
        logger.error(f"Error evaluando Aviso 3: {e}")
        return False

def evaluar_condiciones_aviso_4(condiciones_clima: Dict[str, Any], marwis_data: Optional[Dict] = None) -> bool:
    """Evaluar si se cumplen condiciones para Aviso 4 (Alerta de hielo)"""
    try:
        config = AVISOS_CONFIG['AVISO_4']['condiciones']
        
        temp_amb = condiciones_clima.get('temperatura_actual', 999)
        temp_rocio = condiciones_clima.get('punto_rocio', 999)
        temp_pista = condiciones_clima.get('temperatura_pista', 999)
        humedad = condiciones_clima.get('humedad', 0)
        viento = condiciones_clima.get('viento', 999)
        
        # Verificar condiciones de superficie en MARWIS (últimos 15 min)
        surface_condition = None
        if marwis_data and marwis_data.get('measurements'):
            # Buscar el sensor de condición de superficie
            for measurement in marwis_data['measurements']:
                if 'surface' in measurement.get('SensorChannelName', '').lower():
                    surface_condition = measurement.get('Value', '').upper()
                    break
        
        superficie_humeda = surface_condition in config['surface_condition'] if surface_condition else False
        
        cumple = (
            temp_amb <= config['temp_ambiente_max'] and
            temp_rocio >= (temp_amb + config['temp_rocio_diferencia']) and
            temp_pista < config['temp_pista_max'] and
            humedad >= config['humedad_min'] and
            viento < config['viento_max'] and
            superficie_humeda
        )
        
        return cumple
    except Exception as e:
        logger.error(f"Error evaluando Aviso 4: {e}")
        return False

def evaluar_condiciones_aviso_5(condiciones_clima: Dict[str, Any]) -> bool:
    """Evaluar si se cumplen condiciones para Aviso 5 (Alerta de lluvia)"""
    try:
        config = AVISOS_CONFIG['AVISO_5']['condiciones']
        
        temp_amb = condiciones_clima.get('temperatura_actual', 999)
        temp_rocio = condiciones_clima.get('punto_rocio', 999)
        temp_pista = condiciones_clima.get('temperatura_pista', 999)
        humedad = condiciones_clima.get('humedad', 0)
        viento = condiciones_clima.get('viento', 999)
        
        # Verificar pronóstico de lluvia a 2 horas
        pronostico = condiciones_clima.get('pronostico', {})
        prob_lluvia = pronostico.get('prob_lluvia', 0)
        
        cumple = (
            temp_amb <= config['temp_ambiente_max'] and
            temp_rocio >= (temp_amb + config['temp_rocio_diferencia']) and
            temp_pista < config['temp_pista_max'] and
            humedad >= config['humedad_min'] and
            viento < config['viento_max'] and
            prob_lluvia > 50  # Considerar probable si >50%
        )
        
        return cumple
    except Exception as e:
        logger.error(f"Error evaluando Aviso 5: {e}")
        return False

def evaluar_condiciones_aviso_6(condiciones_clima: Dict[str, Any]) -> bool:
    """Evaluar si se cumplen condiciones para Aviso 6 (Alerta de nieve)"""
    try:
        config = AVISOS_CONFIG['AVISO_6']['condiciones']
        
        temp_amb = condiciones_clima.get('temperatura_actual', 999)
        temp_rocio = condiciones_clima.get('punto_rocio', 999)
        temp_pista = condiciones_clima.get('temperatura_pista', 999)
        humedad = condiciones_clima.get('humedad', 0)
        viento = condiciones_clima.get('viento', 999)
        
        # Verificar pronóstico de nieve a 3 horas
        pronostico = condiciones_clima.get('pronostico', {})
        prob_nieve = pronostico.get('prob_nieve', 0)
        
        cumple = (
            temp_amb <= config['temp_ambiente_max'] and
            temp_rocio >= (temp_amb + config['temp_rocio_diferencia']) and
            temp_pista < config['temp_pista_max'] and
            humedad >= config['humedad_min'] and
            viento < config['viento_max'] and
            prob_nieve > 30  # Considerar probable si >30%
        )
        
        return cumple
    except Exception as e:
        logger.error(f"Error evaluando Aviso 6: {e}")
        return False

def get_latest_marwis_data() -> Optional[Dict]:
    """Obtener datos más recientes de MARWIS desde station_data.json"""
    try:
        station_data_path = os.path.join(os.path.dirname(__file__), 'station_data.json')
        if not os.path.exists(station_data_path):
            logger.warning("Archivo station_data.json no encontrado")
            return None
        
        with open(station_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Compatibilidad con ambos formatos
        if isinstance(data, list):
            return {'measurements': data}
        elif isinstance(data, dict):
            return data
        
        return None
    except Exception as e:
        logger.error(f"Error leyendo station_data.json: {e}")
        return None

def generar_avisos(condiciones_clima: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evalúa las condiciones climáticas y genera los avisos correspondientes
    
    Args:
        condiciones_clima: Diccionario con condiciones climáticas analizadas
        
    Returns:
        Dict con avisos generados y datos de MARWIS
    """
    try:
        logger.info("Iniciando evaluación de condiciones para generación de avisos")
        
        # Obtener datos de MARWIS
        marwis_data = None
        try:
            marwis_data = get_latest_marwis_data()
            logger.info("Datos de MARWIS obtenidos exitosamente")
        except Exception as e:
            logger.warning(f"No se pudieron obtener datos de MARWIS: {e}")
        
        avisos_generados = []
        
        # Evaluar cada tipo de aviso en orden de prioridad
        # AVISO_0: Temperatura bajo cero (MÁXIMA PRIORIDAD)
        if evaluar_condiciones_aviso_0(condiciones_clima):
            aviso = AVISOS_CONFIG['AVISO_0'].copy()
            aviso['tipo'] = 'AVISO_0'
            aviso['prioridad'] = 0  # Máxima prioridad
            aviso['fecha_generacion'] = datetime.now().isoformat()
            avisos_generados.append(aviso)
            logger.info("⚠️ AVISO 0 (Temperatura Bajo Cero - CRÍTICO) generado")
        
        if evaluar_condiciones_aviso_6(condiciones_clima):
            aviso = AVISOS_CONFIG['AVISO_6'].copy()
            aviso['tipo'] = 'AVISO_6'
            aviso['prioridad'] = 1
            aviso['fecha_generacion'] = datetime.now().isoformat()
            avisos_generados.append(aviso)
            logger.info("Aviso 6 (Alerta de nieve) generado")
        
        if evaluar_condiciones_aviso_5(condiciones_clima):
            aviso = AVISOS_CONFIG['AVISO_5'].copy()
            aviso['tipo'] = 'AVISO_5'
            aviso['prioridad'] = 2
            aviso['fecha_generacion'] = datetime.now().isoformat()
            avisos_generados.append(aviso)
            logger.info("Aviso 5 (Alerta de lluvia) generado")
        
        if evaluar_condiciones_aviso_4(condiciones_clima, marwis_data):
            aviso = AVISOS_CONFIG['AVISO_4'].copy()
            aviso['tipo'] = 'AVISO_4'
            aviso['prioridad'] = 3
            aviso['fecha_generacion'] = datetime.now().isoformat()
            avisos_generados.append(aviso)
            logger.info("Aviso 4 (Alerta de hielo) generado")
        
        if evaluar_condiciones_aviso_3(condiciones_clima, marwis_data):
            aviso = AVISOS_CONFIG['AVISO_3'].copy()
            aviso['tipo'] = 'AVISO_3'
            aviso['prioridad'] = 4
            aviso['fecha_generacion'] = datetime.now().isoformat()
            avisos_generados.append(aviso)
            logger.info("Aviso 3 (Alerta de cambio de condiciones) generado")
        
        if evaluar_condiciones_aviso_2(condiciones_clima):
            aviso = AVISOS_CONFIG['AVISO_2'].copy()
            aviso['tipo'] = 'AVISO_2'
            aviso['prioridad'] = 5
            aviso['fecha_generacion'] = datetime.now().isoformat()
            avisos_generados.append(aviso)
            logger.info("Aviso 2 (Umbral de Contingencia) generado")
        
        if evaluar_condiciones_aviso_1(condiciones_clima):
            aviso = AVISOS_CONFIG['AVISO_1'].copy()
            aviso['tipo'] = 'AVISO_1'
            aviso['prioridad'] = 6
            aviso['fecha_generacion'] = datetime.now().isoformat()
            avisos_generados.append(aviso)
            logger.info("Aviso 1 (Umbral de Alerta) generado")
        
        # Ordenar por prioridad
        avisos_generados.sort(key=lambda x: x['prioridad'])
        
        resultado = {
            'avisos_generados': avisos_generados,
            'total_avisos': len(avisos_generados),
            'condiciones_evaluadas': condiciones_clima,
            'datos_marwis': marwis_data,
            'fecha_evaluacion': datetime.now().isoformat()
        }
        
        logger.info(f"Evaluación completada. Total de avisos generados: {len(avisos_generados)}")
        return resultado
        
    except Exception as e:
        logger.error(f"Error generando avisos: {e}")
        return {
            'avisos_generados': [],
            'total_avisos': 0,
            'error': str(e),
            'fecha_evaluacion': datetime.now().isoformat()
        }

def obtener_tareas_procedimiento(tipo_aviso: str) -> List[str]:
    """Obtener tareas a realizar según el procedimiento para cada tipo de aviso"""
    tareas_por_aviso = {
        'AVISO_0': [
            '⚠️ ALERTA CRÍTICA: Temperatura bajo cero detectada',
            'Activación INMEDIATA del protocolo de emergencia por hielo',
            'Inspección urgente de todas las superficies pavimentadas',
            'Aplicación preventiva de descongelantes (urea/glicol)',
            'Verificar condiciones de pista con MARWIS cada 15 minutos',
            'Comunicación inmediata con torre de control',
            'Posicionar equipos de control de hielo en standby',
            'Evaluar restricción de operaciones si es necesario',
            'Notificar a todas las áreas operativas',
            'Documentar todas las acciones tomadas'
        ],
        'AVISO_1': [
            'Monitorear condiciones meteorológicas cada 2 horas',
            'Verificar temperatura de pista mediante MARWIS',
            'Notificar al personal de operaciones',
            'Preparar equipos de control de hielo/nieve',
            'Revisar stock de descongelantes (urea/glicol)'
        ],
        'AVISO_2': [
            'Activar protocolo de contingencia',
            'Inspección inmediata de pistas y rodajes',
            'Aplicación preventiva de descongelantes',
            'Posicionamiento de equipos en áreas críticas',
            'Comunicación con torre de control',
            'Evaluación de operaciones aeroportuarias'
        ],
        'AVISO_3': [
            'Generar OT de Monitoreo de condiciones de superficies pavimentadas',
            'Realizar medición con MARWIS de pista/rodaje/apron',
            'Documentar condiciones de superficie',
            'Reportar hallazgos a operaciones',
            'Evaluar necesidad de tratamiento preventivo'
        ],
        'AVISO_4': [
            'Aplicación inmediata de descongelantes',
            'Tratamiento de todas las superficies pavimentadas',
            'Inspección continua cada 30 minutos',
            'Coordinar con torre de control',
            'Restringir operaciones si es necesario',
            'Documentar aplicación de químicos'
        ],
        'AVISO_5': [
            'Preparar equipos de drenaje',
            'Inspeccionar sistemas de evacuación de agua',
            'Posicionar equipos de barrido',
            'Monitorear acumulación de agua',
            'Evaluar condiciones de fricción'
        ],
        'AVISO_6': [
            'Activar equipo completo de remoción de nieve',
            'Aplicación preventiva de descongelantes',
            'Posicionar tractores y equipos',
            'Preparar stock de urea y glicol',
            'Coordinar con meteorología',
            'Planificar turnos extendidos de personal'
        ]
    }
    
    return tareas_por_aviso.get(tipo_aviso, [])

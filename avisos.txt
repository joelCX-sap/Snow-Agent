#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MÓDULO DE GENERACIÓN DE AVISOS - MVP1 SNOW
================================================================================
Sistema de avisos para operaciones aeroportuarias de control de hielo y nieve.

PROPÓSITO:
    Este módulo implementa el PROCEDIMIENTO MVP1 SNOW para la generación
    determinística de avisos basados en condiciones meteorológicas.
    
CARACTERÍSTICAS:
    - Evaluación determinística (no usa IA/ML)
    - Decisiones auditables y reproducibles
    - Reglas de exclusión explícitas por prioridad
    - Validación robusta de datos de entrada
    
TABLAS IMPLEMENTADAS:
    - TABLA 1: Condiciones para AVISO_1 (Umbral de Alerta)
    - TABLA 3: Condiciones base para AVISO_5 y AVISO_6
    
INTEGRACIÓN:
    - MARWIS: Temperatura de pista
    - Open-Meteo: Pronóstico meteorológico
    - SAP PM: Códigos de aviso para mantenimiento

AUTOR: Sistema MVP1 SNOW
VERSIÓN: 2.0.0
FECHA: 2026-01-28
================================================================================
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json
import os

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES DEL SISTEMA
# =============================================================================

# Temperatura de pista por defecto cuando MARWIS no está disponible
TEMP_PISTA_DEFAULT = -0.1  # °C (hardcoded según procedimiento)

# Valores para datos inválidos/faltantes
VALOR_INVALIDO = 999.0
VALOR_MINIMO = -100.0
VALOR_MAXIMO = 100.0


class TipoAviso(Enum):
    """Enumeración de tipos de aviso con su prioridad (menor = más prioritario)"""
    AVISO_6 = (1, "Alerta de nieve")
    AVISO_5 = (2, "Alerta de lluvia")
    AVISO_1 = (3, "Umbral de Alerta")
    
    def __init__(self, prioridad: int, descripcion: str):
        self.prioridad = prioridad
        self.descripcion = descripcion


# =============================================================================
# REGLAS DE EXCLUSIÓN (DECLARATIVAS)
# =============================================================================
# Define qué avisos son bloqueados por cada tipo de aviso
# Estructura: {aviso_activo: [lista de avisos que bloquea]}

REGLAS_EXCLUSION: Dict[TipoAviso, List[TipoAviso]] = {
    TipoAviso.AVISO_6: [TipoAviso.AVISO_5, TipoAviso.AVISO_1],
    TipoAviso.AVISO_5: [TipoAviso.AVISO_1],
    TipoAviso.AVISO_1: [],  # No bloquea ninguno
}


# =============================================================================
# CONFIGURACIÓN DE AVISOS (CÓDIGOS SAP PM)
# =============================================================================
AVISOS_CONFIG = {
    'AVISO_1': {
        'nombre': 'Umbral de Alerta',
        'clase': 'ALERTA',
        'QMART': 'O1',              # Clase de aviso: Operaciones Aeropuerto
        'QMTXT': 'Umbral de Alerta',
        'TPLNR': 'RGA-LADAIR',      # Ubicación técnica
        'SWERK': 'RGA',             # Centro de emplazamiento
        'INGRP': 'OPE',             # Grupo planificador: Operaciones
        'GEWRK': 'ADM_AD',          # Puesto de trabajo
        'PRIOK': '2',               # Prioridad
        'QMGRP': 'YB-DERR1',        # Grupo modo de fallo: Operativo Nieve
        'QMCOD': 'Y110',            # Modo de fallo: Umbral de Alerta
        'nota': 'Condiciones de TABLA 1 cumplidas'
    },
    'AVISO_5': {
        'nombre': 'Alerta de lluvia',
        'clase': 'ALERTA',
        'QMART': 'O1',
        'QMTXT': 'Alerta de lluvia',
        'TPLNR': 'RGA-LADAIR',
        'SWERK': 'RGA',
        'INGRP': 'OPE',
        'GEWRK': 'ADM_AD',
        'PRIOK': '2',
        'QMGRP': 'YB-DERR1',
        'QMCOD': 'Y114',
        'nota': 'TABLA 3 + pronóstico lluvia ≥70%'
    },
    'AVISO_6': {
        'nombre': 'Alerta de nieve',
        'clase': 'ALERTA',
        'QMART': 'O1',
        'QMTXT': 'Alerta de nieve',
        'TPLNR': 'RGA-LADAIR',
        'SWERK': 'RGA',
        'INGRP': 'OPE',
        'GEWRK': 'ADM_AD',
        'PRIOK': '1',
        'QMGRP': 'YB-DERR1',
        'QMCOD': 'Y115',
        'nota': 'TABLA 3 + pronóstico nieve ≥70%'
    }
}


# =============================================================================
# DATACLASSES PARA DATOS NORMALIZADOS
# =============================================================================

@dataclass
class DatosMeteorologicos:
    """
    Estructura normalizada de datos meteorológicos.
    Todos los valores tienen defaults seguros y validados.
    """
    temperatura_ambiente: float = VALOR_INVALIDO
    temperatura_rocio: float = VALOR_INVALIDO
    temperatura_pista: float = TEMP_PISTA_DEFAULT  # Default según procedimiento
    humedad: float = 0.0
    viento: float = VALOR_INVALIDO
    prob_lluvia: float = 0.0
    prob_nieve: float = 0.0
    fuente_temp_pista: str = "DEFAULT"  # "MARWIS" o "DEFAULT"
    
    def es_valido(self) -> bool:
        """Verifica si los datos mínimos requeridos son válidos"""
        return (
            self.temperatura_ambiente != VALOR_INVALIDO and
            VALOR_MINIMO <= self.temperatura_ambiente <= VALOR_MAXIMO
        )


@dataclass
class ResultadoEvaluacion:
    """Resultado de evaluación de una tabla/condición"""
    cumple: bool
    razon: str
    detalles: Dict[str, Any]


# =============================================================================
# FUNCIONES DE NORMALIZACIÓN DE DATOS
# =============================================================================

def normalizar_valor_numerico(valor: Any, default: float = VALOR_INVALIDO) -> float:
    """
    Normaliza un valor a float, manejando casos especiales.
    
    Args:
        valor: Valor a normalizar (puede ser None, str, int, float)
        default: Valor por defecto si no se puede convertir
        
    Returns:
        Valor numérico normalizado
    """
    if valor is None:
        return default
    
    if isinstance(valor, str):
        valor_lower = valor.lower().strip()
        if valor_lower in ('n/a', 'na', 'null', 'none', ''):
            return default
        try:
            return float(valor)
        except ValueError:
            return default
    
    try:
        resultado = float(valor)
        # Validar rango físico razonable
        if resultado < VALOR_MINIMO or resultado > VALOR_MAXIMO:
            logger.warning(f"Valor fuera de rango físico: {resultado}")
            return default
        return resultado
    except (TypeError, ValueError):
        return default


def normalizar_datos_entrada(condiciones_clima: Dict[str, Any]) -> DatosMeteorologicos:
    """
    Normaliza los datos de entrada a una estructura consistente.
    
    PROCESO:
    1. Extrae valores del diccionario de entrada
    2. Normaliza cada valor a float
    3. Obtiene temperatura de pista desde MARWIS o usa default
    4. Valida rangos físicos
    
    Args:
        condiciones_clima: Diccionario con condiciones climáticas crudas
        
    Returns:
        DatosMeteorologicos normalizados
    """
    # Extraer pronóstico si existe
    pronostico = condiciones_clima.get('pronostico', {}) or {}
    
    # Crear estructura normalizada
    datos = DatosMeteorologicos(
        temperatura_ambiente=normalizar_valor_numerico(
            condiciones_clima.get('temperatura_actual')
        ),
        temperatura_rocio=normalizar_valor_numerico(
            condiciones_clima.get('punto_rocio')
        ),
        humedad=normalizar_valor_numerico(
            condiciones_clima.get('humedad'), default=0.0
        ),
        viento=normalizar_valor_numerico(
            condiciones_clima.get('viento')
        ),
        prob_lluvia=normalizar_valor_numerico(
            pronostico.get('prob_lluvia'), default=0.0
        ),
        prob_nieve=normalizar_valor_numerico(
            pronostico.get('prob_nieve'), default=0.0
        ),
    )
    
    # Obtener temperatura de pista desde MARWIS o usar default
    temp_pista_raw = condiciones_clima.get('temperatura_pista')
    if temp_pista_raw is not None and temp_pista_raw != VALOR_INVALIDO:
        datos.temperatura_pista = normalizar_valor_numerico(temp_pista_raw, TEMP_PISTA_DEFAULT)
        datos.fuente_temp_pista = "ENTRADA"
    else:
        # Intentar obtener desde MARWIS
        marwis_data = obtener_temperatura_pista_marwis()
        if marwis_data is not None:
            datos.temperatura_pista = marwis_data
            datos.fuente_temp_pista = "MARWIS"
        else:
            # Usar valor hardcoded según procedimiento
            datos.temperatura_pista = TEMP_PISTA_DEFAULT
            datos.fuente_temp_pista = "DEFAULT"
            logger.warning(
                f"MARWIS no disponible. Usando temperatura de pista por defecto: {TEMP_PISTA_DEFAULT}°C"
            )
    
    logger.info(
        f"Datos normalizados: T_amb={datos.temperatura_ambiente}°C, "
        f"T_rocío={datos.temperatura_rocio}°C, T_pista={datos.temperatura_pista}°C "
        f"(fuente: {datos.fuente_temp_pista}), Humedad={datos.humedad}%, "
        f"Viento={datos.viento}km/h, P_lluvia={datos.prob_lluvia}%, P_nieve={datos.prob_nieve}%"
    )
    
    return datos


def obtener_temperatura_pista_marwis() -> Optional[float]:
    """
    Obtiene la temperatura de pista desde los datos de MARWIS.
    
    Returns:
        Temperatura de pista en °C o None si no está disponible
    """
    try:
        station_data_path = os.path.join(os.path.dirname(__file__), 'station_data.json')
        
        if not os.path.exists(station_data_path):
            logger.warning("Archivo station_data.json no encontrado")
            return None
        
        with open(station_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Buscar sensor de temperatura de superficie/pista
        measurements = data if isinstance(data, list) else data.get('measurements', [])
        
        for measurement in measurements:
            sensor_name = measurement.get('SensorChannelName', '').lower()
            if any(keyword in sensor_name for keyword in ['surface', 'road', 'pista', 'pavement']):
                if 'temp' in sensor_name:
                    valor = normalizar_valor_numerico(measurement.get('Value'))
                    if valor != VALOR_INVALIDO:
                        logger.info(f"Temperatura de pista obtenida de MARWIS: {valor}°C")
                        return valor
        
        logger.warning("No se encontró sensor de temperatura de pista en MARWIS")
        return None
        
    except Exception as e:
        logger.error(f"Error leyendo datos de MARWIS: {e}")
        return None


# =============================================================================
# FUNCIONES DE EVALUACIÓN DE TABLAS
# =============================================================================

def evaluar_tabla_1(datos: DatosMeteorologicos) -> ResultadoEvaluacion:
    """
    TABLA 1 – AVISO 1 (UMBRAL DE ALERTA)
    
    Condiciones que deben cumplirse TODAS:
    - Tambiente:  3 < T ≤ 6
    - Trocío:     ≥ Tambiente - 3
    - Tpista:     < 0
    - Humedad:    ≥ 56%
    - Viento:     < 36 km/h
    
    Args:
        datos: Datos meteorológicos normalizados
        
    Returns:
        ResultadoEvaluacion con detalle de cumplimiento
    """
    detalles = {
        'temperatura_ambiente': {
            'valor': datos.temperatura_ambiente,
            'condicion': '3 < T ≤ 6',
            'cumple': 3 < datos.temperatura_ambiente <= 6
        },
        'temperatura_rocio': {
            'valor': datos.temperatura_rocio,
            'condicion': f'≥ {datos.temperatura_ambiente - 3:.1f} (Tamb - 3)',
            'cumple': datos.temperatura_rocio >= (datos.temperatura_ambiente - 3)
        },
        'temperatura_pista': {
            'valor': datos.temperatura_pista,
            'condicion': '< 0',
            'cumple': datos.temperatura_pista < 0
        },
        'humedad': {
            'valor': datos.humedad,
            'condicion': '≥ 56%',
            'cumple': datos.humedad >= 56
        },
        'viento': {
            'valor': datos.viento,
            'condicion': '< 36 km/h',
            'cumple': datos.viento < 36
        }
    }
    
    # Verificar que TODAS las condiciones se cumplan
    todas_cumplen = all(d['cumple'] for d in detalles.values())
    
    # Generar razón descriptiva
    if todas_cumplen:
        razon = "TABLA 1 CUMPLIDA: Todas las condiciones satisfechas"
    else:
        condiciones_fallidas = [k for k, v in detalles.items() if not v['cumple']]
        razon = f"TABLA 1 NO CUMPLIDA: Condiciones fallidas: {', '.join(condiciones_fallidas)}"
    
    return ResultadoEvaluacion(
        cumple=todas_cumplen,
        razon=razon,
        detalles=detalles
    )


def evaluar_tabla_3(datos: DatosMeteorologicos) -> ResultadoEvaluacion:
    """
    TABLA 3 – CONDICIONES BASE PARA AVISO 5 Y 6
    
    Condiciones que deben cumplirse TODAS:
    - Tambiente:  T ≤ 0
    - Trocío:     ≥ Tambiente - 1
    - Tpista:     < 0
    - Humedad:    ≥ 63%
    - Viento:     < 33 km/h
    
    Args:
        datos: Datos meteorológicos normalizados
        
    Returns:
        ResultadoEvaluacion con detalle de cumplimiento
    """
    detalles = {
        'temperatura_ambiente': {
            'valor': datos.temperatura_ambiente,
            'condicion': 'T ≤ 0',
            'cumple': datos.temperatura_ambiente <= 0
        },
        'temperatura_rocio': {
            'valor': datos.temperatura_rocio,
            'condicion': f'≥ {datos.temperatura_ambiente - 1:.1f} (Tamb - 1)',
            'cumple': datos.temperatura_rocio >= (datos.temperatura_ambiente - 1)
        },
        'temperatura_pista': {
            'valor': datos.temperatura_pista,
            'condicion': '< 0',
            'cumple': datos.temperatura_pista < 0
        },
        'humedad': {
            'valor': datos.humedad,
            'condicion': '≥ 63%',
            'cumple': datos.humedad >= 63
        },
        'viento': {
            'valor': datos.viento,
            'condicion': '< 33 km/h',
            'cumple': datos.viento < 33
        }
    }
    
    todas_cumplen = all(d['cumple'] for d in detalles.values())
    
    if todas_cumplen:
        razon = "TABLA 3 CUMPLIDA: Todas las condiciones base satisfechas"
    else:
        condiciones_fallidas = [k for k, v in detalles.items() if not v['cumple']]
        razon = f"TABLA 3 NO CUMPLIDA: Condiciones fallidas: {', '.join(condiciones_fallidas)}"
    
    return ResultadoEvaluacion(
        cumple=todas_cumplen,
        razon=razon,
        detalles=detalles
    )


# =============================================================================
# FUNCIONES DE EVALUACIÓN DE AVISOS INDIVIDUALES
# =============================================================================

def evaluar_aviso_1(datos: DatosMeteorologicos) -> Tuple[bool, str, ResultadoEvaluacion]:
    """
    AVISO_1: Umbral de Alerta
    
    Requiere: Cumplir TODAS las condiciones de TABLA 1
    """
    resultado_tabla = evaluar_tabla_1(datos)
    
    logger.info(f"Evaluación AVISO_1 (TABLA 1): {resultado_tabla.razon}")
    return resultado_tabla.cumple, resultado_tabla.razon, resultado_tabla


def evaluar_aviso_5(datos: DatosMeteorologicos) -> Tuple[bool, str, Optional[ResultadoEvaluacion]]:
    """
    AVISO_5: Alerta de Lluvia
    
    Requiere:
    1. Cumplir TABLA 3 (condiciones base)
    2. Pronóstico de lluvia a 2 horas ≥ 70%
    """
    # Evaluar TABLA 3
    resultado_tabla = evaluar_tabla_3(datos)
    
    if not resultado_tabla.cumple:
        razon = f"AVISO_5 NO APLICA: {resultado_tabla.razon}"
        logger.info(f"Evaluación AVISO_5: {razon}")
        return False, razon, resultado_tabla
    
    # Verificar pronóstico de lluvia
    if datos.prob_lluvia >= 70:
        razon = f"AVISO_5 ACTIVO: TABLA 3 cumplida + Prob. lluvia {datos.prob_lluvia}% ≥ 70%"
        logger.info(f"Evaluación AVISO_5: {razon}")
        return True, razon, resultado_tabla
    else:
        razon = f"AVISO_5 NO APLICA: TABLA 3 cumplida pero Prob. lluvia {datos.prob_lluvia}% < 70%"
        logger.info(f"Evaluación AVISO_5: {razon}")
        return False, razon, resultado_tabla


def evaluar_aviso_6(datos: DatosMeteorologicos) -> Tuple[bool, str, Optional[ResultadoEvaluacion]]:
    """
    AVISO_6: Alerta de Nieve
    
    Requiere:
    1. Cumplir TABLA 3 (condiciones base)
    2. Pronóstico de nieve a 3 horas ≥ 70%
    """
    # Evaluar TABLA 3
    resultado_tabla = evaluar_tabla_3(datos)
    
    if not resultado_tabla.cumple:
        razon = f"AVISO_6 NO APLICA: {resultado_tabla.razon}"
        logger.info(f"Evaluación AVISO_6: {razon}")
        return False, razon, resultado_tabla
    
    # Verificar pronóstico de nieve
    if datos.prob_nieve >= 70:
        razon = f"AVISO_6 ACTIVO: TABLA 3 cumplida + Prob. nieve {datos.prob_nieve}% ≥ 70%"
        logger.info(f"Evaluación AVISO_6: {razon}")
        return True, razon, resultado_tabla
    else:
        razon = f"AVISO_6 NO APLICA: TABLA 3 cumplida pero Prob. nieve {datos.prob_nieve}% < 70%"
        logger.info(f"Evaluación AVISO_6: {razon}")
        return False, razon, resultado_tabla


# =============================================================================
# FUNCIÓN DE DECISIÓN FINAL CON EXCLUSIONES
# =============================================================================

def aplicar_reglas_exclusion(avisos_candidatos: Dict[TipoAviso, bool]) -> List[TipoAviso]:
    """
    Aplica las reglas de exclusión para determinar avisos finales.
    
    REGLAS DE PRIORIDAD Y EXCLUSIÓN:
    - AVISO_0 bloquea TODOS los demás
    - AVISO_6 bloquea AVISO_5 y AVISO_1
    - AVISO_5 bloquea AVISO_1
    - AVISO_1 solo se genera si ningún aviso superior aplica
    
    Args:
        avisos_candidatos: Dict con {TipoAviso: bool} indicando si cada aviso cumple condiciones
        
    Returns:
        Lista de avisos finales a generar (después de aplicar exclusiones)
    """
    avisos_finales = []
    avisos_excluidos = set()
    
    # Ordenar por prioridad (menor número = mayor prioridad)
    avisos_ordenados = sorted(
        avisos_candidatos.keys(),
        key=lambda x: x.prioridad
    )
    
    for tipo_aviso in avisos_ordenados:
        cumple = avisos_candidatos[tipo_aviso]
        
        if not cumple:
            continue
        
        if tipo_aviso in avisos_excluidos:
            logger.warning(
                f"{tipo_aviso.name} EXCLUIDO: Bloqueado por aviso de mayor prioridad"
            )
            continue
        
        # Este aviso se genera
        avisos_finales.append(tipo_aviso)
        
        # Aplicar exclusiones para avisos de menor prioridad
        bloqueados = REGLAS_EXCLUSION.get(tipo_aviso, [])
        for aviso_bloqueado in bloqueados:
            if aviso_bloqueado not in avisos_excluidos:
                avisos_excluidos.add(aviso_bloqueado)
                if avisos_candidatos.get(aviso_bloqueado, False):
                    logger.warning(
                        f"{aviso_bloqueado.name} EXCLUIDO: Bloqueado por {tipo_aviso.name} "
                        f"(regla de exclusión declarativa)"
                    )
    
    return avisos_finales


# =============================================================================
# FUNCIÓN PRINCIPAL: generar_avisos (INTERFAZ PÚBLICA)
# =============================================================================

def generar_avisos(condiciones_clima: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evalúa las condiciones climáticas y genera los avisos correspondientes.
    
    PROCESO:
    1. Normalizar datos de entrada
    2. Evaluar cada tipo de aviso según sus tablas
    3. Aplicar reglas de exclusión por prioridad
    4. Generar avisos finales con códigos SAP
    
    Args:
        condiciones_clima: Diccionario con condiciones climáticas desde el sistema meteorológico
        
    Returns:
        Dict con estructura:
        {
            'avisos_generados': [...],
            'total_avisos': int,
            'condiciones_evaluadas': {...},
            'datos_marwis': {...},
            'fecha_evaluacion': str,
            'log_decisiones': [...]
        }
    """
    logger.info("=" * 70)
    logger.info("INICIANDO EVALUACIÓN DE CONDICIONES PARA GENERACIÓN DE AVISOS")
    logger.info("=" * 70)
    
    log_decisiones = []
    
    # PASO 1: Normalizar datos de entrada
    datos = normalizar_datos_entrada(condiciones_clima)
    
    if not datos.es_valido():
        logger.warning("Datos de entrada inválidos o insuficientes")
        return {
            'avisos_generados': [],
            'total_avisos': 0,
            'condiciones_evaluadas': condiciones_clima,
            'datos_marwis': None,
            'fecha_evaluacion': datetime.now().isoformat(),
            'log_decisiones': ["Datos de entrada inválidos"],
            'error': "Datos de entrada inválidos o insuficientes"
        }
    
    # PASO 2: Evaluar cada aviso
    avisos_candidatos = {}
    
    # Evaluar AVISO_6
    cumple_6, razon_6, _ = evaluar_aviso_6(datos)
    avisos_candidatos[TipoAviso.AVISO_6] = cumple_6
    log_decisiones.append(razon_6)
    
    # Evaluar AVISO_5
    cumple_5, razon_5, _ = evaluar_aviso_5(datos)
    avisos_candidatos[TipoAviso.AVISO_5] = cumple_5
    log_decisiones.append(razon_5)
    
    # Evaluar AVISO_1
    cumple_1, razon_1, _ = evaluar_aviso_1(datos)
    avisos_candidatos[TipoAviso.AVISO_1] = cumple_1
    log_decisiones.append(razon_1)
    
    # PASO 3: Aplicar reglas de exclusión
    logger.info("-" * 70)
    logger.info("APLICANDO REGLAS DE EXCLUSIÓN")
    logger.info("-" * 70)
    
    avisos_finales = aplicar_reglas_exclusion(avisos_candidatos)
    
    # PASO 4: Construir respuesta
    avisos_generados = []
    
    for tipo_aviso in avisos_finales:
        config_aviso = AVISOS_CONFIG[tipo_aviso.name].copy()
        config_aviso['tipo'] = tipo_aviso.name
        config_aviso['prioridad'] = tipo_aviso.prioridad
        config_aviso['fecha_generacion'] = datetime.now().isoformat()
        config_aviso['tareas_procedimiento'] = obtener_tareas_procedimiento(tipo_aviso.name)
        avisos_generados.append(config_aviso)
        
        logger.info(f"✓ {tipo_aviso.name} ({tipo_aviso.descripcion}) GENERADO")
    
    # Obtener datos de MARWIS para el resultado
    marwis_data = obtener_datos_marwis_completos()
    
    resultado = {
        'avisos_generados': avisos_generados,
        'total_avisos': len(avisos_generados),
        'condiciones_evaluadas': condiciones_clima,
        'datos_normalizados': {
            'temperatura_ambiente': datos.temperatura_ambiente,
            'temperatura_rocio': datos.temperatura_rocio,
            'temperatura_pista': datos.temperatura_pista,
            'fuente_temp_pista': datos.fuente_temp_pista,
            'humedad': datos.humedad,
            'viento': datos.viento,
            'prob_lluvia': datos.prob_lluvia,
            'prob_nieve': datos.prob_nieve
        },
        'datos_marwis': marwis_data,
        'fecha_evaluacion': datetime.now().isoformat(),
        'log_decisiones': log_decisiones
    }
    
    logger.info("=" * 70)
    logger.info(f"EVALUACIÓN COMPLETADA. Total de avisos generados: {len(avisos_generados)}")
    logger.info("=" * 70)
    
    return resultado


def obtener_datos_marwis_completos() -> Optional[Dict]:
    """Obtener datos completos de MARWIS desde station_data.json"""
    try:
        station_data_path = os.path.join(os.path.dirname(__file__), 'station_data.json')
        if not os.path.exists(station_data_path):
            return None
        
        with open(station_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return {'measurements': data}
        elif isinstance(data, dict):
            return data
        
        return None
    except Exception as e:
        logger.error(f"Error leyendo station_data.json: {e}")
        return None


# =============================================================================
# FUNCIÓN: obtener_tareas_procedimiento (INTERFAZ PÚBLICA)
# =============================================================================

def obtener_tareas_procedimiento(tipo_aviso: str) -> List[str]:
    """
    Obtener tareas a realizar según el procedimiento para cada tipo de aviso.
    
    Args:
        tipo_aviso: Identificador del aviso (AVISO_0, AVISO_1, AVISO_5, AVISO_6)
        
    Returns:
        Lista de tareas a realizar según el procedimiento operativo
    """
    tareas_por_aviso = {
        'AVISO_1': [
            'Monitorear condiciones meteorológicas cada 2 horas',
            'Verificar temperatura de pista mediante MARWIS',
            'Notificar al personal de operaciones',
            'Preparar equipos de control de hielo/nieve',
            'Revisar stock de descongelantes (urea/glicol)'
        ],
        'AVISO_5': [
            'Preparar equipos de drenaje',
            'Inspeccionar sistemas de evacuación de agua',
            'Posicionar equipos de barrido',
            'Monitorear acumulación de agua en pista',
            'Evaluar condiciones de fricción',
            'Coordinar con torre de control sobre estado de pista'
        ],
        'AVISO_6': [
            'Activar equipo completo de remoción de nieve',
            'Aplicación preventiva de descongelantes',
            'Posicionar tractores y equipos de remoción',
            'Preparar stock de urea y glicol',
            'Coordinar con meteorología para actualización continua',
            'Planificar turnos extendidos de personal',
            'Comunicar estado a torre de control'
        ]
    }
    
    return tareas_por_aviso.get(tipo_aviso, [])


# =============================================================================
# CÓDIGO DE PRUEBA (solo se ejecuta directamente)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("TEST DEL MÓDULO DE AVISOS MVP1 SNOW")
    print("=" * 70)
    
    # Escenario 1: Umbral de alerta (TABLA 1)
    print("\n--- ESCENARIO 1: Umbral de alerta ---")
    condiciones_1 = {
        'temperatura_actual': 4.5,
        'punto_rocio': 2.0,
        'temperatura_pista': -0.5,
        'humedad': 65,
        'viento': 20,
        'pronostico': {'prob_lluvia': 30, 'prob_nieve': 10}
    }
    resultado_1 = generar_avisos(condiciones_1)
    print(f"Avisos generados: {[a['tipo'] for a in resultado_1['avisos_generados']]}")
    
    # Escenario 2: Alerta de nieve (TABLA 3 + nieve)
    print("\n--- ESCENARIO 2: Alerta de nieve ---")
    condiciones_2 = {
        'temperatura_actual': -1.0,
        'punto_rocio': -1.5,
        'temperatura_pista': -2.0,
        'humedad': 70,
        'viento': 25,
        'pronostico': {'prob_lluvia': 20, 'prob_nieve': 85}
    }
    resultado_2 = generar_avisos(condiciones_2)
    print(f"Avisos generados: {[a['tipo'] for a in resultado_2['avisos_generados']]}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETADO")
    print("=" * 70)
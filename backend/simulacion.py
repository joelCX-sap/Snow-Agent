#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de Simulación - Escenarios de Prueba
Genera datos simulados para testear avisos y lógica del agente SNOW
"""

import logging
from typing import Dict, Any
from datetime import datetime

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definición de escenarios de simulación
ESCENARIOS_SIMULACION = {
    'nieve': {
        'nombre': 'Escenario de Nieve',
        'descripcion': 'Simula condiciones meteorológicas con alta probabilidad de nieve - GARANTIZA AVISO_6',
        'condiciones': {
            'temperatura_actual': -2.0,
            'punto_rocio': -2.5,  # >= temp_amb - 1
            'temperatura_pista': -0.5,  # < 0
            'humedad': 75,  # >= 63
            'viento': 25,  # < 33
            'visibilidad': 3.5,
            'precipitacion': 2.5,
            'condicion_actual': 'Nublado con nieve ligera',
            'pronostico': {
                'temp_max': 1.0,
                'temp_min': -5.0,
                'prob_lluvia': 10,
                'prob_nieve': 85,  # > 30 - CUMPLE UMBRAL AVISO_6
                'precipitacion_total': 8.0,
                'viento_max': 35
            },
            'condiciones_adversas': ['temperatura bajo cero', 'nieve', 'visibilidad reducida']
        },
        'marwis': {
            'temperatura_superficie': -0.5,
            'condicion_superficie': 'WET',
            'temperatura_aire': -2.0,
            'punto_rocio_superficie': -3.5,
            'humedad_relativa': 75
        }
    },
    'lluvia': {
        'nombre': 'Escenario de Lluvia',
        'descripcion': 'Simula condiciones meteorológicas con lluvia y riesgo de hielo - GARANTIZA AVISO_5',
        'condiciones': {
            'temperatura_actual': -0.5,  # <= 0 - CUMPLE UMBRAL
            'punto_rocio': -1.0,  # >= temp_amb + (-1)
            'temperatura_pista': -0.2,  # < 0 - CUMPLE UMBRAL
            'humedad': 85,  # >= 63 - CUMPLE UMBRAL
            'viento': 28,  # < 33 - CUMPLE UMBRAL
            'visibilidad': 4.0,
            'precipitacion': 5.0,
            'condicion_actual': 'Lluvia moderada',
            'pronostico': {
                'temp_max': 3.0,
                'temp_min': -1.0,
                'prob_lluvia': 90,  # > 50 - CUMPLE UMBRAL AVISO_5
                'prob_nieve': 20,
                'precipitacion_total': 12.0,
                'viento_max': 40
            },
            'condiciones_adversas': ['lluvia', 'temperatura bajo cero', 'viento fuerte']
        },
        'marwis': {
            'temperatura_superficie': -0.2,
            'condicion_superficie': 'DAMP',
            'temperatura_aire': 1.5,
            'punto_rocio_superficie': -0.5,
            'humedad_relativa': 85
        }
    },
    'hielo': {
        'nombre': 'Escenario de Hielo en Pista',
        'descripcion': 'Simula condiciones críticas con formación de hielo en pista - GARANTIZA AVISO_4',
        'condiciones': {
            'temperatura_actual': -0.5,  # <= 0 - CUMPLE UMBRAL
            'punto_rocio': -1.0,  # >= temp_amb + (-1)
            'temperatura_pista': -0.8,  # < 0 - CUMPLE UMBRAL
            'humedad': 90,  # >= 63 - CUMPLE UMBRAL
            'viento': 30,  # < 33 - CUMPLE UMBRAL
            'visibilidad': 2.0,
            'precipitacion': 1.5,
            'condicion_actual': 'Llovizna congelante',
            'pronostico': {
                'temp_max': 2.0,
                'temp_min': -2.0,
                'prob_lluvia': 70,
                'prob_nieve': 40,
                'precipitacion_total': 6.0,
                'viento_max': 38
            },
            'condiciones_adversas': ['temperatura bajo cero', 'lluvia', 'visibilidad reducida', 'viento fuerte']
        },
        'marwis': {
            'temperatura_superficie': -0.8,
            'condicion_superficie': 'WET',
            'temperatura_aire': 0.5,
            'punto_rocio_superficie': -1.0,
            'humedad_relativa': 90,
            'alerta_hielo': True
        }
    }
}

def generar_datos_simulados(escenario: str) -> Dict[str, Any]:
    """
    Genera datos climáticos simulados para el escenario especificado
    
    Args:
        escenario: Tipo de escenario ('nieve', 'lluvia', 'hielo')
        
    Returns:
        Dict con datos simulados completos
    """
    try:
        if escenario not in ESCENARIOS_SIMULACION:
            logger.error(f"Escenario '{escenario}' no válido")
            return {
                'success': False,
                'message': f"Escenario '{escenario}' no existe. Opciones: nieve, lluvia, hielo"
            }
        
        escenario_config = ESCENARIOS_SIMULACION[escenario]
        condiciones = escenario_config['condiciones'].copy()
        marwis = escenario_config['marwis'].copy()
        
        # Agregar metadatos
        condiciones['ubicacion'] = 'Río Grande (Simulación), Tierra del Fuego'
        condiciones['fecha'] = datetime.now().strftime('%Y-%m-%d')
        
        # Estructura compatible con el sistema real
        resultado_simulado = {
            'success': True,
            'simulacion': True,
            'escenario': escenario,
            'nombre_escenario': escenario_config['nombre'],
            'descripcion': escenario_config['descripcion'],
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'ciudad': 'riogrande',
            'clima_obtenido': True,
            'procedimientos_consultados': True,
            'respuesta_generada': True,
            'workflow_disparado': False,
            'datos_clima': {
                'location': {
                    'name': 'Río Grande (Simulación)',
                    'region': 'Tierra del Fuego',
                    'country': 'Argentina',
                    'localtime': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                'current': {
                    'temp_c': condiciones['temperatura_actual'],
                    'condition': {'text': condiciones['condicion_actual']},
                    'wind_kph': condiciones['viento'],
                    'humidity': condiciones['humedad'],
                    'vis_km': condiciones['visibilidad'],
                    'precip_mm': condiciones['precipitacion']
                },
                'forecast': {
                    'forecastday': [{
                        'day': condiciones['pronostico']
                    }]
                }
            },
            'condiciones_analizadas': condiciones,
            'datos_marwis_simulados': marwis,
            'respuesta_llm': generar_respuesta_llm_simulada(escenario, condiciones),
            'fuentes': generar_fuentes_simuladas(escenario),
            'workflow_info': None
        }
        
        logger.info(f"Datos simulados generados para escenario: {escenario}")
        return resultado_simulado
        
    except Exception as e:
        logger.error(f"Error generando datos simulados: {e}")
        return {
            'success': False,
            'message': f"Error: {str(e)}"
        }

def generar_respuesta_llm_simulada(escenario: str, condiciones: Dict[str, Any]) -> str:
    """Genera una respuesta LLM simulada según el escenario"""
    
    respuestas = {
        'nieve': f"""**PROCEDIMIENTO DE OPERACIÓN CON NIEVE**

**Condiciones Detectadas:**
- Temperatura: {condiciones['temperatura_actual']}°C (bajo cero)
- Probabilidad de nieve: {condiciones['pronostico']['prob_nieve']}%
- Visibilidad: {condiciones['visibilidad']} km (reducida)
- Temperatura de pista: {condiciones['temperatura_pista']}°C

**Acciones Requeridas:**

1. **Activación Inmediata del Equipo de Remoción de Nieve**
   - Posicionar tractores con palas en ambos extremos de la pista
   - Activar equipo de barrido y soplado
   - Preparar vehículos de esparcimiento de químicos

2. **Aplicación de Químicos Descongelantes**
   - Aplicar mezcla de urea al 50% en toda la superficie de pista
   - Concentración especial en umbrales y zonas de contacto inicial
   - Aplicar glicol en áreas críticas de rodaje

3. **Monitoreo Continuo**
   - Inspecciones cada 30 minutos con MARWIS
   - Medición de fricción de superficie
   - Reporte continuo a Torre de Control

4. **Comunicaciones**
   - Notificar a todas las aeronaves sobre condiciones de pista
   - NOTAM activo para operaciones con nieve
   - Coordinar con meteorología para actualizaciones

**CRÍTICO:** Con estas condiciones, considerar restricciones operativas si la acumulación supera 5mm/hora.""",
        
        'lluvia': f"""**PROCEDIMIENTO DE OPERACIÓN CON LLUVIA**

**Condiciones Detectadas:**
- Temperatura: {condiciones['temperatura_actual']}°C
- Probabilidad de lluvia: {condiciones['pronostico']['prob_lluvia']}%
- Temperatura de pista: {condiciones['temperatura_pista']}°C (riesgo de congelamiento)
- Precipitación actual: {condiciones['precipitacion']} mm

**Acciones Requeridas:**

1. **Prevención de Formación de Hielo**
   - ALERTA: Temperatura de pista bajo cero con lluvia
   - Aplicación INMEDIATA de descongelantes preventivos
   - Activar calefacción de zonas críticas si disponible

2. **Control de Agua en Superficie**
   - Verificar funcionamiento de sistemas de drenaje
   - Activar equipos de barrido para remover agua acumulada
   - Inspeccionar canales de desagüe

3. **Mediciones de Fricción**
   - Realizar mediciones de coeficiente de fricción cada 2 horas
   - Reportar condiciones de "WET" o "CONTAMINATED" según corresponda
   - Actualizar información de pista en ATIS

4. **Tratamiento Químico**
   - Aplicar glicol en concentración del 30% como preventivo
   - Preparar stock adicional de urea para emergencias
   - Mantener equipos en stand-by

**IMPORTANTE:** Monitoreo continuo de temperatura. Si desciende a 0°C o menos, escalar a protocolo de hielo.""",
        
        'hielo': f"""**PROCEDIMIENTO CRÍTICO: FORMACIÓN DE HIELO EN PISTA**

**ALERTA MÁXIMA - CONDICIONES CRÍTICAS**

**Condiciones Detectadas:**
- Temperatura ambiente: {condiciones['temperatura_actual']}°C
- Temperatura de pista: {condiciones['temperatura_pista']}°C (BAJO CERO)
- Superficie MARWIS: WET + Temperatura negativa = ALTO RIESGO DE HIELO
- Humedad: {condiciones['humedad']}%
- Visibilidad: {condiciones['visibilidad']} km

**ACCIONES INMEDIATAS Y CRÍTICAS:**

1. **RESPUESTA DE EMERGENCIA**
   - Activar TODOS los equipos de control de hielo
   - Personal completo en pista INMEDIATAMENTE
   - Considerar CIERRE TEMPORAL de operaciones

2. **TRATAMIENTO AGRESIVO**
   - Aplicación MASIVA de glicol al 50% en toda la pista
   - Aplicación de urea en concentración máxima
   - Repetir aplicación cada 15-20 minutos
   - NO ESCATIMAR en uso de químicos

3. **INSPECCIONES CONTINUAS**
   - MARWIS cada 15 minutos
   - Inspección visual y táctil de superficie
   - Medición de temperatura de superficie continua
   - Reportes en tiempo real a Torre de Control

4. **COORDINACIÓN OPERATIVA**
   - Notificar INMEDIATAMENTE a:
     * Torre de Control
     * Dirección de Aeropuerto
     * Todas las aerolíneas operando
   - Emitir NOTAM de CONDICIONES CRÍTICAS
   - Activar protocolo de contingencia nivel MÁXIMO

5. **RESTRICCIONES OPERATIVAS**
   - Solo aeronaves certificadas para operación en hielo
   - Aumentar separaciones entre operaciones
   - Procedimientos de aproximación alternativos
   - Considerar desvío de vuelos si condiciones empeoran

**DURACIÓN ESTIMADA:** Mantener operación de emergencia hasta que temperatura de pista supere +2°C de manera estable.

**RECURSOS NECESARIOS:**
- Personal completo (2-3 turnos)
- Stock completo de químicos
- Todos los vehículos operativos
- Comunicación continua con meteorología"""
    }
    
    return respuestas.get(escenario, "Procedimiento no disponible para este escenario")

def generar_fuentes_simuladas(escenario: str) -> list:
    """Genera fuentes de información simuladas"""
    
    fuentes_base = [
        {
            'title': 'Manual de Procedimientos de Operaciones de Invierno',
            'filename': 'procedimientos_invierno_2024.pdf',
            'path': 'documentos/operaciones/invierno',
            'snippet': 'Procedimientos estándar para operaciones con condiciones meteorológicas adversas...'
        },
        {
            'title': 'Protocolo MARWIS de Monitoreo de Superficie',
            'filename': 'marwis_protocol.pdf',
            'path': 'documentos/tecnicos/marwis',
            'snippet': 'Uso del sistema MARWIS para medición continua de condiciones de pista...'
        },
        {
            'title': 'Aplicación de Descongelantes - Guía Técnica',
            'filename': 'guia_descongelantes.pdf',
            'path': 'documentos/mantenimiento',
            'snippet': 'Dosificación y aplicación correcta de urea y glicol según condiciones...'
        }
    ]
    
    return fuentes_base

def obtener_escenarios_disponibles() -> Dict[str, Any]:
    """Retorna lista de escenarios de simulación disponibles"""
    escenarios = []
    for key, config in ESCENARIOS_SIMULACION.items():
        escenarios.append({
            'id': key,
            'nombre': config['nombre'],
            'descripcion': config['descripcion']
        })
    
    return {
        'success': True,
        'escenarios': escenarios,
        'total': len(escenarios)
    }

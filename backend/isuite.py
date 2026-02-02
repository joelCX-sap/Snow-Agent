#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MÓDULO DE INTEGRACIÓN CON SAP INTEGRATION SUITE (CPI)
================================================================================
Sistema de envío de avisos a SAP Integration Suite mediante iFlow HTTP.

PROPÓSITO:
    Este módulo implementa la integración con SAP Integration Suite para
    enviar avisos generados por el sistema MVP1 SNOW a través de un iFlow HTTP.
    
AUTENTICACIÓN:
    - OAuth2 Client Credentials (OBLIGATORIA)
    - Token cacheado en memoria con manejo de expiración
    
CONFIGURACIÓN (Variables de Entorno):
    - ISUITE_OAUTH_TOKEN_URL: URL del endpoint de token OAuth2
    - ISUITE_OAUTH_CLIENT_ID: Client ID para OAuth2
    - ISUITE_OAUTH_CLIENT_SECRET: Client Secret para OAuth2
    - ISUITE_IFLOW_URL: URL del iFlow HTTP en SAP Integration Suite

AUTOR: Sistema MVP1 SNOW
VERSIÓN: 1.0.0
FECHA: 2026-01-30
================================================================================
"""

import os
import time
import logging
import requests
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES Y CONFIGURACIÓN
# =============================================================================

# Margen de seguridad para renovación del token (en segundos)
# Renovar token 60 segundos antes de que expire
TOKEN_EXPIRY_MARGIN = 60

# Timeout por defecto para requests HTTP (en segundos)
DEFAULT_TIMEOUT = 30

# =============================================================================
# CACHE DE TOKEN EN MEMORIA
# =============================================================================

@dataclass
class TokenCache:
    """Cache simple en memoria para el access token OAuth2"""
    access_token: Optional[str] = None
    expires_at: float = 0.0  # Unix timestamp cuando expira
    token_type: str = "Bearer"
    
    def is_valid(self) -> bool:
        """Verifica si el token actual es válido y no ha expirado"""
        if not self.access_token:
            return False
        # Considerar inválido si expira dentro del margen de seguridad
        return time.time() < (self.expires_at - TOKEN_EXPIRY_MARGIN)
    
    def clear(self) -> None:
        """Limpia el cache del token"""
        self.access_token = None
        self.expires_at = 0.0


# Instancia global del cache de token
_token_cache = TokenCache()


# =============================================================================
# EXCEPCIONES PERSONALIZADAS
# =============================================================================

class ISuiteError(Exception):
    """Excepción base para errores de integración con SAP Integration Suite"""
    pass


class OAuthTokenError(ISuiteError):
    """Error al obtener el token OAuth2"""
    pass


class IFlowCallError(ISuiteError):
    """Error al llamar al iFlow de SAP Integration Suite"""
    pass


class ConfigurationError(ISuiteError):
    """Error de configuración (variables de entorno faltantes)"""
    pass


# =============================================================================
# FUNCIONES DE CONFIGURACIÓN
# =============================================================================

def obtener_configuracion() -> Dict[str, str]:
    """
    Obtiene la configuración desde variables de entorno.
    
    Returns:
        Dict con las variables de configuración
        
    Raises:
        ConfigurationError: Si alguna variable requerida no está configurada
    """
    config = {
        'oauth_token_url': os.getenv('ISUITE_OAUTH_TOKEN_URL', ''),
        'oauth_client_id': os.getenv('ISUITE_OAUTH_CLIENT_ID', ''),
        'oauth_client_secret': os.getenv('ISUITE_OAUTH_CLIENT_SECRET', ''),
        'iflow_url': os.getenv('ISUITE_IFLOW_URL', ''),
    }
    
    # Validar que todas las variables requeridas estén configuradas
    variables_faltantes = [key for key, value in config.items() if not value]
    
    if variables_faltantes:
        mensaje = f"Variables de entorno faltantes: {', '.join(variables_faltantes)}"
        logger.error(mensaje)
        raise ConfigurationError(mensaje)
    
    return config


# =============================================================================
# FUNCIONES DE AUTENTICACIÓN OAUTH2
# =============================================================================

def obtener_token_oauth2(force_refresh: bool = False) -> str:
    """
    Obtiene un access token OAuth2 usando Client Credentials.
    
    Implementa cache en memoria para evitar solicitar un nuevo token
    en cada llamada. Solo solicita un nuevo token si:
    - No hay token en cache
    - El token actual ha expirado o está por expirar
    - Se solicita explícitamente con force_refresh=True
    
    Args:
        force_refresh: Si True, fuerza la obtención de un nuevo token
        
    Returns:
        Access token válido
        
    Raises:
        OAuthTokenError: Si no se puede obtener el token
        ConfigurationError: Si la configuración es inválida
    """
    global _token_cache
    
    # Verificar si el token cacheado es válido
    if not force_refresh and _token_cache.is_valid():
        logger.debug("Usando token OAuth2 cacheado")
        return _token_cache.access_token
    
    logger.info("Solicitando nuevo token OAuth2...")
    
    try:
        config = obtener_configuracion()
    except ConfigurationError:
        raise
    
    # Preparar la solicitud de token
    token_url = config['oauth_token_url']
    client_id = config['oauth_client_id']
    client_secret = config['oauth_client_secret']
    
    # Headers para la solicitud de token
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    # Body de la solicitud (OAuth2 Client Credentials)
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    }
    
    try:
        logger.debug(f"Solicitando token a: {token_url}")
        
        response = requests.post(
            token_url,
            headers=headers,
            data=data,
            timeout=DEFAULT_TIMEOUT
        )
        
        # Log del status code para debugging
        logger.debug(f"Respuesta token endpoint: HTTP {response.status_code}")
        
        # Verificar respuesta
        if response.status_code != 200:
            error_detail = ""
            try:
                error_json = response.json()
                error_detail = f" - {error_json.get('error', '')} {error_json.get('error_description', '')}"
            except Exception:
                error_detail = f" - {response.text[:200]}" if response.text else ""
            
            mensaje = f"Error obteniendo token OAuth2: HTTP {response.status_code}{error_detail}"
            logger.error(mensaje)
            raise OAuthTokenError(mensaje)
        
        # Parsear respuesta
        token_data = response.json()
        
        access_token = token_data.get('access_token')
        if not access_token:
            raise OAuthTokenError("Respuesta de token sin access_token")
        
        # Calcular tiempo de expiración
        expires_in = token_data.get('expires_in', 3600)  # Default 1 hora
        expires_at = time.time() + expires_in
        
        # Actualizar cache
        _token_cache.access_token = access_token
        _token_cache.expires_at = expires_at
        _token_cache.token_type = token_data.get('token_type', 'Bearer')
        
        logger.info(f"Token OAuth2 obtenido exitosamente. Expira en {expires_in} segundos")
        
        return access_token
        
    except requests.exceptions.Timeout:
        mensaje = f"Timeout al solicitar token OAuth2 (>{DEFAULT_TIMEOUT}s)"
        logger.error(mensaje)
        raise OAuthTokenError(mensaje)
        
    except requests.exceptions.ConnectionError as e:
        mensaje = f"Error de conexión al solicitar token OAuth2: {str(e)}"
        logger.error(mensaje)
        raise OAuthTokenError(mensaje)
        
    except requests.exceptions.RequestException as e:
        mensaje = f"Error HTTP al solicitar token OAuth2: {str(e)}"
        logger.error(mensaje)
        raise OAuthTokenError(mensaje)


def invalidar_token_cache() -> None:
    """
    Invalida el cache del token OAuth2.
    Útil cuando se recibe un 401 y se necesita forzar la renovación.
    """
    global _token_cache
    logger.info("Invalidando cache de token OAuth2")
    _token_cache.clear()


# =============================================================================
# FUNCIONES DE MAPEO DE PAYLOAD
# =============================================================================

def mapear_aviso_a_payload_isuite(aviso_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapea el JSON del aviso al formato requerido por SAP Integration Suite.
    
    El aviso ya viene generado desde el sistema, esta función solo
    realiza el mapeo a la estructura esperada por el iFlow.
    
    Args:
        aviso_json: Diccionario con el aviso ya generado
        
    Returns:
        Payload formateado para SAP Integration Suite
    """
    # Extraer datos del aviso
    avisos_generados = aviso_json.get('avisos_generados', [])
    condiciones = aviso_json.get('condiciones_evaluadas', {})
    datos_normalizados = aviso_json.get('datos_normalizados', {})
    datos_marwis = aviso_json.get('datos_marwis', {})
    fecha_evaluacion = aviso_json.get('fecha_evaluacion', datetime.now().isoformat())
    
    # Construir payload para SAP Integration Suite
    payload = {
        'header': {
            'source_system': 'MVP1_SNOW',
            'timestamp': fecha_evaluacion,
            'message_type': 'AVISO_METEOROLOGICO',
            'version': '1.0'
        },
        'avisos': [],
        'condiciones_meteorologicas': {
            'temperatura_ambiente': datos_normalizados.get('temperatura_ambiente'),
            'temperatura_rocio': datos_normalizados.get('temperatura_rocio'),
            'temperatura_pista': datos_normalizados.get('temperatura_pista'),
            'fuente_temp_pista': datos_normalizados.get('fuente_temp_pista'),
            'humedad': datos_normalizados.get('humedad'),
            'viento': datos_normalizados.get('viento'),
            'prob_lluvia': datos_normalizados.get('prob_lluvia'),
            'prob_nieve': datos_normalizados.get('prob_nieve'),
        },
        'datos_marwis': datos_marwis,
        'log_decisiones': aviso_json.get('log_decisiones', [])
    }
    
    # Mapear cada aviso generado
    for aviso in avisos_generados:
        aviso_sap = {
            # Campos SAP PM estándar
            'QMART': aviso.get('QMART', ''),           # Clase de aviso
            'QMTXT': aviso.get('QMTXT', ''),           # Descripción
            'TPLNR': aviso.get('TPLNR', ''),           # Ubicación técnica
            'SWERK': aviso.get('SWERK', ''),           # Centro de emplazamiento
            'INGRP': aviso.get('INGRP', ''),           # Grupo planificador
            'GEWRK': aviso.get('GEWRK', ''),           # Puesto de trabajo
            'PRIOK': aviso.get('PRIOK', ''),           # Prioridad
            'QMGRP': aviso.get('QMGRP', ''),           # Grupo modo de fallo
            'QMCOD': aviso.get('QMCOD', ''),           # Modo de fallo
            
            # Campos adicionales del sistema
            'tipo_aviso': aviso.get('tipo', ''),
            'nombre_aviso': aviso.get('nombre', ''),
            'clase_aviso': aviso.get('clase', ''),
            'prioridad_interna': aviso.get('prioridad', 0),
            'fecha_generacion': aviso.get('fecha_generacion', ''),
            'nota': aviso.get('nota', ''),
            
            # Tareas del procedimiento
            'tareas_procedimiento': aviso.get('tareas_procedimiento', [])
        }
        payload['avisos'].append(aviso_sap)
    
    return payload


# =============================================================================
# FUNCIÓN PRINCIPAL: ENVIAR AVISO A SAP INTEGRATION SUITE
# =============================================================================

def enviar_aviso_a_isuite(aviso_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía un aviso ya generado a SAP Integration Suite mediante iFlow HTTP.
    
    Esta es la función pública principal del módulo. Recibe el aviso ya
    generado por el sistema y lo envía a SAP Integration Suite.
    
    PROCESO:
    1. Validar que el aviso_json no esté vacío
    2. Obtener token OAuth2 (desde cache o nuevo)
    3. Mapear el aviso al formato requerido por el iFlow
    4. Enviar el payload al iFlow HTTP
    5. Manejar respuesta y posibles errores
    
    Args:
        aviso_json: Diccionario con el aviso ya generado por el sistema.
                   Se espera la estructura completa retornada por generar_avisos()
        
    Returns:
        Dict con la respuesta del envío:
        {
            'success': bool,
            'status_code': int,
            'response_body': dict o str,
            'message': str,
            'timestamp': str
        }
        
    Raises:
        No lanza excepciones - todos los errores se retornan en el dict de respuesta
    """
    logger.info("=" * 70)
    logger.info("INICIANDO ENVÍO DE AVISO A SAP INTEGRATION SUITE")
    logger.info("=" * 70)
    
    resultado = {
        'success': False,
        'status_code': None,
        'response_body': None,
        'message': '',
        'timestamp': datetime.now().isoformat()
    }
    
    # Validación de entrada
    if not aviso_json:
        resultado['message'] = "Error: aviso_json está vacío o es None"
        logger.error(resultado['message'])
        return resultado
    
    if not isinstance(aviso_json, dict):
        resultado['message'] = f"Error: aviso_json debe ser un dict, recibido: {type(aviso_json)}"
        logger.error(resultado['message'])
        return resultado
    
    # Verificar que hay avisos para enviar
    avisos_generados = aviso_json.get('avisos_generados', [])
    if not avisos_generados:
        resultado['message'] = "No hay avisos generados para enviar"
        resultado['success'] = True  # No es un error, simplemente no hay nada que enviar
        resultado['status_code'] = 200
        logger.info(resultado['message'])
        return resultado
    
    logger.info(f"Avisos a enviar: {len(avisos_generados)}")
    
    # Obtener configuración
    try:
        config = obtener_configuracion()
    except ConfigurationError as e:
        resultado['message'] = f"Error de configuración: {str(e)}"
        logger.error(resultado['message'])
        return resultado
    
    # Obtener token OAuth2
    try:
        access_token = obtener_token_oauth2()
    except OAuthTokenError as e:
        resultado['message'] = f"Error OAuth2: {str(e)}"
        logger.error(resultado['message'])
        return resultado
    except ConfigurationError as e:
        resultado['message'] = f"Error de configuración OAuth2: {str(e)}"
        logger.error(resultado['message'])
        return resultado
    
    # Mapear aviso al formato del iFlow
    try:
        payload = mapear_aviso_a_payload_isuite(aviso_json)
        logger.debug(f"Payload mapeado: {len(str(payload))} caracteres")
    except Exception as e:
        resultado['message'] = f"Error mapeando aviso: {str(e)}"
        logger.error(resultado['message'])
        return resultado
    
    # Preparar headers para el iFlow
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Source-System': 'MVP1_SNOW',
        'X-Message-Type': 'AVISO_METEOROLOGICO'
    }
    
    iflow_url = config['iflow_url']
    
    # Enviar al iFlow con retry en caso de token expirado
    max_retries = 2
    for intento in range(max_retries):
        try:
            logger.info(f"Enviando a iFlow: {iflow_url} (intento {intento + 1}/{max_retries})")
            
            response = requests.post(
                iflow_url,
                headers=headers,
                json=payload,
                timeout=DEFAULT_TIMEOUT
            )
            
            resultado['status_code'] = response.status_code
            
            # Log de respuesta
            logger.info(f"Respuesta iFlow: HTTP {response.status_code}")
            
            # Intentar parsear respuesta como JSON
            try:
                resultado['response_body'] = response.json()
            except Exception:
                resultado['response_body'] = response.text[:1000] if response.text else None
            
            # Evaluar resultado según status code
            if response.status_code in [200, 201, 202]:
                resultado['success'] = True
                resultado['message'] = f"Aviso enviado exitosamente. Status: {response.status_code}"
                logger.info(resultado['message'])
                break
                
            elif response.status_code == 401:
                # Token inválido o expirado - reintentar con nuevo token
                if intento < max_retries - 1:
                    logger.warning("Token rechazado (401). Solicitando nuevo token...")
                    invalidar_token_cache()
                    try:
                        access_token = obtener_token_oauth2(force_refresh=True)
                        headers['Authorization'] = f'Bearer {access_token}'
                        continue
                    except (OAuthTokenError, ConfigurationError) as e:
                        resultado['message'] = f"Error renovando token: {str(e)}"
                        logger.error(resultado['message'])
                        break
                else:
                    resultado['message'] = f"Error de autenticación persistente: HTTP 401"
                    logger.error(resultado['message'])
                    break
                    
            elif response.status_code == 403:
                resultado['message'] = f"Error de autorización: HTTP 403 - Acceso denegado"
                logger.error(resultado['message'])
                break
                
            elif response.status_code >= 400 and response.status_code < 500:
                resultado['message'] = f"Error del cliente: HTTP {response.status_code}"
                logger.error(resultado['message'])
                break
                
            elif response.status_code >= 500:
                resultado['message'] = f"Error del servidor SAP Integration Suite: HTTP {response.status_code}"
                logger.error(resultado['message'])
                break
                
            else:
                resultado['message'] = f"Respuesta inesperada: HTTP {response.status_code}"
                logger.warning(resultado['message'])
                break
                
        except requests.exceptions.Timeout:
            resultado['message'] = f"Timeout al llamar al iFlow (>{DEFAULT_TIMEOUT}s)"
            logger.error(resultado['message'])
            break
            
        except requests.exceptions.ConnectionError as e:
            resultado['message'] = f"Error de conexión al iFlow: {str(e)}"
            logger.error(resultado['message'])
            break
            
        except requests.exceptions.RequestException as e:
            resultado['message'] = f"Error HTTP al llamar al iFlow: {str(e)}"
            logger.error(resultado['message'])
            break
    
    logger.info("=" * 70)
    logger.info(f"ENVÍO COMPLETADO - Success: {resultado['success']}")
    logger.info("=" * 70)
    
    return resultado


# =============================================================================
# FUNCIONES AUXILIARES PÚBLICAS
# =============================================================================

def verificar_configuracion() -> Dict[str, Any]:
    """
    Verifica que la configuración del módulo sea válida.
    Útil para diagnóstico y health checks.
    
    Returns:
        Dict con el estado de la configuración
    """
    resultado = {
        'configuracion_valida': False,
        'variables_configuradas': [],
        'variables_faltantes': [],
        'mensaje': ''
    }
    
    variables = {
        'ISUITE_OAUTH_TOKEN_URL': os.getenv('ISUITE_OAUTH_TOKEN_URL', ''),
        'ISUITE_OAUTH_CLIENT_ID': os.getenv('ISUITE_OAUTH_CLIENT_ID', ''),
        'ISUITE_OAUTH_CLIENT_SECRET': os.getenv('ISUITE_OAUTH_CLIENT_SECRET', ''),
        'ISUITE_IFLOW_URL': os.getenv('ISUITE_IFLOW_URL', ''),
    }
    
    for var, valor in variables.items():
        if valor:
            # No mostrar el valor del secret
            if 'SECRET' in var:
                resultado['variables_configuradas'].append(f"{var}: ***configurado***")
            else:
                resultado['variables_configuradas'].append(f"{var}: {valor[:50]}...")
        else:
            resultado['variables_faltantes'].append(var)
    
    resultado['configuracion_valida'] = len(resultado['variables_faltantes']) == 0
    
    if resultado['configuracion_valida']:
        resultado['mensaje'] = "Configuración válida. Todas las variables están configuradas."
    else:
        resultado['mensaje'] = f"Configuración incompleta. Faltan: {', '.join(resultado['variables_faltantes'])}"
    
    return resultado


def obtener_estado_token() -> Dict[str, Any]:
    """
    Obtiene el estado actual del token OAuth2 cacheado.
    Útil para diagnóstico.
    
    Returns:
        Dict con información del estado del token
    """
    global _token_cache
    
    return {
        'tiene_token': _token_cache.access_token is not None,
        'token_valido': _token_cache.is_valid(),
        'expira_en_segundos': max(0, int(_token_cache.expires_at - time.time())) if _token_cache.access_token else 0,
        'token_type': _token_cache.token_type
    }


# =============================================================================
# CÓDIGO DE PRUEBA (solo se ejecuta directamente)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("TEST DEL MÓDULO DE INTEGRACIÓN SAP INTEGRATION SUITE")
    print("=" * 70)
    
    # Verificar configuración
    print("\n--- Verificación de Configuración ---")
    config_status = verificar_configuracion()
    print(f"Configuración válida: {config_status['configuracion_valida']}")
    print(f"Mensaje: {config_status['mensaje']}")
    
    if config_status['variables_configuradas']:
        print("\nVariables configuradas:")
        for var in config_status['variables_configuradas']:
            print(f"  ✓ {var}")
    
    if config_status['variables_faltantes']:
        print("\nVariables faltantes:")
        for var in config_status['variables_faltantes']:
            print(f"  ✗ {var}")
    
    # Test de envío (solo si la configuración es válida)
    if config_status['configuracion_valida']:
        print("\n--- Test de Envío ---")
        
        # Crear un aviso de prueba (estructura similar a la de avisos.py)
        aviso_test = {
            'avisos_generados': [{
                'tipo': 'AVISO_1',
                'nombre': 'Umbral de Alerta',
                'clase': 'ALERTA',
                'QMART': 'O1',
                'QMTXT': 'Umbral de Alerta - TEST',
                'TPLNR': 'RGA-LADAIR',
                'SWERK': 'RGA',
                'INGRP': 'OPE',
                'GEWRK': 'ADM_AD',
                'PRIOK': '2',
                'QMGRP': 'YB-DERR1',
                'QMCOD': 'Y110',
                'prioridad': 3,
                'fecha_generacion': datetime.now().isoformat(),
                'tareas_procedimiento': [
                    'Tarea de prueba 1',
                    'Tarea de prueba 2'
                ]
            }],
            'total_avisos': 1,
            'condiciones_evaluadas': {
                'temperatura_actual': 4.5,
                'humedad': 65,
                'viento': 20
            },
            'datos_normalizados': {
                'temperatura_ambiente': 4.5,
                'temperatura_rocio': 2.0,
                'temperatura_pista': -0.5,
                'humedad': 65,
                'viento': 20
            },
            'fecha_evaluacion': datetime.now().isoformat(),
            'log_decisiones': ['Test de integración']
        }
        
        # Intentar enviar
        resultado = enviar_aviso_a_isuite(aviso_test)
        
        print(f"\nResultado del envío:")
        print(f"  Success: {resultado['success']}")
        print(f"  Status Code: {resultado['status_code']}")
        print(f"  Mensaje: {resultado['message']}")
        
        if resultado['response_body']:
            print(f"  Response Body: {str(resultado['response_body'])[:200]}...")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETADO")
    print("=" * 70)
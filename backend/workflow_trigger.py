#!/usr/bin/env python3
"""
Módulo para disparar workflow en SAP BTP
Utiliza get_token.py para obtener el token de autenticación
"""

import json
import requests
import sys
from get_token import get_token_from_binding


def trigger_workflow(binding_path: str, agent_analysis_text: str = "TEST AGENT SNOW"):
    """
    Dispara un workflow en SAP BTP usando el token obtenido del binding
    
    Args:
        binding_path (str): Ruta al archivo de binding JSON
        agent_analysis_text (str): Texto para el campo agent_analysis
    
    Returns:
        dict: Respuesta del API del workflow
    """
    
    # Obtener el token usando el módulo get_token
    print("Obteniendo token de autenticación...")
    access_token = get_token_from_binding(binding_path)
    
    # URL del workflow
    workflow_url = "https://spa-api-gateway-bpi-eu-prod.cfapps.eu12.hana.ondemand.com/workflow/rest/v1/workflow-instances"
    
    # Payload para el POST
    payload = {
        "definitionId": "eu12.xp6xzy9lzsyf9cc9.aeropuertos1.mateninimiento",
        "context": {
            "agent_analysis": agent_analysis_text
        }
    }
    
    # Headers para el request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    print(f"\nEnviando request al workflow...")
    print(f"URL: {workflow_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Hacer el POST request
    try:
        response = requests.post(workflow_url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n=== WORKFLOW DISPARADO EXITOSAMENTE ===")
        print(f"Status Code: {response.status_code}")
        print(f"Respuesta: {json.dumps(result, indent=2)}")
        
        return result
        
    except requests.exceptions.HTTPError as e:
        print(f"\nError HTTP: {e}")
        print(f"Status Code: {response.status_code}")
        print(f"Respuesta: {response.text}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"\nError en el request: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"\nError decodificando JSON: {e}")
        print(f"Respuesta raw: {response.text}")
        raise


def main():
    """Función principal - ejecuta el trigger del workflow"""
    if len(sys.argv) < 2:
        print("Uso: python workflow_trigger.py process-automation-service-binding.json [texto_agent_analysis]")
        print("Ejemplo: python workflow_trigger.py process-automation-service-binding.json 'Mi análisis personalizado'")
        sys.exit(1)
    
    binding_path = sys.argv[1]
    agent_analysis = sys.argv[2] if len(sys.argv) > 2 else "TEST AGENT SNOW"
    
    try:
        result = trigger_workflow(binding_path, agent_analysis)
        print(f"\n✅ Workflow disparado correctamente")
        
    except Exception as e:
        print(f"\n❌ Error ejecutando el workflow: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

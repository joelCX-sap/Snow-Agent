#!/usr/bin/env python3
"""
Obtener token OAuth2 desde binding de SAP BTP (XSUAA)
Requiere: pip install requests
"""

import json
import requests
import sys

def get_token_from_binding(binding_path: str):
    with open(binding_path, 'r', encoding='utf-8') as f:
        binding = json.load(f)

    uaa = binding["uaa"]
    url = f"{uaa['url']}/oauth/token"

    client_id = uaa["clientid"]
    client_secret = uaa["clientsecret"]

    # Cabeceras y payload
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}

    print(f"Llamando a {url} ...")

    resp = requests.post(url, data=data, headers=headers, auth=(client_id, client_secret))
    resp.raise_for_status()

    token_data = resp.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise ValueError("No se encontró access_token en la respuesta")

    print("\n=== TOKEN OBTENIDO ===\n")
    print(access_token)
    return access_token

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python get_token.py process-automation-service-binding.json")
        sys.exit(1)

    get_token_from_binding(sys.argv[1])

from dotenv import load_dotenv
import os
import json
import requests
from typing import Optional

load_dotenv()

BASE_URL = "https://viewmondo.com"
URL_TOKEN = f"{BASE_URL}/Token"
API_URL = f"{BASE_URL}/api/v1/GetStationSensors"
STATION_ID = "6e8b98a5-cef4-4399-b29d-eeec07eadf56"

USER = os.getenv("MARWIS_USUARIO")
PASS = os.getenv("MARWIS_PASSWORD")

BASE_DIR = os.path.dirname(__file__)
OUTPUT_JSON = os.path.join(BASE_DIR, "station_data.json")


def _get_bearer_token(username: str, password: str) -> str:
    """
    Obtiene un Bearer token contra /Token usando grant_type=password.
    Retorna el string del access_token.
    """
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    resp = requests.post(URL_TOKEN, data=data, headers=headers, timeout=30)
    resp.raise_for_status()

    payload = resp.json()
    token: Optional[str] = (
        payload.get("access_token")
        or payload.get("accessToken")
        or payload.get("token")
    )
    if not token:
        raise RuntimeError(f"No se recibió access_token en la respuesta de /Token: {payload}")
    return token


def run_marwis() -> list:
    """
    Obtiene un token Bearer y llama a GetStationSensors con Authorization: Bearer.
    Guarda la respuesta (lista de sensores) en station_data.json y retorna la lista.
    """
    if not USER or not PASS:
        raise RuntimeError("Variables de entorno MARWIS_USUARIO y/o MARWIS_PASSWORD no configuradas")

    # 1) Obtener token
    token = _get_bearer_token(USER, PASS)

    # 2) Consumir API con Bearer token
    params = {"station_id": STATION_ID}
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    resp = requests.get(API_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    if not isinstance(data, list):
        raise RuntimeError("La API no devolvió una lista de sensores")

    # 3) Guardar JSON en backend/station_data.json
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return data


if __name__ == "__main__":
    try:
        sensores = run_marwis()
        print(f"✅ {len(sensores)} sensores guardados en {OUTPUT_JSON}")
    except Exception as e:
        print(f"❌ Error ejecutando consulta: {e}")

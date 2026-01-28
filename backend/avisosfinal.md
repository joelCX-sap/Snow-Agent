# Sistema de Avisos MVP1 SNOW - Documento Final
## Lógica Completa de Generación de Avisos

---

## 📋 Resumen Ejecutivo

El sistema MVP1 SNOW genera avisos automáticos para operaciones aeroportuarias de control de hielo y nieve. Este documento describe **cuándo y cómo** se genera cada tipo de aviso.

---

## 🔄 Flujo Completo del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLUJO DE DATOS MVP1 SNOW                            │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
     │   USUARIO   │         │  OPEN-METEO │         │   MARWIS    │
     │  (Consulta) │         │    (API)    │         │  (Estación) │
     └──────┬──────┘         └──────┬──────┘         └──────┬──────┘
            │                       │                       │
            │ 1. Click "Consultar"  │                       │
            ▼                       │                       │
     ┌─────────────┐               │                       │
     │    UI Web   │               │                       │
     │ (consulta-  │               │                       │
     │   clima)    │               │                       │
     └──────┬──────┘               │                       │
            │                       │                       │
            │ 2. GET /weather       │                       │
            ▼                       │                       │
     ┌─────────────┐               │                       │
     │  FastAPI    │◄──────────────┤                       │
     │  Backend    │ 3. Obtener    │                       │
     │             │    pronóstico │                       │
     │             │◄──────────────┼───────────────────────┤
     │             │               │ 4. Leer temp. pista   │
     └──────┬──────┘               │    (station_data.json)│
            │                       │                       │
            │ 5. Evaluar avisos    │                       │
            ▼                       │                       │
     ┌─────────────┐               │                       │
     │  avisos.py  │               │                       │
     │ (Rule       │               │                       │
     │  Engine)    │               │                       │
     └──────┬──────┘               │                       │
            │                       │                       │
            │ 6. Avisos generados  │                       │
            ▼                       │                       │
     ┌─────────────┐               │                       │
     │   UI Web    │               │                       │
     │ (Mostrar    │               │                       │
     │  resultados)│               │                       │
     └─────────────┘               │                       │
```

---

## 📡 Fuentes de Datos

### 1. Open-Meteo (API Meteorológica)

**Endpoint**: `https://api.open-meteo.com/v1/forecast`

**Datos obtenidos**:
| Campo | Descripción | Uso |
|-------|-------------|-----|
| `temperature_2m` | Temperatura ambiente actual | AVISO_0, TABLA 1, TABLA 3 |
| `relative_humidity_2m` | Humedad relativa | TABLA 1, TABLA 3 |
| `wind_speed_10m` | Velocidad del viento | TABLA 1, TABLA 3 |
| `precipitation` | Precipitación actual | Informativo |
| `snowfall` | Nevadas actuales | Informativo |
| `rain` | Lluvia actual | Informativo |

**Cálculo de probabilidades**:
- `prob_lluvia`: % de horas con lluvia en próximas 4h
- `prob_nieve`: % de horas con nieve en próximas 4h + factor temperatura

**Ubicaciones configuradas**:
- Río Grande (-53.7877, -67.7097)
- Amsterdam Schiphol (52.374, 4.8897)
- Bariloche (-41.1335, -71.3103)
- New York JFK (40.6413, -73.7781)

---

### 2. MARWIS (Sensor de Pista)

**Archivo**: `backend/station_data.json`

**Datos buscados**:
- `surface_temp` → Temperatura de superficie de pista
- `road_temp` → Temperatura de pavimento
- `pista_temp` → Temperatura de pista
- `pavement_temp` → Temperatura de pavimento

**Fallback**: Si MARWIS no está disponible, se usa **-0.1°C** como valor hardcoded.

**Actualización de datos MARWIS**:
- Se lee el archivo `station_data.json` en cada consulta
- El archivo debe ser actualizado por el sistema de adquisición de datos del aeropuerto
- Formato esperado: JSON con array de mediciones

---

## 🚨 Tipos de Avisos

### AVISO_0: Temperatura Bajo Cero - Riesgo Crítico de Hielo

**Prioridad**: 0 (MÁXIMA)

**Condición**:
```
Temperatura ambiente < 0°C
```

**Cuándo se genera**:
- Cuando la temperatura del aire está bajo el punto de congelación
- Es el aviso más crítico y **BLOQUEA TODOS LOS DEMÁS**

**Códigos SAP**:
- QMART: O1 (Operaciones Aeropuerto)
- QMCOD: Y116
- QMGRP: YB-DERR1 (Operativo Nieve)
- TPLNR: RGA-LADAIR

**Tareas a ejecutar**:
1. ⚠️ ALERTA CRÍTICA: Temperatura bajo cero detectada
2. Activación INMEDIATA del protocolo de emergencia por hielo
3. Inspección urgente de todas las superficies pavimentadas
4. Aplicación preventiva de descongelantes (urea/glicol)
5. Verificar condiciones de pista con MARWIS cada 15 minutos
6. Comunicación inmediata con torre de control
7. Posicionar equipos de control de hielo en standby
8. Evaluar restricción de operaciones si es necesario
9. Notificar a todas las áreas operativas
10. Documentar todas las acciones tomadas

---

### AVISO_1: Umbral de Alerta

**Prioridad**: 3

**Condiciones (TABLA 1)** - TODAS deben cumplirse:

| Variable | Condición | Ejemplo |
|----------|-----------|---------|
| T_ambiente | 3 < T ≤ 6°C | 4.5°C ✓ |
| T_rocío | ≥ T_amb - 3 | Si T=4.5°C, rocío ≥ 1.5°C |
| T_pista | < 0°C | -0.5°C ✓ |
| Humedad | ≥ 56% | 65% ✓ |
| Viento | < 36 km/h | 20 km/h ✓ |

**Cuándo se genera**:
- Temperatura ambiente en rango de pre-congelamiento (3-6°C)
- Pista ya está bajo cero
- Alta humedad con bajo viento (condiciones de condensación)
- **Solo si NO hay avisos de mayor prioridad activos**

**Códigos SAP**:
- QMART: O1
- QMCOD: Y110
- QMGRP: YB-DERR1
- TPLNR: RGA-LADAIR

**Tareas a ejecutar**:
1. Monitorear condiciones meteorológicas cada 2 horas
2. Verificar temperatura de pista mediante MARWIS
3. Notificar al personal de operaciones
4. Preparar equipos de control de hielo/nieve
5. Revisar stock de descongelantes (urea/glicol)

---

### AVISO_5: Alerta de Lluvia

**Prioridad**: 2

**Condiciones**:
1. **TABLA 3 cumplida** (ver abajo)
2. **Probabilidad de lluvia ≥ 70%** en próximas 2 horas

**TABLA 3** - TODAS deben cumplirse:

| Variable | Condición | Ejemplo |
|----------|-----------|---------|
| T_ambiente | T ≤ 0°C | -0.5°C ✓ |
| T_rocío | ≥ T_amb - 1 | Si T=-0.5°C, rocío ≥ -1.5°C |
| T_pista | < 0°C | -1.0°C ✓ |
| Humedad | ≥ 63% | 70% ✓ |
| Viento | < 33 km/h | 28 km/h ✓ |

**Cuándo se genera**:
- Temperatura ambiente bajo cero
- Alta probabilidad de lluvia (puede congelarse al contacto = lluvia helada)
- **Solo si AVISO_0 no está activo**
- **Bloquea AVISO_1**

**Códigos SAP**:
- QMART: O1
- QMCOD: Y114
- QMGRP: YB-DERR1
- TPLNR: RGA-LADAIR

**Tareas a ejecutar**:
1. Preparar equipos de drenaje
2. Inspeccionar sistemas de evacuación de agua
3. Posicionar equipos de barrido
4. Monitorear acumulación de agua en pista
5. Evaluar condiciones de fricción
6. Coordinar con torre de control sobre estado de pista

---

### AVISO_6: Alerta de Nieve

**Prioridad**: 1

**Condiciones**:
1. **TABLA 3 cumplida** (misma que AVISO_5)
2. **Probabilidad de nieve ≥ 70%** en próximas 3 horas

**Cuándo se genera**:
- Temperatura ambiente bajo cero
- Alta probabilidad de nieve
- **Solo si AVISO_0 no está activo**
- **Bloquea AVISO_5 y AVISO_1**

**Códigos SAP**:
- QMART: O1
- QMCOD: Y115
- QMGRP: YB-DERR1
- TPLNR: RGA-LADAIR

**Tareas a ejecutar**:
1. Activar equipo completo de remoción de nieve
2. Aplicación preventiva de descongelantes
3. Posicionar tractores y equipos de remoción
4. Preparar stock de urea y glicol
5. Coordinar con meteorología para actualización continua
6. Planificar turnos extendidos de personal
7. Comunicar estado a torre de control

---

## 🔒 Reglas de Exclusión

### Matriz de Bloqueos

| Si está activo... | Entonces NO se genera... |
|-------------------|--------------------------|
| AVISO_0 (Temp<0) | AVISO_6, AVISO_5, AVISO_1 |
| AVISO_6 (Nieve) | AVISO_5, AVISO_1 |
| AVISO_5 (Lluvia) | AVISO_1 |
| AVISO_1 (Alerta) | - |

### Justificación

1. **AVISO_0 bloquea todos**: Si ya hay temperatura bajo cero, el protocolo de emergencia es el más completo. Los otros avisos serían redundantes.

2. **AVISO_6 bloquea AVISO_5**: Si hay nieve prevista, el protocolo de nieve incluye todo lo necesario. La lluvia es secundaria.

3. **AVISO_5 bloquea AVISO_1**: La alerta de lluvia con hielo es más severa que el umbral de alerta básico.

---

## 📊 Escenarios de Ejemplo

### Escenario 1: Día de Invierno Frío

```json
{
  "temperatura_actual": -5.0,
  "punto_rocio": -7.0,
  "humedad": 80,
  "viento": 20,
  "pronostico": {
    "prob_lluvia": 10,
    "prob_nieve": 45
  }
}
```

**Evaluación**:
- AVISO_0: -5°C < 0°C → ✅ **ACTIVO**
- AVISO_6: prob_nieve 45% < 70% → ❌ (además sería excluido)
- AVISO_5: prob_lluvia 10% < 70% → ❌
- AVISO_1: temp -5°C no está en 3-6°C → ❌

**Resultado**: `[AVISO_0]`

---

### Escenario 2: Tormenta de Nieve Inminente

```json
{
  "temperatura_actual": -1.0,
  "punto_rocio": -1.5,
  "temperatura_pista": -2.0,
  "humedad": 75,
  "viento": 25,
  "pronostico": {
    "prob_lluvia": 20,
    "prob_nieve": 85
  }
}
```

**Evaluación**:
- AVISO_0: -1°C < 0°C → ✅ **ACTIVO**
- AVISO_6: TABLA 3 OK + nieve 85% → ✅ pero **EXCLUIDO por AVISO_0**
- AVISO_5: prob_lluvia 20% < 70% → ❌
- AVISO_1: temp -1°C no está en 3-6°C → ❌

**Resultado**: `[AVISO_0]`

**Log**: "AVISO_6 EXCLUIDO: Bloqueado por AVISO_0"

---

### Escenario 3: Condiciones de Pre-Congelamiento

```json
{
  "temperatura_actual": 4.5,
  "punto_rocio": 2.0,
  "temperatura_pista": -0.5,
  "humedad": 65,
  "viento": 20,
  "pronostico": {
    "prob_lluvia": 30,
    "prob_nieve": 10
  }
}
```

**Evaluación TABLA 1**:
- T_ambiente: 4.5°C → 3 < 4.5 ≤ 6 ✅
- T_rocío: 2.0°C ≥ (4.5 - 3) = 1.5°C ✅
- T_pista: -0.5°C < 0 ✅
- Humedad: 65% ≥ 56% ✅
- Viento: 20 km/h < 36 km/h ✅

**Resultado**: `[AVISO_1]`

---

### Escenario 4: Lluvia Helada Prevista

```json
{
  "temperatura_actual": -0.3,
  "punto_rocio": -0.8,
  "temperatura_pista": -1.0,
  "humedad": 72,
  "viento": 28,
  "pronostico": {
    "prob_lluvia": 80,
    "prob_nieve": 25
  }
}
```

**Evaluación**:
- AVISO_0: -0.3°C < 0°C → ✅ **ACTIVO**
- AVISO_5: TABLA 3 OK + lluvia 80% → ✅ pero **EXCLUIDO por AVISO_0**
- AVISO_6: prob_nieve 25% < 70% → ❌
- AVISO_1: temp -0.3°C no está en 3-6°C → ❌

**Resultado**: `[AVISO_0]`

---

### Escenario 5: Día Normal (Sin Avisos)

```json
{
  "temperatura_actual": 12.0,
  "punto_rocio": 5.0,
  "temperatura_pista": 10.0,
  "humedad": 45,
  "viento": 15,
  "pronostico": {
    "prob_lluvia": 20,
    "prob_nieve": 0
  }
}
```

**Evaluación**:
- AVISO_0: 12°C ≥ 0°C → ❌
- AVISO_6: 12°C > 0°C → TABLA 3 falla → ❌
- AVISO_5: 12°C > 0°C → TABLA 3 falla → ❌
- AVISO_1: 12°C > 6°C → TABLA 1 falla → ❌

**Resultado**: `[]` (Sin avisos)

---

## 🖥️ Interfaz de Usuario

### Pantalla de Consulta de Clima

**Elementos mostrados**:
1. **Resumen del Clima**: Temperatura, humedad, viento, visibilidad
2. **Indicadores de Probabilidad**: 
   - 🌧️ Probabilidad de Lluvia (tarjeta azul)
   - ❄️ Probabilidad de Nieve (tarjeta índigo)
3. **Forecast Próximas Horas**: 4 tarjetas con datos por hora
4. **Avisos Generados**: Lista con códigos SAP y tareas
5. **Procedimientos LLM**: Respuesta del asistente RAG

### Colores de Probabilidad

| Probabilidad | Color | Descripción |
|--------------|-------|-------------|
| ≥ 70% | Intenso | Alta probabilidad |
| 40-69% | Medio | Probabilidad moderada |
| 1-39% | Suave | Baja probabilidad |
| 0% | Gris | Sin probabilidad |

---

## 📁 Archivos del Sistema

```
backend/
├── avisos.py              # Motor de reglas (Rule Engine)
├── avisos_v2.md           # Documentación técnica
├── avisosfinal.md         # Este documento
├── weather_openmeteo.py   # Integración con Open-Meteo
├── marwis.py              # Utilidades MARWIS
├── station_data.json      # Datos de sensores MARWIS
├── api.py                 # Endpoints FastAPI
└── fastapi_app.py         # Aplicación principal

ui/src/
├── pages/consulta-clima/
│   ├── consulta-clima.html  # Vista de consulta
│   └── consulta-clima.js    # Lógica de UI
└── services/
    └── api.js              # Llamadas al backend
```

---

## 🔧 Configuración Requerida

### Variables de Entorno

```env
# Backend
OPENAI_API_KEY=...          # Para RAG con procedimientos
SAP_API_URL=...             # URL de SAP PM (opcional)
```

### Dependencias Python

```
openmeteo-requests
pandas
pytz
requests-cache
retry-requests
```

---

## 📝 Notas de Implementación

1. **Determinismo**: El sistema NO usa IA para decidir avisos. Las reglas son explícitas y auditables.

2. **Fallback MARWIS**: Si los datos de MARWIS no están disponibles, se usa -0.1°C para garantizar que el sistema siga funcionando.

3. **Exclusiones**: Las reglas de exclusión son declarativas (definidas como datos, no código).

4. **Logging**: Cada decisión se registra con razón específica para auditoría.

5. **Umbral 70%**: Para avisos de precipitación (lluvia/nieve), se requiere probabilidad ≥70% para evitar falsos positivos.

---

*Documento generado para el sistema MVP1 SNOW - Operaciones Aeroportuarias de Control de Hielo y Nieve*
*Versión: 2.0.0 | Fecha: 2026-01-28*
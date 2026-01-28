# Módulo de Generación de Avisos - MVP1 SNOW
## Documentación Técnica v2.0.0

---

## 1. Arquitectura del Módulo

### 1.1 Visión General

El módulo `avisos.py` implementa un **rule engine determinístico** para la generación de avisos operativos en aeropuertos. Está diseñado para ser:

- **Determinístico**: Dado el mismo input, siempre produce el mismo output
- **Auditable**: Cada decisión se registra con su razón
- **Mantenible**: Reglas declarativas separadas de la lógica
- **Safety-Critical**: No usa IA/ML, solo reglas explícitas

### 1.2 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ENTRADA DE DATOS                             │
├─────────────────────────────────────────────────────────────────────┤
│  Open-Meteo API     │     MARWIS Station     │     SAP PM           │
│  (pronóstico)       │     (temp. pista)      │     (códigos)        │
└─────────┬───────────┴──────────┬─────────────┴──────────────────────┘
          │                      │
          ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   NORMALIZACIÓN DE DATOS                            │
│  normalizar_datos_entrada() → DatosMeteorologicos                   │
└─────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   EVALUACIÓN DE TABLAS                              │
├─────────────────────────────────────────────────────────────────────┤
│  TABLA 1 (AVISO_1)  │  TABLA 3 (AVISO_5/6)  │  AVISO_0 (temp<0)    │
│  evaluar_tabla_1()  │  evaluar_tabla_3()    │  evaluar_aviso_0()   │
└─────────────────────┴─────────────────────────┴─────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   REGLAS DE EXCLUSIÓN                               │
│  aplicar_reglas_exclusion() → Lista de avisos finales               │
└─────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   GENERACIÓN DE AVISOS                              │
│  generar_avisos() → Dict con avisos SAP PM                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Estructura de Archivos

```
backend/
├── avisos.py           # Módulo principal (este documento)
├── station_data.json   # Datos de MARWIS (temperatura de pista)
└── avisos_v2.md        # Documentación técnica
```

---

## 2. Flujo de Decisión Paso a Paso

### 2.1 Proceso Completo

```
1. ENTRADA
   └── Recibir condiciones_clima (Dict)

2. NORMALIZACIÓN
   ├── Extraer valores numéricos
   ├── Manejar None, "N/A", strings
   ├── Obtener temp_pista desde MARWIS o usar -0.1°C
   └── Crear DatosMeteorologicos

3. EVALUACIÓN
   ├── AVISO_0: temp_ambiente < 0°C
   ├── AVISO_6: TABLA 3 + prob_nieve ≥ 70%
   ├── AVISO_5: TABLA 3 + prob_lluvia ≥ 70%
   └── AVISO_1: TABLA 1

4. EXCLUSIONES
   ├── AVISO_0 activo → excluir AVISO_6, AVISO_5, AVISO_1
   ├── AVISO_6 activo → excluir AVISO_5, AVISO_1
   ├── AVISO_5 activo → excluir AVISO_1
   └── AVISO_1 solo si ninguno superior

5. SALIDA
   └── Lista de avisos con códigos SAP PM
```

### 2.2 Diagrama de Flujo de Decisión

```
                    ┌─────────────────┐
                    │ Datos de Entrada│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Normalizar     │
                    │  Datos          │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ temp_amb < 0°C? │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                   SÍ                NO
                    │                 │
                    ▼                 ▼
           ┌────────────────┐ ┌────────────────────┐
           │ AVISO_0 ACTIVO │ │ Evaluar TABLA 3    │
           │ (Excluir todos)│ │ (para AVISO 5 y 6) │
           └────────────────┘ └─────────┬──────────┘
                                        │
                              ┌─────────┴─────────┐
                              │                   │
                           CUMPLE             NO CUMPLE
                              │                   │
                              ▼                   ▼
                    ┌──────────────────┐  ┌────────────────┐
                    │ prob_nieve ≥70%? │  │ Evaluar TABLA 1│
                    └────────┬─────────┘  │ (para AVISO_1) │
                             │            └────────────────┘
                    ┌────────┴────────┐
                   SÍ                NO
                    │                 │
                    ▼                 ▼
           ┌────────────────┐ ┌────────────────┐
           │ AVISO_6 ACTIVO │ │ prob_lluvia    │
           │ (Excluir 5,1)  │ │ ≥70%?          │
           └────────────────┘ └───────┬────────┘
                                      │
                             ┌────────┴────────┐
                            SÍ                NO
                             │                 │
                             ▼                 ▼
                    ┌────────────────┐ ┌────────────────┐
                    │ AVISO_5 ACTIVO │ │ Sin aviso de   │
                    │ (Excluir 1)    │ │ precipitación  │
                    └────────────────┘ └────────────────┘
```

---

## 3. Implementación de Tablas

### 3.1 TABLA 1 – Umbral de Alerta (AVISO_1)

**Propósito**: Detectar condiciones de riesgo moderado que requieren preparación preventiva.

| Variable | Condición | Unidad | Descripción |
|----------|-----------|--------|-------------|
| T_ambiente | 3 < T ≤ 6 | °C | Rango crítico pre-congelamiento |
| T_rocío | ≥ T_amb - 3 | °C | Proximidad a punto de condensación |
| T_pista | < 0 | °C | Pista en riesgo de congelamiento |
| Humedad | ≥ 56 | % | Humedad relativa alta |
| Viento | < 36 | km/h | Viento moderado |

**Implementación en código**:

```python
def evaluar_tabla_1(datos: DatosMeteorologicos) -> ResultadoEvaluacion:
    detalles = {
        'temperatura_ambiente': {
            'valor': datos.temperatura_ambiente,
            'condicion': '3 < T ≤ 6',
            'cumple': 3 < datos.temperatura_ambiente <= 6
        },
        'temperatura_rocio': {
            'valor': datos.temperatura_rocio,
            'condicion': f'≥ {datos.temperatura_ambiente - 3:.1f}',
            'cumple': datos.temperatura_rocio >= (datos.temperatura_ambiente - 3)
        },
        # ... resto de condiciones
    }
    todas_cumplen = all(d['cumple'] for d in detalles.values())
```

### 3.2 TABLA 3 – Condiciones Base (AVISO_5 y AVISO_6)

**Propósito**: Establecer el escenario base para precipitación invernal.

| Variable | Condición | Unidad | Descripción |
|----------|-----------|--------|-------------|
| T_ambiente | T ≤ 0 | °C | Temperatura bajo cero |
| T_rocío | ≥ T_amb - 1 | °C | Alta probabilidad de condensación |
| T_pista | < 0 | °C | Pista congelada o en riesgo |
| Humedad | ≥ 63 | % | Humedad relativa muy alta |
| Viento | < 33 | km/h | Viento bajo-moderado |

**Requisitos adicionales**:

- **AVISO_5 (Lluvia)**: TABLA 3 + Pronóstico lluvia 2h ≥ 70%
- **AVISO_6 (Nieve)**: TABLA 3 + Pronóstico nieve 3h ≥ 70%

---

## 4. Reglas de Prioridad y Exclusión

### 4.1 Jerarquía de Prioridades

```
Prioridad 0 (MÁXIMA): AVISO_0 - Temperatura Bajo Cero
Prioridad 1:          AVISO_6 - Alerta de Nieve
Prioridad 2:          AVISO_5 - Alerta de Lluvia
Prioridad 3:          AVISO_1 - Umbral de Alerta
```

### 4.2 Matriz de Exclusiones

| Aviso Activo | Bloquea |
|--------------|---------|
| AVISO_0 | AVISO_6, AVISO_5, AVISO_1 |
| AVISO_6 | AVISO_5, AVISO_1 |
| AVISO_5 | AVISO_1 |
| AVISO_1 | - |

### 4.3 Implementación Declarativa

```python
REGLAS_EXCLUSION: Dict[TipoAviso, List[TipoAviso]] = {
    TipoAviso.AVISO_0: [TipoAviso.AVISO_6, TipoAviso.AVISO_5, TipoAviso.AVISO_1],
    TipoAviso.AVISO_6: [TipoAviso.AVISO_5, TipoAviso.AVISO_1],
    TipoAviso.AVISO_5: [TipoAviso.AVISO_1],
    TipoAviso.AVISO_1: [],
}
```

### 4.4 Justificación de Exclusiones

1. **AVISO_0 bloquea todos**: Cuando la temperatura está bajo cero, las condiciones ya son críticas. Los otros avisos serían redundantes o contraproducentes.

2. **AVISO_6 bloquea AVISO_5**: Si hay nieve, la lluvia es secundaria. El protocolo de nieve es más completo.

3. **AVISO_6 bloquea AVISO_1**: El aviso de nieve implica condiciones más severas que el umbral de alerta.

4. **AVISO_5 bloquea AVISO_1**: La alerta de lluvia con hielo tiene mayor prioridad operativa.

---

## 5. Integración con Otros Sistemas

### 5.1 MARWIS (Sensor de Pista)

**Flujo de datos**:

```
MARWIS Sensor → station_data.json → obtener_temperatura_pista_marwis()
```

**Estrategia de fallback**:

```python
if marwis_data is not None:
    datos.temperatura_pista = marwis_data
    datos.fuente_temp_pista = "MARWIS"
else:
    datos.temperatura_pista = TEMP_PISTA_DEFAULT  # -0.1°C
    datos.fuente_temp_pista = "DEFAULT"
```

**Sensores buscados**:
- `surface_temp`
- `road_temp`
- `pista_temp`
- `pavement_temp`

### 5.2 Forecast Meteorológico (Open-Meteo)

**Datos requeridos**:

| Campo | Uso | Aviso |
|-------|-----|-------|
| `prob_lluvia` | Pronóstico 2h | AVISO_5 |
| `prob_nieve` | Pronóstico 3h | AVISO_6 |
| `temperatura_actual` | Todos los avisos | AVISO_0, 1, 5, 6 |
| `punto_rocio` | Tablas 1 y 3 | AVISO_1, 5, 6 |
| `humedad` | Tablas 1 y 3 | AVISO_1, 5, 6 |
| `viento` | Tablas 1 y 3 | AVISO_1, 5, 6 |

### 5.3 SAP PM (Mantenimiento)

**Códigos generados por aviso**:

| Aviso | QMART | QMCOD | QMGRP | TPLNR |
|-------|-------|-------|-------|-------|
| AVISO_0 | O1 | Y116 | YB-DERR1 | RGA-LADAIR |
| AVISO_1 | O1 | Y110 | YB-DERR1 | RGA-LADAIR |
| AVISO_5 | O1 | Y114 | YB-DERR1 | RGA-LADAIR |
| AVISO_6 | O1 | Y115 | YB-DERR1 | RGA-LADAIR |

---

## 6. Escenarios de Ejemplo

### 6.1 Escenario: Ola de Frío

**Condiciones**:
```json
{
  "temperatura_actual": -5.0,
  "punto_rocio": -7.0,
  "humedad": 80,
  "viento": 20,
  "pronostico": {"prob_lluvia": 10, "prob_nieve": 60}
}
```

**Evaluación**:
1. AVISO_0: temp_amb (-5°C) < 0°C → **ACTIVO**
2. AVISO_6: TABLA 3 cumplida pero prob_nieve (60%) < 70% → No activo
3. AVISO_5: TABLA 3 cumplida pero prob_lluvia (10%) < 70% → No activo
4. AVISO_1: temp_amb (-5°C) no está en rango 3-6 → No activo

**Resultado**: `[AVISO_0]`

**Razón**: La temperatura bajo cero activa el aviso crítico. Aunque la probabilidad de nieve es 60%, no alcanza el umbral de 70% para AVISO_6. De todos modos, AVISO_0 bloquearía los demás.

### 6.2 Escenario: Tormenta de Nieve Inminente

**Condiciones**:
```json
{
  "temperatura_actual": -1.0,
  "punto_rocio": -1.5,
  "temperatura_pista": -2.0,
  "humedad": 75,
  "viento": 25,
  "pronostico": {"prob_lluvia": 20, "prob_nieve": 85}
}
```

**Evaluación**:
1. AVISO_0: temp_amb (-1°C) < 0°C → **ACTIVO**
2. AVISO_6: TABLA 3 cumplida + prob_nieve (85%) ≥ 70% → Candidato pero **EXCLUIDO por AVISO_0**

**Resultado**: `[AVISO_0]`

**Log de exclusión**: "AVISO_6 EXCLUIDO: Bloqueado por AVISO_0 (regla de exclusión declarativa)"

### 6.3 Escenario: Umbral de Alerta

**Condiciones**:
```json
{
  "temperatura_actual": 4.5,
  "punto_rocio": 2.0,
  "temperatura_pista": -0.5,
  "humedad": 65,
  "viento": 20,
  "pronostico": {"prob_lluvia": 30, "prob_nieve": 10}
}
```

**Evaluación TABLA 1**:
- temp_amb: 4.5°C → 3 < 4.5 ≤ 6 ✓
- temp_rocio: 2.0°C ≥ (4.5 - 3) = 1.5°C ✓
- temp_pista: -0.5°C < 0 ✓
- humedad: 65% ≥ 56% ✓
- viento: 20 km/h < 36 km/h ✓

**Resultado**: `[AVISO_1]`

### 6.4 Escenario: Lluvia con Riesgo de Hielo

**Condiciones**:
```json
{
  "temperatura_actual": -0.5,
  "punto_rocio": -1.0,
  "temperatura_pista": -1.5,
  "humedad": 70,
  "viento": 28,
  "pronostico": {"prob_lluvia": 75, "prob_nieve": 30}
}
```

**Evaluación**:
1. AVISO_0: temp_amb (-0.5°C) < 0°C → **ACTIVO**
2. AVISO_5: TABLA 3 cumplida + prob_lluvia (75%) ≥ 70% → Candidato pero **EXCLUIDO por AVISO_0**

**Resultado**: `[AVISO_0]`

---

## 7. Validación y Testing

### 7.1 Tests Incorporados

El módulo incluye tests ejecutables:

```bash
python avisos.py
```

### 7.2 Casos de Prueba Recomendados

| Caso | Descripción | Resultado Esperado |
|------|-------------|-------------------|
| temp_amb = -5°C | Temperatura bajo cero | AVISO_0 |
| temp_amb = 4°C, TABLA 1 OK | Umbral de alerta | AVISO_1 |
| temp_amb = -1°C, nieve 85% | Nieve inminente | AVISO_0 (bloquea 6) |
| temp_amb = -1°C, nieve 50% | Nieve improbable | AVISO_0 |
| temp_amb = 10°C | Sin riesgo | [] |
| datos = None | Sin datos | error |

---

## 8. Mantenimiento y Extensibilidad

### 8.1 Agregar un Nuevo Aviso

1. Agregar entrada en `TipoAviso` enum con prioridad
2. Agregar configuración SAP en `AVISOS_CONFIG`
3. Agregar reglas de exclusión en `REGLAS_EXCLUSION`
4. Implementar función `evaluar_aviso_N()`
5. Agregar tareas en `obtener_tareas_procedimiento()`

### 8.2 Modificar Umbrales

Los umbrales están definidos explícitamente en las funciones de evaluación de tablas:

```python
# TABLA 1
'cumple': 3 < datos.temperatura_ambiente <= 6  # Modificar aquí

# TABLA 3
'cumple': datos.temperatura_ambiente <= 0  # Modificar aquí
```

### 8.3 Logging y Auditoría

Todos los logs usan el formato:

```
NIVEL: [COMPONENTE] Mensaje descriptivo
```

Ejemplo:
```
INFO: Evaluación AVISO_0: AVISO_0 ACTIVO: Temperatura ambiente -2.5°C < 0°C
WARNING: AVISO_6 EXCLUIDO: Bloqueado por AVISO_0 (regla de exclusión declarativa)
```

---

## 9. Glosario

| Término | Definición |
|---------|------------|
| **MARWIS** | Mobile Advanced Road Weather Information System |
| **T_ambiente** | Temperatura del aire ambiente |
| **T_rocío** | Temperatura de punto de rocío |
| **T_pista** | Temperatura de la superficie de pista |
| **SAP PM** | SAP Plant Maintenance |
| **QMART** | Clase de aviso SAP |
| **QMCOD** | Código de modo de fallo SAP |
| **QMGRP** | Grupo de modo de fallo SAP |
| **TPLNR** | Ubicación técnica SAP |

---

## 10. Historial de Cambios

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 2.0.0 | 2026-01-28 | Refactorización completa: tablas explícitas, exclusiones declarativas, dataclasses |
| 1.0.0 | 2026-01-27 | Versión inicial |

---

*Documento generado para el sistema MVP1 SNOW - Operaciones Aeroportuarias de Control de Hielo y Nieve*
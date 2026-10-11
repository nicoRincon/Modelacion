"""
Simulación de eventos discretos de un peaje con dos taquillas.

Sigue la misma lógica del ejemplo "Proceso de Inspección" (Excel):
  - Tiempo entre llegadas  -> exponencial   E = -media * ln(1 - r)
  - Tiempo de pago         -> normal        NORM.INV(r, media, desv)
  - Tiempo de arranque     -> normal        NORM.INV(r, media, desv)
  - Tiempo de llegada      -> acumulado del tiempo entre llegadas
  - Inicio de atención     -> MAX(llegada, momento en que se libera una taquilla)
  - Promedio móvil         -> promedio acumulado del tiempo en el sistema

Todos los tiempos están en minutos.
"""
import math
import random
from statistics import NormalDist, mean, stdev

# --------------------------------------------------------------------------
# Parámetros por defecto (se pueden cambiar desde el formulario de Flask)
# --------------------------------------------------------------------------
# λ = 2.083 carros/min viene del ajuste Poisson de la entrega anterior
# (Mock Traffic Data, caseta 1). Si las llegadas por minuto son Poisson(λ),
# el tiempo entre llegadas es exponencial con media 1/λ = 0.48 min.
LAMBDA_OBSERVADO = 2.083

PARAMETROS_DEFECTO = {
    "n_carros": 1000,         # carros por corrida (≈ 8 horas de operación)
    "n_taquillas": 2,         # situación actual
    "media_llegadas": 0.48,   # min/carro  (exponencial, 1/λ)
    "media_pago": 1.0,        # min        (normal)
    "desv_pago": 0.2,
    "media_arranque": 0.3,    # min        (normal)
    "desv_arranque": 0.05,
    "semilla": 2026,          # entero para resultados reproducibles
}

# Tabla de eventos (equivalente a la diapositiva "Tabla de Eventos")
TABLA_EVENTOS = {
    "Variable de estado": "Tiempo en el sistema del peaje",
    "Entidades": ["Carros"],
    "Eventos": ["Llegada del carro (2)", "Salida del carro: fin de pago + arranque (7)"],
    "Evento secundario": ["Inicio de atención en la taquilla (4)"],
    "Actividades": ["Tiempo entre llegadas (1)", "Tiempo de pago (5)", "Tiempo de arranque (6)"],
}

# Columnas de la tabla de simulación: (clave, encabezado)
COLUMNAS = [
    ("carro", "Carro"),
    ("entre_llegadas", "Tiempo entre llegadas (1)"),
    ("llegada", "Llegada (2)"),
    ("taquilla", "Taquilla (3)"),
    ("inicio", "Inicio de atención (4)"),
    ("t_pago", "Tiempo de pago (5)"),
    ("t_arranque", "Tiempo de arranque (6)"),
    ("salida", "Salida (7)"),
    ("t_espera", "Tiempo en espera (8)"),
    ("t_sistema", "Tiempo en el sistema (9)"),
    ("promedio", "Promedio móvil (10)"),
]


# --------------------------------------------------------------------------
# Generadores de variables aleatorias
# --------------------------------------------------------------------------
def _uniforme(rng):
    """Número aleatorio r en (0, 1), equivalente a RAND()/ALEATORIO()."""
    r = rng.random()
    while r == 0.0:
        r = rng.random()
    return r


def generar_exponencial(media, r):
    """Método de la transformada inversa: E = -media * ln(1 - r)."""
    return -media * math.log(1.0 - r)


def generar_normal(media, desv, r):
    """Normal acumulada inversa, equivalente a NORM.INV(r, media, desv)."""
    return NormalDist(mu=media, sigma=desv).inv_cdf(r)


# --------------------------------------------------------------------------
# Simulación de una corrida
# --------------------------------------------------------------------------
def simular_peaje(n_carros=1000, n_taquillas=2, media_llegadas=0.48,
                  media_pago=1.0, desv_pago=0.2,
                  media_arranque=0.3, desv_arranque=0.05,
                  semilla=None):
    """
    Simula n_carros pasando por el peaje y devuelve la lista de filas
    (una por carro) con las columnas definidas en COLUMNAS.

    Regla de asignación: el carro entra a la taquilla que se libera primero
    (cola única FIFO). Una taquilla queda ocupada mientras el carro paga y
    arranca; apenas arranca, la taquilla puede atender al siguiente.
    """
    rng = random.Random(semilla)
    libre_en = [0.0] * n_taquillas      # momento en que cada taquilla se libera
    filas = []
    llegada = 0.0
    suma_sistema = 0.0

    for i in range(1, n_carros + 1):
        # (1) tiempo entre llegadas y (2) llegada = acumulado
        entre = generar_exponencial(media_llegadas, _uniforme(rng))
        llegada += entre

        # (3) taquilla que se libera primero (empate -> la de menor número)
        k = min(range(n_taquillas), key=lambda j: libre_en[j])

        # (4) inicio de atención = MAX(llegada, liberación de la taquilla)
        inicio = max(llegada, libre_en[k])

        # (5) y (6) tiempos de pago y arranque (se evita que sean <= 0)
        t_pago = max(0.05, generar_normal(media_pago, desv_pago, _uniforme(rng)))
        t_arranque = max(0.02, generar_normal(media_arranque, desv_arranque, _uniforme(rng)))

        # (7) salida del carro
        salida = inicio + t_pago + t_arranque
        libre_en[k] = salida

        # (8) espera y (9) tiempo en el sistema
        t_espera = inicio - llegada
        t_sistema = salida - llegada

        # (10) promedio móvil del tiempo en el sistema
        suma_sistema += t_sistema
        promedio = suma_sistema / i

        filas.append({
            "carro": i,
            "entre_llegadas": entre,
            "llegada": llegada,
            "taquilla": k + 1,
            "inicio": inicio,
            "t_pago": t_pago,
            "t_arranque": t_arranque,
            "salida": salida,
            "t_espera": t_espera,
            "t_sistema": t_sistema,
            "promedio": promedio,
        })
    return filas


# --------------------------------------------------------------------------
# Resumen de una corrida
# --------------------------------------------------------------------------
def calcular_resumen(filas, n_taquillas=2):
    """Indicadores de desempeño a partir de la tabla simulada."""
    if not filas:
        return {}
    n = len(filas)
    horizonte = max(f["salida"] for f in filas)
    ocupacion = [0.0] * n_taquillas
    atendidos = [0] * n_taquillas
    for f in filas:
        ocupacion[f["taquilla"] - 1] += f["t_pago"] + f["t_arranque"]
        atendidos[f["taquilla"] - 1] += 1

    esperaron = sum(1 for f in filas if f["t_espera"] > 1e-9)
    return {
        "promedio_sistema": mean(f["t_sistema"] for f in filas),
        "promedio_espera": mean(f["t_espera"] for f in filas),
        "max_espera": max(f["t_espera"] for f in filas),
        "pct_esperaron": 100.0 * esperaron / n,
        "duracion_total": horizonte,
        "taquillas": [
            {"numero": j + 1,
             "atendidos": atendidos[j],
             "utilizacion": 100.0 * ocupacion[j] / horizonte}
            for j in range(n_taquillas)
        ],
    }


# --------------------------------------------------------------------------
# Estado estable
# --------------------------------------------------------------------------
def detectar_estabilizacion(filas, tolerancia=0.02):
    """
    Devuelve el número de carro desde el cual el promedio móvil se queda
    dentro de ±tolerancia (2 % por defecto) de su valor final.
    Devuelve None si nunca se estabiliza (por ejemplo, si la fila crece sin parar).
    """
    if len(filas) < 10:
        return None
    final = filas[-1]["promedio"]
    margen = abs(final) * tolerancia
    punto = None
    for f in reversed(filas):
        if abs(f["promedio"] - final) <= margen:
            punto = f["carro"]
        else:
            break
    # Si solo "se estabiliza" en el último 10 % de la corrida, no es confiable
    if punto is None or punto > 0.9 * len(filas):
        return None
    return punto


def calcular_carga(media_llegadas, media_pago, media_arranque, n_taquillas):
    """
    Factor de carga = tiempo medio de servicio / (taquillas * tiempo entre llegadas).
    Si es >= 1 las taquillas no alcanzan y el sistema nunca se estabiliza.
    """
    return (media_pago + media_arranque) / (n_taquillas * media_llegadas)


# --------------------------------------------------------------------------
# Réplicas (el análisis estadístico está en Estadistica.py)
# --------------------------------------------------------------------------
def promedio_sin_calentamiento(filas, calentamiento):
    """Tiempo promedio en el sistema descartando los primeros carros (calentamiento)."""
    utiles = filas[calentamiento:] or filas
    return mean(f["t_sistema"] for f in utiles)


def replicar_simulacion(n_replicas=30, calentamiento=100, semilla=None, **params):
    """
    Repite la simulación n_replicas veces. Cada réplica usa su propia semilla
    entera (semilla, semilla+1, ...), así cualquier réplica se puede repetir.
    Si se comparan escenarios con la misma semilla, todos reciben los mismos
    números aleatorios (los mismos carros), lo que hace justa la comparación.

    Devuelve, por réplica, el tiempo promedio en el sistema y la espera promedio
    calculados sin los carros del calentamiento.
    """
    params = {k: v for k, v in {**PARAMETROS_DEFECTO, **params}.items() if k != "semilla"}
    base = semilla if semilla is not None else random.randrange(1, 10**6)
    replicas = []
    for k in range(n_replicas):
        filas = simular_peaje(semilla=base + k, **params)
        utiles = filas[calentamiento:] or filas
        replicas.append({
            "replica": k + 1,
            "semilla": base + k,
            "t_sistema": mean(f["t_sistema"] for f in utiles),
            "t_espera": mean(f["t_espera"] for f in utiles),
        })
    return replicas


def ejecutar(parametros=None):
    """Punto de entrada para Flask: devuelve filas, resumen y columnas."""
    p = {**PARAMETROS_DEFECTO, **(parametros or {})}
    filas = simular_peaje(**p)
    return {
        "parametros": p,
        "columnas": COLUMNAS,
        "filas": filas,
        "resumen": calcular_resumen(filas, p["n_taquillas"]),
        "estabilizacion": detectar_estabilizacion(filas),
        "carga": calcular_carga(p["media_llegadas"], p["media_pago"],
                                p["media_arranque"], p["n_taquillas"]),
        "tabla_eventos": TABLA_EVENTOS,
    }


if __name__ == "__main__":
    r = ejecutar({"n_carros": 10})
    for f in r["filas"]:
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in f.items()})
    print(r["resumen"])
    for c in (2, 3, 4):
        reps = replicar_simulacion(n_replicas=30, n_taquillas=c, semilla=2026)
        print(c, "taquillas:", round(mean(x["t_sistema"] for x in reps), 3), "min")

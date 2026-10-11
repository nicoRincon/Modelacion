"""
Diseño y ejecución del experimento (puntos 7 a 12 de la actividad).

Para cada escenario (número de taquillas) se corren r réplicas con las mismas
semillas, se analiza el tiempo promedio en el sistema y se comparan los
escenarios. Al final se busca el menor número de taquillas que cumple la meta.
"""
from itertools import combinations
from statistics import mean

from Estadistica import analizar, comparar_escenarios
from Modelacion import PARAMETROS_DEFECTO, calcular_carga, replicar_simulacion, simular_peaje

CONFIG_DEFECTO = {
    **PARAMETROS_DEFECTO,
    "taquillas": [2, 3, 4],   # escenarios: actual y propuestos
    "replicas": 30,           # r
    "calentamiento": 200,     # carros que se descartan al inicio (método de Welch)
    "alfa": 0.05,
    "meta": 2.0,              # min: nivel de servicio deseado
    "epsilon": 0.1,           # min: error permitido para la longitud de réplica
}

FACTORES_DEMANDA = [0.9, 1.0, 1.1, 1.2]   # sensibilidad: demanda −10 %, actual, +10 %, +20 %


def parametros_modelo(config, n_taquillas, factor_demanda=1.0):
    p = {k: config[k] for k in PARAMETROS_DEFECTO if k != "semilla"}
    p["n_taquillas"] = n_taquillas
    p["media_llegadas"] = config["media_llegadas"] / factor_demanda
    return p


def correr_escenario(config, c):
    p = parametros_modelo(config, c)
    replicas = replicar_simulacion(n_replicas=config["replicas"], calentamiento=config["calentamiento"],
                                   semilla=config["semilla"], **p)
    datos = [r["t_sistema"] for r in replicas]
    carga = calcular_carga(p["media_llegadas"], p["media_pago"], p["media_arranque"], c)
    a = analizar(datos, config["alfa"], config["meta"], config["epsilon"])
    ic_sup = a["ic"]["intervalo"][1]
    return {
        "c": c,
        "carga": carga,
        "estable": carga < 1,
        "replicas": replicas,
        "datos": datos,
        "espera_media": mean(r["t_espera"] for r in replicas),
        "welch": curva_welch(config, c),
        "cumple": a["meta"]["rechaza"] and ic_sup < config["meta"],
        **a,
    }


def curva_welch(config, c, bloque=50):
    """
    Método de Welch para elegir el calentamiento: promedio del tiempo en el
    sistema por bloques de carros (1–50, 51–100, ...) a lo largo de todas las
    réplicas. Donde la curva deja de subir termina el calentamiento.
    """
    p = parametros_modelo(config, c)
    corridas = [simular_peaje(semilla=config["semilla"] + k, **p) for k in range(config["replicas"])]
    return [mean(mean(f["t_sistema"] for f in corrida[i:i + bloque]) for corrida in corridas)
            for i in range(0, config["n_carros"], bloque)]


def sensibilidad(config):
    """Tiempo promedio en el sistema para cada combinación de taquillas y demanda."""
    tabla = []
    for factor in FACTORES_DEMANDA:
        fila = {"factor": factor, "lambda": factor / config["media_llegadas"], "valores": []}
        for c in config["taquillas"]:
            p = parametros_modelo(config, c, factor)
            reps = replicar_simulacion(n_replicas=config["replicas"], calentamiento=config["calentamiento"],
                                       semilla=config["semilla"], **p)
            w = mean(r["t_sistema"] for r in reps)
            fila["valores"].append({"c": c, "w": w, "cumple": w < config["meta"],
                                    "carga": calcular_carga(p["media_llegadas"], p["media_pago"], p["media_arranque"], c)})
        tabla.append(fila)
    return tabla


def ejecutar_experimento(config):
    escenarios = [correr_escenario(config, c) for c in config["taquillas"]]
    comparaciones = [
        {"a": a["c"], "b": b["c"], **comparar_escenarios(a["datos"], b["datos"], config["alfa"])}
        for a, b in combinations(escenarios, 2)
    ]
    cumplen = [e for e in escenarios if e["cumple"]]
    return {
        "escenarios": escenarios,
        "comparaciones": comparaciones,
        "sensibilidad": sensibilidad(config),
        "recomendado": cumplen[0] if cumplen else None,
        "actual": escenarios[0],
    }

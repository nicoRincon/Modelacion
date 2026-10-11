"""
Verificación y validación del modelo del peaje.

Verificación: ¿el modelo está bien implementado?
  - Se revisa, carro por carro, que se cumplan las relaciones lógico-matemáticas.
  - Se comprueba que las variables aleatorias generadas tengan la media y la
    distribución que se definieron (prueba de Kolmogorov-Smirnov).

Validación: ¿el modelo representa la realidad?
  - Se compara la tasa de llegadas simulada con la observada (λ = 2.083 carros/min).
  - Se compara el tiempo en el sistema con la teoría de colas M/G/c
    (fórmula de Erlang C con la aproximación de Allen-Cunneen).
"""
import math
from statistics import mean, stdev

from scipy import stats

from Modelacion import LAMBDA_OBSERVADO, PARAMETROS_DEFECTO, replicar_simulacion, simular_peaje

TOL = 1e-9


def revisar_relaciones(filas, n_taquillas):
    """Cada regla del modelo se revisa en todos los carros; devuelve (regla, fallos)."""
    libre = [0.0] * n_taquillas
    reglas = {
        "Llegada(i) = Llegada(i−1) + Tiempo entre llegadas(i)": 0,
        "Inicio de atención ≥ Llegada (nadie es atendido antes de llegar)": 0,
        "Inicio = MAX(Llegada, momento en que se libera la taquilla)": 0,
        "Salida = Inicio + Tiempo de pago + Tiempo de arranque": 0,
        "Tiempo en espera = Inicio − Llegada ≥ 0": 0,
        "Tiempo en el sistema = Salida − Llegada": 0,
        "La taquilla asignada es la que se libera primero (cola única FIFO)": 0,
        "Tiempos de pago y arranque positivos": 0,
        "Promedio móvil = promedio acumulado del tiempo en el sistema": 0,
    }
    nombres = list(reglas)
    llegada_ant, suma = 0.0, 0.0
    for i, f in enumerate(filas, start=1):
        k = f["taquilla"] - 1
        chequeos = [
            abs(f["llegada"] - (llegada_ant + f["entre_llegadas"])) < TOL,
            f["inicio"] >= f["llegada"] - TOL,
            abs(f["inicio"] - max(f["llegada"], libre[k])) < TOL,
            abs(f["salida"] - (f["inicio"] + f["t_pago"] + f["t_arranque"])) < TOL,
            abs(f["t_espera"] - (f["inicio"] - f["llegada"])) < TOL and f["t_espera"] >= -TOL,
            abs(f["t_sistema"] - (f["salida"] - f["llegada"])) < TOL,
            libre[k] <= min(libre) + TOL,
            f["t_pago"] > 0 and f["t_arranque"] > 0,
        ]
        suma += f["t_sistema"]
        chequeos.append(abs(f["promedio"] - suma / i) < TOL)
        for nombre, ok in zip(nombres, chequeos):
            if not ok:
                reglas[nombre] += 1
        libre[k] = f["salida"]
        llegada_ant = f["llegada"]
    return [{"regla": r, "fallos": n, "ok": n == 0} for r, n in reglas.items()]


def traza_manual(filas, n_taquillas, cantidad=6):
    """Cálculo paso a paso de los primeros carros, para revisarlo a mano."""
    libre = [0.0] * n_taquillas
    traza = []
    for f in filas[:cantidad]:
        k = f["taquilla"] - 1
        traza.append({
            "carro": f["carro"],
            "llegada": f"{f['llegada'] - f['entre_llegadas']:.3f} + {f['entre_llegadas']:.3f} = {f['llegada']:.3f}",
            "libres": " / ".join(f"T{j + 1}: {t:.3f}" for j, t in enumerate(libre)),
            "inicio": f"MAX({f['llegada']:.3f}; {libre[k]:.3f}) = {f['inicio']:.3f}",
            "salida": f"{f['inicio']:.3f} + {f['t_pago']:.3f} + {f['t_arranque']:.3f} = {f['salida']:.3f}",
            "espera": f"{f['inicio']:.3f} − {f['llegada']:.3f} = {f['t_espera']:.3f}",
            "taquilla": f["taquilla"],
        })
        libre[k] = f["salida"]
    return traza


def revisar_entradas(filas, p, alfa=0.05):
    """¿Las variables aleatorias generadas siguen la distribución definida?"""
    variables = [
        ("Tiempo entre llegadas", "entre_llegadas", "Exponencial", p["media_llegadas"], p["media_llegadas"],
         stats.expon(scale=p["media_llegadas"]).cdf),
        ("Tiempo de pago", "t_pago", "Normal", p["media_pago"], p["desv_pago"],
         stats.norm(p["media_pago"], p["desv_pago"]).cdf),
        ("Tiempo de arranque", "t_arranque", "Normal", p["media_arranque"], p["desv_arranque"],
         stats.norm(p["media_arranque"], p["desv_arranque"]).cdf),
    ]
    resultado = []
    for nombre, clave, dist, media, desv, cdf in variables:
        datos = [f[clave] for f in filas]
        ks = stats.kstest(datos, cdf)
        resultado.append({
            "nombre": nombre, "distribucion": dist,
            "media_teorica": media, "media_simulada": mean(datos),
            "desv_teorica": desv, "desv_simulada": stdev(datos),
            "d": float(ks.statistic), "p": float(ks.pvalue), "ok": ks.pvalue > alfa,
        })
    return resultado


def llegadas_por_minuto(filas):
    """Cuenta cuántos carros llegan en cada minuto completo de la simulación."""
    minutos = int(filas[-1]["llegada"])
    conteo = [0] * minutos
    for f in filas:
        m = int(f["llegada"])
        if m < minutos:
            conteo[m] += 1
    return conteo


def erlang_c(lam, media_servicio, c):
    """Probabilidad de esperar y tiempo medio en fila de una cola M/M/c."""
    a = lam * media_servicio            # carga ofrecida
    rho = a / c
    if rho >= 1:
        return None
    suma = sum(a ** k / math.factorial(k) for k in range(c))
    ultimo = a ** c / (math.factorial(c) * (1 - rho))
    p_espera = ultimo / (suma + ultimo)
    wq = p_espera * media_servicio / (c - a)
    return {"rho": rho, "p_espera": p_espera, "wq": wq}


def teoria_mgc(p, c):
    """
    Aproximación de Allen-Cunneen para M/G/c:
        Wq(M/G/c) ≈ Wq(M/M/c) · (Ca² + Cs²) / 2
    con Ca² = 1 (llegadas Poisson) y Cs² = Var(S) / E(S)².
    """
    media_s = p["media_pago"] + p["media_arranque"]
    var_s = p["desv_pago"] ** 2 + p["desv_arranque"] ** 2
    cs2 = var_s / media_s ** 2
    mmc = erlang_c(1 / p["media_llegadas"], media_s, c)
    if mmc is None:
        return None
    wq = mmc["wq"] * (1 + cs2) / 2
    return {"rho": mmc["rho"], "cs2": cs2, "wq": wq, "w": wq + media_s}


def validar_con_teoria(p, taquillas=(2, 3, 4), replicas=30, calentamiento=200):
    filas = []
    for c in taquillas:
        sim = replicar_simulacion(n_replicas=replicas, calentamiento=calentamiento,
                                  **{**p, "n_taquillas": c})
        w_sim = mean(r["t_sistema"] for r in sim)
        wq_sim = mean(r["t_espera"] for r in sim)
        teo = teoria_mgc(p, c)
        filas.append({
            "c": c,
            "rho": (p["media_pago"] + p["media_arranque"]) / (c * p["media_llegadas"]),
            "w_sim": w_sim, "wq_sim": wq_sim,
            "w_teo": teo["w"] if teo else None,
            "wq_teo": teo["wq"] if teo else None,
            "error": 100 * abs(w_sim - teo["w"]) / teo["w"] if teo else None,
        })
    return filas


def verificar(parametros=None, alfa=0.05):
    """Ejecuta todas las verificaciones y validaciones con una corrida larga."""
    p = {**PARAMETROS_DEFECTO, **(parametros or {})}
    larga = {**p, "n_carros": 20000, "n_taquillas": 4}   # sistema estable para revisar entradas
    filas_larga = simular_peaje(**larga)
    filas = simular_peaje(**p)

    conteo = llegadas_por_minuto(filas_larga)
    lam_sim = mean(conteo)
    return {
        "p": p,
        "relaciones": revisar_relaciones(filas, p["n_taquillas"]),
        "relaciones_larga": revisar_relaciones(filas_larga, 4),
        "traza": traza_manual(filas, p["n_taquillas"]),
        "entradas": revisar_entradas(filas_larga, p, alfa),
        "n_entradas": len(filas_larga),
        "lambda_obs": LAMBDA_OBSERVADO,
        "lambda_sim": lam_sim,
        "dispersion": stdev(conteo) ** 2 / lam_sim,
        "minutos": len(conteo),
        "teoria": validar_con_teoria(p),
            }

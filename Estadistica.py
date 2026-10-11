"""
Análisis estadístico de las réplicas (Semana 10).

Sigue el procedimiento de la presentación:
  1. Estadísticos descriptivos de las réplicas.
  2. Prueba de bondad de ajuste (¿las réplicas son normales?).
  3. Intervalo de confianza:  normal  -> x̄ ± t(α/2, r-1)·s/√r
                              general -> x̄ ± s/√(r·α)   (Tchebycheff)
  4. Longitud de réplica:     normal  -> n = (s·t(α/2, n'-1)/ε)²
                              general -> n = (1/α)·(s/ε)²
  5. Pruebas de hipótesis contra la meta y entre escenarios.
"""
import math
from statistics import mean, median, stdev

from scipy import stats


def describir(datos):
    """Medidas de tendencia central, dispersión y forma."""
    n = len(datos)
    x_bar = mean(datos)
    s = stdev(datos) if n > 1 else 0.0
    ordenados = sorted(datos)
    q1, q3 = cuartil(ordenados, 0.25), cuartil(ordenados, 0.75)
    return {
        "n": n,
        "media": x_bar,
        "mediana": median(datos),
        "varianza": s ** 2,
        "desviacion": s,
        "cv": 100.0 * s / x_bar if x_bar else 0.0,
        "minimo": ordenados[0],
        "maximo": ordenados[-1],
        "rango": ordenados[-1] - ordenados[0],
        "q1": q1,
        "q3": q3,
        "asimetria": float(stats.skew(datos, bias=False)) if n > 2 else 0.0,
        "curtosis": float(stats.kurtosis(datos, bias=False)) if n > 3 else 0.0,
    }


def cuartil(ordenados, p):
    """Percentil con interpolación lineal (igual que PERCENTIL.INC de Excel)."""
    pos = (len(ordenados) - 1) * p
    i = math.floor(pos)
    j = min(i + 1, len(ordenados) - 1)
    return ordenados[i] + (ordenados[j] - ordenados[i]) * (pos - i)


def histograma(datos):
    """Frecuencias con k = ⌈1 + 3.322·log10(n)⌉ intervalos (regla de Sturges)."""
    n = len(datos)
    k = max(1, math.ceil(1 + 3.322 * math.log10(n)))
    minimo, maximo = min(datos), max(datos)
    ancho = (maximo - minimo) / k or 1.0
    frecuencias = [0] * k
    for x in datos:
        frecuencias[min(int((x - minimo) / ancho), k - 1)] += 1
    etiquetas = [f"{minimo + i * ancho:.2f}–{minimo + (i + 1) * ancho:.2f}" for i in range(k)]
    return {"etiquetas": etiquetas, "frecuencias": frecuencias}


def caja(datos):
    """Cinco números del diagrama de caja y valores atípicos (regla 1.5·RIC)."""
    ordenados = sorted(datos)
    q1, q2, q3 = (cuartil(ordenados, p) for p in (0.25, 0.5, 0.75))
    ric = q3 - q1
    li, ls = q1 - 1.5 * ric, q3 + 1.5 * ric
    dentro = [x for x in ordenados if li <= x <= ls]
    return {
        "min": dentro[0], "q1": q1, "mediana": q2, "q3": q3, "max": dentro[-1],
        "atipicos": [x for x in ordenados if x < li or x > ls],
        "escala_min": ordenados[0], "escala_max": ordenados[-1],
    }


def prueba_normalidad(datos, alfa):
    """
    H0: las réplicas siguen una distribución normal.
    Se decide con Shapiro-Wilk (la más potente para muestras pequeñas) y se
    reporta también Kolmogorov-Smirnov como referencia.
    """
    x_bar, s = mean(datos), stdev(datos)
    sw = stats.shapiro(datos)
    ks = stats.kstest(datos, stats.norm(x_bar, s).cdf) if s > 0 else None
    normal = bool(sw.pvalue > alfa)
    return {
        "w": float(sw.statistic),
        "p_sw": float(sw.pvalue),
        "d": float(ks.statistic) if ks else 0.0,
        "p_ks": float(ks.pvalue) if ks else 1.0,
        "normal": normal,
        "conclusion": ("p > α: no se rechaza H0, las réplicas se pueden tratar como normales."
                       if normal else
                       "p ≤ α: se rechaza H0, no se puede asumir normalidad."),
    }


def intervalo_confianza(datos, alfa, normal):
    """Calcula los dos intervalos de la presentación y elige según la normalidad."""
    r = len(datos)
    x_bar, s = mean(datos), stdev(datos)
    t = float(stats.t.ppf(1 - alfa / 2, r - 1))
    margen_t = t * s / math.sqrt(r)
    margen_g = s / math.sqrt(r * alfa)
    return {
        "media": x_bar,
        "t": t,
        "normal": (x_bar - margen_t, x_bar + margen_t),
        "general": (x_bar - margen_g, x_bar + margen_g),
        "elegido": "normal" if normal else "general",
        "intervalo": (x_bar - margen_t, x_bar + margen_t) if normal else (x_bar - margen_g, x_bar + margen_g),
        "margen": margen_t if normal else margen_g,
    }


def replicas_necesarias(datos, alfa, epsilon, normal):
    """Número de réplicas para estimar la media con error ±ε (corrida piloto = datos)."""
    r0, s = len(datos), stdev(datos)
    if normal:
        t = float(stats.t.ppf(1 - alfa / 2, r0 - 1))
        n = (s * t / epsilon) ** 2
        formula = f"n = (s·t/ε)² = ({s:.4f}·{t:.3f}/{epsilon})²"
    else:
        n = (1 / alfa) * (s / epsilon) ** 2
        formula = f"n = (1/α)·(s/ε)² = (1/{alfa})·({s:.4f}/{epsilon})²"
    return {"n": max(2, math.ceil(n)), "formula": formula, "suficiente": r0 >= math.ceil(n)}


def prueba_meta(datos, meta, alfa, normal):
    """
    ¿El tiempo promedio en el sistema es menor que la meta?
      H0: μ ≥ meta  (el escenario NO cumple)
      H1: μ < meta  (el escenario cumple)
    Normal -> t de Student de una muestra; si no -> Wilcoxon de rangos con signo.
    """
    if normal:
        res = stats.ttest_1samp(datos, meta, alternative="less")
        nombre, simbolo = "t de Student (una muestra)", "t"
    else:
        diferencias = [x - meta for x in datos]
        if all(d == 0 for d in diferencias):
            return {"nombre": "Wilcoxon", "simbolo": "W", "estadistico": 0.0, "p": 1.0, "rechaza": False}
        res = stats.wilcoxon(diferencias, alternative="less")
        nombre, simbolo = "Wilcoxon de rangos con signo", "W"
    p = float(res.pvalue)
    return {"nombre": nombre, "simbolo": simbolo, "estadistico": float(res.statistic),
            "p": p, "rechaza": p < alfa}


def comparar_escenarios(actual, propuesto, alfa):
    """
    Compara dos escenarios simulados con las mismas semillas (réplicas pareadas).
      H0: μ_actual − μ_propuesto ≤ 0   (el cambio no reduce el tiempo)
      H1: μ_actual − μ_propuesto > 0   (el cambio reduce el tiempo)
    Si las diferencias son normales -> t pareada; si no -> Wilcoxon pareada.
    """
    diferencias = [a - b for a, b in zip(actual, propuesto)]
    normal = len(set(diferencias)) > 2 and stats.shapiro(diferencias).pvalue > alfa
    if normal:
        res = stats.ttest_rel(actual, propuesto, alternative="greater")
        nombre, simbolo = "t pareada", "t"
    else:
        res = stats.wilcoxon(diferencias, alternative="greater")
        nombre, simbolo = "Wilcoxon pareada", "W"
    p = float(res.pvalue)
    return {"nombre": nombre, "simbolo": simbolo, "estadistico": float(res.statistic),
            "p": p, "rechaza": p < alfa, "diferencia": mean(diferencias),
            "reduccion": 100.0 * mean(diferencias) / mean(actual)}


def analizar(datos, alfa, meta, epsilon):
    """Todo el análisis de un escenario en un solo diccionario."""
    normalidad = prueba_normalidad(datos, alfa)
    normal = normalidad["normal"]
    return {
        "descriptivos": describir(datos),
        "histograma": histograma(datos),
        "caja": caja(datos),
        "normalidad": normalidad,
        "ic": intervalo_confianza(datos, alfa, normal),
        "longitud": replicas_necesarias(datos, alfa, epsilon, normal),
        "meta": prueba_meta(datos, meta, alfa, normal),
    }

"""
==========================================================================
 PRUEBAS ESTADISTICAS PARA NUMEROS PSEUDOALEATORIOS  r_i  en el intervalo (0, 1)
==========================================================================

Este modulo valida un conjunto r = {r_1, r_2, ..., r_n} generado por
cualquiera de los dos algoritmos (Cuadrados Medios o Congruencial Lineal).

Se implementan las cuatro pruebas descritas en el material de las Semanas 3 y 4:

  1. Prueba de medias        ->  valida que   E(x) = 1/2
  2. Prueba de varianza      ->  valida que   V(x) = 1/12
  3. Prueba de uniformidad   ->  valida que   r_i ~ U(0, 1)
                                 (Chi-cuadrada y Kolmogorov-Smirnov)
  4. Prueba de independencia ->  valida la ausencia de correlacion
                                 (corridas arriba y abajo de la media)

Todas las pruebas parten de la distribucion UNIFORME CONTINUA en (0, 1):

        f(x) = 1     si 0 <= x <= 1            (funcion de densidad)
        f(x) = 0     en cualquier otro caso

    de la que se deduce, integrando:

        E(x)  = integral_0^1  x * f(x) dx           = 1/2
        E(x^2)= integral_0^1  x^2 * f(x) dx         = 1/3
        V(x)  = E(x^2) - E(x)^2 = 1/3 - 1/4         = 1/12

NOTA: no se usa SciPy. Las funciones de distribucion (normal estandar y
Chi-cuadrada) se calculan aqui con la funcion gamma incompleta regularizada
(desarrollo en serie + fraccion continua) y con math.erf.
"""

import math


# =====================================================================
# 0. FUNCIONES DE DISTRIBUCION (implementadas sin dependencias externas)
# =====================================================================

def _gammap(a, x):
    """
    Funcion gamma incompleta regularizada  P(a, x) = gamma_inf(a, x) / Gamma(a).
    Es la base para la CDF de la distribucion Chi-cuadrada:
        F_chi2(x; k) = P(k/2, x/2)
    Algoritmo clasico (Numerical Recipes):
      - desarrollo en serie      cuando  x < a + 1
      - fraccion continua (Lentz) cuando  x >= a + 1
    """
    if x <= 0.0:
        return 0.0

    if x < a + 1.0:
        # ---- desarrollo en serie ----
        ap = a
        termino = 1.0 / a
        suma = termino
        for _ in range(1000):
            ap += 1.0
            termino *= x / ap
            suma += termino
            if abs(termino) < abs(suma) * 1e-15:
                break
        return suma * math.exp(-x + a * math.log(x) - math.lgamma(a))

    # ---- fraccion continua (Lentz modificado) ----
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    q = math.exp(-x + a * math.log(x) - math.lgamma(a)) * h
    return 1.0 - q


def norm_cdf(z):
    """CDF de la distribucion normal estandar N(0, 1)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def norm_ppf(p):
    """
    Inversa de la CDF normal estandar (cuantil z tal que  norm_cdf(z) = p).
    Se obtiene por biseccion; suficientemente preciso para 0 < p < 1.
    Ejemplos:  norm_ppf(0.975) = 1.9600 ,  norm_ppf(0.95) = 1.6449
    """
    if p <= 0.0:
        return -40.0
    if p >= 1.0:
        return 40.0
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def chi2_cdf(x, k):
    """CDF de la distribucion Chi-cuadrada con k grados de libertad."""
    if x <= 0.0:
        return 0.0
    return _gammap(k / 2.0, x / 2.0)


def chi2_ppf(p, k):
    """
    Inversa de la CDF Chi-cuadrada (valor de tabla chi2_{p, k}).
    Se obtiene por biseccion sobre chi2_cdf.
    Ejemplo:  chi2_ppf(0.95, 1) ~ 3.8415
    """
    if p <= 0.0:
        return 0.0
    lo, hi = 0.0, 1000.0 + 20.0 * k
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if chi2_cdf(mid, k) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# =====================================================================
# 1. PRUEBA DE MEDIAS   ->   H0: E(x) = 1/2
# =====================================================================

def prueba_medias(r, alfa=0.05):
    """
    Verifica si el valor esperado (promedio) del conjunto es 0.5.

      H0:  mu = 0.5          (no se rechaza  ->  la prueba se APRUEBA)
      H1:  mu != 0.5

    Procedimiento (material Semana 4):
      1. promedio        r_barra = (1/n) * suma(r_i)
      2. limites de aceptacion, usando que  V(x) = 1/12  ->  sigma = 1/sqrt(12 n):
             L_inf = 1/2 - z_{alfa/2} * (1 / sqrt(12 n))
             L_sup = 1/2 + z_{alfa/2} * (1 / sqrt(12 n))
      3. si  L_inf <= r_barra <= L_sup  ->  NO se rechaza H0.
    """
    n = len(r)
    r_barra = sum(r) / n
    sigma = 1.0 / math.sqrt(12.0 * n)
    z = norm_ppf(1.0 - alfa / 2.0)

    li = 0.5 - z * sigma
    ls = 0.5 + z * sigma
    z0 = (r_barra - 0.5) / sigma                 # estadistico de prueba
    p_valor = 2.0 * (1.0 - norm_cdf(abs(z0)))
    pasa = li <= r_barra <= ls

    return {
        "nombre": "Prueba de medias  ->  E(x) = 1/2",
        "aplicable": True,
        "esperado": 0.5,
        "estimado": r_barra,
        "limite_inferior": li,
        "limite_superior": ls,
        "z_critico": z,
        "estadistico": z0,
        "p_valor": p_valor,
        "pasa": pasa,
        "conclusion": (
            "El promedio esta dentro de los limites: NO se rechaza H0, "
            "el conjunto tiene valor esperado 0.5."
            if pasa else
            "El promedio esta fuera de los limites: se RECHAZA H0, "
            "el valor esperado no es 0.5."
        ),
    }


# =====================================================================
# 2. PRUEBA DE VARIANZA   ->   H0: V(x) = 1/12
# =====================================================================

def prueba_varianza(r, alfa=0.05):
    """
    Verifica si la varianza del conjunto es 1/12 (= 0.08333...).

      H0:  sigma^2 = 1/12    (no se rechaza  ->  la prueba se APRUEBA)
      H1:  sigma^2 != 1/12

    Procedimiento (material Semana 4):
      1. varianza muestral:
             V(r) = (1 / (n - 1)) * suma( (r_i - r_barra)^2 )
      2. limites de aceptacion con la Chi-cuadrada de (n - 1) grados de libertad:
             L_inf = chi2_{alfa/2, n-1}     / (12 (n - 1))
             L_sup = chi2_{1 - alfa/2, n-1} / (12 (n - 1))
      3. si  L_inf <= V(r) <= L_sup  ->  NO se rechaza H0.
    """
    n = len(r)
    if n < 2:
        return {"nombre": "Prueba de varianza  ->  V(x) = 1/12",
                "aplicable": False,
                "conclusion": "Se necesitan al menos 2 numeros."}

    r_barra = sum(r) / n
    v = sum((x - r_barra) ** 2 for x in r) / (n - 1)

    chi_inf = chi2_ppf(alfa / 2.0, n - 1)
    chi_sup = chi2_ppf(1.0 - alfa / 2.0, n - 1)
    li = chi_inf / (12.0 * (n - 1))
    ls = chi_sup / (12.0 * (n - 1))

    chi0 = 12.0 * (n - 1) * v                     # estadistico  (n-1)V(r) / (1/12)
    fcdf = chi2_cdf(chi0, n - 1)
    p_valor = 2.0 * min(fcdf, 1.0 - fcdf)
    pasa = li <= v <= ls

    return {
        "nombre": "Prueba de varianza  ->  V(x) = 1/12",
        "aplicable": True,
        "esperado": 1.0 / 12.0,
        "estimado": v,
        "limite_inferior": li,
        "limite_superior": ls,
        "estadistico": chi0,
        "gl": n - 1,
        "p_valor": p_valor,
        "pasa": pasa,
        "conclusion": (
            "La varianza esta dentro de los limites: NO se rechaza H0, "
            "el conjunto tiene varianza 1/12."
            if pasa else
            "La varianza esta fuera de los limites: se RECHAZA H0, "
            "la varianza no es 1/12."
        ),
    }


# =====================================================================
# 3a. PRUEBA DE UNIFORMIDAD - CHI CUADRADA   ->   H0: r_i ~ U(0, 1)
# =====================================================================

def prueba_uniformidad_chi2(r, alfa=0.05):
    """
    Comprueba que los r_i se reparten de forma uniforme en (0, 1).

      H0:  r_i ~ U(0, 1)     (no se rechaza  ->  la prueba se APRUEBA)
      H1:  r_i no son uniformes

    Procedimiento (material Semana 5):
      1. dividir (0, 1) en  m = sqrt(n)  subintervalos de igual tamano.
      2. frecuencia esperada por intervalo:  E_i = n / m.
      3. frecuencia observada  O_i  = cuantos r_i caen en cada intervalo.
      4. estadistico:   chi2 = suma_i  (O_i - E_i)^2 / E_i
      5. si  chi2 <= chi2_{alfa, m-1}  ->  NO se rechaza H0.
    """
    n = len(r)
    m = max(2, round(math.sqrt(n)))
    esperada = n / m

    observadas = [0] * m
    for x in r:
        idx = int(x * m)
        if idx >= m:            # el caso x == 1.0 cae en el ultimo intervalo
            idx = m - 1
        if idx < 0:
            idx = 0
        observadas[idx] += 1

    chi0 = sum((o - esperada) ** 2 / esperada for o in observadas)
    critico = chi2_ppf(1.0 - alfa, m - 1)
    p_valor = 1.0 - chi2_cdf(chi0, m - 1)
    pasa = chi0 <= critico

    return {
        "nombre": "Prueba de uniformidad (Chi-cuadrada)",
        "aplicable": True,
        "m_intervalos": m,
        "frecuencia_esperada": esperada,
        "frecuencias_observadas": observadas,
        "estadistico": chi0,
        "critico": critico,
        "gl": m - 1,
        "p_valor": p_valor,
        "pasa": pasa,
        "conclusion": (
            "chi2 calculado <= chi2 de tabla: NO se rechaza H0, "
            "los numeros son uniformes en (0, 1)."
            if pasa else
            "chi2 calculado > chi2 de tabla: se RECHAZA H0, "
            "los numeros no son uniformes."
        ),
    }


# =====================================================================
# 3b. PRUEBA DE UNIFORMIDAD - KOLMOGOROV-SMIRNOV   ->   H0: r_i ~ U(0, 1)
# =====================================================================

def prueba_uniformidad_ks(r, alfa=0.05):
    """
    Alternativa a la Chi-cuadrada, recomendada para conjuntos pequenos (n < 20).

    Procedimiento (material Semana 5):
      1. ordenar los numeros de menor a mayor:  r_(1) <= r_(2) <= ... <= r_(n)
      2. D+  = max_i ( i/n     - r_(i) )
         D-  = max_i ( r_(i) - (i-1)/n )
         D   = max(D+, D-)
      3. si  D <= D_{alfa, n}  ->  NO se rechaza H0.

    El valor critico D_{alfa, n} se aproxima con la formula de Stephens:
         D_critico = c(alfa) / ( sqrt(n) + 0.12 + 0.11 / sqrt(n) )
    con  c(0.10) = 1.22 ,  c(0.05) = 1.36 ,  c(0.01) = 1.63.
    """
    n = len(r)
    s = sorted(r)

    d_mas = max((i + 1) / n - s[i] for i in range(n))
    d_menos = max(s[i] - i / n for i in range(n))
    d = max(d_mas, d_menos)

    c = {0.10: 1.22, 0.05: 1.36, 0.01: 1.63}.get(round(alfa, 2), 1.36)
    critico = c / (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n))
    pasa = d <= critico

    return {
        "nombre": "Prueba de uniformidad (Kolmogorov-Smirnov)",
        "aplicable": True,
        "d_mas": d_mas,
        "d_menos": d_menos,
        "estadistico": d,
        "critico": critico,
        "pasa": pasa,
        "conclusion": (
            "D <= D critico: NO se rechaza H0, no hay diferencia "
            "significativa con la distribucion uniforme."
            if pasa else
            "D > D critico: se RECHAZA H0, los numeros no siguen "
            "una distribucion uniforme."
        ),
    }


# =====================================================================
# 4. PRUEBA DE INDEPENDENCIA - CORRIDAS ARRIBA Y ABAJO DE LA MEDIA
# =====================================================================

def prueba_independencia_corridas(r, alfa=0.05):
    """
    Comprueba que no exista correlacion entre numeros consecutivos.

      H0:  los numeros del conjunto r son independientes  (se APRUEBA)
      H1:  los numeros del conjunto r no son independientes

    Procedimiento (material Semana 5, ejemplo 2.16):
      1. construir una secuencia de 0 y 1:  1 si r_i > 0.5 ,  0 si r_i <= 0.5.
      2. contar:
             C0 = numero de corridas (rachas de 0 o de 1 consecutivos)
             n0 = cantidad de ceros
             n1 = cantidad de unos           (n0 + n1 = n)
      3. valor esperado y varianza de C0:
             mu    = (2 n0 n1) / n + 1/2
             sigma^2 = [ 2 n0 n1 (2 n0 n1 - n) ] / [ n^2 (n - 1) ]
      4. estadistico:   Z0 = (C0 - mu) / sigma
      5. si  -z_{alfa/2} < Z0 < z_{alfa/2}  ->  NO se rechaza H0.
    """
    n = len(r)
    bits = [1 if x > 0.5 else 0 for x in r]
    n1 = sum(bits)
    n0 = n - n1

    if n0 == 0 or n1 == 0 or n < 3:
        return {
            "nombre": "Prueba de independencia (corridas arriba y abajo de la media)",
            "aplicable": False,
            "conclusion": "No se puede aplicar: se necesitan valores por encima "
                          "y por debajo de 0.5 y al menos 3 numeros.",
        }

    corridas = 1
    for i in range(1, n):
        if bits[i] != bits[i - 1]:
            corridas += 1

    mu = (2.0 * n0 * n1) / n + 0.5
    var = (2.0 * n0 * n1 * (2.0 * n0 * n1 - n)) / (n ** 2 * (n - 1))
    sigma = math.sqrt(var) if var > 0 else float("nan")
    z0 = (corridas - mu) / sigma
    z = norm_ppf(1.0 - alfa / 2.0)
    p_valor = 2.0 * (1.0 - norm_cdf(abs(z0)))
    pasa = -z < z0 < z

    return {
        "nombre": "Prueba de independencia (corridas arriba y abajo de la media)",
        "aplicable": True,
        "corridas": corridas,
        "n0": n0,
        "n1": n1,
        "mu": mu,
        "sigma2": var,
        "estadistico": z0,
        "z_critico": z,
        "p_valor": p_valor,
        "pasa": pasa,
        "conclusion": (
            "Z0 dentro del intervalo (-z, z): NO se rechaza H0, "
            "los numeros son independientes."
            if pasa else
            "Z0 fuera del intervalo (-z, z): se RECHAZA H0, "
            "los numeros no son independientes."
        ),
    }


# =====================================================================
# 5. EJECUTAR TODAS LAS PRUEBAS SOBRE UN CONJUNTO r
# =====================================================================

def ejecutar_pruebas(valores_r, alfa=0.05):
    """
    Aplica las cuatro pruebas al conjunto de numeros r generado por el
    algoritmo (Cuadrados Medios o Congruencial Lineal) y devuelve un
    diccionario con todos los resultados listo para la plantilla HTML.
    """
    r = [float(x) for x in valores_r]
    n = len(r)
    if n < 2:
        return None

    pruebas = {
        "medias": prueba_medias(r, alfa),
        "varianza": prueba_varianza(r, alfa),
        "uniformidad_chi2": prueba_uniformidad_chi2(r, alfa),
        "uniformidad_ks": prueba_uniformidad_ks(r, alfa),
        "independencia": prueba_independencia_corridas(r, alfa),
    }
    aplicables = [p for p in pruebas.values() if p.get("aplicable")]
    aprobadas = [p for p in aplicables if p.get("pasa")]

    return {
        "n": n,
        "alfa": alfa,
        "confianza": round((1.0 - alfa) * 100),
        "resumen": {
            "total": len(aplicables),
            "aprobadas": len(aprobadas),
            "todas_ok": len(aplicables) > 0 and len(aprobadas) == len(aplicables),
        },
        **pruebas,
    }


# =====================================================================
# 6. PRUEBA RAPIDA POR TERMINAL
# =====================================================================

if __name__ == "__main__":
    # Comprobaciones de las funciones de distribucion:
    print("norm_ppf(0.975)  =", round(norm_ppf(0.975), 4), " (esperado 1.9600)")
    print("norm_ppf(0.95)   =", round(norm_ppf(0.95), 4), " (esperado 1.6449)")
    print("chi2_ppf(0.95,1) =", round(chi2_ppf(0.95, 1), 4), " (esperado 3.8415)")
    print("chi2_ppf(0.95,9) =", round(chi2_ppf(0.95, 9), 4), " (esperado 16.919)")
    print("chi2_ppf(0.025,49)=", round(chi2_ppf(0.025, 49), 4), " (esperado 31.555)")

    # Conjunto de 50 numeros del ejemplo 2.16 del material (prueba de corridas):
    datos = [
        0.809, 0.042, 0.432, 0.538, 0.225, 0.88, 0.688, 0.772, 0.036, 0.854,
        0.397, 0.266, 0.821, 0.897, 0.07, 0.721, 0.087, 0.35, 0.779, 0.482,
        0.136, 0.855, 0.453, 0.197, 0.444, 0.799, 0.089, 0.691, 0.545, 0.857,
        0.692, 0.055, 0.348, 0.373, 0.436, 0.29, 0.015, 0.834, 0.599, 0.724,
        0.564, 0.709, 0.946, 0.754, 0.677, 0.128, 0.012, 0.498, 0.6, 0.913,
    ]
    ind = prueba_independencia_corridas(datos)
    print("\nEjemplo 2.16 -> corridas:", ind["corridas"], "| n0:", ind["n0"],
          "| n1:", ind["n1"])
    print("mu =", round(ind["mu"], 2), " sigma^2 =", round(ind["sigma2"], 5),
          " Z0 =", round(ind["estadistico"], 4), " (esperado -1.2484)")

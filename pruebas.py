"""
==========================================================================
PRUEBAS ESTADISTICAS PARA NUMEROS PSEUDOALEATORIOS  r_i  en el intervalo (0, 1)
==========================================================================

Este modulo valida un conjunto r = {r_1, r_2, ..., r_n} generado por cualquiera de los dos algoritmos (Cuadrados Medios o Congruencial Lineal).

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

--------------------------------------------------------------------------
DISTRIBUCIONES DE PROBABILIDAD  (se usan de SciPy, scipy.stats)
--------------------------------------------------------------------------
Cada prueba compara un estadistico con los valores criticos de una
distribucion teorica.  En lugar de programar esas distribuciones a mano
se usan las de SciPy, que son exactas y estan probadas:

  norm   -> Normal estandar  N(0, 1)
             norm.ppf(p)      cuantil z tal que  P(Z <= z) = p     (valor de tabla)
             norm.cdf(z)      probabilidad acumulada  P(Z <= z)
             norm.sf(z)       cola derecha  P(Z > z) = 1 - cdf

  chi2   -> Chi-cuadrada con  df  grados de libertad
             chi2.ppf(p, df)  cuantil (valor de tabla chi2_{p, df})
             chi2.cdf(x, df)  probabilidad acumulada
             chi2.sf(x, df)   cola derecha (se usa como p-valor)

  ksone  -> Distribucion del estadistico D de Kolmogorov-Smirnov de UNA muestra
             ksone.ppf(1 - alfa, n)  ->  valor critico exacto  D_{alfa, n}

  kstest -> Prueba de bondad de ajuste de Kolmogorov-Smirnov ya empaquetada
             kstest(r, 'uniform')  ->  devuelve  (estadistico D, p-valor)

Equivalencia con las tablas
      chi2_{alfa/2, df} (tabla, area alfa/2 a la derecha)  ==  chi2.ppf(1 - alfa/2, df)
      chi2_{1-alfa/2, df}                                  ==  chi2.ppf(alfa/2, df)
"""

import math

from scipy.stats import norm, chi2, ksone, kstest


# =====================================================================
# 1. PRUEBA DE MEDIAS   ->   H0: E(x) = 1/2
# =====================================================================

def prueba_medias(r, alfa=0.05):
    """
    Verifica si el valor esperado (promedio) del conjunto es 0.5.

      H0:  mu = 0.5          (no se rechaza  ->  la prueba se APRUEBA)
      H1:  mu != 0.5

    Procedimiento:
      1. promedio        r_barra = (1/n) * suma(r_i)
      2. limites de aceptacion, usando que para U(0,1) la varianza es 1/12,
         por lo que la media muestral tiene desviacion  sigma = 1/sqrt(12 n):
             L_inf = 1/2 - z_{alfa/2} * (1 / sqrt(12 n))
             L_sup = 1/2 + z_{alfa/2} * (1 / sqrt(12 n))
      3. si  L_inf <= r_barra <= L_sup  ->  NO se rechaza H0.
    """
    n = len(r)

    # --- 1) estimador: media aritmetica de los n numeros -----------------
    r_barra = sum(r) / n

    # --- 2) desviacion teorica de la media muestral ---------------------
    #   Var(r_barra) = Var(X) / n = (1/12) / n   ->   sigma = 1/sqrt(12 n)
    sigma = 1.0 / math.sqrt(12.0 * n)

    # --- 3) valor critico de la Normal --------------------------------
    #   Para una prueba bilateral con nivel alfa se deja alfa/2 en cada cola,
    #   asi que se necesita el cuantil  z_{1 - alfa/2}  (p. ej. 1.96 para alfa=0.05).
    z = norm.ppf(1.0 - alfa / 2.0)

    # --- 4) intervalo (limites) de aceptacion -------------------------
    li = 0.5 - z * sigma
    ls = 0.5 + z * sigma

    # --- 5) estadistico de prueba y p-valor --------------------------
    #   Z0 mide a cuantas sigmas esta el promedio observado del valor esperado 0.5.
    z0 = (r_barra - 0.5) / sigma
    #   p-valor bilateral: probabilidad de un |Z| tan grande o mayor que |Z0|.
    p_valor = 2.0 * norm.sf(abs(z0))

    # --- 6) decision -------------------------------------------------
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

    Procedimiento:
      1. varianza muestral (cuasivarianza, con n - 1 en el denominador):
             V(r) = (1 / (n - 1)) * suma( (r_i - r_barra)^2 )
      2. limites de aceptacion con la Chi-cuadrada de (n - 1) grados de libertad:
             L_inf = chi2_{alfa/2, n-1}     / (12 (n - 1))
             L_sup = chi2_{1 - alfa/2, n-1} / (12 (n - 1))
         (donde chi2_{p, df} = chi2.ppf(p, df) es el cuantil de cola izquierda)
      3. si  L_inf <= V(r) <= L_sup  ->  NO se rechaza H0.
    """
    n = len(r)
    if n < 2:
        return {"nombre": "Prueba de varianza  ->  V(x) = 1/12",
                "aplicable": False,
                "conclusion": "Se necesitan al menos 2 numeros."}

    df = n - 1

    # --- 1) estimador: cuasivarianza muestral -------------------------
    r_barra = sum(r) / n
    v = sum((x - r_barra) ** 2 for x in r) / df

    # --- 2) valores criticos de la Chi-cuadrada con df grados de libertad ---
    #   La cantidad  df * V(r) / sigma0^2  (con sigma0^2 = 1/12) sigue una
    #   Chi-cuadrada con df g.l. bajo H0.  Se aceptan valores entre los
    #   cuantiles alfa/2 y 1 - alfa/2; al despejar V(r) quedan estos limites:
    chi_inf = chi2.ppf(alfa / 2.0, df)          # cuantil pequeno (cola izquierda)
    chi_sup = chi2.ppf(1.0 - alfa / 2.0, df)    # cuantil grande
    li = chi_inf / (12.0 * df)
    ls = chi_sup / (12.0 * df)

    # --- 3) estadistico de prueba y p-valor bilateral ---------------
    #   chi0 = df * V(r) / (1/12) = 12 * df * V(r)
    chi0 = 12.0 * df * v
    fcdf = chi2.cdf(chi0, df)
    p_valor = 2.0 * min(fcdf, 1.0 - fcdf)       # bilateral: 2 * la cola mas cercana

    # --- 4) decision ----------------------------------------------
    pasa = li <= v <= ls

    return {
        "nombre": "Prueba de varianza  ->  V(x) = 1/12",
        "aplicable": True,
        "esperado": 1.0 / 12.0,
        "estimado": v,
        "limite_inferior": li,
        "limite_superior": ls,
        "estadistico": chi0,
        "gl": df,
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

    Procedimiento:
      1. dividir (0, 1) en  m = round(sqrt(n))  subintervalos de igual tamano.
      2. frecuencia esperada por intervalo:  E_i = n / m   (todos iguales).
      3. frecuencia observada  O_i  = cuantos r_i caen en cada intervalo.
      4. estadistico:   chi2 = suma_i  (O_i - E_i)^2 / E_i
      5. si  chi2 <= chi2_{1-alfa, m-1}  ->  NO se rechaza H0.
         (m - 1 grados de libertad: m clases menos 1 por la restriccion
          de que las frecuencias suman n)
    """
    n = len(r)

    # --- 1) numero de subintervalos: regla practica m = raiz(n) -------
    m = max(2, round(math.sqrt(n)))
    esperada = n / m                              # E_i, igual para todos

    # --- 2) contar cuantos numeros caen en cada subintervalo ---------
    #   El subintervalo de x es  int(x * m)  (0 -> [0,1/m), 1 -> [1/m,2/m), ...).
    #   El caso x == 1.0 daria idx = m, se corrige al ultimo intervalo.
    observadas = [0] * m
    for x in r:
        idx = int(x * m)
        if idx >= m:
            idx = m - 1
        elif idx < 0:
            idx = 0
        observadas[idx] += 1

    # --- 3) estadistico chi-cuadrada de bondad de ajuste ------------
    chi0 = sum((o - esperada) ** 2 / esperada for o in observadas)

    # --- 4) valor critico y p-valor con df = m - 1 -----------------
    gl = m - 1
    critico = chi2.ppf(1.0 - alfa, gl)            # cola derecha alfa
    p_valor = chi2.sf(chi0, gl)                   # P(chi2 > chi0)

    # --- 5) decision: se aprueba si el estadistico no supera la tabla ---
    pasa = chi0 <= critico

    return {
        "nombre": "Prueba de uniformidad (Chi-cuadrada)",
        "aplicable": True,
        "m_intervalos": m,
        "frecuencia_esperada": esperada,
        "frecuencias_observadas": observadas,
        "estadistico": chi0,
        "critico": critico,
        "gl": gl,
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
    Compara la distribucion acumulada EMPIRICA de los datos con la teorica
    de U(0, 1) (que es la recta  F(x) = x).

    Procedimiento:
      1. ordenar los numeros de menor a mayor:  r_(1) <= r_(2) <= ... <= r_(n)
      2. D+  = max_i ( i/n      - r_(i) )      (la empirica va por encima)
         D-  = max_i ( r_(i)  - (i-1)/n )      (la empirica va por debajo)
         D   = max(D+, D-)                     (mayor separacion vertical)
      3. si  D <= D_{alfa, n}  ->  NO se rechaza H0.

    El valor critico exacto  D_{alfa, n}  se obtiene de la distribucion
    'ksone' de SciPy:   ksone.ppf(1 - alfa, n).
    El p-valor se obtiene con la prueba ya empaquetada  kstest(r, 'uniform').
    """
    n = len(r)
    s = sorted(r)

    # --- 1) mayores distancias entre la acumulada empirica y la teorica ---
    d_mas = max((i + 1) / n - s[i] for i in range(n))
    d_menos = max(s[i] - i / n for i in range(n))
    d = max(d_mas, d_menos)

    # --- 2) valor critico exacto y p-valor (SciPy) ----------------
    critico = float(ksone.ppf(1.0 - alfa, n))
    p_valor = float(kstest(r, "uniform").pvalue)

    # --- 3) decision ----------------------------------------------
    pasa = d <= critico

    return {
        "nombre": "Prueba de uniformidad (Kolmogorov-Smirnov)",
        "aplicable": True,
        "d_mas": d_mas,
        "d_menos": d_menos,
        "estadistico": d,
        "critico": critico,
        "p_valor": p_valor,
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
    Comprueba que no exista correlacion entre numeros consecutivos: mira el
    ORDEN en que aparecen los numeros, no solo sus valores.

      H0:  los numeros del conjunto r son independientes  (se APRUEBA)
      H1:  los numeros del conjunto r no son independientes

    Procedimiento:
      1. construir una secuencia de 0 y 1:  1 si r_i > 0.5 ,  0 si r_i <= 0.5.
      2. contar:
             C0 = numero de corridas (rachas de 0 o de 1 consecutivos)
             n0 = cantidad de ceros
             n1 = cantidad de unos           (n0 + n1 = n)
      3. bajo H0, C0 es aproximadamente Normal con:
             mu      = (2 n0 n1) / n + 1/2
             sigma^2 = [ 2 n0 n1 (2 n0 n1 - n) ] / [ n^2 (n - 1) ]
      4. estadistico estandarizado:   Z0 = (C0 - mu) / sigma
      5. si  -z_{1-alfa/2} < Z0 < z_{1-alfa/2}  ->  NO se rechaza H0.
    """
    n = len(r)

    # --- 1) secuencia binaria: por encima (1) o por debajo (0) de 0.5 ---
    bits = [1 if x > 0.5 else 0 for x in r]
    n1 = sum(bits)          # cantidad de unos
    n0 = n - n1             # cantidad de ceros

    #   Si todos los numeros caen del mismo lado no hay corridas que contar.
    if n0 == 0 or n1 == 0 or n < 3:
        return {
            "nombre": "Prueba de independencia (corridas arriba y abajo de la media)",
            "aplicable": False,
            "conclusion": "No se puede aplicar: se necesitan valores por encima "
                          "y por debajo de 0.5 y al menos 3 numeros.",
        }

    # --- 2) contar corridas: cada cambio 0<->1 abre una corrida nueva ---
    corridas = 1
    for i in range(1, n):
        if bits[i] != bits[i - 1]:
            corridas += 1

    # --- 3) media y varianza teoricas del numero de corridas ---------
    mu = (2.0 * n0 * n1) / n + 0.5
    var = (2.0 * n0 * n1 * (2.0 * n0 * n1 - n)) / (n ** 2 * (n - 1))
    sigma = math.sqrt(var) if var > 0 else float("nan")

    # --- 4) estadistico estandarizado y valor critico Normal --------
    z0 = (corridas - mu) / sigma
    z = norm.ppf(1.0 - alfa / 2.0)               # p. ej. 1.96 para alfa = 0.05
    p_valor = 2.0 * norm.sf(abs(z0))             # bilateral

    # --- 5) decision: se aprueba si Z0 cae dentro de (-z, z) --------
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
    Aplica las cinco pruebas al conjunto de numeros r generado por el
    algoritmo (Cuadrados Medios o Congruencial Lineal) y devuelve un
    diccionario con todos los resultados listo para la plantilla HTML.

    Pasos:
      1. convertir a float y descartar si hay menos de 2 numeros.
      2. correr las 5 pruebas (medias, varianza, chi2, K-S, corridas).
      3. contar cuantas son APLICABLES y cuantas de esas APROBARON.
      4. armar un 'resumen' (aprobadas / total, todas_ok) para la vista.
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
    # Valores de tabla que usan las pruebas:
    print("norm.ppf(0.975)   =", round(float(norm.ppf(0.975)), 4), " (esperado 1.9600)")
    print("norm.ppf(0.95)    =", round(float(norm.ppf(0.95)), 4), " (esperado 1.6449)")
    print("chi2.ppf(0.95, 1) =", round(float(chi2.ppf(0.95, 1)), 4), " (esperado 3.8415)")
    print("chi2.ppf(0.95, 9) =", round(float(chi2.ppf(0.95, 9)), 4), " (esperado 16.919)")
    print("chi2.ppf(0.025,49)=", round(float(chi2.ppf(0.025, 49)), 4), " (esperado 31.555)")

    # Conjunto de 50 numeros del ejemplo 2.16:
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
          " Z0 =", round(ind["estadistico"], 4))

import math

from scipy.stats import norm, chi2, ksone, kstest


def prueba_medias(numerosAleatorios, nivelSignificancia):
    cantidadNumeros = len(numerosAleatorios)

    promedioNumeros = sum(numerosAleatorios) / cantidadNumeros

    desviacionPromedio = 1.0 / math.sqrt(12.0 * cantidadNumeros)

    valorCriticoNormal = norm.ppf(1.0 - nivelSignificancia / 2.0)

    limiteInferior = 0.5 - valorCriticoNormal * desviacionPromedio
    limiteSuperior = 0.5 + valorCriticoNormal * desviacionPromedio

    estadisticoNormal = (promedioNumeros - 0.5) / desviacionPromedio
    valorP = 2.0 * norm.sf(abs(estadisticoNormal))

    pasaPrueba = limiteInferior <= promedioNumeros <= limiteSuperior

    return {
        "nombre": "Prueba de medias  ->  E(x) = 1/2",
        "aplicable": True,
        "esperado": 0.5,
        "estimado": promedioNumeros,
        "limite_inferior": limiteInferior,
        "limite_superior": limiteSuperior,
        "z_critico": valorCriticoNormal,
        "estadistico": estadisticoNormal,
        "p_valor": valorP,
        "pasa": pasaPrueba,
        "conclusion": (
            "El promedio esta dentro de los limites: NO se rechaza H0, "
            "el conjunto tiene valor esperado 0.5."
            if pasaPrueba else
            "El promedio esta fuera de los limites: se RECHAZA H0, "
            "el valor esperado no es 0.5."
        ),
    }


def prueba_varianza(numerosAleatorios, nivelSignificancia):
    cantidadNumeros = len(numerosAleatorios)
    if cantidadNumeros < 2:
        return {"nombre": "Prueba de varianza  ->  V(x) = 1/12",
                "aplicable": False,
                "conclusion": "Se necesitan al menos 2 numeros."}

    gradosLibertad = cantidadNumeros - 1

    promedioNumeros = sum(numerosAleatorios) / cantidadNumeros
    varianzaMuestral = sum((numero - promedioNumeros) ** 2 for numero in numerosAleatorios) / gradosLibertad

    chiCuadradaInferior = chi2.ppf(nivelSignificancia / 2.0, gradosLibertad)
    chiCuadradaSuperior = chi2.ppf(1.0 - nivelSignificancia / 2.0, gradosLibertad)
    limiteInferior = chiCuadradaInferior / (12.0 * gradosLibertad)
    limiteSuperior = chiCuadradaSuperior / (12.0 * gradosLibertad)

    estadisticoChiCuadrada = 12.0 * gradosLibertad * varianzaMuestral
    probabilidadAcumulada = chi2.cdf(estadisticoChiCuadrada, gradosLibertad)
    valorP = 2.0 * min(probabilidadAcumulada, 1.0 - probabilidadAcumulada)

    pasaPrueba = limiteInferior <= varianzaMuestral <= limiteSuperior

    return {
        "nombre": "Prueba de varianza  ->  V(x) = 1/12",
        "aplicable": True,
        "esperado": 1.0 / 12.0,
        "estimado": varianzaMuestral,
        "limite_inferior": limiteInferior,
        "limite_superior": limiteSuperior,
        "estadistico": estadisticoChiCuadrada,
        "gl": gradosLibertad,
        "p_valor": valorP,
        "pasa": pasaPrueba,
        "conclusion": (
            "La varianza esta dentro de los limites: NO se rechaza H0, "
            "el conjunto tiene varianza 1/12."
            if pasaPrueba else
            "La varianza esta fuera de los limites: se RECHAZA H0, "
            "la varianza no es 1/12."
        ),
    }


def prueba_uniformidad_chi2(numerosAleatorios, nivelSignificancia):
    cantidadNumeros = len(numerosAleatorios)

    cantidadIntervalos = max(2, round(math.sqrt(cantidadNumeros)))
    frecuenciaEsperada = cantidadNumeros / cantidadIntervalos

    frecuenciasObservadas = [0] * cantidadIntervalos
    for numeroAleatorio in numerosAleatorios:
        indiceIntervalo = int(numeroAleatorio * cantidadIntervalos)
        if indiceIntervalo >= cantidadIntervalos:
            indiceIntervalo = cantidadIntervalos - 1
        elif indiceIntervalo < 0:
            indiceIntervalo = 0
        frecuenciasObservadas[indiceIntervalo] += 1

    estadisticoChiCuadrada = sum(
        (frecuencia - frecuenciaEsperada) ** 2 / frecuenciaEsperada
        for frecuencia in frecuenciasObservadas
    )

    gradosLibertad = cantidadIntervalos - 1
    valorCritico = chi2.ppf(1.0 - nivelSignificancia, gradosLibertad)
    valorP = chi2.sf(estadisticoChiCuadrada, gradosLibertad)

    pasaPrueba = estadisticoChiCuadrada <= valorCritico

    return {
        "nombre": "Prueba de uniformidad (Chi-cuadrada)",
        "aplicable": True,
        "m_intervalos": cantidadIntervalos,
        "frecuencia_esperada": frecuenciaEsperada,
        "frecuencias_observadas": frecuenciasObservadas,
        "estadistico": estadisticoChiCuadrada,
        "critico": valorCritico,
        "gl": gradosLibertad,
        "p_valor": valorP,
        "pasa": pasaPrueba,
        "conclusion": (
            "chi2 calculado <= chi2 de tabla: NO se rechaza H0, "
            "los numeros son uniformes en (0, 1)."
            if pasaPrueba else
            "chi2 calculado > chi2 de tabla: se RECHAZA H0, "
            "los numeros no son uniformes."
        ),
    }


def prueba_uniformidad_ks(numerosAleatorios, nivelSignificancia):
    cantidadNumeros = len(numerosAleatorios)
    numerosOrdenados = sorted(numerosAleatorios)

    distanciaSuperior = max(
        (indice + 1) / cantidadNumeros - numerosOrdenados[indice]
        for indice in range(cantidadNumeros)
    )
    distanciaInferior = max(
        numerosOrdenados[indice] - indice / cantidadNumeros
        for indice in range(cantidadNumeros)
    )
    estadisticoKolmogorov = max(distanciaSuperior, distanciaInferior)

    valorCritico = float(ksone.ppf(1.0 - nivelSignificancia, cantidadNumeros))
    valorP = float(kstest(numerosAleatorios, "uniform").pvalue)

    pasaPrueba = estadisticoKolmogorov <= valorCritico

    return {
        "nombre": "Prueba de uniformidad (Kolmogorov-Smirnov)",
        "aplicable": True,
        "d_mas": distanciaSuperior,
        "d_menos": distanciaInferior,
        "estadistico": estadisticoKolmogorov,
        "critico": valorCritico,
        "p_valor": valorP,
        "pasa": pasaPrueba,
        "conclusion": (
            "D <= D critico: NO se rechaza H0, no hay diferencia "
            "significativa con la distribucion uniforme."
            if pasaPrueba else
            "D > D critico: se RECHAZA H0, los numeros no siguen "
            "una distribucion uniforme."
        ),
    }


def prueba_independencia_corridas(numerosAleatorios, nivelSignificancia):
    cantidadNumeros = len(numerosAleatorios)

    indicadoresSuperiores = [1 if numero > 0.5 else 0 for numero in numerosAleatorios]
    cantidadSuperiores = sum(indicadoresSuperiores)
    cantidadInferiores = cantidadNumeros - cantidadSuperiores

    if cantidadInferiores == 0 or cantidadSuperiores == 0 or cantidadNumeros < 3:
        return {
            "nombre": "Prueba de independencia (corridas arriba y abajo de la media)",
            "aplicable": False,
            "conclusion": "No se puede aplicar: se necesitan valores por encima "
                          "y por debajo de 0.5 y al menos 3 numeros.",
        }

    cantidadCorridas = 1
    for indiceNumero in range(1, cantidadNumeros):
        if indicadoresSuperiores[indiceNumero] != indicadoresSuperiores[indiceNumero - 1]:
            cantidadCorridas += 1

    mediaCorridas = (2.0 * cantidadInferiores * cantidadSuperiores) / cantidadNumeros + 0.5
    varianzaCorridas = (
        2.0 * cantidadInferiores * cantidadSuperiores
        * (2.0 * cantidadInferiores * cantidadSuperiores - cantidadNumeros)
        / (cantidadNumeros ** 2 * (cantidadNumeros - 1))
    )
    desviacionCorridas = math.sqrt(varianzaCorridas) if varianzaCorridas > 0 else float("nan")

    estadisticoNormal = (cantidadCorridas - mediaCorridas) / desviacionCorridas
    valorCriticoNormal = norm.ppf(1.0 - nivelSignificancia / 2.0)
    valorP = 2.0 * norm.sf(abs(estadisticoNormal))

    pasaPrueba = -valorCriticoNormal < estadisticoNormal < valorCriticoNormal

    return {
        "nombre": "Prueba de independencia (corridas arriba y abajo de la media)",
        "aplicable": True,
        "corridas": cantidadCorridas,
        "n0": cantidadInferiores,
        "n1": cantidadSuperiores,
        "mu": mediaCorridas,
        "sigma2": varianzaCorridas,
        "estadistico": estadisticoNormal,
        "z_critico": valorCriticoNormal,
        "p_valor": valorP,
        "pasa": pasaPrueba,
        "conclusion": (
            "Z0 dentro del intervalo (-z, z): NO se rechaza H0, "
            "los numeros son independientes."
            if pasaPrueba else
            "Z0 fuera del intervalo (-z, z): se RECHAZA H0, "
            "los numeros no son independientes."
        ),
    }


def ejecutar_pruebas(valoresAleatorios, nivelSignificancia):
    numerosAleatorios = [float(valor) for valor in valoresAleatorios]
    cantidadNumeros = len(numerosAleatorios)
    if cantidadNumeros < 2:
        return None

    pruebas = {
        "medias": prueba_medias(numerosAleatorios, nivelSignificancia),
        "varianza": prueba_varianza(numerosAleatorios, nivelSignificancia),
        "uniformidad_chi2": prueba_uniformidad_chi2(numerosAleatorios, nivelSignificancia),
        "uniformidad_ks": prueba_uniformidad_ks(numerosAleatorios, nivelSignificancia),
        "independencia": prueba_independencia_corridas(numerosAleatorios, nivelSignificancia),
    }
    aplicables = [p for p in pruebas.values() if p.get("aplicable")]
    aprobadas = [p for p in aplicables if p.get("pasa")]

    return {
        "n": cantidadNumeros,
        "alfa": nivelSignificancia,
        "confianza": round((1.0 - nivelSignificancia) * 100),
        "resumen": {
            "total": len(aplicables),
            "aprobadas": len(aprobadas),
            "todas_ok": len(aplicables) > 0 and len(aprobadas) == len(aplicables),
        },
        **pruebas,
    }


if __name__ == "__main__":
    print("norm.ppf(0.975)   =", round(float(norm.ppf(0.975)), 4), " (esperado 1.9600)")
    print("norm.ppf(0.95)    =", round(float(norm.ppf(0.95)), 4), " (esperado 1.6449)")
    print("chi2.ppf(0.95, 1) =", round(float(chi2.ppf(0.95, 1)), 4), " (esperado 3.8415)")
    print("chi2.ppf(0.95, 9) =", round(float(chi2.ppf(0.95, 9)), 4), " (esperado 16.919)")
    print("chi2.ppf(0.025,49)=", round(float(chi2.ppf(0.025, 49)), 4), " (esperado 31.555)")

    datos = [
        0.809, 0.042, 0.432, 0.538, 0.225, 0.88, 0.688, 0.772, 0.036, 0.854,
        0.397, 0.266, 0.821, 0.897, 0.07, 0.721, 0.087, 0.35, 0.779, 0.482,
        0.136, 0.855, 0.453, 0.197, 0.444, 0.799, 0.089, 0.691, 0.545, 0.857,
        0.692, 0.055, 0.348, 0.373, 0.436, 0.29, 0.015, 0.834, 0.599, 0.724,
        0.564, 0.709, 0.946, 0.754, 0.677, 0.128, 0.012, 0.498, 0.6, 0.913,
    ]
    ind = prueba_independencia_corridas(datos, 0.05)
    print("\nEjemplo 2.16 -> corridas:", ind["corridas"], "| n0:", ind["n0"],
          "| n1:", ind["n1"])
    print("mu =", round(ind["mu"], 2), " sigma^2 =", round(ind["sigma2"], 5),
          " Z0 =", round(ind["estadistico"], 4))

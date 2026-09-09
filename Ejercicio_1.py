import math


def extraer_digitos_centrales(numeroCompleto: int, cantidadDigitos: int) -> int:
    cadenaNumero = str(numeroCompleto)
    if len(cadenaNumero) % 2 == 1:
        cadenaNumero = "0" + cadenaNumero
    if len(cadenaNumero) < cantidadDigitos:
        cadenaNumero = cadenaNumero.zfill(cantidadDigitos)
    indiceInicio = (len(cadenaNumero) - cantidadDigitos) // 2
    return int(cadenaNumero[indiceInicio:indiceInicio + cantidadDigitos])


def cuadrados_medios(semillaInicial, cantidadDigitos, numeroIteraciones, detenerEnCiclo=True):
    listaResultados = []
    valorActual = semillaInicial
    valoresVistos = {valorActual: -1}
    cicloDetectado = None
    for numeroIteracion in range(numeroIteraciones):
        cuadradoActual = valorActual * valorActual
        siguienteValor = extraer_digitos_centrales(cuadradoActual, cantidadDigitos)
        numeroAleatorio = siguienteValor / (10 ** cantidadDigitos)
        listaResultados.append({"iteracion": numeroIteracion, "X_i": valorActual, "Y_i": cuadradoActual,
                                "X_i+1": siguienteValor, "r_i": numeroAleatorio})
        if cicloDetectado is None and siguienteValor in valoresVistos:
            cicloDetectado = {"primera_aparicion": valoresVistos[siguienteValor], "repite_iteracion": numeroIteracion,
                              "longitud": numeroIteracion - valoresVistos[siguienteValor], "valor": siguienteValor}
            if detenerEnCiclo:
                break
        valoresVistos[siguienteValor] = numeroIteracion
        valorActual = siguienteValor
    return {"filas": listaResultados, "ciclo": cicloDetectado}

 

def congruencial_lineal(valorInicial, multiplicador, constanteAditiva, modulo, numeroIteraciones, detenerEnCiclo=True):
    listaResultados = []
    valorActual = valorInicial
    valoresVistos = {valorActual: -1}
    cicloDetectado = None
    for numeroIteracion in range(numeroIteraciones):
        valorActual = (multiplicador * valorActual + constanteAditiva) % modulo
        numeroAleatorio = valorActual / (modulo - 1) if modulo > 1 else 0.0
        listaResultados.append({"iteracion": numeroIteracion, "X_i": valorActual, "r_i": numeroAleatorio})
        if cicloDetectado is None and valorActual in valoresVistos:
            cicloDetectado = {"primera_aparicion": valoresVistos[valorActual], "repite_iteracion": numeroIteracion,
                              "longitud": numeroIteracion - valoresVistos[valorActual], "valor": valorActual}
            if detenerEnCiclo:
                break
        valoresVistos[valorActual] = numeroIteracion
    return {"filas": listaResultados, "ciclo": cicloDetectado}


def cumple_periodo_maximo_lineal(modulo, multiplicador, constanteAditiva):
    esPotenciaDeDos = modulo > 0 and (modulo & (modulo - 1) == 0)
    multiplicadorValido = (multiplicador - 1) % 4 == 0
    constanteRelativamentePrima = math.gcd(constanteAditiva, modulo) == 1
    return [
        (esPotenciaDeDos, "m es una potencia de 2 (m = 2^g)"),
        (multiplicadorValido, "a = 1 + 4k, con k entero"),
        (constanteRelativamentePrima, "c es relativo primo a m"),
    ]

ALGORITMOS = {
    "1": {
        "id": "cuadrados_medios", "grupo": "No congruencial",
        "nombre": "Cuadrados medios",
        "congruencial": False,
        "formula": "Yi = (Xi)^2   ->   Xi+1 = dígitos centrales de Yi      ri = Xi+1 / 10^D",
        "descripcion": ("Algoritmo NO congruencial (no usa mod m). Von Neumann, 1940s. "
                        "Eleva la semilla al cuadrado y toma los D dígitos centrales."),
        "campos": [
            {"id": "semilla", "label": "Semilla X0 (D dígitos)", "tipo": "entero", "defecto": 5735},
            {"id": "d", "label": "Cantidad de dígitos D (>3)", "tipo": "entero", "defecto": 4},
        ],
        "columnas": [("iteracion", "i"), ("X_i", "Xi"), ("Y_i", "Yi = (Xi)^2"),
                     ("X_i+1", "Xi+1"), ("r_i", "ri")],
    },
    "2": {
        "id": "lineal", "grupo": "Congruencial",
        "nombre": "Congruencial lineal",
        "congruencial": True,
        "formula": "Xi+1 = (a*Xi + c) mod m      ri = Xi / (m-1)",
        "descripcion": ("Algoritmo CONGRUENCIAL (usa mod m). Lehmer, 1951. "
                        "Alcanza periodo máximo N = m si se cumplen las condiciones "
                        "de Banks, Carson, Nelson y Nicol."),
        "campos": [
            {"id": "x0", "label": "Semilla X0", "tipo": "entero", "defecto": 37},
            {"id": "a", "label": "Multiplicador a", "tipo": "entero", "defecto": 19},
            {"id": "c", "label": "Constante c", "tipo": "entero", "defecto": 33},
            {"id": "m", "label": "Módulo m", "tipo": "entero", "defecto": 100},
        ],
        "columnas": [("iteracion", "i"), ("X_i", "Xi"), ("r_i", "ri")],
    },
}



import math


def extraer_digitos_centrales(numero: int, d: int) -> int:
    """
    Devuelve los D digitos centrales de 'numero'.

    Regla del material (Cuadrados / Productos medios):
      - "Si no es posible obtener los D digitos centrales, se completan con ceros a la IZQUIERDA".
      - Los digitos centrales se toman quitando (len - D) / 2 digitos por
        cada lado. Para que el recorte sea simetrico la cadena debe tener
        longitud PAR (o al menos >= D); por eso:
          * si la longitud es impar  -> se antepone un cero.
          * si la longitud es menor que D -> se rellena a la izquierda hasta D.

    Ejemplos validados con las diapositivas (semilla 5735, D = 4):
        5735^2 = 32890225  -> "3289[0225]"? no: centrales -> 8902
        319^2  = 101761     -> len 6, se quita 1 por lado -> 0176   (r = 0.0176)
        176^2  = 30976      -> len 5 impar -> "030976" -> 3097       (r = 0.3097)
        1000^2 = 1000000    -> len 7 impar -> "01000000" -> 0000  (se degenera)
    """
    s = str(numero)
    if len(s) % 2 == 1:            # longitud impar -> centrar con un cero a la izquierda
        s = "0" + s
    if len(s) < d:                 # numero demasiado corto -> ceros a la izquierda
        s = s.zfill(d)
    inicio = (len(s) - d) // 2
    return int(s[inicio:inicio + d])


# =====================================================================
# 1. ALGORITMO NO CONGRUENCIAL: CUADRADOS MEDIOS
# =====================================================================
#   * NO usa la operacion modulo -> es NO congruencial.
#   * Una sola semilla X0 de D digitos (D > 3).
#   * Recurrencia:   Y_i = (X_i)^2   ->   X_{i+1} = D digitos centrales de Y_i
#                    r_{i+1} = X_{i+1} / 10^D           (queda en el intervalo [0, 1))
#   * No garantiza un periodo largo: puede degenerar a 0 rapidamente
#     (p. ej. con la semilla 1000).

def cuadrados_medios(semilla, d, n_iteraciones, detener_en_ciclo=True):
    resultados = []
    x_actual = semilla
    # La numeracion de iteraciones ARRANCA EN 0 (i = 0, 1, 2, ...).
    # La semilla se registra en la posicion -1 (es "previa" a la iteracion 0),
    # asi el calculo del periodo  longitud = i - primera_aparicion  sigue siendo exacto.
    vistos = {x_actual: -1}         # valor de X  ->  iteracion en la que aparecio
    ciclo = None
    for i in range(n_iteraciones):
        y_i = x_actual * x_actual                      # 1) elevar al cuadrado
        x_siguiente = extraer_digitos_centrales(y_i, d)  # 2) D digitos centrales
        r_i = x_siguiente / (10 ** d)                  # 3) normalizar a (0, 1)
        resultados.append({"iteracion": i, "X_i": x_actual, "Y_i": y_i,
                           "X_i+1": x_siguiente, "r_i": r_i})
        # deteccion de ciclo: si X_{i+1} ya habia salido, la secuencia se repetira
        if ciclo is None and x_siguiente in vistos:
            ciclo = {"primera_aparicion": vistos[x_siguiente], "repite_iteracion": i,
                     "longitud": i - vistos[x_siguiente], "valor": x_siguiente}
            if detener_en_ciclo:
                break
        vistos[x_siguiente] = i
        x_actual = x_siguiente                         # 4) la salida es la nueva semilla
    return {"filas": resultados, "ciclo": ciclo}

 

# =====================================================================
# 2. ALGORITMO CONGRUENCIAL: CONGRUENCIAL LINEAL
# =====================================================================
#   * SI usa la operacion modulo (mod m) -> es CONGRUENCIAL.
#   * Parametros enteros positivos:  X0 (semilla), a (multiplicador), c (constante aditiva), m (modulo).
#   * Recurrencia:   X_{i+1} = (a * X_i + c) mod m       ->   genera 0..m-1
#                    r_i = X_i / (m - 1)                 ->   lleva a (0, 1)
#   * Con c != 0 es "lineal"; si c = 0 se llama "multiplicativo".
#   * Alcanza el periodo maximo N = m si se cumplen las condiciones de
#     Banks, Carson, Nelson y Nicol (ver cumple_periodo_maximo_lineal).

def congruencial_lineal(x0, a, c, m, n_iteraciones, detener_en_ciclo=True):
    resultados = []
    x_actual = x0
    # Iteraciones numeradas DESDE 0.  La semilla X0 queda en la posicion -1.
    vistos = {x_actual: -1}         # valor de X  ->  iteracion en la que aparecio
    ciclo = None
    for i in range(n_iteraciones):
        x_actual = (a * x_actual + c) % m              # nucleo congruencial
        r_i = x_actual / (m - 1) if m > 1 else 0.0     # normalizacion a (0, 1)
        resultados.append({"iteracion": i, "X_i": x_actual, "r_i": r_i})
        # deteccion de ciclo: al repetirse un X, toda la secuencia se repite
        if ciclo is None and x_actual in vistos:
            ciclo = {"primera_aparicion": vistos[x_actual], "repite_iteracion": i,
                      "longitud": i - vistos[x_actual], "valor": x_actual}
            if detener_en_ciclo:
                break
        vistos[x_actual] = i
    return {"filas": resultados, "ciclo": ciclo}


# =====================================================================
# 3. CONDICIONES DE PERIODO MÁXIMO (Banks, Carson, Nelson & Nicol)
# =====================================================================

def cumple_periodo_maximo_lineal(m, a, c):
    es_potencia_de_2 = m > 0 and (m & (m - 1) == 0)
    a_valido = (a - 1) % 4 == 0
    c_relativo_primo = math.gcd(c, m) == 1
    return [
        (es_potencia_de_2, "m es una potencia de 2 (m = 2^g)"),
        (a_valido, "a = 1 + 4k, con k entero"),
        (c_relativo_primo, "c es relativo primo a m"),
    ]

# =====================================================================
# 4. CONFIGURACIÓN DE MENÚ (parámetros y columnas de cada algoritmo)
# =====================================================================

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



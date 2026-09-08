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


# =====================================================================
# 5. FUNCIONES DE ENTRADA POR TERMINAL
# =====================================================================
#   Estas funciones solo se usan al ejecutar  "python Ejercicio_1.py"
#   (modo consola). La aplicacion web (app.py) NO las usa.
#   Todas reintentan hasta recibir un dato valido.

def pedir_entero(mensaje, valor_por_defecto=None, minimo=None, maximo=None):
    """
    Pide un entero por teclado y lo devuelve.
      - Enter vacio  -> devuelve valor_por_defecto (si se dio).
      - texto no numerico  -> avisa y vuelve a preguntar.
      - fuera de [minimo, maximo]  -> avisa y vuelve a preguntar.
    """
    while True:
        entrada = input(mensaje).strip()
        if entrada == "" and valor_por_defecto is not None:
            return valor_por_defecto
        try:
            valor = int(entrada)
        except ValueError:
            print("   -> Debes ingresar un número entero.")
            continue
        if minimo is not None and valor < minimo:
            print(f"   -> El valor debe ser mayor o igual a {minimo}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"   -> El valor debe ser menor o igual a {maximo}.")
            continue
        return valor


def pedir_lista_enteros(mensaje, valor_por_defecto_str):
    """
    Pide varios enteros separados por comas (p. ej. "65, 89, 98") y devuelve
    la lista [65, 89, 98]. Enter vacio usa la cadena por defecto.
    (Lo usa el algoritmo aditivo, que necesita una secuencia previa.)
    """
    while True:
        entrada = input(mensaje).strip()
        if entrada == "":
            entrada = valor_por_defecto_str
        # separar por comas y descartar espacios / campos vacios
        partes = [p.strip() for p in entrada.split(",") if p.strip() != ""]
        if not partes:
            print("   -> Ingresa al menos un número.")
            continue
        try:
            return [int(p) for p in partes]
        except ValueError:
            print("   -> Todos los valores deben ser enteros separados por comas.")


def pedir_si_no(mensaje, valor_por_defecto=True):
    """
    Pregunta de si/no. Devuelve True/False.
    El sufijo [S/n] o [s/N] indica cual es la respuesta por defecto (Enter vacio).
    """
    sufijo = " [S/n]: " if valor_por_defecto else " [s/N]: "
    while True:
        entrada = input(mensaje + sufijo).strip().lower()
        if entrada == "":
            return valor_por_defecto
        if entrada in ("s", "si", "sí", "y", "yes"):
            return True
        if entrada in ("n", "no"):
            return False
        print("   -> Responde 's' o 'n'.")


def elegir_algoritmo():
    """
    Muestra el menu de algoritmos (agrupados en no congruenciales y
    congruenciales, leyendo el campo 'grupo' de ALGORITMOS) y devuelve la
    clave elegida ('1', '2', ...). Reintenta si la opcion no existe.
    """
    print("\n=== Algoritmos NO congruenciales ===")
    for clave, conf in ALGORITMOS.items():
        if conf["grupo"] == "No congruencial":
            print(f"  {clave}. {conf['nombre']}")
    print("\n=== Algoritmos congruenciales ===")
    for clave, conf in ALGORITMOS.items():
        if conf["grupo"] == "Congruencial":
            print(f"  {clave}. {conf['nombre']}")
    while True:
        eleccion = input("\nElige un algoritmo (número): ").strip()
        if eleccion in ALGORITMOS:
            return eleccion
        print("   -> Opción inválida, intenta de nuevo.")


def pedir_parametros(conf):
    """
    Recorre la lista 'campos' del algoritmo (definida en ALGORITMOS) y pide
    cada parametro por teclado, usando el tipo de campo para saber si es un
    entero suelto o una lista de enteros. Devuelve  {id_campo: valor}.
    """
    print(f"\n--- Parámetros para: {conf['nombre']} ---")
    print(f"Fórmula: {conf['formula']}\n")
    valores = {}
    for campo in conf["campos"]:
        if campo["tipo"] == "lista_enteros":
            defecto_str = ",".join(str(v) for v in campo["defecto"])
            mensaje = f"{campo['label']} [{defecto_str}]: "
            valores[campo["id"]] = pedir_lista_enteros(mensaje, defecto_str)
        else:
            mensaje = f"{campo['label']} [{campo['defecto']}]: "
            valores[campo["id"]] = pedir_entero(mensaje, campo["defecto"])
    return valores


# =====================================================================
# 6. EJECUCIÓN Y PRESENTACIÓN DE RESULTADOS  (modo consola)
# =====================================================================

def ejecutar(algoritmo_id, valores, n, detener):
    """
    Despacha al generador correcto segun el 'id' del algoritmo (el campo
    ALGORITMOS[clave]['id']) y devuelve su resultado {'filas', 'ciclo'}.
    Es el equivalente de consola a ejecutar_algoritmo() de app.py.
    """
    if algoritmo_id == "lineal":
        return congruencial_lineal(valores["x0"], valores["a"], valores["c"], valores["m"], n, detener)
    if algoritmo_id == "cuadrados_medios":
        return cuadrados_medios(valores["semilla"], valores["d"], n, detener)
    if algoritmo_id == "productos_medios":
        return productos_medios(valores["semilla0"], valores["semilla1"], valores["d"], n, detener)
    raise ValueError(f"Algoritmo desconocido: {algoritmo_id}")


def mostrar_tabla(columnas, filas, iteracion_ciclo=None):
    """
    Imprime la tabla de iteraciones alineada en columnas.
      columnas       : lista de pares (clave_en_la_fila, etiqueta_a_mostrar)
      filas          : lista de diccionarios que devuelve el generador
      iteracion_ciclo: numero de iteracion donde el ciclo se repite (para marcarla con *)
    """
    if not filas:
        print("No se generaron filas.")
        return

    def texto_celda(fila, key):
        # los r_i se muestran con 4 decimales; el resto tal cual
        valor = fila[key]
        return f"{valor:.4f}" if key == "r_i" else str(valor)

    # 1) calcular el ancho de cada columna = max(largo etiqueta, largo del dato mas largo) + 2
    anchos = []
    for key, label in columnas:
        ancho = len(label)
        for fila in filas:
            ancho = max(ancho, len(texto_celda(fila, key)))
        anchos.append(ancho + 2)

    # 2) encabezado y linea separadora
    encabezado = "".join(label.rjust(ancho) for (key, label), ancho in zip(columnas, anchos))
    print("\n" + encabezado)
    print("-" * len(encabezado))

    # 3) una linea por fila; se marca con * la iteracion donde se cierra el ciclo
    for fila in filas:
        marca = "  *" if fila["iteracion"] == iteracion_ciclo else "   "
        linea = "".join(texto_celda(fila, key).rjust(ancho) for (key, label), ancho in zip(columnas, anchos))
        print(linea + marca)

    if iteracion_ciclo is not None:
        print("\n  (*) fila donde el ciclo se vuelve a repetir")


def mostrar_ciclo(ciclo, detener):
    """
    Explica en palabras el diccionario 'ciclo' que devuelve el generador
    (o avisa si no se detecto ninguno).
    """
    if not ciclo:
        print("\nNo se detectó ningún ciclo dentro del número de iteraciones generado.")
        return
    print(f"\nCiclo detectado -> periodo = {ciclo['longitud']}")
    if ciclo['primera_aparicion'] < 0:
        print(f"  El valor {ciclo['valor']} corresponde a la semilla X0")
    else:
        print(f"  El valor {ciclo['valor']} ya había aparecido en la iteración {ciclo['primera_aparicion']}")
    print(f"  y vuelve a aparecer en la iteración {ciclo['repite_iteracion']}.")
    if detener:
        print("  La generación se detuvo automáticamente en ese punto.")
    else:
        print("  Se continuó generando aunque el ciclo ya se había cerrado.")


def mostrar_periodo_maximo(algoritmo_id, valores):
    """
    Solo para el congruencial lineal: evalua las 3 condiciones de periodo
    maximo y las imprime con [OK]/[NO], mas un veredicto final.
    Para cualquier otro algoritmo no hace nada.
    """
    if algoritmo_id == "lineal":
        condiciones = cumple_periodo_maximo_lineal(valores["m"], valores["a"], valores["c"])
    else:
        return

    print("\n--- Condiciones para periodo máximo (Banks, Carson, Nelson & Nicol) ---")
    for ok, texto in condiciones:
        marca = "OK " if ok else "NO "
        print(f"  [{marca}] {texto}")
    if all(ok for ok, _ in condiciones):
        print("  => Se cumplen todas: el algoritmo alcanza el periodo máximo con estos parámetros.")
    else:
        print("  => No se cumplen todas: el periodo puede ser menor al máximo teórico.")


# =====================================================================
# 7. PROGRAMA PRINCIPAL
# =====================================================================

def main():
    """
    Bucle principal del modo consola:
      1. elegir algoritmo          (elegir_algoritmo)
      2. pedir sus parametros      (pedir_parametros)
      3. pedir n y si detener      (pedir_entero / pedir_si_no)
      4. generar la secuencia      (ejecutar)
      5. mostrar tabla, ciclo y condiciones de periodo maximo
      6. preguntar si se repite; si no, salir.
    """
    print("=" * 64)
    print(" GENERADOR DE NÚMEROS PSEUDOALEATORIOS")
    print(" Modelación · Semana 3 y 4 · Universidad de Cundinamarca")
    print("=" * 64)

    while True:
        # --- 1 y 2) algoritmo y parametros ---------------------------
        clave = elegir_algoritmo()
        conf = ALGORITMOS[clave]
        valores = pedir_parametros(conf)

        # --- 3) cuantos numeros y si parar al detectar ciclo --------
        n = pedir_entero("\nNúmero máximo de iteraciones [50]: ", 50, minimo=1, maximo=100000)
        detener = pedir_si_no("¿Detener automáticamente al completar un ciclo?", True)

        # --- 4) generar ------------------------------------------
        resultado = ejecutar(conf["id"], valores, n, detener)
        filas = resultado["filas"]
        ciclo = resultado["ciclo"]
        iteracion_ciclo = ciclo["repite_iteracion"] if ciclo else None

        # --- 5) mostrar resultados -------------------------------
        print(f"\n>>> {conf['nombre']}")
        print(f">>> {conf['formula']}")
        mostrar_tabla(conf["columnas"], filas, iteracion_ciclo)
        mostrar_ciclo(ciclo, detener)
        mostrar_periodo_maximo(conf["id"], valores)

        # --- 6) otra vuelta? ------------------------------------
        if not pedir_si_no("\n¿Deseas generar otra secuencia?", False):
            break

    print("\nHasta luego.")


# Punto de entrada: solo corre el menu de consola si se ejecuta este archivo
# directamente ("python Ejercicio_1.py"). Al importarlo desde app.py no pasa nada.
if __name__ == "__main__":
    main()
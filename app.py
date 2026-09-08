"""
==========================================================================
 APLICACION WEB (Flask)  -  Generador y validador de numeros pseudoaleatorios
==========================================================================

Este archivo es solo la INTERFAZ: recibe el formulario, valida los datos,
llama a los modulos de calculo y entrega los resultados a la plantilla.
No contiene matematica; esa vive en:

    Ejercicio_1.py  ->  algoritmos generadores (cuadrados medios, congruencial lineal)
    pruebas.py      ->  las 5 pruebas estadisticas

Flujo de una peticion POST:

    formulario  ->  leer_parametros()   (valida)
                ->  ejecutar_algoritmo() (genera la secuencia r)
                ->  cumple_periodo_maximo_lineal()  (solo congruencial)
                ->  ejecutar_pruebas()   (valida la secuencia)
                ->  render_template('index.html', ...)
"""

from flask import Flask, render_template, request, redirect, url_for

from Ejercicio_1 import (
    ALGORITMOS,
    congruencial_lineal,
    cuadrados_medios,
    cumple_periodo_maximo_lineal,
)
from pruebas import ejecutar_pruebas

app = Flask(__name__)

# Niveles de significancia que el usuario puede elegir en el formulario.
# clave (texto que llega del <select>)  ->  valor numerico alfa
ALFAS = {"0.10": 0.10, "0.05": 0.05, "0.01": 0.01}


# =====================================================================
# RUTAS
# =====================================================================

@app.route('/', methods=['GET', 'POST'])
def ejercicio_1():
    """Pagina principal: el usuario elige el algoritmo en el <select>."""
    return generador()


@app.route('/congruencia-lineal', methods=['GET', 'POST'])
def apartado_congruencia_lineal():
    """Atajo que abre la pagina fijada en el algoritmo '2' (congruencial lineal)."""
    return generador('2')


# =====================================================================
# CONTROLADOR PRINCIPAL
# =====================================================================

def generador(algoritmo_fijo=None):
    """
    Arma la respuesta de la pagina para GET y para POST.

    Parametros
      algoritmo_fijo : '1' o '2' si la ruta obliga a un algoritmo; None si
                       el usuario lo elige libremente.

    En GET  -> muestra el formulario con los valores por defecto.
    En POST -> valida, genera la secuencia, corre las pruebas y muestra todo.
    """
    # --- 1) que algoritmo se va a usar ------------------------------
    #   Prioridad:  el que fija la ruta  >  el del formulario (POST)  >
    #               el de la query string (?algoritmo=)  >  '1' por defecto.
    algoritmo = (algoritmo_fijo or request.form.get('algoritmo')
                 or request.args.get('algoritmo', '1'))
    if algoritmo not in ALGORITMOS:
        algoritmo = '1'

    # --- 2) valores que vera el formulario -------------------------
    valores = valores_por_defecto(algoritmo)
    resultado = None        # tabla de iteraciones + info del ciclo
    error = None            # mensaje de error de validacion, si lo hay
    condiciones = None      # condiciones de periodo maximo (solo congruencial)
    pruebas = None          # resultado de las 5 pruebas estadisticas
    alfa_sel = request.form.get('alfa', '0.05')

    # --- 3) si el usuario envio el formulario, procesarlo ----------
    if request.method == 'POST':
        try:
            # 3a) leer y validar los parametros del algoritmo
            valores = leer_parametros(algoritmo)
            # 3b) cuantos numeros generar (1 .. 100000)
            iteraciones = entero_formulario('iteraciones', minimo=1, maximo=100000)
            # 3c) checkbox: detener al detectar el primer ciclo
            detener = request.form.get('detener') == 'on'
            # 3d) generar la secuencia con el algoritmo elegido
            resultado = ejecutar_algoritmo(algoritmo, valores, iteraciones, detener)

            # 3e) condiciones de periodo maximo: SOLO para el congruencial lineal
            if algoritmo == '2':
                condiciones = cumple_periodo_maximo_lineal(
                    valores['m'], valores['a'], valores['c']
                )

            # 3f) pruebas estadisticas sobre la lista de r generada (ambos algoritmos)
            valores_r = [fila['r_i'] for fila in resultado['filas']]
            pruebas = ejecutar_pruebas(valores_r, ALFAS.get(alfa_sel, 0.05))
        except ValueError as exc:
            # cualquier dato invalido llega aqui como texto para mostrarlo en rojo
            error = str(exc)

    # --- 4) renderizar la plantilla con todo lo calculado ---------
    return render_template(
        'index.html',
        algoritmos=ALGORITMOS,
        algoritmo=algoritmo,
        valores=valores,
        resultado=resultado,
        condiciones=condiciones,
        pruebas=pruebas,
        alfas=ALFAS,
        alfa_sel=alfa_sel,
        error=error,
    )


# =====================================================================
# LECTURA Y VALIDACION DEL FORMULARIO
# =====================================================================

def entero_formulario(nombre, minimo=None, maximo=None):
    """
    Devuelve request.form[nombre] convertido a int, validando el rango.
    Si el campo falta, no es entero, o se sale de [minimo, maximo],
    lanza ValueError con un mensaje legible (que la vista muestra al usuario).
    """
    try:
        valor = int(request.form[nombre])
    except (KeyError, ValueError):
        raise ValueError(f'{nombre}: debe ser un número entero.')
    if minimo is not None and valor < minimo:
        raise ValueError(f'{nombre}: debe ser mayor o igual que {minimo}.')
    if maximo is not None and valor > maximo:
        raise ValueError(f'{nombre}: debe ser menor o igual que {maximo}.')
    return valor


def valores_por_defecto(algoritmo):
    """
    Diccionario  {id_campo: valor_por_defecto}  para el algoritmo dado,
    leyendo la definicion de ALGORITMOS. Sirve para pintar el formulario
    en blanco (GET) o para partir de una base en POST.
    """
    return {
        campo['id']: campo['defecto']
        for campo in ALGORITMOS[algoritmo]['campos']
    }


def leer_parametros(algoritmo):
    """
    Lee del formulario TODOS los campos que necesita el algoritmo y los valida.
    Devuelve el diccionario de parametros ya convertidos a int.
    Lanza ValueError (con mensaje) ante cualquier dato invalido.

    Reglas propias de cada algoritmo:
      - Cuadrados medios ('1'):  D > 3  y la semilla debe tener al menos D digitos.
      - Congruencial lineal ('2'):  x0, a, c >= 0  y  m > 1.
    """
    # 1) partir de los valores por defecto y sobrescribir con lo que envio el usuario
    valores = valores_por_defecto(algoritmo)
    for campo in ALGORITMOS[algoritmo]['campos']:
        valores[campo['id']] = entero_formulario(campo['id'])

    # 2) validaciones especificas de CUADRADOS MEDIOS
    if algoritmo == '1':
        if valores['d'] <= 3:
            raise ValueError('D: debe ser mayor que 3.')
        if len(str(abs(valores['semilla']))) < valores['d']:
            raise ValueError('La semilla X0 debe tener al menos D dígitos.')

    # 3) validaciones especificas de CONGRUENCIAL LINEAL
    if algoritmo == '2':
        for clave in ('x0', 'a', 'c'):
            if valores[clave] < 0:
                raise ValueError(f'{clave}: debe ser un entero positivo.')
        if valores['m'] <= 1:
            raise ValueError('m: debe ser mayor que 1.')

    return valores


def ejecutar_algoritmo(algoritmo, valores, iteraciones, detener):
    """
    Segun el algoritmo elegido ('1' o '2') llama al generador correspondiente
    de Ejercicio_1.py y devuelve su resultado  {'filas': [...], 'ciclo': ...}.
    """
    if algoritmo == '1':
        return cuadrados_medios(
            valores['semilla'], valores['d'], iteraciones, detener
        )
    return congruencial_lineal(
        valores['x0'], valores['a'], valores['c'], valores['m'],
        iteraciones, detener
    )


# =====================================================================
# ARRANQUE DEL SERVIDOR DE DESARROLLO
# =====================================================================

if __name__ == '__main__':
    import os
    # debug=True recarga al guardar y muestra errores detallados.
    # El puerto se puede fijar con la variable de entorno PORT (5000 por defecto).
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))

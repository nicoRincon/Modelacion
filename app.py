from flask import Flask, render_template, request, redirect, url_for

from Ejercicio_1 import (
    ALGORITMOS,
    congruencial_lineal,
    cuadrados_medios,
    cumple_periodo_maximo_lineal,
)
from pruebas import ejecutar_pruebas

app = Flask(__name__)

# Niveles de significancia disponibles para las pruebas estadisticas.
ALFAS = {"0.10": 0.10, "0.05": 0.05, "0.01": 0.01}


@app.route('/', methods=['GET', 'POST'])
def ejercicio_1():
    return generador()


@app.route('/congruencia-lineal', methods=['GET', 'POST'])
def apartado_congruencia_lineal():
    return generador('2')


def generador(algoritmo_fijo=None):
    algoritmo = (algoritmo_fijo or request.form.get('algoritmo')
                 or request.args.get('algoritmo', '1'))
    if algoritmo not in ALGORITMOS:
        algoritmo = '1'
    valores = valores_por_defecto(algoritmo)
    resultado = None
    error = None
    condiciones = None
    pruebas = None
    alfa_sel = request.form.get('alfa', '0.05')

    if request.method == 'POST':
        try:
            valores = leer_parametros(algoritmo)
            iteraciones = entero_formulario('iteraciones', minimo=1, maximo=100000)
            detener = request.form.get('detener') == 'on'
            resultado = ejecutar_algoritmo(algoritmo, valores, iteraciones, detener)

            # Solo el congruencial lineal tiene condiciones de periodo maximo.
            if algoritmo == '2':
                condiciones = cumple_periodo_maximo_lineal(
                    valores['m'], valores['a'], valores['c']
                )

            # Pruebas estadisticas sobre el conjunto r generado (ambos algoritmos).
            valores_r = [fila['r_i'] for fila in resultado['filas']]
            pruebas = ejecutar_pruebas(valores_r, ALFAS.get(alfa_sel, 0.05))
        except ValueError as exc:
            error = str(exc)

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


def entero_formulario(nombre, minimo=None, maximo=None):
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
    return {
        campo['id']: campo['defecto']
        for campo in ALGORITMOS[algoritmo]['campos']
    }


def leer_parametros(algoritmo):
    valores = valores_por_defecto(algoritmo)
    for campo in ALGORITMOS[algoritmo]['campos']:
        valores[campo['id']] = entero_formulario(campo['id'])
    if algoritmo == '1':
        if valores['d'] <= 3:
            raise ValueError('D: debe ser mayor que 3.')
        if len(str(abs(valores['semilla']))) < valores['d']:
            raise ValueError('La semilla X0 debe tener al menos D dígitos.')
    if algoritmo == '2':
        for clave in ('x0', 'a', 'c'):
            if valores[clave] < 0:
                raise ValueError(f'{clave}: debe ser un entero positivo.')
        if valores['m'] <= 1:
            raise ValueError('m: debe ser mayor que 1.')
    return valores


def ejecutar_algoritmo(algoritmo, valores, iteraciones, detener):
    if algoritmo == '1':
        return cuadrados_medios(
            valores['semilla'], valores['d'], iteraciones, detener
        )
    return congruencial_lineal(
        valores['x0'], valores['a'], valores['c'], valores['m'],
        iteraciones, detener
    )


if __name__ == '__main__':
    import os
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))

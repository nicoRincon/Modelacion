from flask import Flask, render_template, request, redirect, url_for

from Ejercicio_1 import (
    ALGORITMOS,
    congruencial_lineal,
    cuadrados_medios,
    cumple_periodo_maximo_lineal,
)
from pruebas import ejecutar_pruebas

app = Flask(__name__)

ALFAS = {"0.10": 0.10, "0.05": 0.05, "0.01": 0.01}


@app.route('/index', methods=['GET', 'POST'])
def ejercicio_1():
    return generador()


@app.route('/')
def inicio():
    return render_template('Presentacion.html')


@app.route('/congruencia-lineal', methods=['GET', 'POST'])
def apartado_congruencia_lineal():
    return generador('2')


@app.route('/presentacion')
def presentacion():
    return render_template('Presentacion.html')


def generador(algoritmoFijo=None):
    algoritmoSeleccionado = (algoritmoFijo or request.form.get('algoritmo')
                 or request.args.get('algoritmo', '1'))
    if algoritmoSeleccionado not in ALGORITMOS:
        algoritmoSeleccionado = '1'

    valoresFormulario = valores_por_defecto(algoritmoSeleccionado)
    resultadoGeneracion = None
    mensajeError = None
    condicionesPeriodo = None
    resultadosPruebas = None
    nivelSignificanciaSeleccionado = request.form.get('alfa')

    if request.method == 'POST':
        try:
            valoresFormulario = leer_parametros(algoritmoSeleccionado)
            numeroIteraciones = entero_formulario(
                'iteraciones', valorMinimo=1, valorMaximo=100000
            )
            detenerEnCiclo = request.form.get('detener') == 'on'
            resultadoGeneracion = ejecutar_algoritmo(
                algoritmoSeleccionado, valoresFormulario, numeroIteraciones, detenerEnCiclo
            )

            if algoritmoSeleccionado == '2':
                condicionesPeriodo = cumple_periodo_maximo_lineal(
                    valoresFormulario['m'], valoresFormulario['a'], valoresFormulario['c']
                )

            numerosAleatorios = [fila['r_i'] for fila in resultadoGeneracion['filas']]
            if nivelSignificanciaSeleccionado not in ALFAS:
                raise ValueError('Nivel de significancia: debe seleccionar una opción válida.')
            resultadosPruebas = ejecutar_pruebas(
                numerosAleatorios, ALFAS[nivelSignificanciaSeleccionado]
            )
        except ValueError as exc:
            mensajeError = str(exc)

    return render_template(
        'index.html',
        algoritmos=ALGORITMOS,
        algoritmo=algoritmoSeleccionado,
        valores=valoresFormulario,
        resultado=resultadoGeneracion,
        condiciones=condicionesPeriodo,
        pruebas=resultadosPruebas,
        alfas=ALFAS,
        alfa_sel=nivelSignificanciaSeleccionado,
        error=mensajeError,
    )


def entero_formulario(nombreCampo, valorMinimo=None, valorMaximo=None):
    try:
        valorEntero = int(request.form[nombreCampo])
    except (KeyError, ValueError):
        raise ValueError(f'{nombreCampo}: debe ser un número entero.')
    if valorMinimo is not None and valorEntero < valorMinimo:
        raise ValueError(f'{nombreCampo}: debe ser mayor o igual que {valorMinimo}.')
    if valorMaximo is not None and valorEntero > valorMaximo:
        raise ValueError(f'{nombreCampo}: debe ser menor o igual que {valorMaximo}.')
    return valorEntero


def valores_por_defecto(algoritmoSeleccionado):
    return {
        campo['id']: campo['defecto']
        for campo in ALGORITMOS[algoritmoSeleccionado]['campos']
    }


def leer_parametros(algoritmoSeleccionado):
    valoresFormulario = valores_por_defecto(algoritmoSeleccionado)
    for campoFormulario in ALGORITMOS[algoritmoSeleccionado]['campos']:
        valoresFormulario[campoFormulario['id']] = entero_formulario(campoFormulario['id'])

    if algoritmoSeleccionado == '1':
        if valoresFormulario['d'] <= 3:
            raise ValueError('D: debe ser mayor que 3.')
        if len(str(abs(valoresFormulario['semilla']))) < valoresFormulario['d']:
            raise ValueError('La semilla X0 debe tener al menos D dígitos.')

    if algoritmoSeleccionado == '2':
        for nombreCampo in ('x0', 'a', 'c'):
            if valoresFormulario[nombreCampo] < 0:
                raise ValueError(f'{nombreCampo}: debe ser un entero positivo.')
        if valoresFormulario['m'] <= 1:
            raise ValueError('m: debe ser mayor que 1.')

    return valoresFormulario


def ejecutar_algoritmo(algoritmoSeleccionado, valoresFormulario, numeroIteraciones, detenerEnCiclo):
    if algoritmoSeleccionado == '1':
        return cuadrados_medios(
            valoresFormulario['semilla'], valoresFormulario['d'], numeroIteraciones, detenerEnCiclo
        )
    return congruencial_lineal(
        valoresFormulario['x0'], valoresFormulario['a'], valoresFormulario['c'], valoresFormulario['m'],
        numeroIteraciones, detenerEnCiclo
    )


if __name__ == '__main__':
    import os
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))

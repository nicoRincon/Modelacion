from flask import Flask, render_template, request, redirect, url_for

from Ejercicio_1 import (
    ALGORITMOS,
    congruencial_lineal,
    cumple_periodo_maximo_lineal,
    productos_medios,
)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def ejercicio_1():
    return generador()


@app.route('/congruencia-lineal', methods=['GET', 'POST'])
def apartado_congruencia_lineal():
    return generador('2')


def generador(algoritmo_fijo=None):
    algoritmo = algoritmo_fijo or request.form.get('algoritmo', '1')
    valores = valores_por_defecto(algoritmo)
    resultado = None
    error = None
    condiciones = None

    if request.method == 'POST':
        try:
            valores = leer_parametros(algoritmo)
            iteraciones = entero_formulario('iteraciones', minimo=1, maximo=100000)
            detener = request.form.get('detener') == 'on'
            resultado = ejecutar_algoritmo(algoritmo, valores, iteraciones, detener)
            if algoritmo == '2':
                condiciones = cumple_periodo_maximo_lineal(
                    valores['m'], valores['a'], valores['c']
                )
        except ValueError as exc:
            error = str(exc)

    return render_template(
        'index.html',
        algoritmos=ALGORITMOS,
        algoritmo=algoritmo,
        valores=valores,
        resultado=resultado,
        condiciones=condiciones,
        error=error,
    )


def entero_formulario(nombre, minimo=None, maximo=None):
    valor = int(request.form[nombre])
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
    if algoritmo == '1' and valores['d'] <= 3:
        raise ValueError('d: debe ser mayor que 3.')
    return valores


def ejecutar_algoritmo(algoritmo, valores, iteraciones, detener):
    if algoritmo == '1':
        return productos_medios(
            valores['semilla0'], valores['semilla1'], valores['d'],
            iteraciones, detener
        )
    return congruencial_lineal(
        valores['x0'], valores['a'], valores['c'], valores['m'],
        iteraciones, detener
    )


if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request, send_from_directory

from Ejercicio_1 import (
    ALGORITMOS,
    congruencial_lineal,
    cuadrados_medios,
    cumple_periodo_maximo_lineal,
)
from pruebas import ejecutar_pruebas
from VariablesAleatoria import analizar_excel
from Modelacion import (LAMBDA_OBSERVADO, PARAMETROS_DEFECTO, TABLA_EVENTOS,
                        calcular_carga, ejecutar)
from Experimento import CONFIG_DEFECTO, ejecutar_experimento
from Verificacion import verificar

app = Flask(__name__)

ALFAS = {"0.10": 0.10, "0.05": 0.05, "0.01": 0.01}


@app.route('/index', methods=['GET', 'POST'])
def ejercicio_1():
    return generador()


@app.route('/')
def inicio():
    return render_template('menu.html')


@app.route('/congruencia-lineal', methods=['GET', 'POST'])
def apartado_congruencia_lineal():
    return generador('2')


@app.route('/presentacion')
def presentacion():
    return render_template('Presentacion.html')


@app.route('/cuento-peaje')
def cuento_peaje():
    return send_from_directory(app.root_path, 'El cuento del peaje (ampliada).html')


@app.route('/analisis-datos')
def analisis_datos():
    try:
        analisis = analizar_excel(app.root_path + '/63496000.xlsx')
        error = None
    except (OSError, ValueError) as exc:
        analisis = None
        error = str(exc)
    return render_template('analisis.html', analisis=analisis, error=error)


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

# --------------------------------------------------------------------------
# Peaje: actividad integradora
# --------------------------------------------------------------------------
# Límites de cada campo numérico: (tipo, mínimo, máximo)
LIMITES = {
    "n_carros": (int, 10, 5000),
    "n_taquillas": (int, 1, 5),
    "media_llegadas": (float, 0.05, 10),
    "media_pago": (float, 0.1, 10),
    "desv_pago": (float, 0.01, 5),
    "media_arranque": (float, 0.05, 5),
    "desv_arranque": (float, 0.01, 2),
    "semilla": (int, 0, 10**9),
    "replicas": (int, 5, 200),
    "calentamiento": (int, 0, 2000),
    "meta": (float, 0.1, 100),
    "epsilon": (float, 0.001, 10),
}
NOMBRES = {
    "n_carros": "Número de carros", "n_taquillas": "Número de taquillas",
    "media_llegadas": "Media entre llegadas", "media_pago": "Media de pago",
    "desv_pago": "Desviación de pago", "media_arranque": "Media de arranque",
    "desv_arranque": "Desviación de arranque", "semilla": "Semilla",
    "replicas": "Réplicas", "calentamiento": "Calentamiento", "meta": "Meta", "epsilon": "Error ε",
}


def leer_numeros(form, base):
    """Copia `base` y reemplaza los campos que vengan en el formulario, validando límites."""
    valores = dict(base)
    for clave in base:
        if clave not in LIMITES or clave not in form:
            continue
        texto = form.get(clave, "").strip()
        if texto == "":
            if clave == "semilla":
                valores[clave] = None
            continue
        tipo, minimo, maximo = LIMITES[clave]
        try:
            numero = tipo(float(texto)) if tipo is float else int(texto)
        except ValueError:
            raise ValueError(f"{NOMBRES[clave]}: debe ser un número{' entero' if tipo is int else ''}.")
        if not minimo <= numero <= maximo:
            raise ValueError(f"{NOMBRES[clave]}: debe estar entre {minimo} y {maximo}.")
        valores[clave] = numero
    return valores


@app.route("/modelo")
def modelo():
    p = PARAMETROS_DEFECTO
    return render_template(
        "modelo.html", p=p, lam=LAMBDA_OBSERVADO, meta=CONFIG_DEFECTO["meta"],
        tabla_eventos=TABLA_EVENTOS,
        carga=calcular_carga(p["media_llegadas"], p["media_pago"], p["media_arranque"], p["n_taquillas"]),
    )


@app.route("/peaje", methods=["GET", "POST"])
def peaje():
    error = None
    parametros = PARAMETROS_DEFECTO
    if request.method == "POST":
        try:
            parametros = leer_numeros(request.form, PARAMETROS_DEFECTO)
        except ValueError as exc:
            error = str(exc)
    return render_template("Peaje.html", error=error, **ejecutar(parametros))


@app.route("/verificacion")
def verificacion():
    return render_template("verificacion.html", v=verificar())


@app.route("/experimento", methods=["GET", "POST"])
def experimento():
    error = None
    config = dict(CONFIG_DEFECTO)
    if request.method == "POST":
        try:
            config = leer_numeros(request.form, CONFIG_DEFECTO)
            if config["semilla"] is None:
                config["semilla"] = 2026
            config["alfa"] = ALFAS.get(request.form.get("alfa"), 0.05)
            taquillas = sorted({int(t) for t in request.form.getlist("taquillas") if t.isdigit()})
            if len(taquillas) < 2 or not all(1 <= t <= 6 for t in taquillas):
                raise ValueError("Escenarios: seleccione al menos dos números de taquillas.")
            config["taquillas"] = taquillas
            if config["calentamiento"] >= config["n_carros"] // 2:
                raise ValueError("Calentamiento: debe ser menor que la mitad de los carros por réplica.")
        except ValueError as exc:
            error = str(exc)
            config = dict(CONFIG_DEFECTO)
    return render_template("experimento.html", config=config, error=error, alfas=ALFAS,
                           r=ejecutar_experimento(config))


if __name__ == '__main__':
    import os
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))

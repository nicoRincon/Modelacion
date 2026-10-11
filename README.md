# Modelacion

Aplicación Flask del curso de Modelación y simulación (Universidad de Cundinamarca).

## Ejecutar

```bash
pip install -r requirements.txt
python app.py
```

Abrir http://localhost:5000.

## Actividad integradora: simulación del peaje

Pregunta: ¿cuántas taquillas necesita el peaje para que un carro pase menos de 2 minutos en el sistema,
con llegadas Poisson de λ = 2.083 carros/min (ajustadas en la entrega anterior)?

| Página | Puntos de la actividad | Contenido |
|---|---|---|
| `/modelo` | 1 a 4 | Sistema, problema, variables y relaciones lógico-matemáticas |
| `/peaje` | 5 | Simulación de una corrida: tabla carro por carro y estabilización |
| `/verificacion` | 6 | Revisión automática de las relaciones, pruebas KS de las entradas y comparación con la teoría M/G/c |
| `/experimento` | 7 a 12 | Réplicas, método de Welch, estadísticos, histogramas, cajas, pruebas de hipótesis, intervalos de confianza, escenarios, sensibilidad y conclusión |

## Archivos

| Archivo | Qué hace |
|---|---|
| `Modelacion.py` | Simulador del peaje (misma lógica que el Excel "Proceso de Inspección") y réplicas |
| `Estadistica.py` | Descriptivos, normalidad, intervalos (t y Tchebycheff), longitud de réplica y pruebas de hipótesis |
| `Experimento.py` | Corre los escenarios, la curva de Welch y la sensibilidad a la demanda |
| `Verificacion.py` | Verificación y validación del modelo |
| `app.py` | Rutas de Flask |

Las entregas anteriores (generador de números pseudoaleatorios, pruebas y análisis de datos) siguen disponibles desde el menú.

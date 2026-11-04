from machine import ADC, Pin
from math import sqrt
from time import sleep, ticks_ms, ticks_diff, sleep_us


sensorDC = ADC(Pin(1))
sensorDC.atten(ADC.ATTN_11DB)
sensorDC.width(ADC.WIDTH_12BIT)

rele = Pin(2, Pin.OUT)

sensorACup = ADC(Pin(3))
sensorACup.atten(ADC.ATTN_11DB)

sensorACdn = ADC(Pin(4))
sensorACdn.atten(ADC.ATTN_11DB)

def leer_rms_adc(adc, duracion_ms=1000):
    cantidad = 0
    suma = 0
    suma_cuadrados = 0
    minimo = 4095
    maximo = 0
    inicio = ticks_ms()

    while ticks_diff(ticks_ms(), inicio) < duracion_ms:
        lectura = adc.read()

        cantidad += 1
        suma += lectura
        suma_cuadrados += lectura * lectura
        minimo = min(minimo, lectura)
        maximo = max(maximo, lectura)

        sleep_us(200)

    promedio = suma / cantidad
    varianza = suma_cuadrados / cantidad - promedio * promedio
    rms = sqrt(max(varianza, 0))

    return rms, promedio, minimo, maximo


# Cada canal tiene un nivel de ruido distinto por su sensor y divisor resistivo.
UMBRAL_AC_ENTRADA = 100
UMBRAL_AC_SALIDA = 100
FACTOR_AC_ENTRADA = 232.0 / 700.0
FACTOR_AC_SALIDA = 232.0 / 248.0


def mostrar_estado_sensor(nombre, adc, umbral, factor_ac):
    rms_adc, promedio, minimo, maximo = leer_rms_adc(adc)
    hay_tension = rms_adc >= umbral
    tension_ac = rms_adc * factor_ac if hay_tension else 0.0

    print("Sensor AC", nombre)
    print("RMS ADC:", rms_adc)
    print("Punto medio:", promedio)
    print("Mínimo:", minimo)
    print("Máximo:", maximo)
    print("Tensión AC detectada:", "SÍ" if hay_tension else "NO")
    print("Tensión AC: {:.1f} V".format(tension_ac))

    return hay_tension


while(True):
    print("-----------------")
    mostrar_estado_sensor(
        "Entrada", sensorACup, UMBRAL_AC_ENTRADA, FACTOR_AC_ENTRADA
    )

    print("-----------------")
    mostrar_estado_sensor(
        "Salida", sensorACdn, UMBRAL_AC_SALIDA, FACTOR_AC_SALIDA
    )

    sleep(2)

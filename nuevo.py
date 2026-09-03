x0 = 21
MOD = 31
x1 = (21 * x0 + 15) % MOD
Ri = x1 / (MOD - 1)
cadena = str(Ri)
primeros_5 = cadena[0:6]
print(primeros_5)

for i in range(0, MOD):
    xi = (21 * x1 + 15) % MOD
    Ri = xi / (MOD - 1)
    cadena = str(Ri)
    primeros_5 = cadena[0:6]
    print(primeros_5)
    x1 = xi


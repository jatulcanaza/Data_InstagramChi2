import instaloader
import pandas as pd
import time
import math  # Para funciones matemáticas
import matplotlib.pyplot as plt
from instaloader.exceptions import ConnectionException, BadResponseException
from scipy.stats import chi2  # Para calcular el valor crítico y p-valor

# Configuración
print("*** Sistema de Scrapy en Instagram ***")
nombre_usuario = input("Ingrese su nombre de usuario (Instagram): ")
contrasena_usuario = input("Ingrese la contraseña de su Instagram: ")
nombre_usuario_formateado = nombre_usuario.replace(" ", "_").lower()
output_csv = f"{nombre_usuario_formateado}_seguidores.csv"

# Función para manejar errores y reintentar
def process_profile_with_retry(profile, retries=3):
    for attempt in range(retries):
        try:
            return profile.followers
        except (ConnectionException, BadResponseException):
            print(f"Error al intentar acceder al perfil. Reintento {attempt + 1}/{retries}...")
            time.sleep(10)
    print("No se pudo acceder al perfil después de múltiples intentos.")
    return None

# Crear instancia de Instaloader y autenticarse
loader = instaloader.Instaloader()
try:
    loader.login(nombre_usuario, contrasena_usuario)
except Exception as e:
    print(f"Error al iniciar sesión: {e}")
    exit(1)

# Obtener perfil principal
try:
    profile = instaloader.Profile.from_username(loader.context, nombre_usuario)
except Exception as e:
    print(f"Error al obtener el perfil principal: {e}")
    exit(1)

# Descargar datos de los seguidores
followers = []
try:
    print("Descargando lista de seguidores...")
    followers = list(profile.get_followers())
except Exception as e:
    print(f"Error al descargar la lista de seguidores: {e}")
    exit(1)

# Procesar y extraer información
data = []
print("Procesando seguidores de tus seguidores...")
for idx, person in enumerate(followers, start=1):
    print(f"{idx}/{len(followers)}: Procesando {person.username}...")
    followers_count = process_profile_with_retry(person)
    if followers_count is not None:
        data.append({"username": person.username, "followers": followers_count})

        # Guardar datos parciales en el CSV
        pd.DataFrame(data).to_csv("C:/Users/MyVICTUS/Desktop/seguidores.csv", index=False, sep=';')
    else:
        print(f"Saltando {person.username} debido a error.")
    time.sleep(2)  # Reducir el ritmo de solicitudes para evitar bloqueos

print(f"Datos parciales guardados en {output_csv}")

# Generar gráfico de barras
if data:  # Solo generar el gráfico si hay datos
    df = pd.DataFrame(data)

    # Obtener el primer dígito de cada número de seguidores
    df["first_digit"] = df["followers"].astype(str).str[0].astype(int)

    # Contar la frecuencia de cada dígito
    digit_counts = df["first_digit"].value_counts().sort_index()

    # Cálculo de Chi-Cuadrado
    observed = digit_counts.values
    total_followers = observed.sum()
    expected = [total_followers * (math.log10(1 + 1 / d)) for d in range(1, 10)]
    chi_squared = sum((o - e) ** 2 / e for o, e in zip(observed, expected))
    degrees_of_freedom = len(expected) - 1
    critical_value = chi2.ppf(0.95, degrees_of_freedom)
    p_value = 1 - chi2.cdf(chi_squared, degrees_of_freedom)

    if chi_squared < critical_value:
        conclusion = "Cumple con la Ley de Benford"
    else:
        conclusion = "No cumple con la Ley de Benford"

    # Crear el gráfico
    plt.bar(digit_counts.index, digit_counts.values, color="skyblue")
    plt.xlabel("Primer dígito")
    plt.ylabel("Frecuencia")
    plt.title("Distribución de seguidores por primer dígito (Ley de Benford)")

# Agregar texto con el resultado del Chi-Cuadrado fuera de la cuadrícula
    plt.text(
        10,  # Colocamos el texto fuera de la cuadrícula en el eje X (ajustable)
        max(digit_counts.values) * 0.9,  # Altura donde aparece el texto (ajustable)
        f"Chi-Squared: {chi_squared:.2f}\nCritical Value: {critical_value:.2f}\n{conclusion}",
        fontsize=10, color="red", bbox=dict(facecolor="white", alpha=0.7)
    )

# Configuración del eje x
    plt.xticks(range(1, 10))
    plt.xlim(0, 9)  # Aseguramos que el gráfico no recorte el texto
    plt.ylim(0, max(digit_counts.values) * 1.2)  # Expandir el límite superior para dar espacio

    plt.savefig("grafico_benford_seguidores.png")  # Guardar gráfico como imagen
    plt.show()


else:
    print("No se generó ningún gráfico porque no hay datos suficientes.")

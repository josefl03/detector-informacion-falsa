# Detector Automático de Información Falsa
Sistema para la detección automática de información falsa en periódicos web, utilizando fuentes públicas y modelos de lenguaje.

Este proyecto ha sido desarrollado como Trabajo de Fin de Grado por Jose Fernández 🔗 [Linkedin](https://www.linkedin.com/home?originalSubdomain=es)  🔗[Email](mailto:jose.fernanlo03@gmail.com), y presentado en Junio de 2025 en la Universidad de Alcalá.

En este repositorio se ofrece una guía de cómo instalar y ejecutar la aplicación. Si estás interesado en conocer detalladamente el funcionamiento interno del programa, están disponibles tanto la [wiki](https://deepwiki.com/josefl03/detector-informacion-falsa) como la [memoria](https://github.com/josefl03/detector-informacion-falsa/blob/main/Memoria%20TFG%20-%20Jose%20Fern%C3%A1ndez%20L%C3%B3pez.pdf) del proyecto.
# Estructura
El proyecto está dividido en tres partes:
- **La Librería** (`libreria/`): Es la parte fundamental del programa. Contiene toda la lógica del detector y de las conexiones con bases de datos, modelos de lenguaje, etc.
- **La Aplicación Web** (`webapp/`): Interfaz para realizar las detecciones y obtener datos sobre las noticias y el análisis de forma visual.
- **El Script** (`batch/`): Herramienta de línea de comandos para analizar múltiples URLs a la vez y extraer métricas.
# Ejecución
⚠️ Recuerda que debes establecer las claves de la API en el archivo `.env` antes de ejecutar el proyecto ⚠️

Una vez descargado, solo se requiere tener instalado [docker](https://www.docker.com/) con docker-compose. Tras instalarlo, se debe abrir el directorio con los archivos, y ejecutar la aplicación web con el siguiente comando:

```bash
docker-compose up
```

Tardará varios segundos. Una vez terminado, se abrirá la interfaz gráfica en la dirección: `localhost:8000`, a la que se puede acceder desde el navegador.

Para utilizar el script de análisis múltiple, basta con instalar Python 3.12 y sus dependencias:
```bash
# Instalar requirements
pip install -r requirements.txt

# Habilitar scripts para módulos necesarios
chmod +x scripts/install-mongo.sh
chmod +x scripts/install-ollama.sh
chmod +x scripts/install-python-deps.sh

# Instalarlos
scripts/install-mongo.sh
scripts/install-ollama.sh
scripts/install-python-deps.sh
```

Tras esto, se podrá ejecutar el análisis, tanto para una URL:
```bash
python3 batch/download -u [URL]
```

Como para un archivo con URLs (separadas, una por línea):
```bash
python3 batch/download -f [ARCHIVO]
```
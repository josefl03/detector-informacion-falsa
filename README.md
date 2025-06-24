Sistema para la detección automática de información falsa en periódicos web, utilizando fuentes públicas y modelos de lenguaje.

Este proyecto ha sido desarrollado como Trabajo de Fin de Grado por Jose Fernández ([Linkedin](https://www.linkedin.com/home?originalSubdomain=es)) ([Email](mailto:jose.fernanlo03@gmail.com)), y presentado en Junio de 2025 en la Universidad de Alcalá

En este repositorio se ofrece una guía de cómo instalar y ejecutar la aplicación. Si estás interesado en conocer detalladamente el funcionamiento interno del programa, están disponibles tanto la [wiki](https://deepwiki.com/josefl03/detector-informacion-falsa) como la [memoria](https://github.com/josefl03/detector-informacion-falsa/blob/main/Memoria%20TFG%20-%20Jose%20Fern%C3%A1ndez%20L%C3%B3pez.pdf) del proyecto.
# Estructura
El proyecto está dividido en tres partes:
- **La Librería** (`libreria/`): Es la parte fundamental del programa. Contiene toda la lógica del detector y de las conexiones con bases de datos, modelos de lenguaje, etc.
- **La Aplicación Web** (`webapp/`): Interfaz para realizar las detecciones y obtener datos sobre las noticias y el análisis de forma visual.
- **El Script** (`batch/`): Herramienta de línea de comandos para analizar múltiples URLs a la vez y extraer métricas.
# Instalación
## Aplicación Web
Para instalar la aplicación web únicamente es necesario [docker-compose](https://www.docker.com/)
# Ejecución
Una vez se ha instalado 
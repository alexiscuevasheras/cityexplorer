#### Proyecto Final Análisis de Algoritmos y Complejidad
Equipo 7: Nadia Medina y Alexis Cuevas

# CityExplorer
CityExplorer es una aplicación web diseñada para ayudar a los turistas a planificar su recorrido por la Ciudad de México. Utilizando algoritmos avanzados de optimización de rutas, CityExplorer sugiere itinerarios personalizados basados en las preferencias del usuario, el tiempo disponible y las atracciones turísticas seleccionadas.
## Características
- **Selección de Atracciones**: Los usuarios pueden elegir entre una amplia variedad de atracciones turísticas, incluyendo museos, parques, sitios arqueológicos e históricos.
- **Optimización de Rutas**: La aplicación utiliza algoritmos de optimización para generar
    el itinerario más eficiente, minimizando el tiempo de viaje entre las atracciones seleccionadas.
- **Autocompletado de palabras**: Mediante Trie se autocompletan las palabras tanto para elegir su hotel como para buscar lugares
## Estructuras e infraestructura utilizadas
- **Algoritmos de Optimización**:  Usamos un grafo ponderado donde cada nodo es un punto turístico y cada arista tiene el tiempo de traslado. Como el usuario no necesariamente elige puntos que estén conectados directamente, primero calculamos las distancias reales entre sus opciones con Dijkstra y armamos un grafo completo entre ellos. Sobre ese grafo corremos Prim para encontrar la ruta que minimice el traslado total, y después ordenamos la visita con un DFS que prioriza horarios de cierre y ratings. Para la búsqueda de lugares cercanos al hotel usamos un KD-Tree por coordenadas (convertidas a km para interacción con usuario por medio de Haversine), y para el autocompletado un Trie de prefijos.

- **Frontend**: Envoltorio del notebook en Flask (las funciones del ipynb se copiaron a app.py) y se expusieron como endpoints REST que devuelven JSON. Un archivo HTML con js consume esos endpoints para ofrecer una interfaz interactiva donde el usuario selecciona hotel, elige lugares y recibe la ruta optimizada sin tocar la terminal.

## Cómo Ejecutar la Aplicación
1. Clona el repositorio en tu máquina local.
2. pip install flask
3. pip install collections
4. Ejecuta la aplicación: python3 app.py
5. Abre tu navegador y visita `http://localhost:8080` para acceder a CityExplorer
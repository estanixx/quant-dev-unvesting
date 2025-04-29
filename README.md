# fpcashflow
Solución Financiera para la Empresa Five Pack Alliance.

## How to run
### 1. Instalar requerimientos con sus versiones respectivas
`pip install --upgrade pip
pip install -r requirements.txt`
De esta forma tendrán instalado lo necesario.

### 2. Crear un archivo `.env`
Copia las pautas de `.env.example` en el `.env` y añade los datos respectivos.

### Cambiar requerimientos
`pip list --format=freeze > requirements.txt`

### Correr la app
`python main.py`

## IMPORTANTES
### Explicaciones
- `utils/auth0.py` contiene funciones relacionadas al flujo de autenticación.
- `utils/store.py` contiene los dataframes de los datos que vamos a usar.
- `utils/env.py` contiene la configuración de las variables de entorno.
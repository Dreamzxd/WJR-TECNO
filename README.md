# WJR Tecnosoluciones - Plataforma Web (Flask)

Aplicación web para:

- **Interfaz 1:** Servicios de reparación y compra de repuestos.
- **Interfaz 2:** Compra de accesorios y productos al mayor.
- Formulario de **contacto**.
- **Carrito** de compras por usuario autenticado.
- **Panel admin** para gestionar usuarios, productos, precios y stock.

## Requisitos

- Python 3.10+

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

```bash
python app.py
```

Abre: `http://127.0.0.1:5000`

## Usuario administrador inicial

Se crea automáticamente al iniciar por primera vez:

- Email: `admin@wjr.com`
- Contraseña: `Admin123*`

> Recomendación: cambia estas credenciales en producción.


## Ver la app en teléfono móvil (misma red Wi‑Fi)

1. Ejecuta el servidor escuchando en todas las interfaces:

```bash
flask --app app.py run --host 0.0.0.0 --port 5000
```

2. Identifica la IP local de tu PC (ejemplo `192.168.1.25`).
3. En el teléfono, abre: `http://TU_IP_LOCAL:5000`.

> Ambos dispositivos deben estar conectados a la misma red.

## Subir a la nube (Render)

Este repositorio ya incluye `Procfile` para producción con Gunicorn.

### Pasos

1. Sube el proyecto a GitHub.
2. Crea una cuenta en [Render](https://render.com).
3. Crea un **Web Service** conectado a tu repo.
4. Configura:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. En **Environment Variables** agrega:
   - `SECRET_KEY` con un valor seguro.
6. Despliega y usa la URL pública que Render te entrega.

### Nota importante sobre base de datos

Actualmente se usa SQLite local (`sqlite:///wjr_tecnosoluciones.db`). En nube, para producción real, se recomienda migrar a PostgreSQL para persistencia robusta.

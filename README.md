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

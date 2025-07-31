FROM python:3.10 AS base

WORKDIR /code

# Copiar requirements unificado
COPY ./requirements.txt /code/requirements.txt

# Instalar todas las dependencias (producción + testing)
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copiar código fuente
COPY ./app /code/app

# Stage para producción
FROM base AS production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]

# Stage para tests
FROM base AS test

# Copiar tests
COPY ./unit_test /code/unit_test

# Configurar entorno para tests
ENV PYTHONPATH=/code/app
WORKDIR /code/unit_test

CMD ["python", "-m", "unittest", "test_main", "-v"]
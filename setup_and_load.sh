#!/bin/bash
# Script para levantar el entorno y cargar los datos iniciales

set -e

# Renombrar env.example a .env si no existe
if [ ! -f .env ]; then
    mv env.example .env
fi

# Levantar los servicios con Docker Compose
docker compose up -d

# Esperar a que la base de datos esté lista (ajusta el tiempo si es necesario)
sleep 10

# Ejecutar migraciones y cargar datos iniciales
docker compose exec web python manage.py migrate
docker compose exec web python manage.py loaddata initial_data_custom.json

docker compose exec web python manage.py test

echo "Entorno listo y datos iniciales cargados."

echo "Ejecutando tests"

docker compose exec web python manage.py test

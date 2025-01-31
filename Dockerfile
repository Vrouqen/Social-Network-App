FROM python:3.9

WORKDIR /app

# Copiar el archivo requirements.txt
COPY requirements.txt requirements.txt

# Instalar dependencias necesarias y actualizar pip
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    gcc \
    g++ \
    curl \
    apt-transport-https \
    gnupg2 \
    && apt-get clean

# Evitar la interacción durante la instalación de msodbcsql17 y aceptar la EULA
ENV ACCEPT_EULA=Y
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-prod.list \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y msodbcsql17 \
    && apt-get clean

# Instalar pyodbc con pip
RUN pip install pyodbc

# Limpiar la caché de pip
RUN pip cache purge

# Actualizar pip a la última versión
RUN pip install --upgrade pip

# Instalar las dependencias de Python desde requirements.txt
RUN pip install -r requirements.txt


# Copiar todo el código fuente de la aplicación al contenedor
COPY . .

# Exponer el puerto en el que Flask correrá
EXPOSE 5000

# Ejecutar la aplicación usando el script de espera
CMD ["python", "app.py"]

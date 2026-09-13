# Le librerie di sistema che servono a WeasyPrint sono disponibili via apt su Linux — è il
# motivo per cui Windows ha dato tutti quei problemi (GTK non è nativo lì) e qui invece basta
# questa lista, verificata sulle dipendenze ufficiali del pacchetto Debian "weasyprint" per
# bookworm: le versioni recenti di WeasyPrint non usano più Cairo per disegnare il PDF, quindi
# libcairo2/libgdk-pixbuf non sono più necessarie (a differenza di guide più vecchie in giro).
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt
COPY app.py .

EXPOSE 5000
CMD ["python", "app.py"]

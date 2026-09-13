# Le librerie di sistema che servono a WeasyPrint (Pango, Cairo, GDK-Pixbuf...) sono
# disponibili direttamente via apt su Linux — è il motivo per cui Windows ha dato tutti quei
# problemi (GTK non è nativo lì) e qui invece basta questa lista di pacchetti, niente drammi.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt
COPY app.py .

EXPOSE 5000
CMD ["python", "app.py"]

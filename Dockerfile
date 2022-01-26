FROM dpulpeiro/parrot-olympe:1.8.0-python3.7-slim-buster

COPY requirements.txt /app/requirements.txt
COPY drone_controller.py /app/drone_controller.py

RUN pip install --no-cache-dir -r /app/requirements.txt
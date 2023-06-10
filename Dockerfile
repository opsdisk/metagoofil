FROM python:3

WORKDIR /app

RUN git clone https://github.com/opsdisk/metagoofil /app

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "metagoofil.py", "-o", "/data"]

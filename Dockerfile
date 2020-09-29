FROM python:3
WORKDIR /usr/src/app
RUN git clone https://github.com/opsdisk/metagoofil /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python", "metagoofil.py", "-o", "/data"]

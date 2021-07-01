FROM python:3.9

WORKDIR /app

COPY . .

RUN apt-get update
RUN apt-get install libpcap0.8 -y

RUN pip install -r requirements.txt

CMD ["python3", "./echo_agent/app.py"]

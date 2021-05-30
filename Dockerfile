FROM python:3.9

WORKDIR /app

COPY . .

RUN apt-get update
RUN apt-get install cron -y

RUN service cron start

RUN pip install -r requirements.txt

CMD ["/bin/sh", "echo_agent.app:app", "--host", "0.0.0.0", "--port", "11007"]

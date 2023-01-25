FROM python:latest
WORKDIR /usr/src/app
ENV FLASK_APP=src/application.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development
copy requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
RUN apt-get update
RUN apt-get install iputils-ping -y
CMD ["flask", "run"]
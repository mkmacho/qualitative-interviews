FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
	build-essential \
	apt-utils \
	nginx \
	postgresql \
	postgresql-contrib \
	supervisor && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

COPY config/nginx.conf /etc/nginx/sites-enabled/
RUN echo "\ndaemon off;" >> /etc/nginx/nginx.conf && \
	rm /etc/nginx/sites-enabled/default

COPY config/app.ini /config/
COPY /config/supervisor.conf /etc/supervisor/conf.d/

COPY requirements.txt /config/
RUN pip3 install -r /config/requirements.txt

COPY app /app

EXPOSE 80
CMD ["supervisord", "-n"]

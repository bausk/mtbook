#Grab the latest alpine image
FROM frolvlad/alpine-python3:latest

# Install python and pip
RUN apk add --update python3 bash 
RUN pip3 install --upgrade setuptools
ADD ./requirements.txt /tmp/requirements.txt

# Install dependencies
RUN pip install -qr /tmp/requirements.txt

ENV ENV staging
ENV PORT 8080
# Add our code
ADD ./server /opt/app

WORKDIR /opt/app

# Expose is NOT supported by Heroku
# EXPOSE 5000 		

# Run the image as a non-root user
RUN adduser -D myuser
USER myuser

# Run the app.  CMD is required to run on Heroku
# $PORT is set by Heroku			
CMD gunicorn --bind 0.0.0.0:$PORT main:app --worker-class aiohttp.worker.GunicornWebWorker

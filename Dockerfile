FROM python:3.7-alpine 
# as base                                                                                                
                                                                                                                              
#FROM base as builder                                                                                                          
                                                                                                                              
#RUN mkdir /install                                                                                                            
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev 
# add bash etc as alpine version doesn't have these
RUN apk add linux-headers 
RUN apk add --no-cache bash gawk sed grep bc coreutils
RUN apk --no-cache add libpq
#WORKDIR /install
#COPY requirements.txt /requirements.txt 
#RUN pip install --install-option="--prefix=/install" -r /requirements.txt 

#FROM base

#COPY --from=builder /install /usr/local  
#COPY addresses.py /address
#COPY app/ /address
COPY addresses.py /addresses/
COPY requirements.txt /addresses/
COPY app /addresses/app
#RUN apk --no-cache add libpq
WORKDIR /addresses

RUN mkdir -p /addresses/log

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 8001 and 6033 available to the world outside this container
EXPOSE 8011

# Define environment variables here
# args are passed it from cli or docker-compose.yml
#ARG poptape_auth_user
#ARG poptape_auth_pass
#ENV NAME cliveyg
#ENV POPTAPE_AUTH_USER {$poptape_auth_user}
#ENV POPTAPE_AUTH_PASS {$poptape_auth_pass}

# if -u flag in CMD below doesn't work 
# then uncomment this to see python
# print statements in docker logs
ENV PYTHONUNBUFFERED=0

# Run app.py when the container launches
CMD ["gunicorn", "-b", "0.0.0.0:8011", "addresses:app"]

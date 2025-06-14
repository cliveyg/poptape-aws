FROM python:3.12-slim
# as base

#RUN apk update && apk add postgresql-dev gcc g++ make libffi-dev python3-dev musl-dev openssl-dev
# add bash etc as alpine version doesn't have these
#RUN apk add linux-headers
#RUN apk add --no-cache bash gawk sed grep bc coreutils
#RUN apk --no-cache add libpq

COPY aws.py /aws/
COPY requirements.txt /aws/
COPY app /aws/app
COPY manage.py /aws/manage.py
WORKDIR /aws

RUN mkdir -p /aws/log

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 8040 available to the world outside this container
EXPOSE 8040

# if -u flag in CMD below doesn't work 
# then uncomment this to see python
# print statements in docker logs
ENV PYTHONUNBUFFERED=0

# Run app.py when the container launches
CMD ["gunicorn", "-b", "0.0.0.0:8040", "aws:app"]

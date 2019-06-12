# poptape-address
AWS microservice written in Python Flask with a postgres database backend.

This microservice performs various interactions with AWS

### API routes

```
/aws [GET] (Authenticated)

Returns XXXX for the authenticated user. 
Possible return codes: [200, 404, 401, 502]

```

#### Notes:
Blah

#### Rate limiting:
In addition most routes will return an HTTP status of 429 if too many requests are made in a certain space of time. The time frame is set on a route by route basis.

#### Tests:
Tests can be run from app root using: `pytest --cov=app app/tests`

#### A Title:

#### Docker:
This app can now be run in Docker using the included docker-compose.yml and Dockerfile. The database and roles still need to be created manually after successful deployment of the app in Docker. It's on the TODO list to automate these parts :-)

#### TODO:
* All of it!

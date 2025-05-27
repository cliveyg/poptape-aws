![API Tests](https://github.com/cliveyg/poptape-aws/actions/workflows/api-test.yml/badge.svg)

# poptape-aws
AWS microservice written in Python Flask with a postgres database backend.

This microservice performs various interactions with AWS

Please see [this gist](https://gist.github.com/cliveyg/cf77c295e18156ba74cda46949231d69) to see how this microservice works as part of the auction system software.

### API routes

```
/aws/user [POST] (Authenticated)

Creates an aws user in aws and stores user details in the db. Returns 201 on success.
Possible return codes: [201, 400, 502]

/aws/user [GET] (Authenticated)

Returns aws user details from the db.
Possible return codes: [200, 404]

/aws/user/<user_id> [GET] (Authenticated)

Returns user details for a particular user. Used by admin functionality.
Possible return codes: [200, 400, 404]

/aws/urls [POST] (Authenticated)

Route for creating a set of presigned s3 urls for uploading files to s3.
Possible return codes: [201, 400, 502]

/aws/admin/ratelimited [GET] (Authenticated)

Admin only route for testing rate limiting.

/aws [GET]

Returns a list of api routes.
Possible return codes: [200]

/aws/status [GET]

Returns 200 if microservice is available on network. Does not run checks against db or connections to external aws services.
Possible return codes: [200]

```

#### Notes:
Tests created with Copilot and debugged by me.

#### Rate limiting:
In addition most routes will return an HTTP status of 429 if too many requests are made in a certain space of time. The time frame is set on a route by route basis.

#### Tests:
Tests can be run from app root using: `pytest --cov-config=app/tests/.coveragerc --cov=app app/tests`

#### Docker:
This app can now be run in Docker using the included docker-compose.yml and Dockerfile. The database and roles still need to be created manually after successful deployment of the app in Docker. It's on the TODO list to automate these parts :-)

#### TODO:
* Refine some parts

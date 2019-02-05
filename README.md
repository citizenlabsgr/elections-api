# Elections API

[![CircleCI](https://circleci.com/gh/citizenlabsgr/elections-api.svg?style=svg)](https://circleci.com/gh/citizenlabsgr/elections-api)
[![Waffle.io - Columns and their card count](https://badge.waffle.io/citizenlabsgr/elections-api.svg?columns=Backlog,Started,Review)](https://waffle.io/citizenlabsgr/elections-api)

APIs to check voter registration status and view upcoming ballots in Michigan.

Quick links:
- Browse the source: https://github.com/citizenlabsgr/elections-api
- Report an issue: https://github.com/citizenlabsgr/elections-api/issues
- Contact the maintainers: https://citizenlabs.org/contact

## Overview

These examples use [HTTPie](https://httpie.org/) for brevity, but the interactive documentation below includes raw `curl` requests.

### Registration Status

Check your registration status and fetch your voting precinct:

```
http GET https://michiganelections.io/api/registrations/ "Accept: application/json; version=0" \
first_name==Jace last_name==Browning birth_date==1987-06-02 zip_code==49503
```

### Sample Ballots

Get a link to your sample ballot for upcoming elections:

```
http GET https://michiganelections.io/api/ballots/ "Accept: application/json; version=0" \
precinct_county==Kent precinct_jurisdiction=="City of Grand Rapids" precinct_ward==1 precinct_number==9
```

### Ballot Details

Get more information about the specific proposals on your ballot: 

```
http GET https://michiganelections.io/api/proposals/ "Accept: application/json; version=0" \
precinct_county==Kent precinct_jurisdiction=="City of Grand Rapids" precinct_ward==1 precinct_number==9
```

Get more information about the specific positions and candidates on your ballot:

```
http GET https://michiganelections.io/api/positions/ "Accept: application/json; version=0" \
precinct_county==Kent precinct_jurisdiction=="City of Grand Rapids" precinct_ward==1 precinct_number==9
```

## Documentation

Interactive API documentation powered by [Swagger UI](https://swagger.io/tools/swagger-ui/), can be viewed at <a href="https://michiganelections.io/docs/">michiganelections.io/docs/</a>.

Versions of the API are requested through content negotiation. Your client will receive the highest compatible version for the major version you request.

## History

**Version 0.0.0**

- Coming soon...

# Elections API

[![CircleCI](https://circleci.com/gh/citizenlabsgr/elections-api.svg?style=svg)](https://circleci.com/gh/citizenlabsgr/elections-api)
[![Waffle.io - Columns and their card count](https://badge.waffle.io/citizenlabsgr/elections-api.svg?columns=Backlog,Started,Review)](https://waffle.io/citizenlabsgr/elections-api)

<!-- content -->

APIs to check voter registration status and view ballots for all elections in Michigan.

Quick links:

- Browse the source: https://github.com/citizenlabsgr/elections-api/
- Report an issue: https://github.com/citizenlabsgr/elections-api/issues/
- Contact the maintainers: https://citizenlabs.org/contact/

## Overview

These examples use [HTTPie](https://httpie.org/) for brevity, but the interactive documentation below shows how to do the same using raw `curl` requests.

### Registration Status

Check your registration status and fetch your voting precinct:

```
http GET https://michiganelections.io/api/registrations/ \
  "Accept: application/json; version=1" \
  first_name==Rosalynn last_name==Bliss birth_date==1975-08-03 zip_code==49503
```

### Sample Ballots

Get a link to the official sample ballot for upcoming elections:

```
http GET https://michiganelections.io/api/ballots/ \
  "Accept: application/json; version=1" \
  precinct_county==Kent precinct_jurisdiction=="City of Grand Rapids" \ 
  precinct_ward==2 precinct_number==30
```

### Ballot Details

Get more information about the specific proposals on your ballot: 

```
http GET https://michiganelections.io/api/proposals/ \
  "Accept: application/json; version=1" \
  precinct_county==Kent precinct_jurisdiction=="City of Grand Rapids" \ 
  precinct_ward==2 precinct_number==30
```

Get more information about the specific positions and candidates on your ballot:

```
http GET https://michiganelections.io/api/positions/ \
  "Accept: application/json; version=1" \
  precinct_county==Kent precinct_jurisdiction=="City of Grand Rapids" \ 
  precinct_ward==2 precinct_number==30
```

## Documentation

Interactive API documentation powered by [Swagger UI](https://swagger.io/tools/swagger-ui/), can be viewed at <a href="https://michiganelections.io/docs/">michiganelections.io/docs/</a>.

Versions of the API are requested through content negotiation. Your client will receive the highest compatible version for the major version you request.

## History

**Version 1.0.0**

- Initial public release.

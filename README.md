# Elections API

[![CircleCI](https://img.shields.io/circleci/build/github/citizenlabsgr/elections-api)](https://circleci.com/gh/citizenlabsgr/elections-api)
[![Coveralls](https://img.shields.io/coveralls/github/citizenlabsgr/elections-api)](https://coveralls.io/github/citizenlabsgr/elections-api)

<!-- content -->

APIs to check voter registration status and view ballots for all elections in Michigan.

Quick links:

- Browse the source: https://github.com/citizenlabsgr/elections-api/
- Report an issue: https://github.com/citizenlabsgr/elections-api/issues/
- Contact the maintainers: https://citizenlabs.org/contact/

Sample clients:

- https://explore.michiganelections.io/
- https://vote.citizenlabs.org/

---

## Overview

These examples use [HTTPie](https://httpie.org/) for brevity, but the interactive documentation below shows how to do the same using raw `curl` requests.

### Registration Status

Check your registration status and fetch your voting precinct:

```
http GET https://michiganelections.io/api/registrations/ \
  "Accept: application/json; version=1" \
  first_name==Rosalynn last_name==Bliss birth_date==1975-08-03 zip_code==49503
```

If you are registered to vote, this will return your voting precinct:

```
"precinct": {
    "county": "Kent",
    "jurisdiction": "City of Grand Rapids",
    "ward": "2"
    "number": "30",
    ...
}
```

as well as a unique ID that identifies your precinct:

```
"precinct": {
    "id": 1173,
    ...
}
```

Using either of these pieces of information, you can fetch the details of your specific ballot. The response also includes the districts your address is located in as well as your polling location:

```
"polling_location": [
    "Mayfair Christian Reformed Church",
    "1736 Lyon Ne",
    "Grand Rapids, Michigan 49503"
]
```

### Sample Ballots

Get a link to the official sample ballot for upcoming elections, by precinct ID:

```
http GET https://michiganelections.io/api/ballots/ \
  "Accept: application/json; version=1" \
  precinct_id=1173
```

or by precinct name:

```
http GET https://michiganelections.io/api/ballots/ \
  "Accept: application/json; version=1" \
  precinct_county==Kent precinct_jurisdiction=="City of Grand Rapids" \
  precinct_ward==2 precinct_number==30
```

### Ballot Details: Positions

Get more information about the specific positions and candidates on your ballot, by precinct ID:

```
http GET https://michiganelections.io/api/positions/ \
  "Accept: application/json; version=1" \
  precinct_id=1173
```

or by precinct name:

```
http GET https://michiganelections.io/api/positions/ \
  "Accept: application/json; version=1" \
  precinct_county==Kent precinct_jurisdiction=="City of Grand Rapids" \
  precinct_ward==2 precinct_number==30
```

### Ballot Details: Proposals

Get more information about the specific proposals on your ballot, by precinct ID:

```
http GET https://michiganelections.io/api/proposals/ \
  "Accept: application/json; version=1" \
  precinct_id=1173
```

or by precinct name:

```
http GET https://michiganelections.io/api/proposals/ \
  "Accept: application/json; version=1" \
  precinct_county==Kent precinct_jurisdiction=="City of Grand Rapids" \
  precinct_ward==2 precinct_number==30
```

## Documentation

The browseable API powered by [Django REST Framework](https://www.django-rest-framework.org) can be found here: https://michiganelections.io/api/

Interactive API documentation powered by [Swagger UI](https://swagger.io/tools/swagger-ui/), can be found here: https://michiganelections.io/docs/

Versions of the API are requested through content negotiation. Your client will receive the highest compatible version for the major version you request.

## Contributing

If you would like to contribute to this project, fork this repository or ask for commit access rights during one of our ["Hack Night" events](https://citizenlabs.org/join_us/).

Once you have access rights or a fork, please read the [CONTRIBUTING.md](https://github.com/citizenlabsgr/elections-api/blob/master/CONTRIBUTING.md) file to set up your local environment. Create a branch for every issue you work on and make a pull request to `master` with the corresponding issue attached.

You can also contribute content changes by editing [these files](https://github.com/citizenlabsgr/elections-api/tree/master/content) directly on GitHub. If you would like to know more about us, please check out our [welcome kit](https://github.com/citizenlabsgr/read-first).

## History

**Version 1.0**

- Initial public release.

**Version 1.1**

- Added `possing_location` to the registrations API.
- Added `description` to the district category, election, and party APIs.

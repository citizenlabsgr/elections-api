# Elections API

[![CircleCI](https://img.shields.io/circleci/build/github/citizenlabsgr/elections-api/main)](https://circleci.com/gh/citizenlabsgr/elections-api)
[![Coveralls](https://img.shields.io/coveralls/github/citizenlabsgr/elections-api/main)](https://coveralls.io/github/citizenlabsgr/elections-api)

<!-- content -->

APIs to check voter registration status and view sample ballots for elections in Michigan.

### Quick Links

- Browse the source: https://github.com/citizenlabsgr/elections-api/
- Report an issue: https://github.com/citizenlabsgr/elections-api/issues/
- Contact the maintainers: https://citizenlabs.org/contact/

### Sample Projects

| Website                                   | Purpose               | Status                                                      |
| ----------------------------------------- | --------------------- | ----------------------------------------------------------- |
| https://share.michiganelections.io        | Ballot previews       | [Deployed](https://github.com/citizenlabsgr/ballotshare)    |
| https://vote.citizenlabs.org              | Registration chat bot | [Deployed](https://github.com/citizenlabsgr/mittens)        |
| https://github.com/MI-Vote/mivote-android | Mobile voter app      | [Development](https://github.com/MI-Vote/mivote-android)    |
| https://github.com/MI-Vote/mivote-ios     | Mobile voter app      | [Development](https://github.com/MI-Vote/mivote-android)    |
| https://explore.michiganelections.io      | Election advocacy     | [Discovery](https://github.com/citizenlabsgr/elections-app) |

---

## Overview

These examples use [HTTPie](https://httpie.org/) for brevity, but the interactive documentation below shows how to do the same using raw `curl` requests.

### Registration Status

Check your registration status and fetch your voting precinct with an [API call](https://michiganelections.io/api/registrations/?first_name=Rosalynn&last_name=Bliss&birth_date=1975-08-03&zip_code=49503) like this:

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

Using either of these pieces of information, you can fetch the details of your specific ballot.

#### Voting Locations

The registrations payload also includes your polling location:

```
"polling_location": [
    "Mayfair Christian Reformed Church",
    "1736 Lyon Ne",
    "Grand Rapids, Michigan 49503"
]
```

And the address where you can drop off your signed absentee ballot:

```
"dropbox_location": [
    "300 Ottawa Ave Nw",
    "Grand Rapids, Michigan"
]
```

#### Absentee Information

The registrations payload also includes fields indicating the voter's absentee status and progress of their ballot:

| Field                           | Description                                             |
| ------------------------------- | ------------------------------------------------------- |
| `registered`                    | Voter can participate in the upcoming election          |
| `ballot`                        | Voter will participate in the upcoming election         |
| `absentee`                      | Voter has requested to vote by mail for all elections   |
| `absentee_application_received` | Date (`YYYY-MM-DD`) clerk received absentee application |
| `absentee_ballot_sent`          | Date (`YYYY-MM-DD`) clerk mailed your absentee ballot   |
| `absentee_ballot_received`      | Date (`YYYY-MM-DD`) clear recorded your absentee vote   |

<br>
These dates reset after each election.

### Sample Ballots

Get a link to the official sample ballot for upcoming elections, by precinct ID with an [API call](https://michiganelections.io/api/ballots/?precinct_id=1173) like this:

```
http GET https://michiganelections.io/api/ballots/ \
  "Accept: application/json; version=1" \
  precinct_id==1173
```

or by precinct name with an [API call](https://michiganelections.io/api/ballots/?precinct_county=Kent&precinct_jurisdiction=City%20of%20Grand%20Rapids&precinct_ward=2&precinct_number=30) like this:

```
http GET https://michiganelections.io/api/ballots/ \
  "Accept: application/json; version=1" \
  precinct_county==Kent precinct_jurisdiction=="City of Grand Rapids" \
  precinct_ward==2 precinct_number==30
```

### Ballot Details: Positions

Get more information about the specific positions and candidates on your ballot, by precinct ID with an [API call](https://michiganelections.io/api/positions/?precinct_id=1173) like this:

```
http GET https://michiganelections.io/api/positions/ \
  "Accept: application/json; version=1" \
  precinct_id==1173
```

or by precinct name with an [API call](https://michiganelections.io/api/positions/?precinct_county=Kent&precinct_jurisdiction=City%20of%20Grand%20Rapids&precinct_ward=2&precinct_number=30) like this:

```
http GET https://michiganelections.io/api/positions/ \
  "Accept: application/json; version=1" \
  precinct_county==Kent precinct_jurisdiction=="City of Grand Rapids" \
  precinct_ward==2 precinct_number==30
```

### Ballot Details: Proposals

Get more information about the specific proposals on your ballot, by precinct ID with an [API call](https://michiganelections.io/api/proposals/?precinct_id=1173) like this:

```
http GET https://michiganelections.io/api/proposals/ \
  "Accept: application/json; version=1" \
  precinct_id=1173
```

or by precinct name with an [API call](https://michiganelections.io/api/proposals/?precinct_county=Kent&precinct_jurisdiction=City%20of%20Grand%20Rapids&precinct_ward=2&precinct_number=30) like this:

```
http GET https://michiganelections.io/api/proposals/ \
  "Accept: application/json; version=1" \
  precinct_county==Kent precinct_jurisdiction=="City of Grand Rapids" \
  precinct_ward==2 precinct_number==30
```

## Documentation

The browsable API powered by [Django REST Framework](https://www.django-rest-framework.org) can be found here: https://michiganelections.io/api/

Interactive API documentation powered by [Swagger UI](https://swagger.io/tools/swagger-ui/), can be found here: https://michiganelections.io/docs/

Versions of the API are requested through content negotiation. Your client will receive the highest compatible version for the major version you request.

## Zapier Integration

Get notified about upcoming elections and changes to your registration status using the official Zapier integration: https://zapier.com/apps/michigan-elections

## Contributing

If you would like to contribute to this project, fork this repository or ask for commit access rights during one of our ["Hack Night" events](https://citizenlabs.org/join/).

Once you have access rights or a fork, please read the [CONTRIBUTING.md](https://github.com/citizenlabsgr/elections-api/blob/main/CONTRIBUTING.md) file to set up your local environment. Create a branch for every issue you work on and make a pull request to `main` with the corresponding issue attached.

You can also contribute content changes by editing [these files](https://github.com/citizenlabsgr/elections-api/tree/main/content) directly on GitHub. If you would like to know more about us, please check out our [welcome kit](https://github.com/citizenlabsgr/read-first).

## History

**Version 1.11**

- Added `ballot` to registration and status responses.

**Version 1.10.1**

- Updated `/api/status/` to return a 202 when the Michan Secretary of State website is unavailable.

**Version 1.10**

- Added `/api/status/` to enable triggering when a voter's registration status changes for an upcoming election.

**Version 1.9**

- Added `dropbox_location` to registrations API responses.

**Version 1.8**

- Added `absentee_application_received`, `absentee_ballot_sent`, and `absentee_ballot_received` dates to the registrations API responses to track the progress of each voter's absentee ballot.

**Version 1.7**

- Added `section` to ballot positions API responses to filter primary ballot selection.

**Version 1.6**

- Added `recently_moved` to registrations API responses to indicate that precinct information may not currently be accurate.

**Version 1.5**

- Added `date_humanized` field to elections API responses.

**Version 1.4**

- Added `absentee` to the registrations API responses to indicate that a voter has absentee status.

**Version 1.3**

- Added `description_edit_url` to responses for elections, district categories, parties, and positions.

**Version 1.2**

- Added a glossary API to display descriptions for elections, district categories, parties, and positions.

**Version 1.1**

- Added `polling_location` to the registrations API.
- Added `description` to the district category, election, and party APIs.

**Version 1.0**

- Initial public release.

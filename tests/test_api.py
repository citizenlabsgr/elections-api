# pylint: disable=unused-argument,unused-variable


def describe_registrations():
    def with_valid_identity(expect, client, db):
        response = client.get(
            "/api/registrations/"
            "?first_name=Jace"
            "&last_name=Browning"
            "&birth_date=1987-06-02"
            "&zip_code=49503"
        )

        expect(response.status_code) == 200
        expect(response.data) == [
            {
                "registered": True,
                "districts": [
                    {"category": "Circuit Court", "name": "17th Circuit"},
                    {
                        "category": "Community College District",
                        "name": "Grand Rapids Community College",
                    },
                    {"category": "County", "name": "Kent County"},
                    {
                        "category": "County Commissioner District",
                        "name": "15th District",
                    },
                    {"category": "Court of Appeals", "name": "3rd District"},
                    {"category": "District Court", "name": "61st District"},
                    {
                        "category": "Intermediate School District",
                        "name": "Kent ISD",
                    },
                    {
                        "category": "Jurisdiction",
                        "name": "City of Grand Rapids",
                    },
                    {"category": "Precinct", "name": "9"},
                    {
                        "category": "Probate Court",
                        "name": "Kent County Probate Court",
                    },
                    {
                        "category": "School District",
                        "name": "Grand Rapids Public Schools",
                    },
                    {
                        "category": "State House District",
                        "name": "75th District",
                    },
                    {
                        "category": "State Senate District",
                        "name": "29th District",
                    },
                    {
                        "category": "US Congress District",
                        "name": "3rd District",
                    },
                    {"category": "Ward", "name": "1"},
                ],
            }
        ]

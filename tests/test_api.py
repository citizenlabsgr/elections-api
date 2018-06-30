# pylint: disable=unused-variable


def describe_registrations():
    def with_valid_identity(expect, client):
        response = client.get(
            "/api/registrations/"
            "?first_name=Rick"
            "&last_name=Snyder"
            "&zip_code=48909"
            "&birth_date=1958-09-19"
        )

        expect(response.status_code) == 200
        expect(response.data) == [{"registered": True}]

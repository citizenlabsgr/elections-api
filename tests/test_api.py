# pylint: disable=unused-variable


def describe_registrations():
    def with_valid_identity(expect, client):
        response = client.get(
            "/api/registrations/"
            "?first_name=Jace"
            "&last_name=Browning"
            "&birth_date=1987-06-02"
            "&zip_code=49503"
        )

        expect(response.status_code) == 200
        expect(response.data) == [{"registered": True}]

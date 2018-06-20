from apistar import App, Include, Route, http


def welcome(name=None):
    if name is None:
        return {"message": "Welcome to API Star!"}
    return {"message": "Welcome to API Star, %s!" % name}


def registration(first_name: http.QueryParam, last_name: http.QueryParam):
    return {"registered": False}


routes = [
    Route("/welcome", method="GET", handler=welcome),
    Route("/registration", method="GET", handler=registration),
]

app = App(routes=routes)


if __name__ == "__main__":
    app.serve("127.0.0.1", 5000, debug=True)

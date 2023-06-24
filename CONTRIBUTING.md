## Getting Started

### Requirements

- [asdf](https://asdf-vm.com/guide/getting-started.html)

  - Once installed: `asdf install` to get Python and Poetry

- [direnv](https://direnv.net/)

  - MacOS: `$ brew install direnv`
  - Linux: `$ sudo apt install direnv`
  - Add `direnv hook` to your [shell config](https://direnv.net/)
  - Restart your terminal
  - `$ make .envrc`
  - `$ direnv allow`

- [Postgres](https://www.postgresql.org/)

  - MacOS:
    - `$ brew install postgres` (or your platform's equivalent)
    - `$ brew services start postgres` (or your platform's equivalent)
  - Linux:
    - `$ sudo apt install postgresql`

- [Redis](https://redis.io/)

  - `$ brew install redis` (or your platform's equivalent)
  - `$ brew services start redis` (or your platform's equivalent)

- [Graphviz](https://www.graphviz.org/)

  - MacOS: `$ brew install graphviz` (or your platform's equivalent)
  - Linux: `$ sudo apt install graphviz`

### Data

Generate some representative sample data for manual test:

```
 $ createdb elections_dev
 $ make data
```

Or, Docker option:
```
docker run --rm -e POSTGRES_PASSWORD -e POSTGRES_USER=$USER -e POSTGRES_DB=elections_dev -p 5432:5432 postgres
```

The default Django admin credentials are `admin:password`.

### Local Development

Now you should be able to run the Django client on your local machine. Enter `$ make run` in your terminal, then go to your browser and visit `http://localhost:8000/`. If everything is working correctly, you should be able to see the Michigan Elections API.

---

## Advanced Cases

If your database gets into a weird state, you can reset it from scratch:

```
$ make data/reset
```

You can also download production with valid Heroku credentials:

```
$ make data/production
```

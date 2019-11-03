## Getting Started

### Requirements

- [pyenv](https://github.com/pyenv/pyenv)

  - MacOS: `$ brew install pyenv`
  - Linux: `$ curl https://pyenv.run | bash`
  - Add `pyenv init` to your [shell config](https://github.com/pyenv/pyenv#installation)
  - Restart your terminal
  - `$ pyenv install`
  - Linux: 
    - `$ python3 -m venv .venv`
    - `$ source .venv/bin/activate`

- [Poetry](https://poetry.eustace.io/docs/)

  - (`$ curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python && source $HOME/.poetry/env`)
  - Add poetry to your .bashrc or equivalent configuration file `$ echo "export PATH=~/.poetry/bin:$PATH" >> ~/.baschrc`
  - Linux:
    - `$ poetry install`
    - may need: `$ sudo apt-get install python-dev graphviz libgraphviz-dev pkg-config`
    - re-run `$ poetry install`

- [direnv](https://direnv.net/)

  - MacOS: `$ brew install direnv` (or your platform's equivalent)
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
    - `$ sudo apt install postresql`

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

### Get ready to contribute!

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

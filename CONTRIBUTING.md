## Getting Started

### Requirements

- [pyenv](https://github.com/pyenv/pyenv)

  - `$ brew install pyenv` (or your platform's equivalent)
  - Add `pyenv init` to your [shell config](https://github.com/pyenv/pyenv#installation)
  - Restart your terminal
  - `$ pyenv install`

- [Poetry](https://poetry.eustace.io/docs/)

  - (`$ curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python && source $HOME/.poetry/env`)
  - Add poetry to your .bashrc or equivalent configuration file `$ echo "export PATH=~/.poetry/bin:$PATH" >> ~/.baschrc`

- [direnv](https://direnv.net/)

  - `$ brew install direnv` (or your platform's equivalent)
  - Add `direnv hook` to your [shell config](https://direnv.net/)
  - Restart your terminal
  - `$ make .envrc`
  - `$ direnv allow`

- [Postgres](https://www.postgresql.org/)

  - `$ brew install postgres` (or your platform's equivalent)
  - `$ brew services start postgres` (or your platform's equivalent)

- [Redis](https://redis.io/)

  - `$ brew install redis` (or your platform's equivalent)
  - `$ brew services start redis` (or your platform's equivalent)

- [Graphviz](https://www.graphviz.org/)

  - `$ brew install graphviz` (or your platform's equivalent)

### Data

Generate some representative sample data for manual test:

```
 $ createdb elections_dev
 $ make data
```

### Get ready to contribute!

Now you should be able to run the Django client on your local machine. Enter `$ make run` in your terminal, then go to your browser and visit `http://localhost:8000/`,
if everything is working correctly, you should be able to see the Michigan elections API.

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

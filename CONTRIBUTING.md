## Setup

### Requirements

- pyenv

  - `$ brew install pyenv` (or your platform's equivalent)
  - Add `pyenv init` to your [shell config](https://github.com/pyenv/pyenv#installation)
  - Restart your terminal

- Python 3.7+

  - `$ pyenv install`

- Poetry (`$ curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python && source $HOME/.poetry/env`)

- direnv

  - `$ brew install direnv` (or your platform's equivalent)
  - Add `direnv hook` to your [shell config](https://direnv.net/)
  - Restart your terminal
  - `$ make .envrc`
  - `$ direnv allow`

- Postgres

  - `$ brew install postgres` (or your platform's equivalent)
  - `$ brew services start postgres` (or your platform's equivalent)
  - `$ createdb elections_dev` (or your platform's equivalent)

- Redis
  - `$ brew install redis` (or your platform's equivalent)
  - `$ brew services start redis` (or your platform's equivalent)

### Data

Generate some representative sample data for manual test:

```
$ make data
```

If your database gets into a weird state, you can reset it from scratch:

```
$ make data/reset
```

You can also download production with valid Heroku credentials:

```
$ make data/production
```

## Setup

### Requirements

- pyenv
  - `$ brew install pyenv` (or your platform's equivalent)
  - Add `pyenv init` to your [shell config](https://github.com/pyenv/pyenv#installation)
  - Restart your terminal
- direnv
  - `$ brew install direnv` (or your platform's equivalent)
  - Add `direnv hook` to your [shell config](https://direnv.net/)
  - Restart your terminal
- Python 3.7+
  - `$ pyenv install`
- Poetry (`$ curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python`)
- Redis
  - `$ brew install redis` (or your platform's equivalent)
  - `$ brew services start redis` (or your platform's equivalent)

### Configuration

```
$ make .envrc
$ direnv allow
```

### Data

Generate some representative sample data for manual test:

```
$ createdb elections_dev
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

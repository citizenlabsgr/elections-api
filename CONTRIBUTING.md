## Setup

### Requirements

- pyenv

  - `$ brew install pyenv` (or your platform's equivalent)
  - Add `pyenv init` to your [shell config](https://github.com/pyenv/pyenv#installation)
  - Restart your terminal

- Python 3.7+

  - `$ pyenv install`

- Poetry

  - (`$ curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python && source $HOME/.poetry/env`)
  - Add poetry to your .bashrc or equivalent configuration file `echo "export PATH=~/.poetry/bin:$PATH" >> ~/.baschrc`

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

- Other Dependencies
  - `$ brew install graphviz` (or your platform's equivalent)

### Data

Generate some representative sample data for manual test:

```
 $ make data
```

### Good to go

Now you should be able to run the django client on your local machine. run `make run` in your terminal, then go to your browser and visit `http://localhost:8000/`,
if everything is working correctly, you should be able to see the michigan elections API.

## Advanced Cases

If your database gets into a weird state, you can reset it from scratch:

```
$ make data/reset
```

You can also download production with valid Heroku credentials:

```
$ make data/production
```

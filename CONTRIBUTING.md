## Setup

### Requirements

- pyenv
    + `$ brew install pyenv` (or your platform's equivalent)
    + Add `pyenv init` to your [shell config](https://github.com/pyenv/pyenv#installation)
    + Restart your terminal
- direnv
    + `$ brew install direnv` (or your platform's equivalent)
    + Add `direnv hook` to your [shell config](https://direnv.net/)
    + Restart your terminal
- Python 3.7+
    + `$ pyenv install`
- Poetry (`$ curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python`)
- Redis
    + `$ brew install redis` (or your platform's equivalent)
    + `$ brew services start redis` (or your platform's equivalent)

### Configuration

```
$ make .envrc
$ direnv allow
```

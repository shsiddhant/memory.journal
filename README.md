# memory.journal

[![Python](https://img.shields.io/badge/python-3.11%2B-4B8BBE?style=for-the-badge&logo=python&logoColor=%23FFE873)](https://www.python.org/)
[![LICENSE: MIT](https://img.shields.io/badge/LICENSE-MIT-green?style=for-the-badge)](LICENSE)

A simple and lightweight journaling app.


## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Roadmap](#roadmap)
- [Development](#development)
- [License](#license)


## Features

- Simple and easy to use interface.
- Unlimited number of journals.
- Password protection to keep memories safe.
- Unlimited number of entries/memories.
- Markdown support for formatting entries/memories.
- Runs offline and keeps your journals private.


## Installation

The package should soon be available on PyPI. For now, you can install 
directly from the repository with pip. 

```shell
$ pip install "memory.journal @ git+https://github.com/shsiddhant/memory.journal.git"
```

```shell
$ export FLASK_APP=memoryjournal
$ flask --app memoryjournal init-db # Initiate Database for first use
$ flask run --host=0.0.0.0 # Run the app
```

## Roadmap

- [ ] User friendly installation and use.
- [ ] Media attachments
- [ ] Export to PDF and DayOne/Journey.cloud formats
- [ ] Markdown preview while adding/editing memories
- Markdown extensions (https://facelessuser.github.io/pymdown-extensions/)
    - [ ] strikethrough
    - [ ] highlight
    - [ ] checklists
    - [ ] syntax highlighting
    - [ ] LaTeX

## Development


If you'd like to explore, improve, fix something, report bugs, or suggest any feature ideas, you are welcome to contribute.

To get started, you can have a look at the [issue tracker](https://github.com/shsiddhant/memory.journal/issues). If you want to report a bug or make a feature request, please open a [new issue](https://github.com/shsiddhant/memory.journal/issues/new/choose) using an appropriate template.

See [CONTRIBUTING](CONTRIBUTING.md) for a detailed overview of the contributing guidelines.


## License
[![LICENSE: MIT](https://img.shields.io/badge/LICENSE-MIT-green?style=for-the-badge)](LICENSE)



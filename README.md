<p align="center" markdown=1>
  <i>Python library for FastAPI, boosting SQLAlchemy and Redis with pagination, error handling, and session management.</i>
</p>
<p align="center" markdown=1>
<a href="https://github.psa-cloud.com/gtf08/hil-fastapi-utils">
  <img src="https://img.shields.io/badge/Python-3.10 | 3.11 | 3.12-40cd60" alt="Supported Python Versions"/>
</a>
</p>
<hr>
<p align="justify">
<b>FastGear</b> is a comprehensive Python library designed for <b>FastAPI</b>. It provides robust support for both 
    asynchronous and synchronous operations with <b>SQLAlchemy</b> and asynchronous operations with <b>Redis</b>. Key 
    features include dynamic pagination, custom error handling, automatic database session management within a context 
    manager, and much more.
</p>
<hr>

**Source Code**: <a href="https://github.com/hmarcuzzo/fastgear" target="_blank">https://github.com/hmarcuzzo/fastgear</a>


## Features
- **Fully Async**: Leverages Python's async capabilities for non-blocking database operations.
- **SQLAlchemy 2.0**: Works with the latest SQLAlchemy version for robust database interactions.
- **Redis Support**: Provides support for Redis for caching and other operations.
- **Dynamic Query Building**: Supports building simple queries dynamically, including filtering, sorting, and pagination.
- **Built-in Offset Pagination**: Comes with ready-to-use offset pagination.
- **Custom Error Handling**: Provides custom error handling for better debugging and user experience.
- **Session Management**: Automatically manages database sessions within a context manager.

## Requirements

Before installing FastGear, ensure you have the following prerequisites:

* **Python:** Version 3.10 or newer.
* **FastAPI:** FastGear is built to work with FastAPI, so having FastAPI in your project is essential.
* **SQLAlchemy:** FastGear uses SQLAlchemy 2.0 for database operations, so you need SQLAlchemy 2.0 or newer.
* **Pydantic V2:** FastGear leverages Pydantic models for data validation and serialization, so you need Pydantic 2.0 or newer.
* **Redis:** If you plan to use Redis with FastGear, you need to have Redis installed and running in a version 5.0 or newer.

# Installing

To install the `fastgear` package, follow these steps:

## Using pip
Run the following command:
```sh
pip install fastgear
```

## Using Poetry
Run the following command:
```sh
poetry add fastgear
```

## License

This project is licensed under the terms of the MIT license.

# Contributing to FastGear

Thank you for your interest in contributing to FastGear! This guide is meant to make it easy for you to get started.

## Setting Up Your Development Environment

### Cloning the Repository
Start by forking and cloning the FastGear repository:

```sh
git clone https://github.com/YOUR-GITHUB-USERNAME/fastgear.git
```

### Using uv for Dependency Management
FastGear uses `uv` for managing dependencies. If you don't have uv installed, follow the instructions on the [official uv website](https://docs.astral.sh/uv/).

Once `uv` is installed, navigate to the cloned repository and sync all the dependencies:
```sh
cd fastgear
uv sync
```
- **Notes**:
  - You can include optional dependency groups using the `--group` flag:
    - `dev`: development dependencies.
    - `test`: testing dependencies.

### Activating the Virtual Environment
`uv` creates a virtual environment for your project. Activate it using:

```sh
source .venv/bin/activate
```

## Making Contributions

### Coding Standards
- Follow PEP 8 guidelines.
- Write meaningful tests for new features or bug fixes.

### Testing with Pytest
FastGear uses pytest for testing. Run tests using:
```sh
uv run pytest
```

### Linting
FastGear uses Ruff with several included configurations for style and linting:
```sh
ruff check --fix
ruff format
```

- To ensure your commits comply with the expected standards, you can use the pre-commit tool. 
Install it with:
    ```sh
    uv run pre-commit install
    ```

Ensure your code passes linting and pre-commit checks before submitting.

## Submitting Your Contributions

### Creating a Pull Request
After making your changes:

- Update the documentation (eg. `README.md`) if necessary.
- Push your changes to your fork.
- Open a pull request with a clear description of your changes.
  - The project follow the [gitmoji](https://gitmoji.dev/) convention for commit messages. 
  Please use the appropriate emoji to indicate the type of change you are making.


### Code Reviews
- Address any feedback from code reviews.
- Once approved, your contributions will be merged into the main branch.

Thank you for contributing to **FastGear** 🚀

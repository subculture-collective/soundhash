# How to Contribute to SoundHash

First off, thank you for considering a contribution! We're excited to have you here. This guide will help you get set up and start contributing.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Setting Up Your Development Environment

To ensure a smooth and consistent development process, this project uses `uv` for dependency management and `pre-commit` to automate code quality checks.

### 1. Fork and Clone the Repository

Start by forking the repository to your own GitHub account and then cloning it to your local machine.

```bash
git clone [https://github.com/YourUsername/soundhash.git](https://github.com/YourUsername/soundhash.git)
cd soundhash
````

### 2. Install Dependencies
We recommend using a Python virtual environment to keep project dependencies isolated.

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Install the required packages
pip install -r requirements.txt
pip install pre-commit
```

### 3. Set Up Pre-Commit Hooks

This is a crucial step. The pre-commit hooks will automatically format and lint your code every time you make a commit, ensuring it meets our quality standards.

```bash
pre-commit install
```

Now, every time you run `git commit`, `ruff` will automatically check your code.

## Our Workflow

### 1. Find an Issue

Look for an open issue that you'd like to work on. If you have an idea for a new feature or a bug fix, please open a new issue first to discuss it with the team.

### 2. Create a New Branch

Create a new branch for your changes. Please use a descriptive name.

```bash
# Example for a new feature
git checkout -b feat/add-new-feature

# Example for a bug fix
git checkout -b fix/resolve-bug
```

### 3. Make Your Changes

Write your code\! Make sure to follow the existing style and structure.

### 4. Commit Your Work

When you're ready to commit, the pre-commit hooks will run automatically. If they find any issues, they might automatically fix them for you. If so, you'll just need to `git add` the changes and commit again.

```bash
git add .
git commit -m "feat: Briefly describe your new feature"
```

### 5. Open a Pull Request

Push your branch to your fork and open a pull request against the main repository. In your PR description, please link to the issue you are resolving (e.g., `Fixes #123`).

## Code Style and Quality

  * **Linting & Formatting:** We use `ruff` to handle all linting, formatting, and import sorting. The pre-commit hooks will take care of this for you.
  * **Clarity:** Write clean, readable, and well-commented code where necessary.

Thank you again for your contribution\!

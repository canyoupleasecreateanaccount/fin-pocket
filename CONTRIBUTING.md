# Contributing to fin-pocket

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository on GitHub.

2. Clone your fork locally:

```bash
git clone git@github.com:<your-username>/fin-pocket.git
cd fin-pocket
```

3. Create a virtual environment and install dev dependencies:

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
pip install -e ".[dev]"
```

4. Create a feature branch:

```bash
git checkout -b feature/your-feature-name
```

## Making Changes

- Write clear, concise code.
- Add tests for new signals or features in the `tests/` folder.
- Ensure all tests pass before submitting:

```bash
pytest -v
```

## Submitting a Pull Request

1. Push your branch to your fork:

```bash
git push origin feature/your-feature-name
```

2. Open a Pull Request against the `main` branch of the original repository.

3. In the PR description:
   - Describe **what** your change does and **why**.
   - Reference any related issues (e.g. `Closes #12`).
   - Include screenshots of the chart if the change affects visualization.

4. Wait for CI checks to pass (tests run automatically on every PR).

5. A maintainer will review your PR. Please address any feedback.

## Adding a New Signal

1. Create a new file in `fin_pocket/signals/` (inherit from `BaseSignal`).
2. Implement `calculate(df)` and `plot(fig, df, row)` methods.
3. Register it in `fin_pocket/signals/__init__.py`.
4. Add a CLI flag in `fin_pocket/cli.py`.
5. Write tests in `tests/test_<signal_name>.py`.
6. Update `README.md` feature table.

## Code Style

- Use type hints where reasonable.
- Follow existing naming conventions in the codebase.
- Keep commits focused — one logical change per commit.

## Reporting Issues

Open an issue at [GitHub Issues](https://github.com/canyoupleasecreateanaccount/fin-pocket/issues) with:

- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

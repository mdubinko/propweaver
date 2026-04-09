# Release Process

This project publishes with GitHub trusted publishing:

- `workflow_dispatch` publishes the current commit to TestPyPI
- `v*` tags publish to PyPI

## One-Time Setup

1. Create a `testpypi` environment in GitHub and add the TestPyPI trusted publisher.
2. Create a `pypi` environment in GitHub and add the PyPI trusted publisher.
3. Restrict the `pypi` environment as desired for tagged releases.

## Local Verification

Use the project virtualenv if present:

```bash
.venv/bin/python -m pytest
```

Clean generated artifacts before building:

```bash
./bin/dev.sh clean
```

Install release tooling and build fresh artifacts:

```bash
uv pip install -e ".[dev]"
uv run python -m build
uv run twine check dist/*
```

Smoke-test the built wheel in an isolated environment:

```bash
python3 -m venv /tmp/propweaver-release-venv
/tmp/propweaver-release-venv/bin/pip install dist/propweaver-0.2.1-py3-none-any.whl
/tmp/propweaver-release-venv/bin/python -c "from propweaver import PropertyGraph; print(PropertyGraph)"
```

## TestPyPI Release

1. Push the release commit to GitHub.
2. Run the `Publish Python Distribution` workflow manually.
3. Confirm the `Publish To TestPyPI` job succeeds.
4. Validate installation from TestPyPI:

```bash
python3 -m venv /tmp/propweaver-testpypi-venv
/tmp/propweaver-testpypi-venv/bin/pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple propweaver==0.2.1
```

## PyPI Release

After the TestPyPI install check passes:

```bash
git tag v0.2.1
git push origin v0.2.1
```

That tag triggers the PyPI publish job automatically.

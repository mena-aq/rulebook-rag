## General Rules
- Follow PEP 8.
- Keep the code simple and modular.
- Prefer functions over classes unless a class is clearly justified.
- Avoid unnecessary abstractions.
- Do not duplicate logic.
- Write readable, maintainable code.

## Configuration
- Never hardcode API keys, model names, file paths, or runtime parameters.
- Store secrets in `.env`.
- Store application settings in `config/config.yaml`.
- Load configuration only through `config/config.py`.

## Prompts
- Never hardcode prompts.
- Store all prompts in `prompts/*.md`.
- Load prompts using `utils/prompt_loader.py`.

## Code Style
- All Python code must follow PEP 8.
- Use 2 blank lines for top-level code, and 1 blank line between class methods
- Use type hints for all functions.
- Use descriptive variable and function names.
- Keep functions small and focused on a single responsibility.
- Always use absolute imports
- Add meaningful block comments for complex sections of code
- Use the `logging` module instead of `print()` for debugging or production code.

### Docstring Format
Every function should include:
- A brief description of what the function does.
- `Args` describing each parameter.
- `Returns` describing the return value.
- `Raises` if the function can raise exceptions.

## Project Philosophy
- When multiple implementations are possible, choose the simplest solution that satisfies the requirements.


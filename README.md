# Java Code Migrator
This tool leverages LLMs to create a migration plan for legacy java code that uses relational databases to a java 21 SpringBoot 3.x application that uses MongoDB instead of the relational databases.

## System Requirements
- Python **3.11** (higher versions may work, but this was tested with 3.11)
- Poetry **2.x**
- Tested on Windows 11 but should also work on any Unix-based OS

## Configuration

All application settings are managed via [`config.ini`](./config.ini).

### Key Settings

- `api_key`: Your OpenAI key (**required**).
- `openai_model`: Model to use (e.g., `gpt-4o-mini`). Larger models may yield better results.
- `input_project`: Folder name inside `./input/` that contains the legacy codebase.
- `file_extensions_to_analyze`: Comma-separated file types (e.g., `java,xml`).
- `file_extensions_to_migrate`: Filter for which files to generate migrated versions for.
- `cache_llm_responses`: If `true`, reuses LLM results unless the input changes.

## Getting Started
1. Clone the repository
2. Create a virtual environment:
```bash
python3.11 -m venv .venv
```
3. Install dependencies using poetry:
```bash
poetry install
```
4. Validate that all the config fields are properly set in [config file](./config.ini)
5. Run the tool from the project's root directory:
```bash
poetry run python ./src/main.py
```
6. Check your results in the `./output/` directory:
  - `migration_plan.md`: final output

## Linting, Typing, and Testing
All quality checks are automated via pre-commit hooks.
### Run All Checks Manually
```bash
pre-commit run --all-files
```
**This includes:**
- Ruff for formatting + linting
- Mypy for type checking
- Pytest for running unit tests and generating coverage

### View Coverage Report (tested with Windows)
```bash
# macOS/Linux
open htmlcov/index.html

# Windows
start htmlcov\index.html
```

## Pre-commit Hook Setup
To automatically enforce code quality before every commit:
```bash
pre-commit install
```

## Code Layout
| Folder        | Purpose                                                                      |
|---------------|------------------------------------------------------------------------------|
| `src/`        | Application source code                                                      |
| `tests/`      | Unit tests                                                                   |
| `input/`      | Input repositories (select the one to analyze via `input_project` in config) |
| `output/`     | Output files including LLM responses and the final migration plan            |
| `resources/`  | Prompt templates and the markdown Jinja template used to generate output     |

## Sample Output
A sample migration plan generated for the `kitchensink` legacy project is available here:
[output/migration_plan.md](./output/migration_plan.md)

**The LLM used for generating this output is OpenAI's gpt-4o-mini**

## Potential Improvements
- Use specialized LLMs per stage (e.g., summarization vs. schema design vs. code migration). Currently, the same LLM is used in all stages.
- Create more structure in the final output JSON. The migration plan markdown file is created from an inline JSON object. Use a pydantic model/dataclass to improve readability and redundancy.
- Experiment with other LLMs and compare the results. It might be more beneficial to unify some of the structured LLM calls.
- Consider containerizing the application, depending on how it's aimed to be run. If it's run via a CICD pipeline(jenkins, gitlab CI, github actions, etc) it's simpler to retain the application as it is now.
- Create auditing and analytics for LLM prompts and responses.
- Add logging in a logstash(the application currently logs to a stdout)
- Add monitoring metrics with a tool like prometheus to monitor performance and LLM usage.
- Extend unit tests to simulate more realistic migration scenarios with richer mock data

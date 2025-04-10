import asyncio
from pathlib import Path

from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

from service.migration_planner import create_migration_plan
from util.config import get_config
from util.log_manager import LogManager, log_time
from util.md_utils import generate_markdown_from_json

OUTPUT_TEMPLATE_PATH = Path("./resources/output_templates/migration_plan.md.j2")
OUTPUT_RESULT_PATH = Path("./output/migration_plan.md")

log = LogManager.get_logger()
config = get_config()
if config.cache_llm_responses:
    log.info("Using cached LLM responses.")
    set_llm_cache(SQLiteCache("./cache/.langchain.db"))


async def main() -> None:
    async with log_time("Code migration planner", log):
        code_migration_output = await create_migration_plan()
        # Add the repository name for the title placeholder
        code_migration_output["application_name"] = config.input_project
        generate_markdown_from_json(code_migration_output, OUTPUT_TEMPLATE_PATH, OUTPUT_RESULT_PATH)


if __name__ == "__main__":
    asyncio.run(main())

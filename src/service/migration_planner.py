import asyncio
import dataclasses
import json
from collections import defaultdict
from pathlib import Path
from typing import List, Any, Dict

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from model.llm_response_models import CurrentApplication, MongoDBSchema, MigratedFileSchema, ImplementationPlan
from model.util_data_classes import AnalyzedFileDefinition
from util.config import get_config
from util.log_manager import LogManager, log_time


LLM_RESPONSE_OUTPUT_BASE_DIR = "./output/llm_responses"

log = LogManager.get_logger()
config = get_config()
doc_and_analysis: List[AnalyzedFileDefinition] = []

llm = ChatOpenAI(model=config.openai_model, api_key=SecretStr(config.openai_key), temperature=config.temperature)


def _load_files() -> List[Document]:
    input_project_path = f"./input/{config.input_project}"
    extensions = config.file_extensions_to_analyze.split(",")
    documents = []
    for extension in extensions:
        loader = DirectoryLoader(
            input_project_path,
            glob=f"**/*.{extension}",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        documents.extend(loader.load())

    log.info("Loaded %d files to analyze", len(documents))
    return documents


async def _analyze_file(doc: Document) -> str:
    with open("./resources/prompts_templates/analyze_java_file.prompt", "r") as f:
        prompt_template = PromptTemplate(template=f.read(), input_variables=["file_content"])

    path = Path(str(doc.metadata.get("source")))
    try:
        chain = prompt_template | llm
        response = await chain.ainvoke({"file_content": doc.page_content})
        log.info("Successfully analyzed file: %s with LLM", path.name)
        doc_and_analysis.append(
            AnalyzedFileDefinition(doc, str(response.content), path.name, str(doc.metadata.get("source")), path.suffix)
        )
        return str(response.content)
    except Exception as e:
        log.exception("Failed to analyze the input repository file: %s", path.name)
        raise e


async def _create_application_overview(analyses: List[str]) -> CurrentApplication:
    json_structured_llm = llm.with_structured_output(CurrentApplication)
    with open("./resources/prompts_templates/create_application_overview.prompt", "r") as f:
        prompt_template = PromptTemplate(
            template=f.read(),
            input_variables=["analyses"],
        )
    try:
        chain = prompt_template | json_structured_llm
        response = await chain.ainvoke({"analyses": analyses})
        log.info("Successfully generated an application overview")
        return response  # type: ignore
    except Exception as e:
        log.exception("Failed to generate application summary")
        raise e


async def _create_mongo_db_schema(analyses: List[str], schema: str) -> MongoDBSchema:
    json_structured_llm = llm.with_structured_output(MongoDBSchema)
    with open("./resources/prompts_templates/create_mongodb_schema.prompt", "r") as f:
        prompt_template = PromptTemplate(
            template=f.read(),
            input_variables=["analyses", "schema"],
        )
    try:
        chain = prompt_template | json_structured_llm
        response = await chain.ainvoke({"analyses": analyses, "schema": schema})
        log.info("Successfully generated a MongoDB schema.")
        return response  # type: ignore
    except Exception as e:
        log.exception("Failed to generate a MongoDB Schema")
        raise e


async def _migrate_file(file_description: AnalyzedFileDefinition) -> Dict[str, Any]:
    json_structured_llm = llm.with_structured_output(MigratedFileSchema)
    with open("./resources/prompts_templates/migrate_file.prompt", "r") as f:
        prompt_template = PromptTemplate(
            template=f.read(),
            input_variables=["analysis", "file_content"],
        )
    try:
        chain = prompt_template | json_structured_llm
        response = await chain.ainvoke(
            {"analysis": file_description.analysis, "file_content": file_description.doc.page_content}
        )
        log.info("Successfully generated a new migrated file to replace: %s", file_description.relative_path)
        return response.model_dump() | dataclasses.asdict(file_description)  # type: ignore
    except Exception as e:
        log.exception("Failed to generate a new migrated file for: %s", file_description.relative_path)
        raise e


async def _create_implementation_plan(
    existing_files: List[str], new_files: List[str], mongo_db_schemas: List[str]
) -> ImplementationPlan:
    json_structured_llm = llm.with_structured_output(ImplementationPlan)
    with open("./resources/prompts_templates/create_implementation_plan.prompt", "r") as f:
        prompt_template = PromptTemplate(
            template=f.read(),
            input_variables=["existing_files", "analyses", "new_files", "mongo_db_schemas"],
        )
    try:
        chain = prompt_template | json_structured_llm
        response = await chain.ainvoke(
            {"existing_files": existing_files, "new_files": new_files, "mongo_db_schemas": mongo_db_schemas}
        )
        log.info("Successfully generated an implementation plan")
        return response  # type: ignore
    except Exception as e:
        log.exception("Failed to generate an implementation plan")
        raise e


def _categorize_migrated_files(migrated_files: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    result = defaultdict(list)

    for migrated_file in migrated_files:
        result[migrated_file.get("file_category", "uncategorized")].append(migrated_file)
    return {"migrated_files": dict(result)}


def _log_llm_responses(
    analyses: List[str],
    overview: CurrentApplication,
    mongo_db_schemas: List[MongoDBSchema],
    migrated_files: List[Dict[str, Any]],
    implementation_plan: ImplementationPlan,
) -> None:
    with open(f"{LLM_RESPONSE_OUTPUT_BASE_DIR}/file_analyses.txt", "w") as f:
        text = "\n".join(analyses)
        f.write(text)
    with open(f"{LLM_RESPONSE_OUTPUT_BASE_DIR}/application_overview.json", "w") as f:
        json.dump(overview.model_dump(), f, indent=2)
    for mongo_db_schema in mongo_db_schemas:
        with open(f"{LLM_RESPONSE_OUTPUT_BASE_DIR}/{mongo_db_schema.collection_name}.json", "w") as f:
            json.dump(mongo_db_schema.model_dump(), f, indent=2)
    for migrated_file in migrated_files:
        with open(f"{LLM_RESPONSE_OUTPUT_BASE_DIR}/{migrated_file['name']}", "w") as f:
            f.write(migrated_file["new_file"])
    with open(f"{LLM_RESPONSE_OUTPUT_BASE_DIR}/implementation_plan.json", "w") as f:
        json.dump(implementation_plan.model_dump(), f, indent=2)


async def create_migration_plan() -> Dict[str, Any]:
    async with log_time("Repository file loading", log):
        existing_files = _load_files()
    async with log_time(f"Analyzing {len(existing_files)} repository files with LLM", log):
        analyses = await asyncio.gather(*(_analyze_file(file) for file in existing_files))
    if not analyses:
        raise Exception("Couldn't analyze requested files")
    async with log_time("Generating an application overview with LLM", log):
        overview = await _create_application_overview(analyses)
    if len(overview.database_tables) > 0:
        async with log_time("Generating a MongoDB schemas with LLM", log):
            mongo_db_schemas = await asyncio.gather(
                *(_create_mongo_db_schema(analyses, db_table.db_schema) for db_table in overview.database_tables)
            )
    async with log_time("Generating migrated files with LLM", log):
        migrated_files = await asyncio.gather(
            *(
                _migrate_file(file)
                for file in doc_and_analysis
                if file.file_extension in config.file_extensions_to_migrate
            )
        )
    async with log_time("Generating an implementation plan with LLM", log):
        implementation_plan = await _create_implementation_plan(
            list(map(lambda file: file.page_content, existing_files)),
            list(map(lambda file: file["new_file"], migrated_files)),
            list(map(lambda schema: schema.schema, mongo_db_schemas)),
        )

    if config.log_llm_responses:
        _log_llm_responses(analyses, overview, mongo_db_schemas, migrated_files, implementation_plan)

    return (
        overview.model_dump()
        | {"mongo_db_schemas": list(map(lambda schema: schema.model_dump(), mongo_db_schemas))}
        | _categorize_migrated_files(migrated_files)
        | implementation_plan.model_dump()
    )

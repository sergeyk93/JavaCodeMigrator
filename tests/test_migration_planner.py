from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from model.llm_response_models import (
    CurrentApplication,
    DBTable,
    MongoDBSchema,
    MongoDBDesignDecision,
    MigratedFileSchema,
    ImplementationPlan,
    ImplementationStep,
    ImplementationConsideration,
    MigratedAppTestingStrategy,
)
from service.migration_planner import create_migration_plan


@pytest.mark.asyncio
@patch("service.migration_planner._load_files")
async def test_create_migration_plan_success(mock_load_files: MagicMock, mock_ainvoke_pipeline: Any) -> None:
    mock_doc = Document(page_content="public class Test {}", metadata={"source": "input/Test.java"})
    mock_load_files.return_value = [mock_doc]
    mock_ainvoke_pipeline.side_effect = [
        # This is for `_analyze_file`: it expects `.content`
        MagicMock(content="Mocked analysis content"),
        # For `_create_application_overview`
        CurrentApplication(
            application_summary="Mocked app summary",
            db_entities=[],
            database_tables=[DBTable(name="users", db_schema="CREATE TABLE users (...)")],
            repositories=[],
            database_configurations=[],
            api_definitions=[],
        ),
        # For `_create_mongo_db_schema`
        MongoDBSchema(
            collection_name="users",
            mongo_db_schema="{ _id: ObjectId, name: String }",
            schema_decisions=[MongoDBDesignDecision(name="Design rationale", considerations=["Simplified data model"])],
        ),
        # For `_migrate_file`
        MigratedFileSchema(
            new_file="public class Migrated {}",
            file_category="Service",
        ),
        # For `_create_implementation_plan`
        ImplementationPlan(
            implementation_steps=[ImplementationStep(name="Step 1", sub_tasks=["Task A", "Task B"])],
            data_initialization_script="db.collection.insertMany(...)",
            additional_considerations=[
                ImplementationConsideration(consideration_name="Observability", consideration_points=["Add logging"])
            ],
            testing_strategy=MigratedAppTestingStrategy(
                unit_test_considerations=["Write focused tests"],
                integration_test_considerations=["Ensure MongoDB config"],
                test_class_template="@SpringBootTest",
            ),
        ),
    ]

    result: Dict[str, Any] = await create_migration_plan()

    assert result["application_summary"] == "Mocked app summary"
    assert result["mongo_db_schemas"][0]["collection_name"] == "users"
    assert result["migrated_files"]["Service"][0]["name"] == "Test.java"
    assert result["migrated_files"]["Service"][0]["new_file"] == "public class Migrated {}"
    assert result["implementation_steps"][0]["name"] == "Step 1"
    assert result["data_initialization_script"].startswith("db.collection.insertMany")
    assert "unit_test_considerations" in result["testing_strategy"]
    assert "integration_test_considerations" in result["testing_strategy"]
    assert result["testing_strategy"]["test_class_template"] == "@SpringBootTest"


@pytest.mark.asyncio
async def test_create_migration_plan_no_analysis_raises(mock_ainvoke_pipeline: Any) -> None:
    # No files analyzed, simulating empty analysis case
    mock_ainvoke_pipeline.return_value = None

    with pytest.raises(Exception):
        await create_migration_plan()

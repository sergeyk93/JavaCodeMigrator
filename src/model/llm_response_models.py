from typing import List

from pydantic import BaseModel, Field


class DBEntity(BaseModel):
    entity_name: str
    summary: str


class DBTable(BaseModel):
    name: str
    db_schema: str = Field(description="The table's schema including constraints in a code format.")


class APIDefinition(BaseModel):
    api_name: str
    api_path: str
    api_summary: str


class CurrentApplication(BaseModel):
    application_summary: str = Field(
        description="A paragraph containing a comprehensible summary of the analyzed application. It should include at the very least a programming language, web framework, databases used, and the main tech stack."
    )
    db_entities: List[DBEntity] = Field(
        description="All the analyzed DB entities with a one liner describing their purpose."
    )
    database_tables: List[DBTable] = Field(
        description="A list of all the analyzed database tables and their respective schemas."
    )
    repositories: List[str] = Field(description="A list of deductions on all the DAL repository classes.")
    database_configurations: List[str] = Field(description="A list of the analyzed database configuration")
    api_definitions: List[APIDefinition] = Field(
        description="A list of APIs. The API name is mapped to the path a short summary on the purpose of the API."
    )


class MongoDBDesignDecision(BaseModel):
    name: str = Field(
        description="A name that represents the design decision for recommending the proposed MongoDB schema."
    )
    considerations: List[str] = Field(description="A list of considerations that led to make the design decision.")


class MongoDBSchema(BaseModel):
    collection_name: str = Field(
        description="The name of the collection that will be created in MongoDB. Use the same name of the original table if applicable."
    )
    mongo_db_schema: str = Field(
        description="The proposed MongoDB schema to replace the schema of the existing application."
    )
    schema_decisions: List[MongoDBDesignDecision]


class MigratedFileSchema(BaseModel):
    new_file: str = Field(description="The proposed file to replace the file given in the prompt.")
    file_category: str = Field(description="The spring stereotype of that file")


class ImplementationStep(BaseModel):
    name: str = Field(
        description="A name that describes the goal of the implementation step. For example: 'Set up MongoDB environment' or 'Update service layer'"
    )
    sub_tasks: List[str] = Field(
        description="An ordered list of sub tasks that need to be completed to complete the implementation step."
    )


# This class might be redundant because ImplementationStep is the same. Keeping it because of the field names that are less likely to confuse the LLM to repeat steps.
class ImplementationConsideration(BaseModel):
    consideration_name: str = Field(
        description="The name of the implementation consideration. For example: 'Performance Optimization'."
    )
    consideration_points: List[str] = Field(
        description="A list of points that describe what aspects need to be considered."
    )


class MigratedAppTestingStrategy(BaseModel):
    unit_test_considerations: List[str] = Field(
        description="A list of points to consider when writing unit tests for the new migrated code."
    )
    integration_test_considerations: List[str] = Field(
        description="A list of points to consider when writing integration tests for the new migrated code. Notably with the new MongoDB dependency."
    )
    test_class_template: str = Field(
        description="A SpringBoot test class template for writing integration tests with MongoDB. Make sure to use all the proper annotation for this template to be ready to be used."
    )


class ImplementationPlan(BaseModel):
    implementation_steps: List[ImplementationStep] = Field(
        description="An ordered list of all the implementation steps for migrating the codebase from the analyzed files to the new files and technologies."
    )
    data_initialization_script: str = Field(
        description="A data initialization script to add initial data to the new MongoDB collection/s."
    )
    additional_considerations: List[ImplementationConsideration] = Field(
        description="A list of additional considerations the implementer might be interested in. This list is an addition to the implementation steps and mainly focuses on non-functional aspects like performance and serviceability."
    )
    testing_strategy: MigratedAppTestingStrategy = Field(
        description="A testing strategy for testing the newly migrated code."
    )

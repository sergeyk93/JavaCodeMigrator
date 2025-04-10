from typing import Any, Generator

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_ainvoke_pipeline() -> Generator[AsyncMock, Any, None]:
    with patch("service.migration_planner.PromptTemplate.__or__") as mock_pipe:
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock()
        mock_pipe.return_value = mock_chain
        yield mock_chain.ainvoke

"""Unit tests for base use case classes."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from services.orchestrator.shared.application.base_use_case import UseCase


class TestUseCase:
    """Test base UseCase class."""

    def test_use_case_is_abstract(self):
        """Test that UseCase cannot be instantiated directly."""
        with pytest.raises(TypeError):
            UseCase()

    def test_use_case_subclass_creation(self):
        """Test creating a concrete use case subclass."""

        class ConcreteUseCase(UseCase):
            async def execute(self, *args, **kwargs):
                return {"result": "success", "args": args, "kwargs": kwargs}

        use_case = ConcreteUseCase()
        assert isinstance(use_case, UseCase)
        assert isinstance(use_case, ConcreteUseCase)

    @pytest.mark.asyncio
    async def test_use_case_execution(self):
        """Test use case execution."""

        class TestUseCase(UseCase):
            def __init__(self):
                self.executed = False
                self.execution_args = None
                self.execution_kwargs = None

            async def execute(self, *args, **kwargs):
                self.executed = True
                self.execution_args = args
                self.execution_kwargs = kwargs
                return {"executed": True, "data": "test"}

        use_case = TestUseCase()

        # Test execution with no arguments
        result = await use_case.execute()
        assert result == {"executed": True, "data": "test"}
        assert use_case.executed is True
        assert use_case.execution_args == ()
        assert use_case.execution_kwargs == {}

        # Reset for next test
        use_case.executed = False

        # Test execution with arguments
        result = await use_case.execute("arg1", "arg2", key1="value1", key2="value2")
        assert result == {"executed": True, "data": "test"}
        assert use_case.executed is True
        assert use_case.execution_args == ("arg1", "arg2")
        assert use_case.execution_kwargs == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_use_case_exception_handling(self):
        """Test that use cases can raise exceptions."""

        class FailingUseCase(UseCase):
            async def execute(self, *args, **kwargs):
                raise ValueError("Use case failed")

        use_case = FailingUseCase()

        with pytest.raises(ValueError, match="Use case failed"):
            await use_case.execute()

    @pytest.mark.asyncio
    async def test_use_case_return_types(self):
        """Test use cases can return different types."""

        class StringUseCase(UseCase):
            async def execute(self, *args, **kwargs):
                return "string result"

        class DictUseCase(UseCase):
            async def execute(self, *args, **kwargs):
                return {"key": "value"}

        class ListUseCase(UseCase):
            async def execute(self, *args, **kwargs):
                return [1, 2, 3]

        class NoneUseCase(UseCase):
            async def execute(self, *args, **kwargs):
                return None

        string_result = await StringUseCase().execute()
        dict_result = await DictUseCase().execute()
        list_result = await ListUseCase().execute()
        none_result = await NoneUseCase().execute()

        assert string_result == "string result"
        assert dict_result == {"key": "value"}
        assert list_result == [1, 2, 3]
        assert none_result is None


class TestUseCaseIntegration:
    """Test use case integration patterns."""

    @pytest.mark.asyncio
    async def test_use_case_chaining(self):
        """Test chaining multiple use cases."""

        class FirstUseCase(UseCase):
            async def execute(self, *args, **kwargs):
                return {"step": 1, "data": "first"}

        class SecondUseCase(UseCase):
            async def execute(self, first_result, *args, **kwargs):
                return {
                    "step": 2,
                    "data": "second",
                    "previous": first_result
                }

        first_uc = FirstUseCase()
        second_uc = SecondUseCase()

        first_result = await first_uc.execute()
        second_result = await second_uc.execute(first_result)

        assert first_result == {"step": 1, "data": "first"}
        assert second_result["step"] == 2
        assert second_result["previous"] == first_result

    @pytest.mark.asyncio
    async def test_use_case_with_dependencies(self):
        """Test use case with dependency injection."""

        class Repository:
            def __init__(self):
                self.data = {"items": []}

            async def save(self, item):
                self.data["items"].append(item)
                return item

        class CreateItemUseCase(UseCase):
            def __init__(self, repository: Repository):
                self.repository = repository

            async def execute(self, item_data, *args, **kwargs):
                saved_item = await self.repository.save(item_data)
                return {"created": True, "item": saved_item}

        repository = Repository()
        use_case = CreateItemUseCase(repository)

        result = await use_case.execute({"name": "Test Item", "value": 42})

        assert result["created"] is True
        assert result["item"] == {"name": "Test Item", "value": 42}
        assert len(repository.data["items"]) == 1
        assert repository.data["items"][0] == {"name": "Test Item", "value": 42}

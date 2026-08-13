# Python Testing Patterns

## Test Structure

Use pytest with the Arrange-Act-Assert pattern:

```python
def test_user_registration():
    # Arrange
    user_data = {"email": "test@example.com", "password": "secure123"}
    
    # Act
    result = register_user(user_data)
    
    # Assert
    assert result.email == "test@example.com"
    assert result.is_active is True
```

## Fixtures

Use fixtures for shared setup:

```python
@pytest.fixture
def sample_user():
    return User(name="Test", email="test@example.com")

def test_user_fixture(sample_user):
    assert sample_user.name == "Test"
```

## Mocking

Use `unittest.mock` for external dependencies:

```python
from unittest.mock import patch, MagicMock

@patch("mymodule.external_api")
def test_api_call(mock_api):
    mock_api.get_user.return_value = {"id": 1, "name": "Alice"}
    
    result = get_user_name(1)
    
    assert result == "Alice"
    mock_api.get_user.assert_called_once_with(1)
```

## Parameterized Tests

Use `pytest.mark.parametrize` for multiple test cases:

```python
@pytest.mark.parametrize("input,expected", [
    (2, 4),
    (3, 9),
    (5, 25),
])
def test_square(input, expected):
    assert square(input) == expected
```

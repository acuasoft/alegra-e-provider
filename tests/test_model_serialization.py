"""Test Pydantic model serialization to ensure proper V2 API usage."""
import json
import warnings

from alegra.models.address import Address
from alegra.models.company import Company


class TestModelSerialization:
    """Test that models use Pydantic V2 API correctly."""

    def test_model_dump_json_instead_of_deprecated_json(self):
        """Test that model_dump_json() works correctly without deprecation warnings."""
        company_data = Company(
            name="Test Company",
            identification="123456789",
            dv="0",
            useAlegraCertificate=True,
            organizationType=1,
            identificationType="31",
            email="test@example.com",
            address=Address(
                address="Test St",
                city="11001",
                department="11",
                country="CO",
            ),
        )

        # Test model_dump_json() - the correct Pydantic V2 method
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            json_str = company_data.model_dump_json()
            
            # Should not generate any deprecation warnings
            pydantic_warnings = [
                warning for warning in w 
                if "PydanticDeprecated" in str(warning.category)
            ]
            assert len(pydantic_warnings) == 0, (
                "model_dump_json() should not generate deprecation warnings"
            )

        # Verify the JSON is valid
        parsed = json.loads(json_str)
        assert parsed["name"] == "Test Company"
        assert parsed["identification"] == "123456789"
        assert parsed["email"] == "test@example.com"

    def test_deprecated_json_method_generates_warning(self):
        """Test that the deprecated json() method generates a warning."""
        company_data = Company(
            name="Test Company",
            identification="123456789",
            dv="0",
            useAlegraCertificate=True,
            organizationType=1,
            identificationType="31",
            email="test@example.com",
            address=Address(
                address="Test St",
                city="11001",
                department="11",
                country="CO",
            ),
        )

        # Test that json() generates a deprecation warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            json_str = company_data.json()
            
            # Should generate a deprecation warning
            pydantic_warnings = [
                warning for warning in w 
                if "PydanticDeprecated" in str(warning.category)
            ]
            assert len(pydantic_warnings) > 0, (
                "json() should generate a PydanticDeprecatedSince20 warning"
            )
            assert "model_dump_json" in str(pydantic_warnings[0].message)

    def test_model_dump_for_dict_serialization(self):
        """Test that model_dump() works correctly for dict serialization."""
        company_data = Company(
            name="Test Company",
            identification="123456789",
            dv="0",
            useAlegraCertificate=True,
            organizationType=1,
            identificationType="31",
            email="test@example.com",
            address=Address(
                address="Test St",
                city="11001",
                department="11",
                country="CO",
            ),
        )

        # Test model_dump() - the correct Pydantic V2 method for dict conversion
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            data_dict = company_data.model_dump()
            
            # Should not generate any deprecation warnings
            pydantic_warnings = [
                warning for warning in w 
                if "PydanticDeprecated" in str(warning.category)
            ]
            assert len(pydantic_warnings) == 0, (
                "model_dump() should not generate deprecation warnings"
            )

        # Verify the dict is correct
        assert isinstance(data_dict, dict)
        assert data_dict["name"] == "Test Company"
        assert data_dict["identification"] == "123456789"
        assert data_dict["email"] == "test@example.com"
        assert isinstance(data_dict["address"], dict)

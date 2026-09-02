# Alegra API Client

This project provides an API client for the Alegra platform using the `pydantic` and `requests` libraries. The modular structure allows for flexible and extensible resource management.

## Installation

1. Clone the repository.
2. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Configuration

Create a configuration object to handle API key and environment settings.

```python
from config import ApiConfig

config = ApiConfig(api_key='your_api_key', environment='sandbox')
```

## Usage

Initialize the API client with the configuration:

```python
from client import ApiClient

client = ApiClient(config)
```

### Company Operations

#### Create a Company

```python
from models.company import Company, NotificationByEmail

company_data = Company(
    useAlegraCertificate=True,
    notificationByEmail=NotificationByEmail(enabled=True)
)
new_company = client.companies.create(company_data)
print(new_company.id, new_company.name)
```

#### Get a Company

```python
company = client.companies.get("company_id")
print(company.id, company.name)
```

#### Update a Company

```python
updated_data = Company(name="Updated Company Name")
updated_company = client.companies.update("company_id", updated_data)
print(updated_company.name)
```

#### List Companies

```python
companies = client.companies.list()
for company in companies:
    print(company.id, company.name)
```

### Payroll Operations

#### Create a Payroll

```python
from models.payroll import Payroll

payroll_data = Payroll(
    prefix="NE",
    number=1,
    governmentData={"key": "value"}
)
new_payroll = client.payrolls.create(payroll_data)
print(new_payroll.id, new_payroll.prefix)
```

#### Get a Payroll

```python
payroll = client.payrolls.get("payroll_id")
print(payroll.id, payroll.prefix)
```

#### Update a Payroll

```python
updated_data = Payroll(prefix="NE", number=2)
updated_payroll = client.payrolls.update("payroll_id", updated_data)
print(updated_payroll.number)
```

#### List Payrolls

```python
payrolls = client.payrolls.list()
for payroll in payrolls:
    print(payroll.id, payroll.prefix)
```

#### Replace a Payroll

```python
replacement_data = Payroll(prefix="NE", number=2, governmentData={"key": "new_value"})
replaced_payroll = client.payrolls.perform_subaction("payroll_id", "replace", replacement_data)
print(replaced_payroll.id, replaced_payroll.number)
```

#### Cancel a Payroll

```python
cancel_response = client.payrolls.perform_subaction("payroll_id", "cancel")
print(cancel_response)
```

### DIAN Operations

#### List DIAN Resources

```python
dian_resources = client.dian.list()
for resource in dian_resources:
    print(resource.id, resource.name)
```

### Test Set Operations

#### Create a Test Set

```python
from models.test_set import TestSet

test_set_data = TestSet(
    type="test",
    governmentId="gov123",
    idCompany="company_id"
)
new_test_set = client.test_sets.create(test_set_data)
print(new_test_set.id)
```

#### Get a Test Set

```python
test_set = client.test_sets.get("test_set_id")
print(test_set.id, test_set.type)
```

## Error Handling

Every error the client raises intentionally is an `AlegraApiError`:

- **`AlegraConfigurationError`**: invalid `ApiConfig` (bad `environment`, blank `api_key`)
- **`AlegraHttpError`**: an HTTP error response, or a network/transport failure. Carries `.status_code` (`None` for network errors), `.url`, and `.response`
- **`AlegraResponseParseError`**: a "successful" response didn't have the expected shape

```python
from alegra import AlegraApiError, AlegraHttpError

try:
    new_company = client.companies.create(company_data)
except AlegraHttpError as e:
    print(f"Request to {e.url} failed with status {e.status_code}")
except AlegraApiError as e:
    print(f"An error occurred: {e}")
```

## Working with Pydantic Models

This library uses Pydantic V2 for data validation. When working with models, use the Pydantic V2 API:

### Serializing Models to JSON

```python
from alegra.models.company import Company

company = Company(...)

# ✅ Correct - Use model_dump_json() (Pydantic V2)
json_string = company.model_dump_json()

# ❌ Deprecated - Avoid using json() (will be removed in Pydantic V3)
json_string = company.json()  # Generates deprecation warning
```

### Serializing Models to Dictionary

```python
# ✅ Correct - Use model_dump() (Pydantic V2)
data_dict = company.model_dump()

# ❌ Deprecated - Avoid using dict() (will be removed in Pydantic V3)
data_dict = company.dict()  # Generates deprecation warning
```

For more information, see the [Pydantic V2 Migration Guide](https://docs.pydantic.dev/latest/migration/).

## License

This project is licensed under the MIT License.

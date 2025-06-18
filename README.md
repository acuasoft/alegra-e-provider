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

The library provides comprehensive error handling with specific exception classes for different types of errors:

### Exception Classes

- **`AlegraApiError`**: Base class for all API-related errors
- **`AlegraHttpError`**: General HTTP errors with detailed information
- **`AlegraAuthenticationError`**: Authentication failures (401)
- **`AlegraAuthorizationError`**: Authorization failures (403)
- **`AlegraNotFoundError`**: Resource not found (404)
- **`AlegraValidationError`**: Validation errors (422)
- **`AlegraRateLimitError`**: Rate limit exceeded (429)
- **`AlegraServerError`**: Server errors (5xx)
- **`AlegraResponseParseError`**: Response parsing failures
- **`AlegraConfigurationError`**: Configuration errors

### Usage Example

```python
from alegra import ApiClient, ApiConfig, AlegraAuthenticationError, AlegraNotFoundError

try:
    config = ApiConfig(api_key="your_api_key", environment="production")
    client = ApiClient(config)
    
    # This might raise various exceptions
    invoice = client.invoices.get("some_invoice_id")
    
except AlegraAuthenticationError as e:
    print(f"Authentication failed: {e}")
    print(f"Status code: {e.status_code}")
    
except AlegraNotFoundError as e:
    print(f"Invoice not found: {e}")
    print(f"URL: {e.url}")
    
except AlegraApiError as e:
    print(f"API error occurred: {e}")
    if e.response:
        print(f"Response data: {e.response}")
```

### Error Information

All HTTP error exceptions include:
- `status_code`: HTTP status code
- `response_text`: Raw response text
- `url`: The URL that was requested
- `response`: Parsed response data (when available)

## License

This project is licensed under the MIT License.

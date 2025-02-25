import vcr
from vcr.unittest import VCRTestCase

from alegra.client import ApiClient
from alegra.config import ApiConfig
from alegra.models.company import Address, Company, GovernmentStatus


class TestCompanyResource(VCRTestCase):
    def setUp(self):
        self.config = ApiConfig(api_key="REDACTED", environment="sandbox")
        self.client = ApiClient(self.config)

    @vcr.use_cassette(
        "tests/fixtures/vcr_cassettes/test_create_company.yaml",
        filter_headers=["authorization"],
    )
    def test_create_company(self):
        company_data = Company(
            name="Soluciones Alegra S.A.S",
            identification="111111111",
            dv="2",
            useAlegraCertificate=True,
            governmentStatus=GovernmentStatus(payrolls="AUTHORIZED"),
            organizationType=1,
            identificationType="31",
            regimeCode="R-99-PN",
            email="email@email.com",
            phone="1234567890",
            address=Address(
                address="Cra. 13 #12-12 Edificio A & A",
                city="11001",
                department="11",
                country="CO",
            ),
        )

        company = self.client.companies.create(company_data)

        self.assertEqual(company.name, "Soluciones Alegra S.A.S")
        self.assertEqual(company.identification, "111111111")
        self.assertEqual(company.dv, "2")
        self.assertTrue(company.useAlegraCertificate)
        self.assertEqual(company.organizationType, 1)
        self.assertEqual(company.identificationType, "31")
        self.assertEqual(company.regimeCode, "R-99-PN")
        self.assertEqual(company.email, "email@email.com")
        self.assertEqual(company.address.address, "Cra. 13 #12-12 Edificio A & A")
        self.assertEqual(company.address.city, "11001")
        self.assertEqual(company.address.department, "11")
        self.assertEqual(company.address.country, "CO")

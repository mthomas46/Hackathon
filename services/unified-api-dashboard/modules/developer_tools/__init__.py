class ClientCodeGenerator:
    async def generate_client(self, *args):
        return "class Client: pass"


class APIValidator:
    async def validate_openapi_spec(self, *args):
        return {"valid": True}


class IntegrationTester:
    async def run_test_suite(self, *args):
        return {"passed": True}


__all__ = ["ClientCodeGenerator", "APIValidator", "IntegrationTester"]

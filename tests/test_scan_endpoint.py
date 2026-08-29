import unittest

from models.schemas import AnalysisPack, ScanStartRequest
from server.api.scan import scan


class ScanEndpointTestCase(unittest.TestCase):
    def test_scan_endpoint_returns_response_for_all_active_packs(self):
        for pack in [
            AnalysisPack.DANGEROUS_API,
            AnalysisPack.SECRETS,
            AnalysisPack.INJECTION,
            AnalysisPack.AUTHORIZATION,
        ]:
            with self.subTest(pack=pack):
                request = ScanStartRequest(
                    workspace_path=".",
                    source_code="print('hello')",
                    pack=pack,
                )

                response = scan(request)

                self.assertEqual(response.status, "completed")
                self.assertIsInstance(response.findings, list)
                self.assertEqual(response.finding_count, len(response.findings))


if __name__ == "__main__":
    unittest.main()

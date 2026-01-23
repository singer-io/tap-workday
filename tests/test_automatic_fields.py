"""Test that with no fields selected for a stream automatic fields are still
replicated."""

import unittest
from tap_tester.base_suite_tests.automatic_fields_test import \
    MinimumSelectionTest

from base import WorkdayBaseTest, WorkdayBaseTestFinancialManagement


class WorkdayAutomaticFieldsStandard(MinimumSelectionTest, WorkdayBaseTest):
    """Test automatic fields replication for Absence/Performance streams (standard credentials).
    
    Only tests streams accessible with standard credentials to avoid authorization errors.
    """

    @staticmethod
    def name():
        return "tap_tester_workday_automatic_fields_test_standard"

    def streams_to_test(self):
        # Only test streams accessible with standard credentials
        streams_to_exclude = set()
        return set(self.testable_streams).difference(streams_to_exclude)


@unittest.skip("Skipping Financial Management test - credentials failing with 'invalid username or password' error")
class WorkdayAutomaticFieldsFinancial(MinimumSelectionTest, WorkdayBaseTestFinancialManagement):
    """Test automatic fields replication for Financial/HR/Staffing streams (financial management credentials).
    
    SKIPPED: Financial Management credentials (QLIK_ISU_USER25@talend_dpt1) are currently failing
    with authentication errors. All 22 streams fail with "SOAP Fault: invalid username or password".
    This indicates expired credentials, insufficient permissions, or account lockout.
    Requires investigation with Workday system administrator before enabling.
    
    Heavy streams are excluded to avoid timeouts.
    """

    @staticmethod
    def name():
        return "tap_tester_workday_automatic_fields_test_financial"

    def streams_to_test(self):
        # Exclude heavy streams from testing to avoid timeouts
        streams_to_exclude = {
            "financial_management_journals",
            "financial_management_ledgers",
        }
        return set(self.testable_streams).difference(streams_to_exclude)

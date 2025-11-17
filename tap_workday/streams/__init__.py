from tap_workday.streams.absence_management import AbsenceInputs, OverrideBalances
from tap_workday.streams.financial_management import (
    CostCenters,
    PositionBudgets,
    Organizations as FmOrganizations,
    CustomerCategories,
    FundHierarchies,
    FundingSources,
    Funds,
    FundTypes,
    Journals,
    JournalSources,
    LedgerAccountSummaries,
    Ledgers,
    ProgramHierarchies,
    Programs,
    RevenueCategories,
    RevenueCategoryHierarchies,
    SpendCategoryHierarchies,
    SupplierCategories,
)
from tap_workday.streams.human_resources import (
    JobCategories,
    JobFamilyGroups,
    JobProfiles,
    Locations,
    Organizations,
)
from tap_workday.streams.performance_management import (
    CertificationIssuers,
    Competencies,
    CompetencyCategories,
    Degrees,
)
from tap_workday.streams.staffing import Organizations as StaffingOrganizations

STREAMS = {
    # Human_Resources
    "human_resources_job_categories": JobCategories,
    "human_resources_job_family_groups": JobFamilyGroups,
    "human_resources_job_profiles": JobProfiles,
    "human_resources_locations": Locations,
    "human_resources_organizations": Organizations,
    # Financial_Management
    "financial_management_cost_centers": CostCenters,
    "financial_management_customer_categories": CustomerCategories,
    "financial_management_fund_hierarchies": FundHierarchies,
    "financial_management_fund_types": FundTypes,
    "financial_management_funding_sources": FundingSources,
    "financial_management_funds": Funds,
    "financial_management_journal_sources": JournalSources,
    "financial_management_journals": Journals,
    "financial_management_ledger_account_summaries": LedgerAccountSummaries,
    "financial_management_ledgers": Ledgers,
    "financial_management_organizations": FmOrganizations,
    "financial_management_position_budgets": PositionBudgets,
    "financial_management_program_hierarchies": ProgramHierarchies,
    "financial_management_programs": Programs,
    "financial_management_revenue_categories": RevenueCategories,
    "financial_management_revenue_category_hierarchies": RevenueCategoryHierarchies,
    "financial_management_spend_category_hierarchies": SpendCategoryHierarchies,
    "financial_management_supplier_categories": SupplierCategories,
    # Staffing
    "staffing_organizations": StaffingOrganizations,
    # Absence_Management
    "absence_management_override_balances": OverrideBalances,
    "absence_management_absence_inputs": AbsenceInputs,
    # Performance_Management
    "performance_management_certification_issuers": CertificationIssuers,
    "performance_management_competencies": Competencies,
    "performance_management_competency_categories": CompetencyCategories,
    "performance_management_degrees": Degrees,
}

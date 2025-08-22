from tap_workday.streams.absence_management.get_override_balances import GetOverrideBalances

from tap_workday.streams.human_resources.get_organizations import GetOrganizations
from tap_workday.streams.human_resources.get_job_categories import GetJobCategories

STREAMS = {
    # Absence_Management
    "get_override_balances": GetOverrideBalances,

    # Human_Resources
    "get_organizations": GetOrganizations,
    "get_job_categories": GetJobCategories
}

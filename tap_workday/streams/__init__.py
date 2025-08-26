from tap_workday.streams.absence_management import OverrideBalances, AbsenceInputs
from tap_workday.streams.human_resources import Organizations, JobCategories

STREAMS = {
    # Absence_Management
    "absence_management_override_balances": OverrideBalances,
    "absence_management_absence_inputs": AbsenceInputs,
    # Human_Resources
    "human_resources_job_categories": JobCategories,
    "human_resources_organizations": Organizations,
}

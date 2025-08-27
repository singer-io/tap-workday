from tap_workday.streams.absence_management import OverrideBalances, AbsenceInputs
from tap_workday.streams.human_resources import (
    Organizations,
    JobCategories,
    JobFamilyGroups,
    JobProfiles,
    Locations,
)
from tap_workday.streams.performance_management import (
    CertificationIssuers,
    Competencies,
    CompetencyCategories,
    Degrees,
)


STREAMS = {
    # Absence_Management
    "absence_management_override_balances": OverrideBalances,
    "absence_management_absence_inputs": AbsenceInputs,

    # Human_Resources
    "human_resources_job_categories": JobCategories,
    "human_resources_job_family_groups": JobFamilyGroups,
    "human_resources_job_profiles": JobProfiles,
    "human_resources_locations": Locations,
    "human_resources_organizations": Organizations,

    # Performance_Management
    "performance_management_certification_issuers": CertificationIssuers,
    "performance_management_competencies": Competencies,
    "performance_management_competency_categories": CompetencyCategories,
    "performance_management_degrees": Degrees,
}

from tap_workday.streams.human_resources.get_organizations import GetOrganizations
from tap_workday.streams.human_resources.get_job_categories import GetJobCategories

STREAMS = {
    "get_organizations": GetOrganizations,
    "get_job_categories": GetJobCategories
}


from zeep.helpers import serialize_object

from tap_workday.streams.abstracts import FullTableStream
from tap_workday.streams.common import get_workday_client, emit_full_table, safe_get_records


class Organizations(FullTableStream):
    """Staffing.Get_Organizations stream.

    Reuses centralized helpers from `common.py` and `abstracts.py` to keep logic
    consistent with Human_Resources.Get_Organizations.
    """

    tap_stream_id = "staffing_get_organizations"
    replication_method = "FULL_TABLE"
    # Workday Organization reference commonly exposes Organization_ID.value
    key_properties = ["Organization_ID.value"]
    # In both HR and Staffing responses, the leaf array/object is typically "Organization"
    data_key = "Organization"

    def get_client(self):
        cfg = self.client.config
        # Allow overriding version via config; default to a recent common version
        version = cfg.get("staffing_version", "v44.2")
        return get_workday_client(
            tenant=cfg["tenant"],
            username=cfg["username"],
            password=cfg["password"],
            service="Staffing",
            version=version,
        )

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()

        # The Staffing service exposes Get_Organizations with similar request/response
        # shapes. We call it without filters to pull a full snapshot.
        response = client.service.Get_Organizations()
        serialized = serialize_object(response)

        # Safely extract the list even if Response_Data or Organization is None/singular.
        records = safe_get_records(serialized, self.data_key)

        # Emit schema + transformed records via the shared helper.
        return emit_full_table(self, records)

import xml.etree.ElementTree as ET
from typing import List, Optional
from datetime import datetime

from core.customs_tracking.dto.progress_detail import ProgressDetail
from core.customs_tracking.api_spec.unipass_api_spec import (
    TAG_PROCESS_DETAIL,
    TAG_PROCESS_DATETIME,
    TAG_PROCESS_STATUS,
    TAG_PROCESS_COMMENT,
    UNIPASS_INPUT_FORMATTER,
    UNIPASS_OUTPUT_FORMATTER,
    NA
)

def parse_progress(xml: str) -> Optional[List[ProgressDetail]]:
    root = ET.fromstring(xml)
    nodes = root.findall(f".//{TAG_PROCESS_DETAIL}")
    progress_list = []

    for node in nodes:
        process_datetime = _get_tag_value(node, TAG_PROCESS_DATETIME)
        status = _get_tag_value(node, TAG_PROCESS_STATUS) or NA
        comment = _get_tag_value(node, TAG_PROCESS_COMMENT) or ""

        try:
            if process_datetime and len(process_datetime) == 14:
                dt = datetime.strptime(process_datetime, UNIPASS_INPUT_FORMATTER)
                datetime_str = dt.strftime(UNIPASS_OUTPUT_FORMATTER)
            else:
                datetime_str = process_datetime or NA
        except Exception:
            datetime_str = process_datetime

        progress_list.append(ProgressDetail(datetime=datetime_str, status=status, comment=comment))

    progress_list.sort(key=lambda x: (x.datetime or ""), reverse=False)
    return progress_list or None

def _get_tag_value(element: ET.Element, tag: str) -> Optional[str]:
    tag_node = element.find(tag)
    return tag_node.text if tag_node is not None else None
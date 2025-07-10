import re

# XML tag constants
TAG_PROCESS_DETAIL = "cargCsclPrgsInfoDtlQryVo"
TAG_PROCESS_DATETIME = "prcsDttm"
TAG_PROCESS_STATUS = "cargTrcnRelaBsopTpcd"
TAG_PROCESS_COMMENT = "rlbrCn"

# API parameter constants
PARAM_API_KEY = "crkyCn"
PARAM_CARGO_NO = "cargMtNo"
PARAM_HBL_NO = "hblNo"
PARAM_MBL_NO = "mblNo"
PARAM_BL_YEAR = "blYy"

# Fallback value
NA = "N/A"

# Date format patterns
UNIPASS_INPUT_FORMATTER = "%Y%m%d%H%M%S"
UNIPASS_OUTPUT_FORMATTER = "%Y-%m-%d %H:%M:%S"

# Regex pattern for cargo number validation
CARGO_NO_PATTERN = re.compile(r"^(?=.*[A-Z])(?=.*\d)[A-Z0-9]{15}$|^(?=.*[A-Z])(?=.*\d)[A-Z0-9]{19}$")

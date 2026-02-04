"""Constants for insurance eligibility checking."""

# Service Type Codes
SERVICE_TYPE_CODE_HEALTH_BENEFIT = "30"
SERVICE_TYPE_CODE_OFFICE_VISIT = "98"

# Status Codes
STATUS_CODE_ACTIVE = "1"
STATUS_ACTIVE_COVERAGE = "Active Coverage"

# Coverage Level Codes
COVERAGE_LEVEL_CODE_COPAY = "B"

# Network Indicators
NETWORK_IN_NETWORK = "Y"
NETWORK_OUT_OF_NETWORK = "N"

# API Configuration
STEDI_API_TIMEOUT = 30
STEDI_API_MAX_RETRIES = 3
STEDI_RETRY_MIN_WAIT = 2
STEDI_RETRY_MAX_WAIT = 10
STEDI_ELIGIBILITY_ENDPOINT = "/2024-04-01/change/medicalnetwork/eligibility/v3"

# STEDI Request Configuration
# just to test with AETNA mock payer eventually the plan here would be to add multi-payer support (Better for production)
STEDI_CONTROL_NUMBER = "000000001"
STEDI_TRADING_PARTNER_SERVICE_ID = "60054"
STEDI_PROVIDER_NPI = "1999999984"
STEDI_PROVIDER_ORG_NAME = "Paratus Health"

# Voice Agent
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice

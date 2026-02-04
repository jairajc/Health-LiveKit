"""STEDI API client for insurance eligibility checks."""

import os
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.constants import (
    SERVICE_TYPE_CODE_HEALTH_BENEFIT,
    SERVICE_TYPE_CODE_OFFICE_VISIT,
    STEDI_API_MAX_RETRIES,
    STEDI_API_TIMEOUT,
    STEDI_CONTROL_NUMBER,
    STEDI_ELIGIBILITY_ENDPOINT,
    STEDI_PROVIDER_NPI,
    STEDI_PROVIDER_ORG_NAME,
    STEDI_RETRY_MAX_WAIT,
    STEDI_RETRY_MIN_WAIT,
    STEDI_TRADING_PARTNER_SERVICE_ID,
)
from src.utils.exceptions import StediAPIError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StediClient:
    """Client for interacting with the STEDI API."""

    def __init__(self):
        self.api_url = os.getenv("STEDI_API_URL", "https://healthcare.us.stedi.com")
        self.api_key = os.getenv("STEDI_API_KEY")

        if not self.api_key:
            logger.warning("STEDI_API_KEY not set in environment")

        self.timeout = STEDI_API_TIMEOUT

        # Allow overriding constants with environment variables
        self.control_number = os.getenv(
            "STEDI_CONTROL_NUMBER", STEDI_CONTROL_NUMBER
        )
        self.trading_partner_id = os.getenv(
            "STEDI_TRADING_PARTNER_SERVICE_ID", STEDI_TRADING_PARTNER_SERVICE_ID
        )
        self.provider_npi = os.getenv("STEDI_PROVIDER_NPI", STEDI_PROVIDER_NPI)
        self.provider_org_name = os.getenv(
            "STEDI_PROVIDER_ORG_NAME", STEDI_PROVIDER_ORG_NAME
        )

    def _build_eligibility_payload(
        self,
        first_name: str,
        last_name: str,
        member_id: str,
        date_of_birth: str | None = None,
    ) -> dict[str, Any]:
        """Build STEDI eligibility request payload.

        Args:
            first_name: Subscriber first name
            last_name: Subscriber last name
            member_id: Insurance member ID
            date_of_birth: Date of birth in YYYYMMDD format (optional, defaults to test value)
        """
        # test mode date of birth if not provided
        dob = date_of_birth or "20040404"

        return {
            "controlNumber": self.control_number,
            "tradingPartnerServiceId": self.trading_partner_id,
            "subscriber": {
                "firstName": first_name,
                "lastName": last_name,
                "memberId": member_id,
                "dateOfBirth": dob,
            },
            "provider": {
                "npi": self.provider_npi,
                "organizationName": self.provider_org_name,
            },
            "encounter": {
                "serviceTypeCodes": [
                    SERVICE_TYPE_CODE_HEALTH_BENEFIT,
                    SERVICE_TYPE_CODE_OFFICE_VISIT,
                ],
            },
        }

    def _validate_response(
        self,
        response: httpx.Response,
        member_id: str,
    ) -> dict[str, Any]:
        """Validate and extract data from STEDI API response."""
        # non-success status
        if response.status_code != httpx.codes.OK:
            error_msg = f"STEDI API returned status {response.status_code}"
            logger.error(
                "eligibility_check_failed",
                status_code=response.status_code,
                error=response.text,
            )
            raise StediAPIError(error_msg, response.status_code)

        # success case - extract and return data
        response_data = response.json()
        logger.info(
            "eligibility_check_success",
            member_id=member_id,
            has_subscriber=bool(response_data.get("subscriber")),
        )
        return response_data

    @retry(
        stop=stop_after_attempt(STEDI_API_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=STEDI_RETRY_MIN_WAIT, max=STEDI_RETRY_MAX_WAIT),
        reraise=True,
    )
    async def check_eligibility(
        self,
        first_name: str,
        last_name: str,
        member_id: str,
        date_of_birth: str | None = None,
    ) -> dict[str, Any]:
        """Check insurance eligibility via STEDI API."""
        logger.info(
            "checking_eligibility",
            first_name=first_name,
            last_name=last_name,
            member_id=member_id,
        )

        # request components
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        payload = self._build_eligibility_payload(
            first_name, last_name, member_id, date_of_birth
        )
        url = f"{self.api_url}{STEDI_ELIGIBILITY_ENDPOINT}"

        # only http request
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as e:
            logger.error("eligibility_check_timeout", error=str(e))
            raise StediAPIError("STEDI API request timed out") from e
        except httpx.RequestError as e:
            logger.error("eligibility_check_error", error=str(e))
            raise StediAPIError(f"STEDI API request failed: {str(e)}") from e

        # validate response
        return self._validate_response(response, member_id)

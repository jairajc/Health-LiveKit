"""Insurance eligibility assistant with function tools."""

from typing import TypedDict

from livekit.agents import Agent, function_tool
from livekit.agents.llm import ToolError

from src.logic.copay_finder import CopayFinder
from src.logic.eligibility_checker import EligibilityChecker
from src.prompts.insurance_agent import INSURANCE_AGENT_INSTRUCTIONS
from src.services.stedi_client import StediClient
from src.utils.exceptions import StediAPIError
from src.utils.logger import get_logger

logger = get_logger(__name__)


# tool return types for better type safety
class ToolStatusResponse(TypedDict):
    """Standard tool status response."""

    status: str
    message: str


class CoverageDetails(TypedDict):
    """Coverage status details."""

    status: str | None
    status_code: str | None


class CoverageStatusResponse(TypedDict):
    """Insurance coverage status response."""

    status: str
    message: str
    details: CoverageDetails


class CopayFoundResponse(TypedDict):
    """Response when copay is found."""

    status: str
    amount: str
    network_status: str
    message: str


class CopayNotFoundResponse(TypedDict):
    """Response when copay is not found."""

    status: str
    message: str


class InsuranceAssistant(Agent):
    """Voice agent for collecting and verifying insurance eligibility."""

    def __init__(self):
        super().__init__(instructions=INSURANCE_AGENT_INSTRUCTIONS)

        self.stedi_client = StediClient()
        self.eligibility_checker = EligibilityChecker()
        self.copay_finder = CopayFinder()

        # store collected patient data
        self.patient_data = {}

    @function_tool()
    async def collect_patient_name(
        self,
        first_name: str,
        last_name: str,
    ) -> ToolStatusResponse:
        """Store and confirm patient's first and last name."""
        logger.info(
            "collect_patient_name",
            first_name=first_name,
            last_name=last_name,
        )

        if not first_name or not first_name.strip():
            raise ToolError("Please provide your first name.")

        if not last_name or not last_name.strip():
            raise ToolError("Please provide your last name.")

        self.patient_data["first_name"] = first_name.strip()
        self.patient_data["last_name"] = last_name.strip()

        return {
            "status": "success",
            "message": f"Got it. I have {first_name} {last_name}. Is that correct?",
        }

    @function_tool()
    async def collect_member_id(
        self,
        member_id: str,
    ) -> ToolStatusResponse:
        """Store and confirm insurance member ID."""
        logger.info(
            "collect_member_id",
            member_id=member_id,
        )

        # missing member ID
        if not member_id or not member_id.strip():
            raise ToolError("Please provide your member ID.")

        # invalid length
        if len(member_id.strip()) < 5:
            raise ToolError(
                "That member ID seems too short. "
                "Please provide your full member ID."
            )

        # normalize to uppercase for api compatibility found this while testing
        normalized_id = member_id.strip().upper()

        # store in instance
        self.patient_data["member_id"] = normalized_id

        # spell back for confirmation using normalized version
        spelled_id = " ".join(normalized_id)
        return {
            "status": "success",
            "message": f"I have member ID: {spelled_id}. Is that correct?",
        }

    @function_tool()
    async def run_stedi_query(
        self,
        first_name: str,
        last_name: str,
        member_id: str,
    ) -> ToolStatusResponse:
        """Query STEDI API for insurance eligibility."""
        logger.info(
            "run_stedi_query",
            first_name=first_name,
            last_name=last_name,
            member_id=member_id,
        )

        try:
            response = await self.stedi_client.check_eligibility(
                first_name=first_name,
                last_name=last_name,
                member_id=member_id,
            )
        except StediAPIError as e:
            logger.error("stedi_query_failed", error=str(e))
            raise ToolError(
                "I'm having trouble connecting to the insurance system. "
                "Would you like me to connect you with a representative?"
            ) from e

        # Store in instance
        self.patient_data["first_name"] = first_name
        self.patient_data["last_name"] = last_name
        self.patient_data["member_id"] = member_id
        self.patient_data["stedi_response"] = response

        return {
            "status": "success",
            "message": "Successfully retrieved eligibility information",
        }

    @function_tool()
    async def validate_stedi_response(self) -> ToolStatusResponse:
        """Validate the STEDI API response stored in session."""
        logger.info("validate_stedi_response")

        # no response stored
        if "stedi_response" not in self.patient_data:
            raise ToolError(
                "No eligibility data found. Let me check your information again."
            )

        response = self.patient_data["stedi_response"]
        validation_result = self.eligibility_checker.validate_response(response)

        # validation fails
        if not validation_result.is_valid:
            logger.warning(
                "validation_failed",
                error=validation_result.error_message,
            )
            raise ToolError(
                "I'm having trouble reading your insurance information. "
                "Let me verify your details again. "
                "Could you please confirm your name and member ID?"
            )

        return {
            "status": "valid",
            "message": "Eligibility information validated successfully",
        }

    @function_tool()
    async def check_insurance_active(self) -> CoverageStatusResponse:
        """Check if the insurance coverage is active."""
        logger.info("check_insurance_active")

        # no response stored
        if "stedi_response" not in self.patient_data:
            raise ToolError("No eligibility data found")

        response = self.patient_data["stedi_response"]
        active_result = self.eligibility_checker.check_active_coverage(response)

        # store result in instance
        self.patient_data["insurance_active"] = active_result.is_active

        # inactive coverage
        if not active_result.is_active:
            logger.warning("insurance_not_active", status=active_result.status)
            return {
                "status": "inactive",
                "message": "Coverage appears to be inactive",
                "details": {
                    "status": active_result.status,
                    "status_code": active_result.status_code,
                },
            }

        return {
            "status": "active",
            "message": "Coverage is active",
            "details": {
                "status": active_result.status,
                "status_code": active_result.status_code,
            },
        }

    @function_tool()
    async def find_stc98_copay(self) -> CopayFoundResponse | CopayNotFoundResponse:
        """Find office visit copay (service type code 98)."""
        logger.info("find_stc98_copay")

        # no response stored
        if "stedi_response" not in self.patient_data:
            raise ToolError("No eligibility data found")

        response = self.patient_data["stedi_response"]
        copay_result = self.copay_finder.find_copay(response)

        # store result in instance
        self.patient_data["copay_info"] = {
            "found": copay_result.found,
            "amount": copay_result.amount,
            "network_status": copay_result.network_status,
        }

        # copay not found
        if not copay_result.found:
            logger.warning("copay_not_found")
            return {
                "status": "not_found",
                "message": (
                    "I couldn't find specific copay details for office visits "
                    "in your benefits. I recommend contacting your insurance "
                    "provider directly for this information."
                ),
            }

        # message based on network status
        amount = copay_result.amount
        network_status = copay_result.network_status

        if network_status == "in_network":
            message = (
                f"Great news! Your copay for in-network office visits is ${amount}. "
                "This applies when you see providers in your insurance network."
            )
            return {
                "status": "found",
                "amount": amount,
                "network_status": network_status,
                "message": message,
            }

        # out-of-network
        if network_status == "out_of_network":
            message = (
                f"I found a copay amount of ${amount}, but this appears to be "
                "for out-of-network providers. For in-network coverage details, "
                "please contact your insurance provider."
            )
            return {
                "status": "found",
                "amount": amount,
                "network_status": network_status,
                "message": message,
            }

        # unknown network status
        message = (
            f"Your copay for office visits is ${amount}, though I couldn't "
            "determine the specific network status. I recommend verifying with "
            "your insurance provider whether this applies to in-network or "
            "out-of-network visits."
        )
        return {
            "status": "found",
            "amount": amount,
            "network_status": network_status,
            "message": message,
        }

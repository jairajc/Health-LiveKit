"""Logic for validating and checking insurance eligibility."""

from dataclasses import dataclass
from typing import Any

from src.utils.constants import (
    SERVICE_TYPE_CODE_HEALTH_BENEFIT,
    STATUS_ACTIVE_COVERAGE,
    STATUS_CODE_ACTIVE,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of eligibility response validation."""

    is_valid: bool
    error_message: str | None = None


@dataclass
class ActiveCoverageResult:
    """Result of active coverage check."""

    is_active: bool
    status: str | None = None
    status_code: str | None = None
    service_type_codes: list[str] | None = None


class EligibilityChecker:
    """Checker for insurance eligibility validation and status."""

    def _is_coverage_active(self, status: str | None, status_code: str | None) -> bool:
        """Check if coverage status indicates active coverage."""
        return status == STATUS_ACTIVE_COVERAGE or status_code == STATUS_CODE_ACTIVE

    def validate_response(self, response: dict[str, Any]) -> ValidationResult:
        """Validate STEDI eligibility response structure."""
        logger.debug("validating_response", has_response=bool(response))

        if not response:
            return ValidationResult(
                is_valid=False,
                error_message="Empty response from STEDI API",
            )

        # errors in response
        errors = response.get("errors")
        if errors:
            error_msg = f"STEDI API returned errors: {errors}"
            logger.warning("validation_failed_errors", errors=errors)
            return ValidationResult(is_valid=False, error_message=error_msg)

        # subscriber information
        subscriber = response.get("subscriber")
        if not subscriber:
            logger.warning("validation_failed_no_subscriber")
            return ValidationResult(
                is_valid=False,
                error_message="No subscriber information in response",
            )

        # plan status information
        plan_status = response.get("planStatus")
        if not plan_status:
            logger.warning("validation_failed_no_plan_status")
            return ValidationResult(
                is_valid=False,
                error_message="No plan status information in response",
            )

        logger.info("validation_success")
        return ValidationResult(is_valid=True)

    def check_active_coverage(
        self, response: dict[str, Any]
    ) -> ActiveCoverageResult:
        """Check if the insurance has active coverage."""
        logger.debug("checking_active_coverage")

        plan_statuses = response.get("planStatus", [])

        # no plan statuses to check
        if not plan_statuses:
            logger.warning("no_plan_statuses")
            return ActiveCoverageResult(
                is_active=False,
                status=None,
                status_code=None,
                service_type_codes=None,
            )

        for plan_status in plan_statuses:
            # skip if not health benefit plan
            service_type_codes = plan_status.get("serviceTypeCodes", [])
            if SERVICE_TYPE_CODE_HEALTH_BENEFIT not in service_type_codes:
                continue

            # health benefit plan
            status = plan_status.get("status")
            status_code = plan_status.get("statusCode")
            is_active = self._is_coverage_active(status, status_code)

            logger.info(
                "found_health_benefit_plan",
                status=status,
                status_code=status_code,
                service_type_codes=service_type_codes,
                is_active=is_active,
            )

            return ActiveCoverageResult(
                is_active=is_active,
                status=status,
                status_code=status_code,
                service_type_codes=service_type_codes,
            )

        # no health benefit plan
        logger.warning("no_health_benefit_plan_found")
        return ActiveCoverageResult(
            is_active=False,
            status=None,
            status_code=None,
            service_type_codes=None,
        )

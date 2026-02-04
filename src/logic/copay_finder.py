"""Logic for finding copay information in eligibility responses."""

from dataclasses import dataclass
from typing import Any, Literal

from src.utils.constants import (
    COVERAGE_LEVEL_CODE_COPAY,
    NETWORK_IN_NETWORK,
    NETWORK_OUT_OF_NETWORK,
    SERVICE_TYPE_CODE_OFFICE_VISIT,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

NetworkStatus = Literal["in_network", "out_of_network", "unknown"]


@dataclass
class CopayResult:
    """Result of copay search."""

    found: bool
    amount: str | None = None
    network_status: NetworkStatus = "unknown"


class CopayFinder:
    """Finder for copay information in eligibility responses."""

    def _determine_network_status(self, network_indicator: str | None) -> NetworkStatus:
        """Determine network status from indicator code."""
        if network_indicator == NETWORK_IN_NETWORK:
            return "in_network"
        if network_indicator == NETWORK_OUT_OF_NETWORK:
            return "out_of_network"
        return "unknown"

    def find_copay(
        self,
        response: dict[str, Any],
        service_type_code: str = SERVICE_TYPE_CODE_OFFICE_VISIT,
    ) -> CopayResult:
        """Find copay information for a specific service type."""
        logger.debug("finding_copay", service_type_code=service_type_code)

        benefits_information = response.get("benefitsInformation", [])

        # no benefits to check
        if not benefits_information:
            logger.warning("no_benefits_information", service_type_code=service_type_code)
            return CopayResult(found=False)

        for benefit in benefits_information:
            # skip if not a copay benefit
            code = benefit.get("code")
            if code != COVERAGE_LEVEL_CODE_COPAY:
                continue

            #  skip if not for the requested service type
            service_type_codes = benefit.get("serviceTypeCodes", [])
            if service_type_code not in service_type_codes:
                continue

            # matching copay 
            amount = benefit.get("benefitAmount")
            network_indicator = benefit.get("inPlanNetworkIndicatorCode")
            network_status = self._determine_network_status(network_indicator)

            logger.info(
                "copay_found",
                amount=amount,
                network_status=network_status,
                service_type_code=service_type_code,
            )

            return CopayResult(
                found=True,
                amount=amount,
                network_status=network_status,
            )

        logger.warning(
            "copay_not_found",
            service_type_code=service_type_code,
            num_benefits=len(benefits_information),
        )

        return CopayResult(found=False)

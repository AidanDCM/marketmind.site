"""Marketing models (Phase 12).

Initial scaffolding for Campaign and related entities.
"""

from .attribution_event import AttributionEvent
from .bundle_result import BundleResult
from .bundle_trial import BundleTrial
from .campaign import Campaign
from .campaign_asset import CampaignAsset
from .customer_cohort import CustomerCohort
from .customer_journey import CustomerJourney
from .experiment import Experiment
from .experiment_result import ExperimentResult
from .experiment_variant import ExperimentVariant

__all__ = [
    "Campaign",
    "CampaignAsset",
    "Experiment",
    "ExperimentResult",
    "CustomerJourney",
    "AttributionEvent",
    "ExperimentVariant",
    "BundleTrial",
    "BundleResult",
    "CustomerCohort",
]

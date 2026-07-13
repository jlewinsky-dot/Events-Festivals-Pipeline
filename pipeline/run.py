import logging

from discovery.get_serp import get_serp_events
from analysis.dedup_on_emails import deduplicate
from analysis.profitability import classify_profitability_batch

logger = logging.getLogger(__name__)


def run_pipeline_for_site(cities):
    """Discover, dedup, and classify events for a single site's cities."""
    logger.info("Fetching Serp events")
    events = get_serp_events(cities)
    events = deduplicate(events)
    events = classify_profitability_batch(events)
    logger.info("Finished fetching Serp events")
    return events
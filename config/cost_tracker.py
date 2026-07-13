import threading
import logging

logger = logging.getLogger(__name__)

# Cost per token (OpenAI lists prices per million, I store per token)
PRICING = {
    "gpt-5": {"input": 1.25 / 1_000_000, "output": 10.00 / 1_000_000},
    "gpt-5-search-api": {"input": 1.25 / 1_000_000, "output": 10.00 / 1_000_000, "per_search": 10.00 / 1_000},
    "gpt-4.1-mini": {"input": 0.40 / 1_000_000, "output": 1.60 / 1_000_000},
}

# Pricing per serp call
SERPAPI_COST_PER_CALL = 275.00 / 30_000


class CostTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self.reset() # Resets all counts

    # Zeros the token count, zeroes the call counts, zeroes the serp count
    def reset(self):
        with self._lock: # Ensures counter is incremented before any other threads can increment
            # creates key and input, output, calls for each model in the pricing dict
            self.openai = {model: {"input_tokens": 0, "output_tokens": 0, "calls": 0} for model in PRICING}
            self.serpapi_calls = 0


    def track_openai(self, model, usage):
        with self._lock:
            # Get the used model counts and increment
            increment_model = self.openai.get(model) # Getting which model to increment
            if increment_model:
                increment_model["input_tokens"] += usage.prompt_tokens
                increment_model["output_tokens"] += usage.completion_tokens
                increment_model["calls"] += 1

    def track_serpapi(self):
        with self._lock:
            self.serpapi_calls += 1

    def cost_for(self, model):
        data = self.openai[model]
        price = PRICING[model]
        # Calculating the total cost
        cost = data["input_tokens"] * price["input"] + data["output_tokens"] * price["output"]
        if "per_search" in price:
            cost += data["calls"] * price["per_search"]
        return cost

    # Creating summary rows output
    def summary_rows(self):
        with self._lock:
            rows = [("Cost Summary", "")]
            total = 0.0
            for model, data in self.openai.items():
                if data["calls"] == 0:
                    continue
                cost = self.cost_for(model)
                total += cost
                rows.append((f"{model} Calls:", data["calls"]))
                rows.append((f"{model} Input tokens:", f"{data['input_tokens']:,}"))
                rows.append((f"{model} Output tokens:", f"{data['output_tokens']:,}"))
                rows.append((f"{model} Cost:", f"${cost:.4f}"))

            serpapi_cost = self.serpapi_calls * SERPAPI_COST_PER_CALL
            total += serpapi_cost
            rows.append(("SerpAPI Calls:", self.serpapi_calls))
            rows.append(("SerpAPI Cost:",  f"${serpapi_cost:.4f}"))
            rows.append(("TOTAL:",         f"${total:.4f}"))
            return rows

    def print_summary(self):
        lines = ["\nCost Summary"]
        for label, value in self.summary_rows()[1:]:   # skip the header row
            lines.append(f"  {label:<24} {value}")
        lines.append("========================\n")
        logger.info("\n".join(lines))


tracker = CostTracker()
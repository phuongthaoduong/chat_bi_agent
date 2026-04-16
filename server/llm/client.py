import json
import logging

from openai import OpenAI

from config import QWEN_API_KEY, QWEN_BASE_URL, QWEN_MODEL
from llm.prompts import (
    DASHBOARD_SYSTEM_PROMPT,
    build_dataset_inventory,
    build_profile_detail,
)
from models.domain import (
    AnalysisIntent,
    AnalysisPlan,
    ChartSpec,
    DashboardSuggestion,
    DataSource,
    FilterCondition,
    SheetProfile,
    SortSpec,
)

logger = logging.getLogger(__name__)


def parse_dashboard_response(raw: str) -> DashboardSuggestion:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {e}")

    if "plans" not in data:
        raise ValueError("Missing 'plans' in LLM response")

    plans = []
    for p in data["plans"]:
        source = DataSource(
            file_name=p["source"]["file_name"],
            sheet_name=p["source"]["sheet_name"],
        )
        filters = None
        if p.get("filters"):
            filters = [
                FilterCondition(field=f["field"], operator=f["operator"], value=f["value"])
                for f in p["filters"]
            ]
        sort = None
        if p.get("sort"):
            sort = SortSpec(field=p["sort"]["field"], direction=p["sort"]["direction"])

        chart = None
        if p.get("chart"):
            chart = ChartSpec(
                chart_type=p["chart"]["chart_type"],
                title=p["chart"]["title"],
                x_axis=p["chart"].get("x_axis"),
                y_axis=p["chart"].get("y_axis"),
            )

        plans.append(
            AnalysisPlan(
                source=source,
                intent=AnalysisIntent(p["intent"]),
                target_fields=p["target_fields"],
                group_by=p.get("group_by"),
                filters=filters,
                sort=sort,
                limit=p.get("limit"),
                chart=chart,
            )
        )

    return DashboardSuggestion(
        insights=data.get("insights", []),
        plans=plans,
    )


class LLMClient:
    def __init__(self):
        self._client = OpenAI(
            api_key=QWEN_API_KEY,
            base_url=QWEN_BASE_URL,
        )

    def suggest_dashboard(self, profiles: list[SheetProfile]) -> DashboardSuggestion:
        inventory = build_dataset_inventory(profiles)
        detail = build_profile_detail(profiles)

        prompt = DASHBOARD_SYSTEM_PROMPT.format(
            dataset_inventory=inventory,
            profile_detail=detail,
        )

        response = self._client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        raw = response.choices[0].message.content
        logger.info("LLM dashboard response: %s", raw)

        try:
            return parse_dashboard_response(raw)
        except (ValueError, KeyError) as e:
            logger.warning("First LLM parse failed (%s), retrying...", e)
            response = self._client.chat.completions.create(
                model=QWEN_MODEL,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": raw},
                    {
                        "role": "user",
                        "content": "Your response was not valid JSON. Please respond with ONLY the JSON structure, no markdown or code fences.",
                    },
                ],
                temperature=0.1,
            )
            raw = response.choices[0].message.content
            return parse_dashboard_response(raw)

import json
import logging

from openai import OpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from llm.prompts import (
    CHAT_CLASSIFY_PROMPT,
    CHAT_FORMAT_COMPUTATIONAL_PROMPT,
    CHAT_FORMAT_CONVERSATIONAL_PROMPT,
    DASHBOARD_SYSTEM_PROMPT,
    build_dataset_inventory,
    build_profile_detail,
    format_chat_history,
)
from models.domain import (
    AnalysisIntent,
    AnalysisPlan,
    AnalysisResult,
    ChartSpec,
    DashboardSuggestion,
    DataSource,
    FilterCondition,
    Message,
    QuestionInterpretation,
    QuestionType,
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


def parse_question_interpretation(raw: str) -> QuestionInterpretation:
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

    question_type = QuestionType(data["question_type"])

    plan = None
    if data.get("plan"):
        p = data["plan"]
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
        plan = AnalysisPlan(
            source=source,
            intent=AnalysisIntent(p["intent"]),
            target_fields=p["target_fields"],
            group_by=p.get("group_by"),
            filters=filters,
            sort=sort,
            limit=p.get("limit"),
            chart=chart,
        )

    return QuestionInterpretation(question_type=question_type, plan=plan)


class LLMClient:
    def __init__(self):
        self._client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )

    def suggest_dashboard(self, profiles: list[SheetProfile]) -> DashboardSuggestion:
        inventory = build_dataset_inventory(profiles)
        detail = build_profile_detail(profiles)

        prompt = DASHBOARD_SYSTEM_PROMPT.format(
            dataset_inventory=inventory,
            profile_detail=detail,
        )

        response = self._client.chat.completions.create(
            model=DEEPSEEK_MODEL,
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
                model=DEEPSEEK_MODEL,
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

    def interpret_question(
        self,
        question: str,
        profiles: list[SheetProfile],
        chat_history: list[Message],
    ) -> QuestionInterpretation:
        inventory = build_dataset_inventory(profiles)
        detail = build_profile_detail(profiles)
        history = format_chat_history(chat_history)

        prompt = CHAT_CLASSIFY_PROMPT.format(
            dataset_inventory=inventory,
            profile_detail=detail,
            chat_history=history,
            question=question,
        )

        response = self._client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        raw = response.choices[0].message.content
        logger.info("LLM classify response: %s", raw)

        try:
            return parse_question_interpretation(raw)
        except (ValueError, KeyError) as e:
            logger.warning("First classify parse failed (%s), retrying...", e)
            response = self._client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": raw},
                    {
                        "role": "user",
                        "content": "Your response was not valid JSON. Please respond with ONLY the JSON structure, no markdown.",
                    },
                ],
                temperature=0.1,
            )
            raw = response.choices[0].message.content
            return parse_question_interpretation(raw)

    def format_answer(
        self,
        question: str,
        plan: AnalysisPlan | None,
        result: AnalysisResult | None,
        profiles: list[SheetProfile],
        chat_history: list[Message],
    ) -> str:
        if plan and result:
            result_json = json.dumps(self._serialize_result(result), indent=2)
            prompt = CHAT_FORMAT_COMPUTATIONAL_PROMPT.format(
                question=question,
                result_json=result_json,
            )
        else:
            inventory = build_dataset_inventory(profiles)
            detail = build_profile_detail(profiles)
            history = format_chat_history(chat_history)
            prompt = CHAT_FORMAT_CONVERSATIONAL_PROMPT.format(
                dataset_inventory=inventory,
                profile_detail=detail,
                chat_history=history,
                question=question,
            )

        response = self._client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    def _serialize_result(self, result: AnalysisResult) -> dict:
        data = result.data
        if hasattr(data, "items"):
            return {"type": "list", "items": data.items}
        elif hasattr(data, "value"):
            return {"type": "scalar", "label": data.label, "value": data.value}
        elif hasattr(data, "rows"):
            return {"type": "table", "columns": data.columns, "rows": data.rows}
        return {}

"""The model must be able to look up real places, and must survive it failing."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest

import bot
from places import Place

PLACE = Place(
    name="Surf Point Cafe",
    address="Rawai, Phuket",
    maps_url="https://maps.google.com/?cid=99",
    place_id="abc",
)


@dataclass
class FakeCall:
    name: str
    arguments: str
    call_id: str = "call_1"
    type: str = "function_call"

    def model_dump(self, exclude_none: bool = False) -> dict:
        return {"type": self.type, "name": self.name, "call_id": self.call_id}


@dataclass
class FakeResponse:
    output_text: str = ""
    output: list = field(default_factory=list)


@dataclass
class FakeOpenAI:
    """Replays scripted responses and records what it was asked."""

    scripted: list
    calls: list = field(default_factory=list)

    @property
    def responses(self):
        return self

    def create(self, *, model, input, tools=None):
        self.calls.append({"input": list(input), "tools": tools})
        return self.scripted[min(len(self.calls) - 1, len(self.scripted) - 1)]


@dataclass
class FakePlaces:
    results: list
    queries: list = field(default_factory=list)

    async def search(self, query, *, limit=5, open_now=False):
        self.queries.append((query, open_now))
        return self.results


@pytest.fixture
def wire(monkeypatch):
    def _wire(scripted, places=None):
        fake_client = FakeOpenAI(scripted)
        monkeypatch.setattr(bot, "client", fake_client)
        monkeypatch.setattr(bot, "places", places)
        return fake_client

    return _wire


def call(query="cafe Rawai", open_now=None):
    arguments = {"query": query}
    if open_now is not None:
        arguments["open_now"] = open_now
    return FakeCall(name="find_places", arguments=json.dumps(arguments))


@pytest.mark.asyncio
async def test_tool_result_is_fed_back_and_final_answer_returned(wire):
    places = FakePlaces([PLACE])
    fake = wire(
        [
            FakeResponse(output=[call(open_now=True)]),
            FakeResponse(output_text=f"Surf Point Cafe: {PLACE.maps_url}"),
        ],
        places,
    )

    answer = await bot.run_model([{"role": "user", "content": "кафе в Равае"}])

    assert answer == f"Surf Point Cafe: {PLACE.maps_url}"
    assert places.queries == [("cafe Rawai", True)]

    tool_output = fake.calls[1]["input"][-1]
    assert tool_output["call_id"] == "call_1"
    payload = json.loads(tool_output["output"])
    assert payload["places"] == [PLACE.for_model()]
    # The function_call itself must precede its output.
    assert fake.calls[1]["input"][-2]["type"] == "function_call"


@pytest.mark.asyncio
async def test_tool_is_offered_only_when_place_search_is_configured(wire):
    fake = wire([FakeResponse(output_text="Привет")], None)

    await bot.run_model([{"role": "user", "content": "привет"}])

    assert fake.calls[0]["tools"] == []


@pytest.mark.asyncio
async def test_tool_is_offered_when_place_search_is_configured(wire):
    fake = wire([FakeResponse(output_text="Привет")], FakePlaces([]))

    await bot.run_model([{"role": "user", "content": "привет"}])

    assert fake.calls[0]["tools"] == [bot.FIND_PLACES_TOOL]


def test_prompt_promises_a_lookup_only_when_one_is_available(monkeypatch):
    """Without a key Mike must not stall waiting for a search he cannot run."""
    monkeypatch.setattr(bot, "places", None)
    assert bot.PLACE_SEARCH_PROMPT not in bot.system_prompt()

    monkeypatch.setattr(bot, "places", FakePlaces([]))
    assert bot.PLACE_SEARCH_PROMPT in bot.system_prompt()


@pytest.mark.asyncio
async def test_no_results_are_reported_to_the_model_as_an_empty_list(wire):
    fake = wire(
        [
            FakeResponse(output=[call()]),
            FakeResponse(output_text="Не нашёл такого места"),
        ],
        FakePlaces([]),
    )

    assert await bot.run_model([]) == "Не нашёл такого места"
    assert json.loads(fake.calls[1]["input"][-1]["output"]) == {"places": []}


@pytest.mark.asyncio
async def test_tool_call_without_place_search_reports_unavailable(wire):
    """The model can still ask for the tool from replayed history."""
    fake = wire(
        [FakeResponse(output=[call()]), FakeResponse(output_text="Подскажу иначе")],
        None,
    )

    assert await bot.run_model([]) == "Подскажу иначе"
    assert json.loads(fake.calls[1]["input"][-1]["output"])["places"] == []


@pytest.mark.asyncio
async def test_malformed_tool_arguments_do_not_raise(wire):
    places = FakePlaces([])
    wire(
        [
            FakeResponse(output=[FakeCall(name="find_places", arguments="{not json")]),
            FakeResponse(output_text="ок"),
        ],
        places,
    )

    assert await bot.run_model([]) == "ок"
    assert places.queries == [("", False)]


@pytest.mark.asyncio
async def test_unknown_tool_is_reported_back_instead_of_crashing(wire):
    fake = wire(
        [
            FakeResponse(output=[FakeCall(name="book_flight", arguments="{}")]),
            FakeResponse(output_text="Не умею"),
        ],
        FakePlaces([]),
    )

    assert await bot.run_model([]) == "Не умею"
    assert "unknown tool" in fake.calls[1]["input"][-1]["output"]


@pytest.mark.asyncio
async def test_endless_tool_calling_is_capped_and_still_answers(wire):
    """A model that only ever calls tools must not loop forever."""
    looping = FakeResponse(output=[call()])
    fake = wire([looping] * bot.MAX_TOOL_ROUNDS, FakePlaces([PLACE]))

    await bot.run_model([])

    assert len(fake.calls) == bot.MAX_TOOL_ROUNDS + 1
    assert fake.calls[-1]["tools"] is None


@pytest.mark.asyncio
async def test_several_tool_calls_in_one_turn_are_all_serviced(wire):
    places = FakePlaces([PLACE])
    fake = wire(
        [
            FakeResponse(
                output=[
                    call(query="cafe Rawai"),
                    FakeCall(
                        name="find_places",
                        arguments=json.dumps({"query": "beach Rawai"}),
                        call_id="call_2",
                    ),
                ]
            ),
            FakeResponse(output_text="Вот варианты"),
        ],
        places,
    )

    assert await bot.run_model([]) == "Вот варианты"
    assert [query for query, _ in places.queries] == ["cafe Rawai", "beach Rawai"]
    assert [
        item["call_id"]
        for item in fake.calls[1]["input"]
        if item.get("type") == "function_call_output"
    ] == ["call_1", "call_2"]

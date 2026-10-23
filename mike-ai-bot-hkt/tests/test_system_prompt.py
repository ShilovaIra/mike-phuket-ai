"""What Mike is told to say when someone wants a hotel or a job."""

from __future__ import annotations

from bot import system_prompt

REFUSAL = "Беру заявки только на аренду или покупку виллы, квартиры, дома или комнаты."


def test_an_opening_hotel_or_job_is_only_the_refusal():
    prompt = system_prompt()

    assert REFUSAL in prompt
    assert "Если чат начинается с отеля или работы" in prompt
    assert "не задавай ни одного вопроса" in prompt
    assert "Весь ответ — только эта фраза" in prompt


def test_a_hotel_or_job_during_a_rent_or_buy_continues_with_the_home():
    prompt = system_prompt()

    assert (
        "Если во время аренды или покупки просят отель или работу, скажи эту фразу"
        in prompt
    )
    assert "затем задай следующий вопрос про жильё" in prompt


def test_a_hotel_name_used_as_a_landmark_still_gets_a_guide_answer():
    prompt = system_prompt()

    assert "Название отеля как ориентир — не запрос отеля" in prompt
    assert "отвечай на сам вопрос" in prompt


def test_a_job_request_is_refused_without_an_interview():
    prompt = system_prompt()

    assert (
        "Если человек просит работу, вакансию, подработку или хочет устроиться — не помогай."
        in prompt
    )
    assert "Не спрашивай сферу, опыт или должность." in prompt


def test_a_hostel_guesthouse_land_shop_or_office_gets_the_same_refusal():
    prompt = system_prompt()

    assert (
        "Той же одной фразой отвечай на отель, хостел, гестхаус, землю, магазин или офис."
        in prompt
    )


def test_a_lead_is_only_for_renting_or_buying_a_home():
    prompt = system_prompt()

    assert "Заявку собирай только когда человек хочет снять или купить жильё" in prompt
    assert "вилла, квартира, дом, комната или просто жильё" in prompt
    assert "Срок проживания не важен." in prompt
    assert "Не спрашивай тип жилья." in prompt
    assert "Для комнаты не спрашивай число спален." in prompt
    assert "ЗАЯВКА_ГОТОВА пиши только для такой заявки." in prompt
    assert "Если человек хочет снять или купить жильё, мягко выясняй:" in prompt
    assert "Если человек интересуется недвижимостью" not in prompt


def test_mike_offers_rent_or_buy_of_a_home():
    prompt = system_prompt()

    assert (
        "Помогай туристам с пляжами, ресторанами, маршрутами, экскурсиями, транспортом и арендой или покупкой жилья."
        in prompt
    )
    assert "транспортом и недвижимостью" not in prompt

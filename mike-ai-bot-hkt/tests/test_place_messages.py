"""Several places in one answer go out as one message per place."""

from __future__ import annotations

from place_messages import place_messages

TOM_YUM = (
    "https://www.google.com/maps/search/?api=1&query=Tom+Yum+Goong+Nai+Harn+Phuket"
)
SMILE = "https://www.google.com/maps/search/?api=1&query=Smile+Bar+%26+Cafe+Phuket"


def test_two_maps_links_become_two_place_messages_and_the_header_is_dropped():
    answer = (
        "Вот ссылки:\n\n"
        "Tom Yum Goong Nai Harn:\n"
        f"{TOM_YUM}\n\n"
        "Smile Bar & Cafe:\n"
        f"{SMILE}"
    )

    messages = place_messages(answer)

    assert [message.text for message in messages] == [
        f"Tom Yum Goong Nai Harn:\n{TOM_YUM}",
        f"Smile Bar & Cafe:\n{SMILE}",
    ]
    assert all(message.is_place for message in messages)


def test_two_maps_links_without_a_blank_line_still_split():
    answer = f"Tom Yum Goong Nai Harn:\n{TOM_YUM}\nSmile Bar & Cafe:\n{SMILE}"

    messages = place_messages(answer)

    assert [message.text for message in messages] == [
        f"Tom Yum Goong Nai Harn:\n{TOM_YUM}",
        f"Smile Bar & Cafe:\n{SMILE}",
    ]
    assert [message.is_place for message in messages] == [True, True]


def test_a_note_stays_with_the_place_above_and_the_closing_line_is_separate():
    answer = (
        "Tom Yum Goong Nai Harn:\n"
        f"{TOM_YUM}\n\n"
        "Острее, сидят у моря.\n\n"
        "Smile Bar & Cafe:\n"
        f"{SMILE}\n\n"
        "Сказать, как доехать?"
    )

    messages = place_messages(answer)

    assert [message.text for message in messages] == [
        f"Tom Yum Goong Nai Harn:\n{TOM_YUM}\n\nОстрее, сидят у моря.",
        f"Smile Bar & Cafe:\n{SMILE}",
        "Сказать, как доехать?",
    ]
    assert [message.is_place for message in messages] == [True, True, False]


def test_one_maps_link_or_none_stays_one_message():
    one_place = (
        "Вот ссылка:\n\n"
        "Tom Yum Goong Nai Harn:\n"
        f"{TOM_YUM}\n\n"
        "Сказать, как доехать?"
    )
    none = "На Най Харне вечером тихо."

    one_message = place_messages(one_place)
    no_link = place_messages(none)

    assert [(message.text, message.is_place) for message in one_message] == [
        (one_place, True)
    ]
    assert [(message.text, message.is_place) for message in no_link] == [
        (none, False)
    ]


def test_a_partner_link_stays_with_its_place_when_another_place_follows():
    partner = "https://example.com/tom-yum"
    answer = (
        "Tom Yum Goong Nai Harn:\n"
        f"{partner}\n\n"
        f"{TOM_YUM}\n\n"
        "Smile Bar & Cafe:\n"
        f"{SMILE}"
    )

    messages = place_messages(answer)

    assert [message.text for message in messages] == [
        f"Tom Yum Goong Nai Harn:\n{partner}\n\n{TOM_YUM}",
        f"Smile Bar & Cafe:\n{SMILE}",
    ]
    assert [message.is_place for message in messages] == [True, True]

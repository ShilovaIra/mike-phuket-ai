from bot import parse_admin_ids


def test_parse_admin_ids_empty():
    assert parse_admin_ids(None) == frozenset()
    assert parse_admin_ids("") == frozenset()
    assert parse_admin_ids("  ,  ") == frozenset()


def test_parse_admin_ids_single():
    assert parse_admin_ids("417936797") == frozenset({"417936797"})


def test_parse_admin_ids_comma_separated():
    assert parse_admin_ids("111, 222") == frozenset({"111", "222"})

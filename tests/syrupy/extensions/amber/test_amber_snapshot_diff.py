def test_snapshot_diff(snapshot):
    my_dict = {
        "field_0": True,
        "field_1": "no_value",
        "nested": {
            "field_0": 1,
        },
    }
    assert my_dict == snapshot
    my_dict["field_1"] = "yes_value"
    assert my_dict == snapshot(diff=0)
    my_dict["nested"]["field_0"] = 2
    assert my_dict == snapshot(diff=0)


def test_snapshot_diff_id(snapshot):
    my_dict = {
        "field_0": True,
        "field_1": "no_value",
        "field_2": 0,
        "field_3": None,
        "field_4": 1,
        "field_5": False,
        "field_6": (True, "hey", 2, None),
        "field_7": {False, "no", 0, None},
    }
    my_dict["nested"] = dict(my_dict)
    assert my_dict == snapshot(index="large snapshot")
    my_dict["field_1"] = "yes_value"
    assert my_dict == snapshot(diff="large snapshot")
    my_dict["nested"]["field_0"] = 2
    assert my_dict == snapshot(index="case3", diff="large snapshot")

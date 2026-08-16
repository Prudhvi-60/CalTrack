from app.services.nutrition_db.normalizer import FoodNormalizer


def test_aliases_and_plurals() -> None:
    normalizer = FoodNormalizer(
        ["rice", "dal", "chapati", "egg", "yogurt", "chicken", "chickpea", "brown rice"]
    )
    assert normalizer.normalize("chapatis").canonical == "chapati"
    assert normalizer.normalize("rotis").canonical == "chapati"
    assert normalizer.normalize("lentils").canonical == "dal"
    assert normalizer.normalize("lentil curry").canonical == "dal"
    assert normalizer.normalize("eggs").canonical == "egg"
    assert normalizer.normalize("boiled eggs").canonical == "egg"
    assert normalizer.normalize("white rice").canonical == "rice"
    assert normalizer.normalize("basmati rice").canonical == "rice"


def test_does_not_fuzzy_match_unrelated_foods() -> None:
    normalizer = FoodNormalizer(["rice", "dal", "chicken", "chickpea"])
    result = normalizer.normalize("plastic fork")
    assert result.method == "unmatched"
    chicken = normalizer.normalize("chicken")
    assert chicken.canonical == "chicken"
    chickpea = normalizer.normalize("chickpea")
    assert chickpea.canonical == "chickpea"


def test_brown_rice_is_not_stripped_to_white_rice() -> None:
    normalizer = FoodNormalizer(["rice", "brown rice"])
    assert normalizer.normalize("brown rice").canonical == "brown rice"

from chat.services.language import detect_language


def test_english():
    assert detect_language("Where can I pay my tuition fees?") == "en"


def test_khmer():
    assert detect_language("តើខ្ញុំអាចបង់ថ្លៃសិក្សានៅឯណា?") == "km"


def test_mixed_mostly_khmer():
    assert detect_language("តើ exam ចាប់ផ្តើមនៅពេលណា?") == "km"


def test_mostly_english_with_one_khmer_word():
    assert detect_language("When is the final exam for year 4 students? អរគុណ") == "en"


def test_numbers_only_defaults_to_english():
    assert detect_language("2026 ?!") == "en"

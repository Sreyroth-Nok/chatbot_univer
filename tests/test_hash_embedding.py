import math

from knowledge.services.hash_embedding import DIM, hash_embed


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))  # vectors are already unit length


def test_dimension_and_unit_length():
    vec = hash_embed("library opening hours")
    assert len(vec) == DIM
    assert math.isclose(math.sqrt(sum(v * v for v in vec)), 1.0, rel_tol=1e-9)


def test_similar_questions_are_closer_than_unrelated():
    faq = hash_embed("Q: What are the library opening hours? A: Monday to Saturday")
    similar = hash_embed("library opening hours")
    unrelated = hash_embed("how do I pay tuition by bank transfer")
    assert cosine(faq, similar) > cosine(faq, unrelated)


def test_khmer_text_matches_itself_best():
    faq = hash_embed("តើបណ្ណាល័យបើកម៉ោងប៉ុន្មាន")
    same_topic = hash_embed("បណ្ណាល័យបើកម៉ោង")
    other = hash_embed("ថ្លៃសិក្សា")
    assert cosine(faq, same_topic) > cosine(faq, other)


def test_empty_text_is_still_a_valid_vector():
    vec = hash_embed("")
    assert len(vec) == DIM and math.isclose(sum(v * v for v in vec), 1.0)

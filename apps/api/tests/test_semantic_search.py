import numpy as np

from app.search.semantic.semantic_search import SemanticSearch


def _make_search(embedding_fn) -> SemanticSearch:
    # Bypass __init__ (which builds a real DatabaseService/VectorDatabase and loads
    # the multi-GB SigLIP model) -- calculate_slerp_embedding only needs a callable
    # embedding_function, so we stub that in directly.
    search = SemanticSearch.__new__(SemanticSearch)
    search.embedding_function = embedding_fn
    return search


def test_slerp_identical_vectors_no_divide_by_zero():
    vec = np.array([1.0, 0.0, 0.0])
    search = _make_search(lambda inputs: [vec, vec])

    result = search.calculate_slerp_embedding("text", np.zeros((3, 3)), alpha=0.8)

    assert result.shape == (1, 3)
    assert not np.isnan(result).any()
    np.testing.assert_allclose(result[0], vec)


def test_slerp_orthogonal_vectors():
    text_vec = np.array([1.0, 0.0])
    image_vec = np.array([0.0, 1.0])
    search = _make_search(lambda inputs: [text_vec, image_vec])

    result = search.calculate_slerp_embedding("text", np.zeros((2, 2)), alpha=0.5)

    assert result.shape == (1, 2)
    assert not np.isnan(result).any()
    expected = np.array([1.0, 1.0]) / np.sqrt(2)
    np.testing.assert_allclose(result[0], expected, atol=1e-8)
    np.testing.assert_allclose(np.linalg.norm(result[0]), 1.0, atol=1e-8)


def test_slerp_generic_pair_returns_unit_2d_vector():
    text_vec = np.array([1.0, 0.2, 0.3])
    image_vec = np.array([0.4, 1.0, -0.2])
    search = _make_search(lambda inputs: [text_vec, image_vec])

    result = search.calculate_slerp_embedding("text", np.zeros((3, 3)), alpha=0.3)

    assert result.shape == (1, 3)
    assert not np.isnan(result).any()
    np.testing.assert_allclose(np.linalg.norm(result[0]), 1.0, atol=1e-8)


def test_slerp_honours_alpha_parameter():
    text_vec = np.array([1.0, 0.0])
    image_vec = np.array([0.0, 1.0])
    search = _make_search(lambda inputs: [text_vec, image_vec])

    near_text = search.calculate_slerp_embedding("t", np.zeros((2, 2)), alpha=0.99)
    near_image = search.calculate_slerp_embedding("t", np.zeros((2, 2)), alpha=0.01)

    assert near_text[0][0] > near_image[0][0]

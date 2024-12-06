import pandas as pd
from src.ml.utils import target_transform


def test_target_transform():
    """ Testa a função target_transform. """

    train = pd.DataFrame({"target": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
    target = "target"
    horizon = 3

    expected_output = pd.DataFrame({
        'target_t1': [2, 3, 4, 5, 6, 7, 8],
        'target_t2': [3, 4, 5, 6, 7, 8, 9],
        'target_t3': [4, 5, 6, 7, 8, 9, 10]
    })

    result = target_transform(train, target, horizon)
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_output)  # noqa

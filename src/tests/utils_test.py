import pandas as pd
from src.ml.utils import target_transform


def test_target_transform():
    """ Testa a função target_transform. """

    train = pd.DataFrame({"target": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]})
    target = "target"
    horizon = 3

    expected_output = pd.DataFrame({
        'target_t1': [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        'target_t2': [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
        'target_t3': [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],

    })

    result = target_transform(train, target, horizon)
    print(result)
    print("expected_output")
    print(expected_output)
    pd.testing.assert_frame_equal(result, expected_output)  # noqa

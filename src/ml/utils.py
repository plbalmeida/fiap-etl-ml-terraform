import pandas as pd


def target_transform(train, target, horizon):
    """
    Transforma a coluna alvo para prever múltiplos passos à frente.

    Concatena colunas deslocadas da coluna alvo para criar um DataFrame que
    contém os valores da coluna alvo para múltiplos passos à frente, até o horizonte
    especificado.

    Args:
        train (pd.DataFrame): O DataFrame de treino contendo a(s) coluna(s) de dados.
        target (str): O nome da coluna alvo que se deseja transformar.
        horizon (int): O número de passos à frente que se deseja prever.

    Returns:
        pd.DataFrame: Um DataFrame contendo as colunas da coluna alvo deslocadas
        para prever múltiplos passos à frente. As colunas são nomeadas no formato 
        `target_t{i+1}`, onde `i` é o número do passo.

    Example:
        >>> train = pd.DataFrame({'target': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
        >>> target_transform(train, 'target', 3)
           target_t1  target_t2  target_t3
        0        2.0        3.0        4.0
        1        3.0        4.0        5.0
        2        4.0        5.0        6.0
        3        5.0        6.0        7.0
        4        6.0        7.0        8.0
        5        7.0        8.0        9.0
        6        8.0        9.0       10.0
    """  # noqa 401
    y = pd.concat([train[target].shift(-i) for i in range(0, horizon)], axis=1).dropna()  # noqa 401
    y.columns = [f"{target}_t{i+1}" for i in range(0, horizon)]
    return y

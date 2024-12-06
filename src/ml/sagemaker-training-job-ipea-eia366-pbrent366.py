import os
import sys
from datetime import datetime

import boto3
import awswrangler as wr
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.experimental import enable_halving_search_cv  # noqa
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from sklearn.model_selection import HalvingGridSearchCV, TimeSeriesSplit
from sklearn.multioutput import RegressorChain
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from utils import target_transform


def train():
    # configurações do s3
    s3 = boto3.client("s3")
    bucket_name = "s3-bucket-ipea-eia366-pbrent366"

    # formato do dataproc no padrão esperado (yyyymmdd)
    timestamp = datetime.now().strftime("%Y%m%d")
    dataproc = f"dataproc={timestamp}"

    # caminho do s3 onde os dados de entrada estão armazenados
    s3_path = os.environ.get("S3_PATH", f"s3://{bucket_name}/final/{dataproc}/")  # noqa
    df = wr.s3.read_parquet(path=s3_path)
    df = df.sort_values(by=["ano", "mes"], ascending=[True, True])

    # divisão dos dados de treino e teste
    train_size = int(len(df) * 0.70)
    train, test = df.iloc[:train_size], df.iloc[train_size:]

    X_train = train.drop(columns="preco_medio_usd").copy()
    y_train = target_transform(train, "preco_medio_usd", 6)
    X_train = X_train.iloc[:len(y_train)]

    X_test = test.drop(columns="preco_medio_usd").copy()
    y_test = target_transform(test, "preco_medio_usd", 6)
    X_test = X_test.iloc[:len(y_test)]

    # pipeline
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RegressorChain(base_estimator=GradientBoostingRegressor(random_state=42), random_state=42))  # noqa
    ])

    # hiperparâmetros
    param_grid = {
        "model__base_estimator__n_estimators": [100, 200, 300],
        "model__base_estimator__max_depth": [3, 5, 8]
    }

    # busca em grade com HalvingGridSearchCV
    halving_grid_search = HalvingGridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        factor=3,
        cv=TimeSeriesSplit(n_splits=6),
        scoring="neg_root_mean_squared_error",
        random_state=42,
        n_jobs=-1,
        verbose=1
    )

    halving_grid_search.fit(X_train, y_train)
    y_pred = halving_grid_search.predict(X_test)

    # avaliação de performance
    mae = mean_absolute_error(y_test, y_pred, multioutput="raw_values")
    mape = mean_absolute_percentage_error(y_test, y_pred, multioutput="raw_values")  # noqa

    models_performance = pd.DataFrame({
        "Previsão": [f"M+{i}" for i in range(1, 6+1)],
        "Mean Absolute Error": mae,
        "Mean Absolute Percentage Error": mape
    })

    # previsões
    X_pred = df.drop(columns="preco_medio_usd")[-6:]
    predictions = halving_grid_search.predict(X_pred)

    # extraindo somente as previsões principais (diagonal da matriz)
    final_predictions = [predictions[i, i] for i in range(predictions.shape[0])]  # noqa

    preds_df = pd.DataFrame({
        "Horizonte": [f"M+{i+1}" for i in range(len(final_predictions))],
        "Previsao": final_predictions
    })

    preds_df["Mean Absolute Error"] = models_performance["Mean Absolute Error"]
    preds_df["Mean Absolute Percentage Error"] = models_performance["Mean Absolute Percentage Error"]  # noqa

    # upload do das previsões para o s3
    predictions_path = "/tmp/predictions.csv"
    preds_df.to_csv(predictions_path)
    s3.upload_file(predictions_path, bucket_name, f"predictions/{dataproc}/predictions.csv")  # noqa


if __name__ == '__main__':
    train()
    sys.exit(0)

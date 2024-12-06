import sys
import logging
import boto3
import time
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql.functions import (
    avg, 
    col, 
    concat,
    current_date,
    date_format,
    lag,
    lpad,
    max,
    min,
    quarter,
    stddev,
    to_date
)
from pyspark.sql.window import Window


# configura o Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# parâmetros de execução do Glue (se houver)
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

# configura o SparkContext e o GlueContext
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# inicializando o job Glue
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# lendo os dados da tabela do Glue Catalog com a partição mais recente
database_name = "workspace_db"
table_name = "tb_pet_bru_raw"

dyf = glueContext.create_dynamic_frame.from_catalog(database=database_name, table_name=table_name)
df = dyf.toDF()

most_recent_partition = df.agg({"dataproc": "max"}).collect()[0][0]
df = df.filter(col("dataproc") == most_recent_partition)

# log do schema do DataFrame
logger.info("Schema do DataFrame após leitura da tabela:")
df.printSchema()

# obtendo o ano e mês corrente
current_year = date_format(current_date(), "yyyy").cast("int")
current_month = date_format(current_date(), "MM").cast("int")

# filtro para remover os dados do mês corrente
df = df.filter(~((col("year") == current_year) & (col("month") == current_month)))

# remove registros com valores ausentes em "value_usd"
df = df.na.drop(subset=["value_usd"])

# média mensal de preço do petróleo bruto
df = df.groupBy("year", "month").agg(avg("value_usd").alias("preco_medio_usd"))

# cria a coluna "anomes" utilizando os campos "year" e "month"
df = df.withColumn("anomes", to_date(concat(col("year").cast("string"), lpad(col("month").cast("string"), 2, "0")), "yyyyMM"))

# ordena o DataFrame por data
window_spec = Window.orderBy("anomes")

# cria lags de 1 a 6 meses
df = df.withColumn("lag_1_mes_preco_medio_usd", lag("preco_medio_usd", 1).over(window_spec)) \
       .withColumn("lag_2_meses_preco_medio_usd", lag("preco_medio_usd", 2).over(window_spec)) \
       .withColumn("lag_3_meses_preco_medio_usd", lag("preco_medio_usd", 3).over(window_spec)) \
       .withColumn("lag_4_meses_preco_medio_usd", lag("preco_medio_usd", 4).over(window_spec)) \
       .withColumn("lag_5_meses_preco_medio_usd", lag("preco_medio_usd", 5).over(window_spec)) \
       .withColumn("lag_6_meses_preco_medio_usd", lag("preco_medio_usd", 6).over(window_spec))

# média móvel de 6 meses
df = df.withColumn("media_movel_6_meses_preco_medio_usd", avg(col("preco_medio_usd")).over(window_spec.rowsBetween(-6, -1)))

# desvio padrão móvel de 6 meses
df = df.withColumn("desvio_padrao_movel_6_meses_preco_medio_usd", stddev(col("preco_medio_usd")).over(window_spec.rowsBetween(-6, -1)))

# valor mínimo e máximo dos últimos 6 meses
df = df.withColumn("valor_minimo_6_meses_preco_medio_usd", min(col("preco_medio_usd")).over(window_spec.rowsBetween(-6, -1))) \
       .withColumn("valor_maximo_6_meses_preco_medio_usd", max(col("preco_medio_usd")).over(window_spec.rowsBetween(-6, -1)))

# componentes sazonais: ano, mês e trimestre
df = df.withColumn("trimestre", quarter("anomes"))
df = df.withColumnRenamed("year", "ano")
df = df.withColumnRenamed("month", "mes")

# cria a coluna de partição "dataproc" no formato "yyyyMMdd"
df = df.withColumn("dataproc", date_format(current_date(), "yyyyMMdd").cast("int"))

# remove o campo "anomes"
df = df.drop("anomes")

# remove linhas com valores NaN que foram criados ao fazer o shift ou nas agregações
df = df.dropna()

# log de count e número de registros no DataFrame transformado
transformed_record_count = df.count()
logger.info(f"Número de registros no DataFrame transformado: {transformed_record_count}")

# diretório S3 para salvar os dados transformados
transformed_data_path = "s3://s3-bucket-ipea-eia366-pbrent366/interim/"

# salva os dados transformados em formato parquet no S3, particionando por data de processamento
df.write.mode("overwrite").partitionBy("dataproc").parquet(transformed_data_path)

# cliente do boto3 para Glue
glue_client = boto3.client("glue")

# define a tabela para os dados transformados
table_name = "tb_pet_bru_interim"
transformed_table_location = transformed_data_path

# definição da tabela transformada com partição
transformed_table_input = {
    'Name': table_name,
    'StorageDescriptor': {
        'Columns': [
            {"Name": "ano", "Type": "bigint"},
            {"Name": "mes", "Type": "bigint"},
            {"Name": "preco_medio_usd", "Type": "double"},
            {"Name": "lag_1_mes_preco_medio_usd", "Type": "double"},
            {"Name": "lag_2_meses_preco_medio_usd", "Type": "double"},
            {"Name": "lag_3_meses_preco_medio_usd", "Type": "double"},
            {"Name": "lag_4_meses_preco_medio_usd", "Type": "double"},
            {"Name": "lag_5_meses_preco_medio_usd", "Type": "double"},
            {"Name": "lag_6_meses_preco_medio_usd", "Type": "double"},
            {"Name": "media_movel_6_meses_preco_medio_usd", "Type": "double"},
            {"Name": "desvio_padrao_movel_6_meses_preco_medio_usd", "Type": "double"},
            {"Name": "valor_minimo_6_meses_preco_medio_usd", "Type": "double"},
            {"Name": "valor_maximo_6_meses_preco_medio_usd", "Type": "double"},
            {"Name": "trimestre", "Type": "int"}
        ],
        'Location': transformed_table_location,
        'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
        'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
        'Compressed': False,
        'SerdeInfo': {
            'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe',
            'Parameters': {'serialization.format': '1'}
        }
    },
    'PartitionKeys': [{"Name": "dataproc", "Type": "int"}],  # Particionando por dataproc
    'TableType': 'EXTERNAL_TABLE'
}

# cria ou atualiza a tabela transformada no Glue Catalog
try:
    glue_client.get_table(DatabaseName=database_name, Name=table_name)
    logger.info(f"Tabela '{table_name}' já existe no Glue Catalog. Atualizando tabela...")
    glue_client.update_table(DatabaseName=database_name, TableInput=transformed_table_input)
    logger.info(f"Tabela '{table_name}' atualizada no Glue Catalog.")
except glue_client.exceptions.EntityNotFoundException:
    glue_client.create_table(DatabaseName=database_name, TableInput=transformed_table_input)
    logger.info(f"Tabela '{table_name}' criada no Glue Catalog.")

logger.info(f"Tabela '{table_name}' disponível no Athena.")

# executa MSCK REPAIR TABLE para descobrir partições
repair_table_query = f"MSCK REPAIR TABLE {database_name}.{table_name}"
logger.info(f"Executando comando: {repair_table_query}")
spark.sql(repair_table_query)
logger.info(f"Comando MSCK REPAIR TABLE executado com sucesso para a tabela '{table_name}'.")

# finaliza o job Glue
job.commit()

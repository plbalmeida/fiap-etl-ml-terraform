import sys
import logging
import boto3
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql.functions import col, current_date, date_format
from pyspark.sql.types import DecimalType, IntegerType


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

# lendo os dados da tabela transformada do Glue Catalog
database_name = "workspace_db"
transformed_table_name = "tb_pet_bru_interim"

dyf = glueContext.create_dynamic_frame.from_catalog(database=database_name, table_name=transformed_table_name)
df = dyf.toDF()

most_recent_partition = df.agg({"dataproc": "max"}).collect()[0][0]
df = df.filter(col("dataproc") == most_recent_partition)

# log do schema do DataFrame após leitura da partição mais recente
logger.info("Schema do DataFrame após leitura da partição mais recente:")
df.printSchema()

# log de count e número de registros no DataFrame após filtrar a partição mais recente
logger.info(f"Número de registros após filtrar a partição mais recente: {df.count()}")

# forçando os tipos de dados
df = df.select(
    col("ano").cast(IntegerType()),
    col("mes").cast(IntegerType()),
    col("preco_medio_usd").cast(DecimalType(5, 2)),
    col("lag_1_mes_preco_medio_usd").cast(DecimalType(5, 2)),
    col("lag_2_meses_preco_medio_usd").cast(DecimalType(5, 2)),
    col("lag_3_meses_preco_medio_usd").cast(DecimalType(5, 2)),
    col("lag_4_meses_preco_medio_usd").cast(DecimalType(5, 2)),
    col("lag_5_meses_preco_medio_usd").cast(DecimalType(5, 2)),
    col("lag_6_meses_preco_medio_usd").cast(DecimalType(5, 2)),
    col("media_movel_6_meses_preco_medio_usd").cast(DecimalType(5, 2)),
    col("desvio_padrao_movel_6_meses_preco_medio_usd").cast(DecimalType(5, 2)),
    col("valor_minimo_6_meses_preco_medio_usd").cast(DecimalType(5, 2)),
    col("valor_maximo_6_meses_preco_medio_usd").cast(DecimalType(5, 2)),
    col("trimestre").cast(IntegerType()),
    col("dataproc").cast(IntegerType())
)

# log do schema do DataFrame após a conversão de tipos
logger.info("Schema do DataFrame após a conversão de tipos:")
df.printSchema()

# cria a coluna "dataproc" no formato "yyyyMMdd" para particionamento
df = df.withColumn("dataproc", date_format(current_date(), "yyyyMMdd").cast("int"))

# log de count e número de registros no DataFrame final
final_record_count = df.count()
logger.info(f"Número de registros no DataFrame final: {final_record_count}")

# diretório S3 para salvar os dados finais prontos para consumo
final_data_path = "s3://s3-bucket-ipea-eia366-pbrent366/final/"

# salva os dados finais em formato parquet no S3, particionando por data de processamento
df.write.mode("overwrite").partitionBy("dataproc").parquet(final_data_path)

# cliente do boto3 para Glue
glue_client = boto3.client("glue")

# define o nome do database e tabela para os dados finais
table_name = "tb_pet_bru_final"
final_table_location = final_data_path

# definição da tabela final com partição
final_table_input = {
    'Name': table_name,
    'StorageDescriptor': {
        'Columns': [
            {"Name": "ano", "Type": "int"},
            {"Name": "mes", "Type": "int"},
            {"Name": "preco_medio_usd", "Type": "decimal(5,2)"},
            {"Name": "lag_1_mes_preco_medio_usd", "Type": "decimal(5,2)"},
            {"Name": "lag_2_meses_preco_medio_usd", "Type": "decimal(5,2)"},
            {"Name": "lag_3_meses_preco_medio_usd", "Type": "decimal(5,2)"},
            {"Name": "lag_4_meses_preco_medio_usd", "Type": "decimal(5,2)"},
            {"Name": "lag_5_meses_preco_medio_usd", "Type": "decimal(5,2)"},
            {"Name": "lag_6_meses_preco_medio_usd", "Type": "decimal(5,2)"},
            {"Name": "media_movel_6_meses_preco_medio_usd", "Type": "decimal(5,2)"},
            {"Name": "desvio_padrao_movel_6_meses_preco_medio_usd", "Type": "decimal(5,2)"},
            {"Name": "valor_minimo_6_meses_preco_medio_usd", "Type": "decimal(5,2)"},
            {"Name": "valor_maximo_6_meses_preco_medio_usd", "Type": "decimal(5,2)"},
            {"Name": "trimestre", "Type": "int"}
        ],
        'Location': final_table_location,
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

# cria ou atualiza a tabela final no Glue Catalog
try:
    glue_client.get_table(DatabaseName=database_name, Name=table_name)
    logger.info(f"Tabela '{table_name}' já existe no Glue Catalog. Atualizando tabela...")
    glue_client.update_table(DatabaseName=database_name, TableInput=final_table_input)
    logger.info(f"Tabela '{table_name}' atualizada no Glue Catalog.")
except glue_client.exceptions.EntityNotFoundException:
    glue_client.create_table(DatabaseName=database_name, TableInput=final_table_input)
    logger.info(f"Tabela '{table_name}' criada no Glue Catalog.")

logger.info(f"Tabela '{table_name}' disponível no Athena.")

# executa MSCK REPAIR TABLE para descobrir partições
repair_table_query = f"MSCK REPAIR TABLE {database_name}.{table_name}"
logger.info(f"Executando comando: {repair_table_query}")
spark.sql(repair_table_query)
logger.info(f"Comando MSCK REPAIR TABLE executado com sucesso para a tabela '{table_name}'.")

# finaliza o job Glue
job.commit()

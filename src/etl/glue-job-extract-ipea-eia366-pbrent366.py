import sys
import logging
import boto3
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from awsglue.job import Job
from pyspark.context import SparkContext
import ipeadatapy as ip
from pyspark.sql.functions import current_date, date_format


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

# obtenção da série temporal do preço do petróleo bruto
cod = "EIA366_PBRENT366"
eia366 = ip.timeseries(cod)

# converte de pandas DataFrame para DataFrame do PySpark
df = spark.createDataFrame(eia366)

# renomeia as colunas para corresponder aos nomes esperados
df = df.withColumnRenamed("CODE", "code") \
       .withColumnRenamed("RAW DATE", "raw_date") \
       .withColumnRenamed("DAY", "day") \
       .withColumnRenamed("MONTH", "month") \
       .withColumnRenamed("YEAR", "year") \
       .withColumnRenamed("VALUE (US$)", "value_usd")

# coluna de data de processamento no formato "yyyyMMdd"
df = df.withColumn("dataproc", date_format(current_date(), "yyyyMMdd").cast("int"))

# log do schema do DataFrame
logger.info("Schema do DataFrame:")
df.printSchema()

# log de count e log do número de registros no DataFrame
record_count = df.count()
logger.info(f"Número de registros no DataFrame: {record_count}")

# diretório S3 para salvar os dados brutos particionados
raw_data_path = "s3://s3-bucket-ipea-eia366-pbrent366/raw/"

# salva os dados brutos em formato parquet no S3, particionando por data de processamento
df.write.mode("overwrite").partitionBy("dataproc").parquet(raw_data_path)

# cliente do boto3 para Glue
glue_client = boto3.client("glue")

database_name = "workspace_db"
table_name = "tb_pet_bru_raw"
table_location = raw_data_path

# verifica se o banco de dados existe e crie se necessário
try:
    glue_client.get_database(Name=database_name)
except glue_client.exceptions.EntityNotFoundException:
    glue_client.create_database(
        DatabaseInput={'Name': database_name}
    )
    logger.info(f"Banco de dados '{database_name}' criado no Glue Catalog.")

# definição da tabela
table_input = {
    'Name': table_name,
    'StorageDescriptor': {
        'Columns': [
            {"Name": "code", "Type": "string"},
            {"Name": "raw_date", "Type": "string"},
            {"Name": "day", "Type": "bigint"},
            {"Name": "month", "Type": "bigint"},
            {"Name": "year", "Type": "bigint"},
            {"Name": "value_usd", "Type": "double"}
        ],
        'Location': table_location,
        'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
        'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
        'Compressed': False,
        'SerdeInfo': {
            'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe',
            'Parameters': {'serialization.format': '1'}
        }
    },
    'PartitionKeys': [{"Name": "dataproc", "Type": "int"}],
    'TableType': 'EXTERNAL_TABLE'
}

# cria ou atualiza a tabela no Glue Catalog
try:
    glue_client.get_table(DatabaseName=database_name, Name=table_name)
    logger.info(f"Tabela '{table_name}' já existe no Glue Catalog. Atualizando tabela...")
    glue_client.update_table(DatabaseName=database_name, TableInput=table_input)
    logger.info(f"Tabela '{table_name}' atualizada no Glue Catalog.")
except glue_client.exceptions.EntityNotFoundException:
    glue_client.create_table(DatabaseName=database_name, TableInput=table_input)
    logger.info(f"Tabela '{table_name}' criada no Glue Catalog.")

logger.info(f"Tabela '{table_name}' disponível no Athena.")

# executa MSCK REPAIR TABLE para descobrir partições
repair_table_query = f"MSCK REPAIR TABLE {database_name}.{table_name}"
logger.info(f"Executando comando: {repair_table_query}")
spark.sql(repair_table_query)
logger.info(f"Comando MSCK REPAIR TABLE executado com sucesso para a tabela '{table_name}'.")

# finaliza o job Glue
job.commit()

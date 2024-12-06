# imagem base do Python
FROM python:3.9-slim

# diretório de trabalho no container
WORKDIR /app

# copia o arquivo de requisitos para o diretório de trabalho
COPY requirements.txt .

# instala as dependências da aplicação
RUN pip install --no-cache-dir -r requirements.txt

# copia os scripts para o container
COPY src/ml/ .

# define o script principal como entrypoint
ENTRYPOINT ["python", "sagemaker-training-job-ipea-eia366-pbrent366.py"]
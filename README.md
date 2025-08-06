# django_kafka
Python Vert Kafka utils lib

## 📦 Gerenciamento de Dependências com pip-tools

Este projeto utiliza `pip-tools` para gerenciar dependências de forma mais controlada e reproduzível.

### Instalação do pip-tools
```bash
pip install pip-tools
```

### Como usar

#### ✅ Adicionar uma nova biblioteca
1. Adicione a biblioteca no arquivo `requirements.in` (sem versão específica):
```bash
# Para bibliotecas do PyPI
echo "nova-biblioteca" >> requirements.in

# Para repositórios Git
echo "package_name @ git+https://github.com/user/repo.git@branch" >> requirements.in
```

2. Compile o requirements.txt:
```bash
pip-compile requirements.in
```

#### 🔄 Instalar/Atualizar pacotes no ambiente virtual
```bash
# Instalar todas as dependências
pip-sync requirements.txt

# Ou se preferir pip install tradicional
pip install -r requirements.txt
```

#### ⬆️ Atualizar dependências
```bash
# Atualizar todas as bibliotecas para versões mais recentes
pip-compile --upgrade requirements.in

# Atualizar apenas uma biblioteca específica
pip-compile --upgrade-package django requirements.in

# Instalar as atualizações
pip-sync requirements.txt
```

#### 📋 Comandos úteis
```bash
# Verificar dependências desatualizadas
pip list --outdated

# Gerar requirements.txt sem alterar versões
pip-compile requirements.in

# Sincronizar ambiente (remove pacotes não listados)
pip-sync requirements.txt
```
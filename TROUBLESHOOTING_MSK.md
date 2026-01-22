# Guia de Troubleshooting para Erros Intermitentes no AWS MSK

## O Problema

O erro intermitente que você está enfrentando:
```
REQTMOUT|...: Timed out ApiVersionRequest in flight (after 10010ms, timeout #0)
```

É comum em clusters AWS MSK e indica problemas de conectividade/timeout.

## Principais Causas Identificadas

### 1. **Configurações de Timeout Inadequadas**
- O timeout padrão de 10 segundos é muito baixo para AWS
- Latência variável entre aplicação e MSK
- Problemas de rede intermitentes

### 2. **Falta de Configurações de Retry**
- Sem retry automático para falhas temporárias
- Sem backoff strategy para reconexões

### 3. **Overhead de Criação de Conexão**
- Criar novo Producer a cada mensagem é ineficiente
- Não reutiliza conexões estabelecidas

## Soluções Implementadas

### 1. **Producer Robusto (função original melhorada)**
```python
from django_kafka.producer import producer

# Uso normal com configurações robustas
producer("vertc-teams-notifications", "{}")
```

### 2. **Producer Persistente (recomendado para alta frequência)**
```python
from django_kafka.producer import producer_persistent, flush_producer

# Para múltiplas mensagens
producer_persistent("vertc-teams-notifications", "{}")
producer_persistent("vertc-teams-notifications", "{}")

# Força envio de todas as mensagens
flush_producer()
```

## Verificações Recomendadas no Cluster MSK

### 1. **Configurações de Rede**
```bash
# Teste conectividade básica
telnet b-1.mskverthmldedicated.h1agaf.c19.kafka.us-east-1.amazonaws.com 9092

# Verifique DNS resolution
nslookup b-1.mskverthmldedicated.h1agaf.c19.kafka.us-east-1.amazonaws.com
```

### 2. **Security Groups**
- Porta 9092 (plaintext) ou 9094/9096 (SSL) liberada
- Regras de entrada e saída configuradas
- Source/destination corretos

### 3. **Configurações do Cluster**
No AWS Console, verifique:
- **Client Information**: Versão dos clientes suportada
- **Security Settings**: Tipo de autenticação
- **Monitoring**: Métricas de conectividade e erros

### 4. **Limites e Throttling**
- `ClientConnectionCount` (máximo de conexões)
- `RequestTime` (latência das requisições)
- `ThrottledTime` (tempo de throttling)

## Monitoramento Recomendado

### Adicione logs detalhados:
```python
import logging
logging.basicConfig(level=logging.INFO)

# Para debug mais detalhado do Kafka
kafka_logger = logging.getLogger('confluent_kafka')
kafka_logger.setLevel(logging.DEBUG)
```

### Métricas CloudWatch para monitorar:
- `ActiveControllerCount`
- `ClientConnectionCount`
- `RequestHandlerAvgIdlePercent`
- `NetworkRxErrors`
- `NetworkTxErrors`

## Configurações de Settings.py para MSK

```python
# settings.py
KAFKA_BOOTSTRAP_SERVER = "b-1.mskverthmldedicated.h1agaf.c19.kafka.us-east-1.amazonaws.com:9092"
KAFKA_CLIENT_ID = "verctops-hml-front"

# Se usar autenticação (descomente conforme necessário)
# KAFKA_SECURITY_PROTOCOL = "SASL_SSL"
# KAFKA_SASL_MECHANISM = "AWS_MSK_IAM"
```

## Próximos Passos

1. **Teste com as novas configurações** - O producer agora tem timeouts maiores e retry automático
2. **Use producer_persistent** para aplicações com muitas mensagens
3. **Monitore métricas** do MSK no CloudWatch
4. **Verifique conectividade** de rede periodicamente
5. **Considere múltiplos bootstrap servers** para redundância

## Se o Problema Persistir

1. **Verifique configuração de rede** da sua aplicação
2. **Teste em horários diferentes** para identificar padrões
3. **Considere usar outro broker** do cluster como teste
4. **Abra ticket com AWS Support** se necessário

# Docker Deployment Guide

Руководство по развертыванию Telegram LLM Bot в Docker контейнере.

## Требования

- Docker 20.0+
- Docker Compose 2.0+
- 512MB RAM минимум
- Интернет соединение для API запросов

## Быстрый старт

1. **Подготовка конфигурации:**
   ```bash
   cp env.production.template .env.production
   # Отредактируйте .env.production с вашими реальными токенами
   ```

2. **Запуск бота:**
   ```bash
   ./scripts/docker-start.sh
   ```

3. **Просмотр логов:**
   ```bash
   ./scripts/docker-logs.sh
   ```

4. **Остановка бота:**
   ```bash
   ./scripts/docker-stop.sh
   ```

## Управляющие скрипты

### `./scripts/docker-start.sh`
- Собирает Docker образ
- Создает и запускает контейнер
- Проверяет статус запуска

### `./scripts/docker-stop.sh`
- Останавливает и удаляет контейнер
- Показывает статус операции

### `./scripts/docker-logs.sh`
- Показывает логи контейнера
- Поддерживает несколько режимов просмотра

### `./scripts/docker-rebuild.sh`
- Пересобирает образ с нуля
- Полезно после изменений в коде

## Конфигурация

### Обязательные переменные окружения

```bash
# В файле .env.production
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
OPENROUTER_API_KEY=your_openrouter_api_key
```

### Опциональные переменные

```bash
LLM_MODEL=anthropic/claude-3-haiku-20240307
LLM_TEMPERATURE=0.7
LOG_LEVEL=INFO
DEBUG=false
```

## Мониторинг

### Проверка статуса
```bash
docker-compose ps
```

### Просмотр ресурсов
```bash
docker stats telegram-llm-bot
```

### Health check
```bash
docker-compose exec telegram-llm-bot python -c "import sys; sys.exit(0)"
```

## Troubleshooting

### Контейнер не запускается
1. Проверьте логи: `./scripts/docker-logs.sh`
2. Убедитесь что .env.production настроен правильно
3. Проверьте что токены действительны

### Ошибки API
- Проверьте TELEGRAM_BOT_TOKEN
- Проверьте OPENROUTER_API_KEY
- Убедитесь в наличии интернета

### Высокое потребление ресурсов
- Проверьте настройки LLM модели
- Рассмотрите использование более легкой модели
- Настройте лимиты в docker-compose.yml

## Backup и восстановление

### Backup логов
```bash
docker cp telegram-llm-bot:/app/logs ./backup-logs-$(date +%Y%m%d)
```

### Экспорт контейнера
```bash
docker commit telegram-llm-bot telegram-llm-bot:backup-$(date +%Y%m%d)
```

## Обновление

1. Остановите бот: `./scripts/docker-stop.sh`
2. Обновите код из Git
3. Пересоберите: `./scripts/docker-rebuild.sh`

## Безопасность

- Контейнер запускается от непривилегированного пользователя
- Чувствительные данные хранятся в .env.production (не в Git)
- Ограничения ресурсов предотвращают DoS
- Health checks обеспечивают контроль работоспособности

## Production checklist

- [ ] .env.production настроен с реальными токенами
- [ ] Docker daemon запущен
- [ ] Достаточно дискового пространства (1GB+)
- [ ] Настроен мониторинг логов
- [ ] Настроено автоматическое перезапуск (restart: unless-stopped)
- [ ] Проверена работа health check

# Развертывание Telegram LLM Bot на Render.com

## Обзор

Это пошаговое руководство по развертыванию Telegram LLM Bot на облачной платформе Render.com. Render предоставляет бесплатный план с 750 часами в месяц, что позволяет работать боту 24/7.

## Подготовка к развертыванию

### Шаг 1: Убедитесь в готовности проекта

Проверьте, что у вас есть:
- ✅ Dockerfile в корне проекта
- ✅ docker-compose.yml (для локального тестирования)
- ✅ env.production.template
- ✅ Исходный код в GitHub репозитории

### Шаг 2: Оптимизация Dockerfile для облачного развертывания

Наш существующий Dockerfile уже оптимизирован для production, но убедимся в правильности настроек:

```dockerfile
# Проверьте, что используется правильный порт
ENV PORT=8000
EXPOSE 8000

# Убедитесь, что логи идут в stdout для Render
ENV PYTHONUNBUFFERED=1
```

## Регистрация и настройка Render.com

### Шаг 1: Создание аккаунта

1. Перейдите на [render.com](https://render.com)
2. Нажмите **"Get Started for Free"**
3. Выберите **"Sign up with GitHub"** для простой интеграции
4. Авторизуйте Render для доступа к вашим репозиториям

### Шаг 2: Подключение репозитория

1. На главной странице Render нажмите **"New +"**
2. Выберите **"Web Service"**
3. Подключите ваш GitHub репозиторий с ботом
4. Если репозиторий приватный, предоставьте доступ

## Конфигурация Web Service

### Шаг 3: Основные настройки

**Build Settings:**
- **Repository:** Ваш GitHub репозиторий
- **Branch:** `main` (или ваша основная ветка)
- **Root Directory:** оставьте пустым
- **Environment:** `Docker`
- **Build Command:** *(автоматически определяется из Dockerfile)*
- **Start Command:** *(автоматически определяется из Dockerfile)*

**Service Details:**
- **Name:** `telegram-llm-bot` (или любое уникальное имя)
- **Region:** выберите ближайший к вам регион
- **Branch:** `main`
- **Auto-Deploy:** `Yes` ✅

### Шаг 4: Настройка Environment Variables

В разделе **"Environment Variables"** добавьте:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
LLM_MODEL=anthropic/claude-3-haiku-20240307
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
LOG_LEVEL=INFO
DEBUG=false
PYTHONUNBUFFERED=1
PORT=8000
```

**⚠️ Важно:** Используйте реальные токены вместо placeholder значений!

### Шаг 5: Выбор плана

- Выберите **"Free Plan"**
- Лимиты: 512MB RAM, Shared CPU, 750 часов/месяц
- Нажмите **"Create Web Service"**

## Процесс развертывания

### Шаг 6: Мониторинг деплоя

1. После создания сервиса начнется автоматическая сборка
2. Отслеживайте процесс в разделе **"Logs"**
3. Первая сборка может занять 5-10 минут

**Ожидаемые этапы:**
```
==> Cloning from https://github.com/your-username/telegram-llm-bot...
==> Building Docker image...
==> Installing dependencies...
==> Starting application...
==> Service is live 🎉
```

### Шаг 7: Проверка успешного запуска

В логах должны появиться сообщения:
```
telegram-llm-bot | 2024-XX-XX XX:XX:XX - root - INFO - Logging configured successfully
telegram-llm-bot | 2024-XX-XX XX:XX:XX - src.bot.bot - INFO - Bot started: @YourBot
telegram-llm-bot | 2024-XX-XX XX:XX:XX - src.bot.bot - INFO - Starting polling...
```

## Настройка автоматического деплоя

### Шаг 8: GitHub Integration

Render автоматически настраивает webhook для вашего репозитория:

1. При каждом push в ветку `main` будет запускаться новый деплой
2. Render пересоберет Docker образ
3. Новая версия бота автоматически заменит старую

### Шаг 9: Управление деплоями

В панели Render вы можете:
- **Просматривать логи** в реальном времени
- **Откатывать деплои** к предыдущим версиям
- **Приостанавливать/возобновлять** сервис
- **Изменять environment variables**

## Мониторинг и управление

### Просмотр логов

```bash
# В веб-интерфейсе Render:
# 1. Откройте ваш сервис
# 2. Перейдите на вкладку "Logs"
# 3. Логи обновляются в реальном времени
```

### Метрики производительности

Render предоставляет:
- **CPU Usage** - использование процессора
- **Memory Usage** - использование памяти
- **Response Time** - время отклика
- **Error Rate** - количество ошибок

### Health Checks

Render автоматически мониторит ваше приложение:
- Проверяет доступность каждые 30 секунд
- Автоматически перезапускает при сбоях
- Уведомляет об проблемах (при настройке)

## Устранение неполадок

### Частые проблемы и решения

**1. Бот не запускается**
```bash
# Проверьте логи на ошибки:
# - Неправильные environment variables
# - Ошибки в токенах API
# - Проблемы с Docker образом
```

**2. Исчерпание лимитов**
```bash
# На бесплатном плане:
# - 750 часов/месяц (31 день × 24 часа = 744 часа)
# - Upgrade до Starter плана ($7/месяц) для безлимитного времени
```

**3. Спящий режим (Sleep Mode)**
```bash
# Бесплатные сервисы засыпают после 15 минут бездействия
# Решения:
# - Upgrade до платного плана
# - Настройка периодических "ping" запросов
# - Использование cron-job сервисов для пробуждения
```

### Команды для отладки

**Проверка статуса через Render CLI:**
```bash
# Установка Render CLI
npm install -g @render/cli

# Авторизация
render auth login

# Просмотр логов
render logs --service telegram-llm-bot

# Информация о сервисе
render service info telegram-llm-bot
```

## Обновление приложения

### Автоматическое обновление

1. Внесите изменения в код
2. Зафиксируйте и отправьте в GitHub:
   ```bash
   git add .
   git commit -m "Update bot functionality"
   git push origin main
   ```
3. Render автоматически начнет новый деплой

### Ручное обновление

1. В панели Render откройте ваш сервис
2. Нажмите **"Manual Deploy"**
3. Выберите ветку для деплоя
4. Нажмите **"Deploy"**

## Безопасность и лучшие практики

### Управление секретами

- ✅ **Никогда не коммитьте** токены в код
- ✅ **Используйте Environment Variables** в Render
- ✅ **Регулярно ротируйте** API ключи
- ✅ **Ограничьте права** GitHub токенов

### Мониторинг безопасности

- 🔍 **Отслеживайте логи** на подозрительную активность
- 🔍 **Настройте уведомления** о сбоях
- 🔍 **Регулярно обновляйте** зависимости

## Заключение

После выполнения всех шагов:
- ✅ Ваш бот работает в облаке 24/7
- ✅ Автоматически обновляется при изменениях кода
- ✅ Логи и метрики доступны в веб-интерфейсе
- ✅ Не требует обслуживания локального сервера

**Полезные ссылки:**
- [Render.com Documentation](https://render.com/docs)
- [Docker on Render](https://render.com/docs/docker)
- [Environment Variables](https://render.com/docs/environment-variables)
- [Troubleshooting Guide](https://render.com/docs/troubleshooting-deploys)

**Поддержка:**
- Render Support: support@render.com
- Community: [Render Community](https://community.render.com/)
- Status Page: [status.render.com](https://status.render.com/)

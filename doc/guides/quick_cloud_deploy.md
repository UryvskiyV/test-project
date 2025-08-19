# Быстрое развертывание в облаке - Render.com

## 🚀 За 5 минут до облачного бота!

### Шаг 1: Подготовка
1. Убедитесь что код в GitHub репозитории
2. У вас есть токены: `TELEGRAM_BOT_TOKEN` и `OPENROUTER_API_KEY`

### Шаг 2: Регистрация на Render.com
1. Перейти на [render.com](https://render.com)
2. **"Get Started for Free"** → **"Sign up with GitHub"**
3. Авторизовать доступ к репозиториям

### Шаг 3: Создание Web Service
1. **"New +"** → **"Web Service"**
2. Выбрать ваш репозиторий
3. Настроить:
   - **Name:** `telegram-llm-bot`
   - **Environment:** `Docker`
   - **Branch:** `main`
   - **Auto-Deploy:** `Yes`

### Шаг 4: Environment Variables
Добавить в разделе **"Environment Variables"**:
```
TELEGRAM_BOT_TOKEN=your_actual_bot_token
OPENROUTER_API_KEY=your_actual_api_key
LLM_MODEL=anthropic/claude-3-haiku-20240307
LOG_LEVEL=INFO
PORT=8000
```

### Шаг 5: Деплой
1. **"Create Web Service"**
2. Ждать 5-10 минут (первая сборка)
3. В логах увидеть: `Bot started: @YourBot`

### ✅ Готово!
- Бот работает в облаке 24/7
- Автоматически обновляется при push в GitHub
- Мониторинг на https://dashboard.render.com

### 🔗 Полная инструкция
См. [doc/guides/render_deployment.md](render_deployment.md) для подробностей.

### 📊 Health Check
Проверить статус: `https://your-app.onrender.com/health`

### 🆘 Проблемы?
1. Проверьте логи в Render Dashboard
2. Убедитесь что токены правильные
3. Проверьте статус на [status.render.com](https://status.render.com)

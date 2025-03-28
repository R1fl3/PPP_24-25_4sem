
# Encryption API Project

## 📦 Установка

1. Клонировать или распаковать проект.
2. Установить зависимости:

```
pip install -r requirements.txt
```

##  Запуск


В первом терминале-сервере запускаем
uvicorn main:app --reload 
Во втором терминале запускаем
celery -A celery_worker worker --loglevel=info --pool=solo 


## 🔑 Авторизация

1. Зарегистрируйтесь через `/api/auth/sign-up/`
2. Получите токен через `/api/auth/login/`
3. Используйте токен в заголовке `Authorization: Bearer <token>` при запросах на `/api/encryption/encode` и `/decode`

## 🧩 Эндпоинты

### Регистрация
POST `/api/auth/sign-up/`

### Логин
POST `/api/auth/login/`

### Сжатие и шифрование
POST `/api/encryption/encode`

### Дешифровка и распаковка
POST `/api/encryption/decode`

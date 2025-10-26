# CI/CD Lab - OpenBMC Testing Pipeline

Лабораторная работа по настройке CI/CD pipeline для тестирования OpenBMC с использованием Jenkins в Docker.

## Структура проекта

```
cicd_lab/
├── docker-compose.yml          # Docker Compose конфигурация
├── Jenkinsfile                 # Jenkins pipeline
├── requirements.txt            # Python зависимости
├── scripts/                    # Скрипты для управления QEMU
│   ├── start_qemu.sh          # Запуск QEMU с OpenBMC
│   └── stop_qemu.sh           # Остановка QEMU
├── web_ui_tests/              # Web UI тесты (Selenium)
│   ├── web_ui_tests.py
│   └── conftest.py
├── redfish_api_tests/         # Redfish API тесты
│   └── Redfish_API_tests.py
├── load_tests/                # Нагрузочное тестирование (Locust)
│   └── Locust.py
├── romulus/                   # Образ OpenBMC для QEMU
│   └── obmc-phosphor-image-romulus-20250902012112.static.mtd
└── chromedriver/              # ChromeDriver для Selenium
    └── chromedriver
```

## Запуск

### 1. Запуск Jenkins в Docker

```bash
# Запуск контейнеров
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f jenkins
```

### 2. Доступ к Jenkins

- URL: http://localhost:8080
- Jenkins будет доступен после полной инициализации (установка зависимостей может занять несколько минут)

### 3. Настройка Jenkins Job

1. Откройте Jenkins в браузере
2. Создайте новый Pipeline job
3. В настройках Pipeline выберите "Pipeline script from SCM"
4. Укажите путь к репозиторию или используйте "Pipeline script"
5. Скопируйте содержимое `Jenkinsfile` в Pipeline script

### 4. Запуск Pipeline

Pipeline включает следующие этапы:

1. **Подготовка окружения** - создание директорий для артефактов
2. **Запуск QEMU с OpenBMC** - запуск виртуальной машины с OpenBMC
3. **Web UI Тесты** - тестирование веб-интерфейса с помощью Selenium
4. **Redfish API Тесты** - тестирование REST API
5. **Нагрузочное тестирование** - тестирование производительности с Locust
6. **Сборка артефактов** - создание отчетов и сохранение результатов

## Тесты

### Web UI Тесты
- Авторизация в системе OpenBMC
- Тестирование блокировки учетной записи
- Проверка температурных датчиков

### Redfish API Тесты
- Аутентификация через Redfish API
- Получение информации о системе
- Управление питанием
- Мониторинг температуры CPU
- Управление сессиями

### Нагрузочное тестирование
- Тестирование API под нагрузкой
- 10 пользователей в течение 60 секунд
- Проверка производительности системы

## Артефакты

После выполнения pipeline в Jenkins будут доступны:

- HTML отчеты тестов
- JUnit XML файлы
- Скриншоты Web UI тестов
- Логи QEMU
- Отчеты Locust
- Общий сводный отчет

## Требования

- Docker и Docker Compose
- Минимум 4GB RAM для QEMU
- Порты 8080, 50000, 2443 должны быть свободны

## Устранение неполадок

### QEMU не запускается
- Проверьте наличие MTD файла в директории `romulus/`
- Убедитесь, что порт 2443 свободен
- Проверьте логи: `docker-compose logs jenkins`

### Тесты не проходят
- Убедитесь, что OpenBMC полностью загрузился
- Проверьте доступность https://localhost:2443
- Проверьте логи тестов в Jenkins

### Chrome/Selenium ошибки
- Убедитесь, что ChromeDriver совместим с версией Chrome
- Проверьте настройки headless режима в conftest.py

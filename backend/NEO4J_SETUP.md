# Инструкции по запуску Neo4j

## Вариант 1: Docker Desktop (рекомендуется)

1. **Установите Docker Desktop для Windows:**
   - Скачайте с https://www.docker.com/products/docker-desktop/
   - Установите и запустите Docker Desktop
   - Дождитесь полного запуска (иконка в трее должна быть зеленой)

2. **Запустите Neo4j контейнер:**
   ```powershell
   docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
   ```

3. **Проверьте запуск:**
   - Откройте http://localhost:7474
   - Логин: neo4j
   - Пароль: password

## Вариант 2: Neo4j Desktop (без Docker)

1. **Скачайте Neo4j Desktop:**
   - Перейдите на https://neo4j.com/download/
   - Скачайте Neo4j Desktop для Windows
   - Установите программу

2. **Создайте базу данных:**
   - Откройте Neo4j Desktop
   - Нажмите "New" → "Create Project"
   - Нажмите "Add" → "Local DBMS"
   - Имя: aerodoc
   - Пароль: password
   - Версия: 5.x или новее

3. **Запустите базу данных:**
   - Нажмите кнопку "Start" рядом с созданной БД
   - Дождитесь запуска (статус станет "Running")

4. **Обновите настройки подключения:**
   В файле `backend/env/neo4j.env`:
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   ```

## Вариант 3: Neo4j Aura (облачная версия, бесплатный уровень)

1. **Создайте аккаунт:**
   - Перейдите на https://neo4j.com/cloud/aura/
   - Зарегистрируйтесь
   - Создайте бесплатную инстанцию

2. **Получите данные подключения:**
   - Скопируйте Connection URI
   - Сохраните пароль

3. **Обновите настройки:**
   В файле `backend/env/neo4j.env`:
   ```env
   NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=ваш_пароль
   ```

## Проверка подключения

После запуска Neo4j проверьте подключение:

```powershell
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')); driver.verify_connectivity(); print('Подключение успешно!'); driver.close()"
```

## Запуск построения графа

После успешного подключения к Neo4j:

```powershell
cd backend
python -m src.services.knowledge_graph
```

## Просмотр графа

1. Откройте Neo4j Browser: http://localhost:7474
2. Введите логин и пароль
3. Выполните запрос для просмотра:
   ```cypher
   MATCH (n) RETURN n LIMIT 25
   ```

## Остановка и очистка

### Docker:
```powershell
# Остановить контейнер
docker stop neo4j

# Удалить контейнер
docker rm neo4j

# Удалить данные (если нужно начать заново)
docker volume prune
```

### Neo4j Desktop:
- Нажмите "Stop" в интерфейсе

## Troubleshooting

### Ошибка "docker: error during connect"
- Docker Desktop не запущен. Запустите Docker Desktop и дождитесь его полного запуска

### Ошибка "Unable to retrieve routing information"
- Neo4j еще не запустился. Подождите 30-60 секунд после запуска контейнера
- Проверьте, что порт 7687 не занят: `netstat -ano | findstr :7687`

### Ошибка "Authentication failed"
- Проверьте пароль в `backend/env/neo4j.env`
- Убедитесь, что пароль совпадает с тем, что использовался при создании БД

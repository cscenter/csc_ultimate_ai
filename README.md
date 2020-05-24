# Сервер песочницы для задач AI курса ML

DEMO: http://ultimategame.ml/

Описание задания: https://github.com/cscenter/ml_hw_ai

## Установка (Mac,Linux)

*Увы нет инструкции под Windows. Если вы расширите проект примером запуска для Windows. Пожалуйста сделайте пулл реквест, 
либо напишите Алексею Пшеничному izhleba@gmail.com*

 0.  Необходимо установить git и pipenv.
    https://www.atlassian.com/git/tutorials/install-git
    https://github.com/pypa/pipenv#installation
 
 1. Cкачиваем репозиторий с кодом и заходим в директорию с проектом.
    ```
    git clone git@github.com:cscenter/csc_ultimate_ai.git
    cd csc_ultimate_ai
    ```

 2. Устанвливаем все необходимые python пакеты. Вводим в теримнал:

    ```
    pipenv install
    pipenv update
    ```

 3. Запускам пример из двух агентов. Вводим в теримнал:

    ```
    ./run_local_example.sh
    ```
    В выводе смотрим статистику и распределенеи мест по агентам. 
    
## Решение частых проблем

Порой при тестировании агентов, некоторые процессы с ними не умирают, 
они продолжают жить и вклиниваться в работу. 
Отследить эти процессы можно следующими способами:
- Попытаться найти их в процессах python `ps aux | grep python`
- Попытаться найти их с более специфичной фильтрацией `ps aux | grep csc_ultimate_ai`

Далее воспользуйтесь `kill <pid>`

 

# Домашнее задание по курсу "Машинное обучение ч.2"

Предлагается реализовать агента для простой многопользовательской игры с другими агентами.
Это вариант многораундовой ультимативной игры.

## Правила игры

Для игры выбирают двух случайных участников. Дальше выбирают в паре участника (proposer), 
которому дают возможность сделать ультиматум. Наприме есть 100 долларов/очков/леденцов. 
Он (proposer) должен разделить эти плюшки в каком-то соотношении. К примеру, 100 себе и 0 второму участнику (responder). 
Или 70 себе и 30 второму участнику. Второй участник (responder) может либо согласиться на этот ультиматум.
Тогда произойдёт сделка, каждый получит в соответствии с предложенным разбиением. 
 Либо отказаться. Тогда оба получают 0.

Проводится множество раундов, после которых сравниваются статистики набранных долларов/очков/леденцов 
и распределяются места. Набравшему болбьше всех первое и т.д.

## Метрика успеха

В качестве метрики успешности агента принимается нижняя граница доверительного интервала в две сигмы 
от его среднего заработка.
Если `gains` - это массив заработков размера `n`, то `score = mean(gains) - 2 * std(gains) / sqrt(n)`. 

## Установка (Mac,Linux)

*Если вы расширите прокт примером запуска для Windows. Пожалуйста сделайте пулл реквест, 
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
    
## Создание своего агента

### Структура класса
Для написания своего агента необходимо создать класс отнаследовавшись от базового класса 
`agent.base.BaseAgent`. Далее нужно реализовать следующие методы:
- `def get_my_name(self)` возвращяет строкой ваше имя и фамилию 
- `def offer_action(self, data)` возващяет размер вашего предложения (int) некоторому агенту в раунде. 
Данные об агенте и общем размере разделяемых средства находятся в `data` 
структура класса описана здесь `base.protocol.OfferRequest`. Размером вашего предложения `offer` это то сколько 
вы предлагаете оставить другому агенту, в случае принятия его, ваша награда будет равна `total_amount - offer`.
- `deal_action(self, data)` возвращяет ответ (bool) согласны ли вы на предложение 
от некоторого агента. Данные об агенте и о размере предложения находятся в `data` 
структура класса описана здесь `base.protocol.DealRequest` 
- `def round_result_action(self, data: RoundResult)` метод вызывается по окончанию раунда, собщяет общие 
результаты в `data` описание `base.protocol.RoundResult`. 

### Структуры данных и их поля
####OfferRequest
```
round_id: int - номер раунда
target_agent_uid: str - идентификатор агента которому будет отосланно предложение
total_amount: int - общее количество которое необходимо разделить
```
####DealRequest
```
round_id: int - номер раунда
from_agent_uid: str - идентификатор агента от которого поступило предложение
total_amount: int - общий размер разделяемых средств
offer: int - предложение от агента
```
####RoundResult
```
round_id: int - номер раунда
win: bool - True если раунд успешен и предложение принято, False - в противном случае
agent_gain: Dict[str, int] - ассоциативный массив с размерами наград, ключ - идентификатор агентов раунда
disconnection_failure: bool - флаг показывает что во время раунда произошел дисконект одного из участников
```

###Приме агента
Простой агент без памяти, который всегда делит поровну и принимает любое не нулевое предложение.
```python
class DummyAgent(BaseAgent):

    def get_my_name(self):
        return 'Dummy'

    def offer_action(self, m):
        return m.total_amount // 2

    def deal_action(self, m):
        if m.offer > 0:
            return True
        else:
            return False

    def round_result_action(self, data):
        pass
```

### Общие правила, рекомендации и советы
1. В качестве идентификаторов агентоа используются строковые представления UUID. После того как подключаться все агенты,
 сервер оповестит вас о вашем uid, его можно будет узнать из поля agent_id. Обратите внимание после инициализации класса
  это поле будет `None` до оповещения от сервера. 
2. Если агент не отвечает более чем 2 секунды, он удаляется из обработки, никакие дальнейшие его сообщения не обрабатываются. 
Однако все проведенные раунды учитываются в финальном рейтинге.
3. Если нужна длительная инициализация проведите ее в методе __init__, так как сервер будет 1 минуту ждать инициализации всех агентов.
4. Если клиент не ответил что он готов к работе в течении минуты, то он удаляется из игры.
5. За любые попытки прямого использования сетевого протокола игры, будет дисквалификация. 



## Решение частых проблем

Порой при тестировании агентов, некоторые процессы с ними не умирают, 
они продолжают работать и вклиниваться в работу. 
Отследить эти процессы можно следующими способами:
- Попытаться найти их в процессах python `ps aux | grep python`
- Попытаться найти их с более специфичной фильтрацией `ps aux | grep csc_ultimate_ai`

Далее воспользуйтес `kill <pid>`

 

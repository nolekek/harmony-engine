# Строгая математическая модель системы гармонизации

## 1. Пространство звуковысотности и ладовой структуры

### 1.1. Абсолютные и относительные высоты
Пусть $\mathbb{P} = \{0, 1, \dots, 127\}$ — пространство высот MIDI (полутоны, где $C_4 = 60$).
Определим циклическую группу классов высот:
$$\mathbb{PC} = \mathbb{Z}_{12} = \{0, 1, \dots, 11\}$$
Оператор приведения абсолютной высоты $p \in \mathbb{P}$ к классу высоты:
$$\text{pc}(p) = p \pmod{12}$$

### 1.2. Ладовая система (Key & Scale Degrees)
Тональность определяется парой $K = (t_0, M)$, где:
- $t_0 \in \mathbb{PC}$ — тоника (тоникальный класс высоты, напр. $C = 0, D = 2$).
- $M \in \{\text{Major}, \text{MinorHarmonic}, \text{MinorNatural}\}$ — ладовый вектор смещений $\Delta = (\delta_0, \delta_1, \dots, \delta_6)$:
  $$\Delta_{\text{Major}} = (0, 2, 4, 5, 7, 9, 11)$$
  $$\Delta_{\text{MinorHarmonic}} = (0, 2, 3, 5, 7, 8, 11)$$

Ступень лада $d \in \mathbb{Z}_7 = \{0, 1, \dots, 6\}$ (соответствует I, II, ..., VII).
Класс высоты ступени $d$ в тональности $K$:
$$\text{pc}_K(d) = (t_0 + \Delta[d]) \pmod{12}$$

---

## 2. Модель аккорда и вертикали SATB

### 2.1. Четырехголосный срез (SATB State)
Вертикаль в момент времени $t \in \{1, \dots, N\}$ описывается 4-мерным вектором:
$$\mathbf{v}_t = (S_t, A_t, T_t, B_t) \in \mathbb{P}^4$$

### 2.2. Геометрические ограничения вертикали (Static Validity)
Вектор $\mathbf{v}_t$ является статически допустимым ($\text{Valid}(\mathbf{v}_t) = 1$) тогда и только тогда, когда:
1. **Строгая упорядоченность по высоте (отсутствие перекрещивания):**
   $$S_t \ge A_t \ge T_t \ge B_t$$
2. **Диапазоны голосов:**
   $$S_t \in [60, 81], \quad A_t \in [55, 74], \quad T_t \in [48, 67], \quad B_t \in [40, 60]$$
3. **Акустические пределы расстояний (отсутствие разрывов фактуры):**
   $$S_t - A_t \le 12$$
   $$A_t - T_t \le 12$$
   $$T_t - B_t \le 24$$
4. **Соответствие аккордовой структуре (Pitch Class Membership):**
   Пусть $\text{ChordPC}(F_t) \subset \mathbb{PC}$ — множество разрешенных классов высот аккорда функции $F_t$:
   $$\forall X \in \{S_t, A_t, T_t, B_t\}: \quad \text{pc}(X) \in \text{ChordPC}(F_t)$$
5. **Предикат удвоений:**
   Множество кратностей классов высот в $\mathbf{v}_t$ удовлетворяет нормативам Бригады:
   $$\text{Mult}(F_t, \mathbf{v}_t) = \text{True}$$

---

## 3. Модель перехода (Voice-Leading Transition & Cost Function)

При переходе между двумя вертикалями $\mathbf{v}_{t-1} \to \mathbf{v}_t$ вычисляется стоимость ребра $C(\mathbf{v}_{t-1}, \mathbf{v}_t)$:

$$C(\mathbf{v}_{t-1}, \mathbf{v}_t) = H(\mathbf{v}_{t-1}, \mathbf{v}_t) + S(\mathbf{v}_{t-1}, \mathbf{v}_t)$$

### 3.1. Функция жестких ограничений (Hard Constraints)
$$H(\mathbf{v}_{t-1}, \mathbf{v}_t) = \begin{cases} 0, & \text{если все предикаты соблюдены} \\ +\infty, & \text{если нарушено хотя бы одно правило} \end{cases}$$

Предикаты $H$:
1. **Параллельные квинты и октавы:**
   Для любой пары голосов $(X, Y) \in \{S, A, T, B\}^2$, $X \ne Y$:
   $$\text{interval}(X_{t-1}, Y_{t-1}) \equiv 7 \pmod{12} \;\land\; \text{interval}(X_t, Y_t) \equiv 7 \pmod{12} \;\land\; \Delta X \cdot \Delta Y > 0 \implies \text{VIOLATION}$$
   $$\text{interval}(X_{t-1}, Y_{t-1}) \equiv 0 \pmod{12} \;\land\; \text{interval}(X_t, Y_t) \equiv 0 \pmod{12} \;\land\; \Delta X \cdot \Delta Y > 0 \implies \text{VIOLATION}$$
2. **Противоположные квинты и октавы:**
   Аналогично при $\Delta X \cdot \Delta Y < 0$, если результирующий интервал чистый.
3. **Скрытые квинты/октавы крайних голосов:**
   $$\Delta S \cdot \Delta B > 0 \;\land\; (S_t - B_t) \pmod{12} \in \{0, 7\} \;\land\; |\Delta S| > 2 \implies \text{VIOLATION}$$
4. **Перекрывание голосов:**
   $$A_t > S_{t-1} \lor A_t < T_{t-1} \implies \text{VIOLATION}$$
   $$T_t > A_{t-1} \lor T_t < B_{t-1} \implies \text{VIOLATION}$$
5. **Запрещенные мелодические шаги:**
   $$\forall X \in \{S, A, T, B\}: \quad |X_t - X_{t-1}| \in \{3 \text{ (ув.2 в миноре)}, 10, 11 \text{ (септимы)}\} \implies \text{VIOLATION}$$
6. **Обязательное разрешение диссонансов (D43 и D2):**
   - Для $D^4_3$: бас $B_{t-1} = \text{II}$ ступень (квинта доминанты). Разрешается в $T_{53}$ (шаг баса вниз: $B_t = B_{t-1} - 1 \lor B_t = B_{t-1} - 2$) или в $T_6$ (шаг баса вверх: $B_t = B_{t-1} + 1 \lor B_t = B_{t-1} + 2$). Септима аккорда (IV ступень) в верхних голосах обязана разрешаться на секунду вниз в III ступень.
   - Для $D_2$: бас $B_{t-1} = \text{IV}$ ступень (септима доминанты). Разрешается строго в $T_6$ с обязательным шагом баса вниз на секунду ($B_t = B_{t-1} - 1 \lor B_t = B_{t-1} - 2$).

### 3.2. Функция мягких штрафов (Soft Cost)
$$S(\mathbf{v}_{t-1}, \mathbf{v}_t) = w_1 \cdot \text{Movement}(A, T) + w_2 \cdot \text{BassMotion}(B, S) + w_3 \cdot \text{LeapCost}(B)$$
- **Закон кратчайшего пути:**
  $$\text{Movement}(A, T) = |A_t - A_{t-1}| + |T_t - T_{t-1}|$$
- **Противоположное движение баса относительно сопрано:**
  $$\text{BassMotion}(B, S) = \begin{cases} -5.0, & \text{если } \Delta B \cdot \Delta S < 0 \\ +2.0, & \text{если } \Delta B \cdot \Delta S > 0 \\ 0.0, & \text{иначе} \end{cases}$$

---

## 4. Алгоритм глобальной оптимизации (Viterbi Dynamic Programming)

Пусть для каждого временного шага $t \in \{1, \dots, N\}$ сформировано множество допустимых вертикалей:
$$\mathcal{V}_t = \{\mathbf{v}_{t, 1}, \mathbf{v}_{t, 2}, \dots, \mathbf{v}_{t, K_t}\}, \quad |\mathcal{V}_t| \le K_{\max} \approx 40$$

Определим функцию оптимальной накопленной стоимости $\delta_t(j)$ для $j \in \{1, \dots, |\mathcal{V}_t|\}$:
$$\delta_1(j) = \text{InitCost}(\mathbf{v}_{1, j})$$
$$\delta_t(j) = \min_{1 \le i \le |\mathcal{V}_{t-1}|} \Big( \delta_{t-1}(i) + C(\mathbf{v}_{t-1, i}, \mathbf{v}_{t, j}) \Big)$$

Массив обратных указателей для восстановления траектории:
$$\psi_t(j) = \arg\min_{1 \le i \le |\mathcal{V}_{t-1}|} \Big( \delta_{t-1}(i) + C(\mathbf{v}_{t-1, i}, \mathbf{v}_{t, j}) \Big)$$

После достижения шага $N$:
$$j_N^* = \arg\min_{j} \delta_N(j)$$
$$j_{t-1}^* = \psi_t(j_t^*), \quad t = N, N-1, \dots, 2$$

### Теорема сложности:
- **Время работы:** $\sum_{t=2}^N |\mathcal{V}_{t-1}| \cdot |\mathcal{V}_t| \le N \cdot K_{\max}^2$. При $N=16, K_{\max}=40 \implies \approx 25\,600$ операций. Время инференса $< 5$ мс.
- **Память:** $O(N \cdot K_{\max})$ — полиномиальная, не превышает 100 КБ.
- **Глобальная оптимальность:** В силу принципа оптимальности Беллмана алгоритм гарантированно находит путь с наименьшей суммарной стоимостью без риска застревания в локальных минимумах.

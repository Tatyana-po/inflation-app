# app.py
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go

# ==================== НАСТРОЙКА СТРАНИЦЫ ====================
st.set_page_config(
    page_title="Моделирование инфляции в Беларуси",
    page_icon="📈",
    layout="wide"
)

# ==================== ИНИЦИАЛИЗАЦИЯ SESSION_STATE ====================
if 'usd_change' not in st.session_state:
    st.session_state.usd_change = 0.0
if 'm2_growth' not in st.session_state:
    st.session_state.m2_growth = 12.0
if 'wage_growth' not in st.session_state:
    st.session_state.wage_growth = 8.0
if 'use_crisis' not in st.session_state:
    st.session_state.use_crisis = False
if 'forecast_calculated' not in st.session_state:
    st.session_state.forecast_calculated = False

# Функции для сценариев (меняют session_state и перезапускают страницу)
def set_optimistic():
    st.session_state.usd_change = -3.0
    st.session_state.m2_growth = 8.0
    st.session_state.wage_growth = 6.0
    st.session_state.use_crisis = False
    st.session_state.forecast_calculated = False
    st.rerun()

def set_baseline():
    st.session_state.usd_change = 0.0
    st.session_state.m2_growth = 12.0
    st.session_state.wage_growth = 8.0
    st.session_state.use_crisis = False
    st.session_state.forecast_calculated = False
    st.rerun()

def set_pessimistic():
    st.session_state.usd_change = 10.0
    st.session_state.m2_growth = 18.0
    st.session_state.wage_growth = 12.0
    st.session_state.use_crisis = False
    st.session_state.forecast_calculated = False
    st.rerun()

def set_reset():
    st.session_state.usd_change = 0.0
    st.session_state.m2_growth = 12.0
    st.session_state.wage_growth = 8.0
    st.session_state.use_crisis = False
    st.session_state.forecast_calculated = False
    st.rerun()

# ==================== ЗАГРУЗКА МОДЕЛИ И ДАННЫХ ====================
@st.cache_resource
def load_model():
    return joblib.load('model.pkl')

@st.cache_data
def load_data():
    df = pd.read_excel('конечная таблица данных.xlsx', header=3)
    df.columns = ['date', 'usd_change', 'inf', 'm2_growth', 'wage_real', 
                  'inf_lag1', 'm2_growth_lag6', 'd_crisis']
    df['date'] = pd.to_datetime(df['date'])
    
    # Расчёт годовой инфляции (за 12 месяцев)
    df['inf_yearly'] = df['inf'].rolling(window=12).apply(
        lambda x: (1 + x/100).prod() - 1, raw=True
    ) * 100
    
    return df

# Загружаем модель и данные
model = load_model()
df_hist = load_data()
df_clean = df_hist.dropna().copy()

# Коэффициенты модели
coefs = model.params

# ==================== ЗАГОЛОВОК ====================
st.title("📈 Моделирование инфляции в Республике Беларусь")
st.markdown("### Анализ причин и последствий инфляционных процессов")
st.markdown("---")

# ==================== БОКОВАЯ ПАНЕЛЬ ====================
st.sidebar.header("🎛️ Параметры экономической политики")

# Кнопки быстрых сценариев
st.sidebar.markdown("### 🚀 Быстрые сценарии")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.button("📉 Оптимистичный", on_click=set_optimistic)
with col2:
    st.button("📊 Базовый", on_click=set_baseline)

col3, col4 = st.sidebar.columns(2)
with col3:
    st.button("📈 Пессимистичный", on_click=set_pessimistic)
with col4:
    st.button("🔄 Сброс", on_click=set_reset)

st.sidebar.markdown("---")

# ВРЕМЕННЫЕ СЛАЙДЕРЫ (для отображения, но не для расчёта)
temp_usd_change = st.sidebar.slider(
    "Изменение курса USD/BYN (%)", 
    -15.0, 30.0, value=st.session_state.usd_change, step=0.5,
    help="➕ Девальвация (рост курса) увеличивает инфляцию\n➖ Укрепление (снижение курса) снижает инфляцию"
)

temp_m2_growth = st.sidebar.slider(
    "Рост денежной массы M2 (%)", 
    -10.0, 30.0, value=st.session_state.m2_growth, step=0.5,
    help="Чем быстрее растёт M2, тем выше инфляция (с лагом 6 месяцев)"
)

temp_wage_growth = st.sidebar.slider(
    "Рост реальной заработной платы (%)", 
    -10.0, 25.0, value=st.session_state.wage_growth, step=0.5,
    help="Рост доходов населения → рост спроса → рост цен"
)

temp_use_crisis = st.sidebar.checkbox(
    "Учесть кризисный шок (март 2022)", 
    value=st.session_state.use_crisis,
    help="В марте 2022 инфляция достигла 6.1% из-за внешних факторов"
)

st.sidebar.markdown("---")

# Кнопка расчёта
run_forecast = st.sidebar.button("🔮 Рассчитать прогноз", type="primary")

# При нажатии кнопки — сохраняем временные значения в session_state
if run_forecast:
    st.session_state.usd_change = temp_usd_change
    st.session_state.m2_growth = temp_m2_growth
    st.session_state.wage_growth = temp_wage_growth
    st.session_state.use_crisis = temp_use_crisis
    st.session_state.forecast_calculated = True

# ==================== РЕЗУЛЬТАТЫ ПРОГНОЗА ====================
if st.session_state.forecast_calculated:
    st.header("📊 Результаты прогнозирования")
    
    # Берём значения из session_state (сохранённые при нажатии кнопки)
    usd_change = st.session_state.usd_change
    m2_growth = st.session_state.m2_growth
    wage_growth = st.session_state.wage_growth
    use_crisis = st.session_state.use_crisis
    
    last_row = df_clean.iloc[-1:].copy()
    crisis_value = 1 if use_crisis else 0
    
    X_pred = pd.DataFrame({
        'const': [1],
        'usd_change': [usd_change],
        'm2_growth': [m2_growth],
        'wage_real': [wage_growth],
        'inf_lag1': [last_row['inf'].values[0]],
        'm2_growth_lag6': [last_row['m2_growth'].values[0]],
        'd_crisis': [crisis_value]
    })
    
    pred_monthly = model.predict(X_pred)[0]
    pred_yearly = ((1 + pred_monthly / 100) ** 12 - 1) * 100
    
    st.session_state.pred_monthly = pred_monthly
    st.session_state.pred_yearly = pred_yearly
    st.session_state.crisis_value = crisis_value
    st.session_state.usd_change_val = usd_change
    st.session_state.m2_growth_val = m2_growth
    st.session_state.wage_growth_val = wage_growth
    
    # ==================== МЕТРИКИ ====================
    col_metric1, col_metric2 = st.columns(2)
    
    with col_metric1:
        st.metric(
            label="📆 Помесячная инфляция", 
            value=f"{pred_monthly:.3f}%",
            delta="выше нормы" if pred_monthly > 0.7 else "в пределах нормы"
        )
    
    with col_metric2:
        st.metric(
            label="📈 Годовая инфляция (эквивалент)", 
            value=f"{pred_yearly:.2f}%",
            delta="выше цели 7%" if pred_yearly > 7 else "ниже цели 7%"
        )
    
    # Цветовая индикация
    if pred_monthly < 0.3:
        st.success(f"✅ Низкая помесячная инфляция ({pred_monthly:.3f}%)")
    elif pred_monthly < 0.7:
        st.info(f"ℹ️ Умеренная помесячная инфляция ({pred_monthly:.3f}%)")
    elif pred_monthly < 1.2:
        st.warning(f"⚠️ Повышенная помесячная инфляция ({pred_monthly:.3f}%)")
    else:
        st.error(f"🔴 Высокая помесячная инфляция ({pred_monthly:.3f}%)")
    
    if pred_yearly < 5:
        st.success(f"✅ Годовая инфляция ({pred_yearly:.2f}%) — низкая")
    elif pred_yearly < 7:
        st.info(f"ℹ️ Годовая инфляция ({pred_yearly:.2f}%) — в пределах цели НБРБ")
    elif pred_yearly < 10:
        st.warning(f"⚠️ Годовая инфляция ({pred_yearly:.2f}%) — выше цели")
    else:
        st.error(f"🔴 Годовая инфляция ({pred_yearly:.2f}%) — высокая")
    
    st.markdown("---")
    
    # ==================== ДЕКОМПОЗИЦИЯ ====================
    col_left_dec, col_right_dec = st.columns(2)
    
    with col_left_dec:
        st.subheader("📋 Декомпозиция факторов")
        contributions = {
            'Курс USD': coefs['usd_change'] * usd_change,
            'Денежная масса M2': coefs['m2_growth'] * m2_growth,
            'Заработная плата': coefs['wage_real'] * wage_growth,
            'Инерция': coefs['inf_lag1'] * last_row['inf'].values[0],
            'Лаг M2 (6 мес.)': coefs['m2_growth_lag6'] * last_row['m2_growth'].values[0],
            'Кризисный шок': coefs['d_crisis'] * crisis_value,
            'Свободный член': coefs['const']
        }
        
        for name, contrib in contributions.items():
            st.write(f"{name}: **{contrib:.6f} п.п.**")
    
    with col_right_dec:
        st.subheader("📊 Визуализация вклада факторов")
        
        contrib_names = list(contributions.keys())
        contrib_values = list(contributions.values())
        
        sorted_pairs = sorted(zip(contrib_values, contrib_names), reverse=True)
        sorted_values = [pair[0] for pair in sorted_pairs]
        sorted_names = [pair[1] for pair in sorted_pairs]
        
        colors = ['#2ecc71' if v > 0 else '#e74c3c' if v < 0 else '#95a5a6' for v in sorted_values]
        text_labels = [f"{v:.6f} п.п." for v in sorted_values]
        
        fig_contrib = go.Figure()
        fig_contrib.add_trace(go.Bar(
            x=sorted_values,
            y=sorted_names,
            orientation='h',
            marker_color=colors,
            text=text_labels,
            textposition='outside'
        ))
        fig_contrib.add_vline(x=0, line_dash="solid", line_color="gray", line_width=1)
        fig_contrib.update_layout(
            title="Вклад факторов в помесячную инфляцию",
            xaxis_title="Вклад (процентные пункты)",
            yaxis_title="Фактор",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_contrib, use_container_width=True)
    
    st.markdown("---")
    
    # ==================== ПРОГНОЗ НА 12 МЕСЯЦЕВ ====================
    st.subheader("🔮 Прогноз инфляции на 12 месяцев")
    
    forecast_months = 12
    forecast_values = []
    yearly_forecast = []
    
    current_inf = pred_monthly
    current_crisis = crisis_value
    current_usd_change = usd_change
    current_m2_growth_val = m2_growth
    current_wage_val = wage_growth
    
    for i in range(forecast_months):
        forecast_values.append(current_inf)
        current_inf = (coefs['const'] + 
                       coefs['usd_change'] * current_usd_change +
                       coefs['m2_growth'] * current_m2_growth_val +
                       coefs['wage_real'] * current_wage_val +
                       coefs['inf_lag1'] * current_inf +
                       coefs['d_crisis'] * current_crisis)
        current_crisis = 0
        if current_inf < -1:
            current_inf = -1
        if current_inf > 15:
            current_inf = 15
    
    for i in range(forecast_months):
        start_idx = max(0, i - 11)
        product = 1.0
        for j in range(start_idx, i + 1):
            product *= (1 + forecast_values[j] / 100)
        yearly_forecast.append((product - 1) * 100)
    
    tab_f1, tab_f2 = st.tabs(["📊 Помесячный прогноз", "📈 Годовой прогноз"])
    
    with tab_f1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, forecast_months+1)), 
            y=forecast_values,
            mode='lines+markers', 
            name='Помесячная инфляция',
            line=dict(color='red', width=3)
        ))
        fig.update_layout(title="Прогноз помесячной инфляции", xaxis_title="Месяц от текущего", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        forecast_table = pd.DataFrame({
            'Месяц': list(range(1, forecast_months+1)),
            'Прогноз помесячной инфляции (%)': [round(v, 3) for v in forecast_values]
        })
        st.dataframe(forecast_table, use_container_width=True)
    
    with tab_f2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, forecast_months+1)), 
            y=yearly_forecast,
            mode='lines+markers', 
            name='Годовая инфляция',
            line=dict(color='green', width=3)
        ))
        fig.add_hline(y=7, line_dash="dash", line_color="red", annotation_text="Цель НБРБ (7%)")
        fig.update_layout(title="Прогноз годовой инфляции", xaxis_title="Месяц от текущего", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        yearly_table = pd.DataFrame({
            'Месяц': list(range(1, forecast_months+1)),
            'Прогноз годовой инфляции (%)': [round(v, 3) for v in yearly_forecast]
        })
        st.dataframe(yearly_table, use_container_width=True)
    
    st.caption("📌 **Помесячный прогноз** показывает ожидаемую инфляцию за каждый месяц. " +
               "**Годовой прогноз** показывает накопленную инфляцию за последние 12 месяцев.")
    
    st.markdown("---")
    
    # ==================== СТАТИСТИКА МОДЕЛИ ====================
    st.subheader("📊 Статистика модели")
    
    rus_names = {
        'const': 'Свободный член',
        'usd_change': 'Изменение курса USD/BYN',
        'm2_growth': 'Рост денежной массы M2',
        'wage_real': 'Рост реальной заработной платы',
        'inf_lag1': 'Инфляция в предыдущем месяце',
        'm2_growth_lag6': 'Рост M2 (лаг 6 месяцев)',
        'd_crisis': 'Кризисный шок (март 2022)'
    }
    
    col_coef1, col_coef2 = st.columns(2)
    
    with col_coef1:
        st.write("#### Коэффициенты регрессии")
        coef_df = pd.DataFrame({
            'Переменная': [rus_names.get(var, var) for var in coefs.index],
            'Коэффициент': coefs.values,
            'P-значение': model.pvalues.values
        })
        st.dataframe(coef_df.style.format({'Коэффициент': '{:.4f}', 'P-значение': '{:.6f}'}), use_container_width=True)
    
    with col_coef2:
        st.write("#### Метрики качества")
        st.write(f"**R²:** {model.rsquared:.4f}")
        st.write(f"**Скорректированный R²:** {model.rsquared_adj:.4f}")
        st.write(f"**F-статистика:** {model.fvalue:.2f}")
        st.write(f"**Количество наблюдений:** {len(df_clean)}")
        
        st.write("#### Уравнение регрессии")
        
        eq_parts = [f"{coefs['const']:.4f}"]
        if coefs['usd_change'] > 0:
            eq_parts.append(f"+ {coefs['usd_change']:.4f}·Курс")
        else:
            eq_parts.append(f"- {abs(coefs['usd_change']):.4f}·Курс")
        if coefs['m2_growth'] > 0:
            eq_parts.append(f"+ {coefs['m2_growth']:.4f}·M2")
        else:
            eq_parts.append(f"- {abs(coefs['m2_growth']):.4f}·M2")
        if coefs['wage_real'] > 0:
            eq_parts.append(f"+ {coefs['wage_real']:.4f}·Зарплата")
        else:
            eq_parts.append(f"- {abs(coefs['wage_real']):.4f}·Зарплата")
        if coefs['inf_lag1'] > 0:
            eq_parts.append(f"+ {coefs['inf_lag1']:.4f}·Инфляция_прошлая")
        else:
            eq_parts.append(f"- {abs(coefs['inf_lag1']):.4f}·Инфляция_прошлая")
        if coefs['m2_growth_lag6'] > 0:
            eq_parts.append(f"+ {coefs['m2_growth_lag6']:.4f}·M2_лаг6")
        else:
            eq_parts.append(f"- {abs(coefs['m2_growth_lag6']):.4f}·M2_лаг6")
        if coefs['d_crisis'] > 0:
            eq_parts.append(f"+ {coefs['d_crisis']:.4f}·Кризис")
        else:
            eq_parts.append(f"- {abs(coefs['d_crisis']):.4f}·Кризис")
        
        equation = " + ".join(eq_parts).replace("+ -", "- ")
        st.code(f"Инфляция = {equation}", language="python")

else:
    st.info("👈 **Настройте параметры в левой панели и нажмите «Рассчитать прогноз»**")
    st.markdown("""
    ### 📌 Что вы увидите после расчёта:
    - **Прогноз помесячной и годовой инфляции**
    - **Декомпозицию факторов** — вклад каждого показателя
    - **Визуализацию вклада факторов** (горизонтальный график)
    - **Прогноз на 12 месяцев** (помесячный и годовой)
    - **Статистику модели** (коэффициенты, R², уравнение)
    """)

# ==================== ИСТОРИЧЕСКИЕ ГРАФИКИ (всегда внизу) ====================
st.markdown("---")
st.header("📜 Историческая справка: Динамика инфляции в Беларуси")
st.markdown("Данные Белстата за 2016–2026 гг.")

tab_hist1, tab_hist2, tab_hist3 = st.tabs(["📊 Помесячная инфляция", "📈 Годовая инфляция", "📊 Гистограмма (по годам)"])

with tab_hist1:
    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Scatter(
        x=df_hist['date'], 
        y=df_hist['inf'], 
        mode='lines+markers',
        name='Помесячная инфляция',
        line=dict(color='blue', width=2),
        marker=dict(size=4, color='blue')
    ))
    fig_monthly.add_hline(y=0, line_dash="solid", line_color="gray", line_width=1)
    fig_monthly.update_layout(
        title="Инфляция (% к предыдущему месяцу)",
        xaxis_title="Дата",
        yaxis_title="Инфляция (%)",
        height=400
    )
    st.plotly_chart(fig_monthly, use_container_width=True)
    st.caption("📌 Помесячная инфляция — изменение цен относительно предыдущего месяца.")

with tab_hist2:
    fig_yearly = go.Figure()
    fig_yearly.add_trace(go.Scatter(
        x=df_hist['date'], 
        y=df_hist['inf_yearly'], 
        mode='lines+markers',
        name='Годовая инфляция',
        line=dict(color='red', width=2),
        marker=dict(size=4, color='red')
    ))
    fig_yearly.add_hline(y=7, line_dash="dash", line_color="green", annotation_text="Цель НБРБ (7%)")
    fig_yearly.update_layout(
        title="Годовая инфляция (за последние 12 месяцев)",
        xaxis_title="Дата",
        yaxis_title="Инфляция (% годовых)",
        height=400
    )
    st.plotly_chart(fig_yearly, use_container_width=True)
    st.caption("📌 Годовая инфляция — рост цен за последние 12 месяцев.")

with tab_hist3:
    st.write("#### Годовая инфляция по годам")
    
    df_temp = df_hist.copy()
    df_temp['year'] = df_temp['date'].dt.year
    yearly_by_year = df_temp.groupby('year')['inf_yearly'].last().dropna()
    yearly_by_year = yearly_by_year[(yearly_by_year.index >= 2017) & (yearly_by_year.index <= 2025)]
    
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Bar(
        x=yearly_by_year.index.astype(str),
        y=yearly_by_year.values,
        name='Годовая инфляция',
        marker_color='steelblue',
        text=[f"{v:.1f}%" for v in yearly_by_year.values],
        textposition='outside'
    ))
    fig_hist.add_hline(y=7, line_dash="dash", line_color="red", annotation_text="Цель НБРБ (7%)")
    fig_hist.update_layout(
        title="Годовая инфляция по годам (декабрь к декабрю)",
        xaxis_title="Год",
        yaxis_title="Инфляция (% годовых)",
        height=450
    )
    st.plotly_chart(fig_hist, use_container_width=True)
    st.caption("📌 Гистограмма показывает итоговую годовую инфляцию за каждый календарный год.")

# ==================== ФУТЕР ====================
st.markdown("---")
st.markdown("""
**📚 Источники данных:** Белстат, Национальный банк Республики Беларусь  
**🧮 Методология:** Множественная линейная регрессия (OLS) с лаговыми переменными  
**📅 Период:** 2017–2026 (111 наблюдений)  
**👨‍💻 Курсовой проект:** Компьютерное моделирование экономических систем
""")
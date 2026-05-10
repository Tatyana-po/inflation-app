# train_model.py
import pandas as pd
import numpy as np
import statsmodels.api as sm
import joblib

# Загрузка данных
df = pd.read_excel('конечная таблица данных.xlsx', header=3)

# Переименовываем столбцы
df.columns = ['date', 'usd_change', 'inf', 'm2_growth', 'wage_real', 
              'inf_lag1', 'm2_growth_lag6', 'd_crisis']

# Удаляем строки с пропусками (NA)
df_clean = df.dropna().copy()

print(f"Загружено наблюдений: {len(df_clean)}")
print(f"Период: с {df_clean['date'].iloc[0]} по {df_clean['date'].iloc[-1]}")

# Подготовка переменных
X = df_clean[['usd_change', 'm2_growth', 'wage_real', 'inf_lag1', 'm2_growth_lag6', 'd_crisis']]
y = df_clean['inf']

# Добавляем константу (свободный член)
X = sm.add_constant(X)

# Обучаем модель OLS
model = sm.OLS(y, X).fit()

# Выводим результаты
print("\n" + "="*60)
print("РЕЗУЛЬТАТЫ РЕГРЕССИИ")
print("="*60)
print(f"R² = {model.rsquared:.4f}")
print(f"Скорректированный R² = {model.rsquared_adj:.4f}")
print(f"F-статистика = {model.fvalue:.2f} (p = {model.f_pvalue:.6f})")
print("\nКоэффициенты:")
for var, coef in model.params.items():
    print(f"  {var:15} : {coef:.6f}")
    print(f"                    (p-значение: {model.pvalues[var]:.6f})")

# Сохраняем модель
joblib.dump(model, 'model.pkl')
print("\n✅ Модель сохранена в файл 'model.pkl'")
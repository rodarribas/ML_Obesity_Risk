# LIBRERÍAS

# Tratamiento de datos
import pandas as pd
import numpy as np

# Modelos y métricas
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier
import lightgbm as lgb
from sklearn.ensemble import RandomForestClassifier, VotingClassifier

# Procesado
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler

# Otros
import joblib
import warnings
warnings.filterwarnings('ignore')
# ------------------------------------------------------------------------------------------------------------------------------------------------

# LECTURA
df = pd.read_csv(r'.\data\raw\train.csv')
# ------------------------------------------------------------------------------------------------------------------------------------------------


# PROCESADO INICIAL
# drop columns
df.drop(columns='id', inplace=True)

# lowercase
df = df.rename(columns=str.lower)

# gender
df.rename(columns={'gender':'male'}, inplace=True)
df['male'] = df['male'].map({'Female':0, 'Male':1})

# binary_cols
binary_cols = ['family_history_with_overweight', 'favc', 'smoke', 'scc']
for column in binary_cols:
    df[column] = df[column].map({'no':0, 'yes':1})

# mtrans
df['mtrans_s'] = df.mtrans.map({'Public_Transportation': 'public',
                                      'Automobile': 'private',
                                      'Walking': 'physic',
                                      'Motorbike':'private',
                                      'Bike':'physic'})

# NOTA: como es un train.py genérico, en este script no se redondearán las columnas señaladas en el notebook 1 ni se eliminarán outliers
# ------------------------------------------------------------------------------------------------------------------------------------------------


# PREPROCESAMIENTO
# División X e y
X = df.drop(columns='nobeyesdad')
y = df['nobeyesdad']

# OHE
ohe = OneHotEncoder(sparse=False, handle_unknown='ignore', dtype=int)

encoded_mtrans = pd.DataFrame(ohe.fit_transform(X[['mtrans']]),
                             columns=ohe.get_feature_names_out(['mtrans']),
                             index=X.index)
encoded_mtrans.drop(columns='mtrans_physic', inplace=True) # Elimino una de las columnas para mejorar el rendimiento
X = pd.concat([X, encoded_mtrans], axis=1).drop(columns='mtrans') # Concateno

# MAPEO
X.caec = X.caec.map({'no':0,
                     'Sometimes':1,
                     'Frequently':2,
                     'Always':3})
X.calc = X.calc.map({'no':0,
                     'Sometimes':1,
                     'Frequently':2})
y = y.map({'Insufficient_Weight':0,
           'Normal_Weight':1,
           'Overweight_Level_I':2,
           'Overweight_Level_II':3,
           'Obesity_Type_I':4,
           'Obesity_Type_II':5,
           'Obesity_Type_III':6})

# LOG
X.age = np.log(X.age)
X.weight = np.log(X.weight)
X.height = np.log(X.height)

# ESCALADO
minmax = MinMaxScaler()
X = pd.DataFrame(minmax.fit_transform(X),
                 columns=X.columns,
                 index=X.index)

# Selección columnas
df = pd.concat([X, y], axis=1)[['age', 'height', 'weight', 'family_history_with_overweight', 'favc', 'fcvc', 'caec', 'ch2o', 'faf', 'nobeyesdad']]
# ------------------------------------------------------------------------------------------------------------------------------------------------


# ENTRENAMIENTO
# Train-Test split
X_train, X_test, y_train, y_test = train_test_split(df.drop(columns=['nobeyesdad']),
                                                    df['nobeyesdad'],
                                                    test_size=0.2,
                                                    random_state=42,
                                                    stratify=df['nobeyesdad'])

# Instanciación de modelos
LGBM_1 = lgb.LGBMClassifier(num_leaves=50,
              learning_rate=0.1,
              n_estimators=100,
              max_depth=5,
              min_child_samples=30,
              subsample=0.8,
              colsample_bytree=1.0)


XGB_1 = XGBClassifier(n_estimators=100,
              learning_rate=0.1,
              max_depth=7,
              subsample=0.8,
              colsample_bytree=0.6)


RF_1 = RandomForestClassifier(n_estimators=150,
              max_depth=15,
              min_samples_split=8,
              min_samples_leaf=4,
              bootstrap=True)

# Voting ensemble
voting_clf = VotingClassifier(
    estimators=[('lgbm', LGBM_1),
                ('xgb', XGB_1),
                ('rf', RF_1),],
    voting='soft',
    verbose=False)

# Entrenamiento y validación
voting_clf.fit(X_train, y_train)
print(f'El modelo entrenado tiene un accuracy de {accuracy_score(y_test, voting_clf.predict(X_test))} sobre el test')
# ------------------------------------------------------------------------------------------------------------------------------------------------


# GUARDADO
joblib.dump(voting_clf, r'.\models\new_model.sav')

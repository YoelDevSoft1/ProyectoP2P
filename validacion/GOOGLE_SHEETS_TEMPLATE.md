# 📊 TEMPLATE GOOGLE SHEETS PARA TRACKING

## Cómo Crear tu Hoja de Tracking

### Paso 1: Crear Nueva Hoja
1. Ir a [Google Sheets](https://sheets.google.com)
2. Crear nueva hoja: "ProyectoP2P - Validación 30 Días"
3. Crear 4 pestañas (tabs):
   - **Dashboard**
   - **Oportunidades Diarias**
   - **Predicciones ML**
   - **Resumen Semanal**

---

## 📋 PESTAÑA 1: Dashboard

### Columnas:
```
A: Fecha
B: Trades Hoy (sistema)
C: Profit Hoy (sistema)
D: Oportunidades Detectadas
E: Oportunidades Verificadas
F: % Reales
G: Profit Potencial (manual)
H: Notas
```

### Ejemplo de Datos:
```
Fecha       | Trades | Profit   | Detectadas | Verificadas | % Reales | Profit Pot | Notas
2025-11-11  | 50     | $80,494  | 0          | 0           | -        | $0         | Día inicial
2025-11-12  | 55     | $85,230  | 5          | 4           | 80%      | $45        | 4/5 eran reales
2025-11-13  | 48     | $78,120  | 8          | 6           | 75%      | $67        | Buenas oportunidades
```

### Fórmulas Útiles:
```
% Reales (columna F):
=IF(D2>0, E2/D2, 0)

Total del Mes:
=SUM(B2:B31)  // En celda abajo de la columna

Promedio:
=AVERAGE(B2:B31)
```

---

## 📋 PESTAÑA 2: Oportunidades Diarias

### Columnas:
```
A: Fecha/Hora
B: Par (USDT/COP, etc)
C: Tipo (Spot→P2P, Triangle, etc)
D: Precio Buy (sistema)
E: Precio Sell (sistema)
F: Spread % (sistema)
G: Precio Buy (Binance real)
H: Precio Sell (Binance real)
I: Spread % (real)
J: Ejecutable? (Sí/No)
K: Profit Potencial ($1000)
L: Notas
```

### Ejemplo:
```
Fecha/Hora      | Par       | Tipo    | Buy(S) | Sell(S) | Spread(S) | Buy(R) | Sell(R) | Spread(R) | Ejecutable | Profit | Notas
2025-11-12 9:15 | USDT/COP  | Spot→P2P| 4,120  | 4,185   | 1.58%     | 4,118  | 4,182   | 1.55%     | Sí        | $15.50 | Verificado ✓
2025-11-12 10:30| USDT/VES  | Triangle| 36.2   | 36.8    | 1.66%     | 36.3   | 36.6    | 0.83%     | No        | $8.30  | Spread menor
```

### Cómo Llenar:
1. Sistema detecta oportunidad → Copiar columnas A-F
2. Abrir Binance → Verificar precios reales → Llenar G-H
3. Calcular spread real (I) = (H-G)/G * 100
4. Decidir si es ejecutable (J) = Si spread real >0.5%
5. Calcular profit (K) = $1000 * (I/100) - fees
6. Agregar notas (L)

---

## 📋 PESTAÑA 3: Predicciones ML

### Columnas:
```
A: Fecha Predicción
B: Hora
C: Par
D: Precio Predicho
E: Spread Predicho (%)
F: Confidence
G: Precio Real (24h después)
H: Spread Real (24h después)
I: Error Precio (%)
J: Correcto? (Sí/No)
K: Notas
```

### Ejemplo:
```
Fecha Pred  | Hora  | Par      | Pred  | Spread | Conf | Real  | S.Real | Error | Correcto | Notas
2025-11-12  | 09:00 | USDT/COP | 4,150 | 1.2%   | 78%  | 4,145 | 1.1%   | -0.12%| Sí       | Dentro margen
2025-11-13  | 09:00 | USDT/COP | 4,160 | 1.3%   | 65%  | 4,180 | 1.5%   | +0.48%| No       | Subió más
```

### Fórmulas:
```
Error % (columna I):
=(G2-D2)/D2*100

Correcto (columna J):
=IF(ABS(I2)<5%, "Sí", "No")

Accuracy Total:
=COUNTIF(J:J,"Sí")/COUNTA(J:J)  // Al final de columna
```

---

## 📋 PESTAÑA 4: Resumen Semanal

### Formato:
```
SEMANA 1 (Nov 11-17)
========================

Métricas del Sistema:
- Total Trades: XXX
- Profit Tracked: $XX,XXX
- Promedio/día: $X,XXX

Oportunidades:
- Detectadas: XXX
- Verificadas: XXX
- % Reales: XX%
- Profit Potencial: $X,XXX

Predicciones ML:
- Total: XX
- Accuracy: XX%
- Error Promedio: X.XX%

Win Rate (Paper Trading):
- Oportunidades ejecutables: XX
- Hubieran sido rentables: XX
- Win Rate: XX%

ROI Estimado:
- Con $1,000 capital: $XXX (XX%)
- Con $10,000 capital: $X,XXX (XX%)

Problemas/Blockers:
- [Lista]

Aprendizajes:
- [Lista]

Próxima Semana:
- [Tareas]
```

---

## 📊 GRÁFICOS RECOMENDADOS

### Gráfico 1: Equity Curve (Paper Trading)
- **Tipo**: Línea
- **Eje X**: Fecha
- **Eje Y**: Profit Acumulado
- **Datos**: Suma acumulada de columna G (Dashboard)

### Gráfico 2: Win Rate Diario
- **Tipo**: Columnas
- **Eje X**: Fecha
- **Eje Y**: % de Oportunidades Reales
- **Datos**: Columna F (Dashboard)

### Gráfico 3: Accuracy ML
- **Tipo**: Pastel (Pie)
- **Categorías**: Correctas vs Incorrectas
- **Datos**: Columna J (Predicciones ML)

### Gráfico 4: Profit Potencial por Tipo
- **Tipo**: Barras
- **Categorías**: Spot→P2P, Triangle, etc
- **Eje Y**: Suma de Profit
- **Datos**: Agrupado de Oportunidades Diarias

---

## 🎯 INDICADORES CLAVE (KPIs)

### En Dashboard Tab:
```
═══════════════════════════════
        RESUMEN 30 DÍAS
═══════════════════════════════

Total Oportunidades:    [=COUNTA(D:D)-1]
Verificadas Reales:     [=SUM(E:E)]
% Accuracy:             [=SUM(E:E)/COUNTA(D:D)-1]

Profit Potencial Total: [=SUM(G:G)]
Promedio por Opp:       [=AVERAGE(G:G)]

Mejor Día:              [=MAX(G:G)]
Fecha Mejor Día:        [=INDEX(A:A,MATCH(MAX(G:G),G:G,0))]

ML Accuracy:            [Ver Predicciones!XX]
```

---

## 📱 COMPARTIR HOJA (Opcional)

### Para Beta Testers:
1. Crear copia de la hoja
2. Compartir como "Ver solamente"
3. Link público para transparencia

### Para Público (Después de 30 días):
1. Crear versión resumida
2. Solo Dashboard y Gráficos
3. Sin datos sensibles

---

## 🔄 PROCESO DIARIO (5-10 min)

### Cada Mañana (9 AM):
1. Correr `python monitor_system.py`
2. Revisar `daily_logs/summary_FECHA.md`
3. Copiar métricas a Dashboard tab
4. Si hay oportunidades, ir a Binance
5. Verificar manualmente
6. Llenar Oportunidades Diarias tab

### Cada Semana (Domingo):
1. Calcular totales semanales
2. Crear gráficos
3. Llenar Resumen Semanal tab
4. Identificar patrones
5. Ajustar estrategia si necesario

---

## 📋 TEMPLATE DESCARGABLE

### Opción 1: Crear desde Cero
Usa las columnas arriba y crea tu hoja

### Opción 2: Link a Template (Una vez que lo hagas)
Puedes crear tu template y guardarlo como "Template - ProyectoP2P Validation"

---

## 🎓 TIPS

### Tip 1: Formato Condicional
```
En columna F (% Reales):
- Verde si >70%
- Amarillo si 50-70%
- Rojo si <50%

Formato → Formato condicional → Escala de colores
```

### Tip 2: Proteger Fórmulas
```
Seleccionar celdas con fórmulas
→ Datos → Proteger hoja
→ Permitir edición de celdas específicas
```

### Tip 3: Validación de Datos
```
Columna J (Ejecutable):
→ Datos → Validación de datos
→ Lista: "Sí,No"
```

### Tip 4: Backup Automático
```
Google Sheets hace backup automático
Pero además:
- Archivo → Historial de versiones
- Ver cambios anteriores
```

---

## ✅ CHECKLIST DE SETUP

- [ ] Crear Google Sheet nueva
- [ ] Crear 4 pestañas
- [ ] Configurar columnas Dashboard
- [ ] Configurar columnas Oportunidades
- [ ] Configurar columnas Predicciones ML
- [ ] Configurar Resumen Semanal
- [ ] Agregar fórmulas básicas
- [ ] Crear 2-3 gráficos
- [ ] Testear con datos de ejemplo
- [ ] Listo para tracking real

---

**Tiempo Setup**: 30-45 minutos
**Tiempo Diario**: 5-10 minutos
**Valor**: Tracking preciso, evidencia verificable, análisis visual

---

**Última actualización**: 2025-11-11

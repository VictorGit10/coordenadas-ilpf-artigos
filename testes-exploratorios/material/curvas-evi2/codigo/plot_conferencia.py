# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MESES = ['Out', 'Nov', 'Dez', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out+1']
d = pd.read_csv('validacao_20.csv')
sel = [28, 16, 747, 17, 66, 1120]
fig, axes = plt.subplots(2, 3, figsize=(13, 7))
x = np.arange(13)
for ax, ID in zip(axes.ravel(), sel):
    r = d[d.ID == ID].iloc[0]
    csv = [r[f'csv_{i:02d}'] for i in range(1, 14)]
    calc = [r[f'calc_{i:02d}'] for i in range(1, 14)]
    ax.plot(x, csv, 'o', ms=6, mfc='white', mec='#c53030', mew=1.6, label='Planilha', zorder=3)
    ax.plot(x, calc, '-', color='#2b6cb0', lw=2.0, label='Calculado', zorder=2)
    ax.set_title(f"ID {ID} — classe {int(r['classe'])} — {r['cropYear']}\nMAD={r['mad']:.2e}  r={r['corr']:.6f}", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(MESES, fontsize=7, rotation=45)
    ax.grid(alpha=0.2)
    if ID == 28:
        ax.legend(fontsize=8, frameon=False, loc='upper left')
fig.suptitle('Conferência do método: planilha (círculos) × nosso cálculo (linha) — 6 registros', fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig('conferencia_6.png', dpi=200)
print('ok')

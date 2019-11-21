df.set_index('date')
df.groupby('date').mean().plot()
df.plot(x='date', y='star_pu.oral_antibacterials_item')
plt.legend(loc='center left', bbox_to_anchor=(1.0,0.5))

df.set_index('date')
df.groupby('date')['star_pu.oral_antibacterials.item'].mean().plot()
plt.legend(loc='center left', bbox_to_anchor=(1.0,0.5))

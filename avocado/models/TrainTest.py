import numpy as np
from time import gmtime, strftime
import matplotlib.pyplot as plt

from sklearn.gaussian_process import GaussianProcessRegressor
import sklearn.gaussian_process.kernels as Kernels
import sklearn.metrics
import scipy.stats
import os
import pandas as pd
import datetime

from avocado.utils.data import get_data
 

region = 'WestTexNewMexico'
df, X_train, y_train, X_test, y_test = get_data(region=region)

# print(df)



#print(df.head())
#print(df.groupby(df.index.year).describe())


# gp_kernel = Kernels.ExpSineSquared(2.0, 6.0, periodicity_bounds=(1e-2, 1e5)) \
#     + Kernels.WhiteKernel() \
#     + Kernels.RBF() \
#     + Kernels.Matern() \
#     + Kernels.RationalQuadratic() \
#     + Kernels.WhiteKernel(1e-1)

# periodicity of 358 is 1 year. performs poorly on test
# Best: 100., 200.
gp_kernel = Kernels.ExpSineSquared(20., periodicity=358., periodicity_bounds=(1e-2, 1e8)) \
    + 0.8 * Kernels.RationalQuadratic(alpha=20., length_scale=80.) \
    + Kernels.WhiteKernel(1e2)

gpr = GaussianProcessRegressor(kernel=gp_kernel, normalize_y=True, n_restarts_optimizer=10)
gpr.fit(X_train, y_train)

# Predict using gaussian process regressor
y_gpr_train, y_std_train = gpr.predict(X_train, return_std=True)
y_gpr_test, y_std_test = gpr.predict(X_test, return_std=True)

# Plot results
y_gpr_train = y_gpr_train.flatten()
y_gpr_test = y_gpr_test.flatten()
y_train = y_train.flatten()
y_test = y_test.flatten()
X_train = X_train.flatten()
X_test = X_test.flatten()


rmse_train = np.sqrt(((y_gpr_train - y_train) ** 2).mean())
r_2_train = sklearn.metrics.r2_score(y_gpr_train, y_train)

rmse_test = np.sqrt(((y_gpr_test - y_test) ** 2).mean())
r_2_test = sklearn.metrics.r2_score(y_gpr_test, y_test)

print(f'Train RMSE: {rmse_train}')
print(f'Train R2 score: {r_2_train}')
print(f'Test RMSE: {rmse_test}')
print(f'Test R2 score: {r_2_test}')

z = 1.96
CI_lower_bound_train = y_gpr_train - z * y_std_train
CI_higher_bound_train = y_gpr_train + z * y_std_train

out_of_CI_ptc_train = np.sum((y_train < CI_lower_bound_train) | (y_train > CI_higher_bound_train)) / len(y_train) * 100

CI_lower_bound_test = y_gpr_test - z * y_std_test
CI_higher_bound_test = y_gpr_test + z * y_std_test

out_of_CI_ptc_test = np.sum((y_test < CI_lower_bound_test) | (y_test > CI_higher_bound_test)) / len(y_test) * 100

print(f'Train CI ptc: {out_of_CI_ptc_train}')
print(f'Test CI ptc: {out_of_CI_ptc_test}')

print(f'Model: {str(gpr.kernel_)}')

# Plotting

fig, ax = plt.subplots(figsize=(10, 5))

plt.scatter(X_train, y_train, c='k', s=10, label='Train')
plt.scatter(X_test, y_test, c='r', s=10, label='Test')
plt.plot(X_train, y_gpr_train, color='darkorange', lw=2, label='GP')
plt.plot(X_test, y_gpr_test, color='darkorange', lw=2)
plt.fill_between(X_train, CI_lower_bound_train, CI_higher_bound_train, color='blue', alpha=0.2, label='95% PPC interval')
plt.fill_between(X_test, CI_lower_bound_test, CI_higher_bound_test, color='blue', alpha=0.2)
plt.fill_between(X_train, y_gpr_train - y_std_train, y_gpr_train + y_std_train, color='blue', alpha=0.4, label='GP stdev')
plt.fill_between(X_test, y_gpr_test - y_std_test, y_gpr_test + y_std_test, color='blue', alpha=0.4)
plt.xlabel('Time (Weekly)')
plt.ylabel('Average Avocado Price (USD)')
plt.title(f'GPR: {region} Organic Avocado Price')

xticks = list(df.index.strftime('%m-%d-%Y'))
# Only show every 10th tick
for i in range(len(xticks)):
    if i % 10:
        xticks[i] = ''

plt.xticks(np.concatenate((X_train, X_test)), labels=xticks)

# Rotates x axis date labels by 45 degrees
for label in ax.xaxis.get_ticklabels():
    label.set_rotation(45)

#ax.set_ylim(bottom=np.min(np.concatenate((y_train, y_test))), top=np.max(np.concatenate((y_train, y_test))))

plt.legend(loc='upper left', scatterpoints=1, prop={'size': 8})

#plt.grid(which='both', alpha=0.5)
plt.grid(linewidth=0.25, alpha=0.5)
plt.subplots_adjust(bottom=0.22)
plt.savefig(f'figures/GPR_{strftime("%Y_%m_%d_%H_%M_%S", gmtime())}.png')
plt.show()

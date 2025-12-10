import numpy as np
import matplotlib.pyplot as plt
import os

# Check if data file exists 
if not os.path.exists('data.csv'):
    print("Error: data.csv file does not exist. Please run simulate_data.py first to generate data.")
    exit(1)

# Load data from file
data = np.loadtxt('data.csv', delimiter=',')

# Calculate basic statistics
mean_value = np.mean(data)
median_value = np.median(data)
std_value = np.std(data)

# Print statistical results
print("Data Analysis Results:")
print(f"Number of data points: {len(data)}")
print(f"Mean: {mean_value:.2f}")
print(f"Median: {median_value:.2f}")
print(f"Standard deviation: {std_value:.2f}")
print(f"Minimum: {np.min(data):.2f}")
print(f"Maximum: {np.max(data):.2f}")
print(f"First quartile (25%): {np.percentile(data, 25):.2f}")
print(f"Third quartile (75%): {np.percentile(data, 75):.2f}")

# Plot histogram
plt.figure(figsize=(12, 8))

# First subplot - Basic histogram
plt.subplot(2, 2, 1)
plt.hist(data, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
plt.title('Data Distribution Histogram')
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.grid(True, alpha=0.3)

# Second subplot - Histogram with statistical information
plt.subplot(2, 2, 2)
plt.hist(data, bins=30, alpha=0.7, color='lightgreen', edgecolor='black')
plt.axvline(mean_value, color='red', linestyle='dashed', linewidth=2, label=f'Mean: {mean_value:.2f}')
plt.axvline(median_value, color='blue', linestyle='dashed', linewidth=2, label=f'Median: {median_value:.2f}')
plt.title('Histogram with Statistical Information')
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.legend()
plt.grid(True, alpha=0.3)

# Third subplot - Box plot
plt.subplot(2, 2, 3)
plt.boxplot(data, vert=False)
plt.title('Box Plot')
plt.grid(True, alpha=0.3)

# Fourth subplot - Q-Q plot
from scipy import stats
plt.subplot(2, 2, 4)
stats.probplot(data, dist="norm", plot=plt)
plt.title('Q-Q Plot (Normality Test)')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('analysis_plots.png')
print("Analysis plots have been saved to analysis_plots.png")
plt.show()
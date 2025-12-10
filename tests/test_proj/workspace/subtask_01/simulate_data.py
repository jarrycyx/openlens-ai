import numpy as np
import matplotlib.pyplot as plt
import os

# Set random seed for reproducible results
np.random.seed(42)

# Generate normally distributed data
mean = 100
std_dev = 15
sample_size = 1000

data = np.random.normal(mean, std_dev, sample_size)

# Save data to current directory
np.savetxt('data.csv', data, delimiter=',')

# Print basic statistical information of the data
print(f"Generated {sample_size} normally distributed data points")
print(f"Mean: {np.mean(data):.2f}")
print(f"Standard deviation: {np.std(data):.2f}")
print(f"Minimum: {np.min(data):.2f}")
print(f"Maximum: {np.max(data):.2f}")
print(f"Data has been saved to data.csv")

# Plot and save histogram
plt.figure(figsize=(10, 6))
plt.hist(data, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
plt.title('Histogram of Normally Distributed Data')
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.grid(True, alpha=0.3)
plt.savefig('data_histogram.png')
print("Histogram has been saved to data_histogram.png")
plt.show()
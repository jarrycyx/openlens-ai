import numpy as np
import matplotlib.pyplot as plt
import os
from scipy import stats

def load_data(file_path='data.csv'):
    """Load data file   """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Error: {file_path} file does not exist. Please run simulate_data.py first to generate data.")
    return np.loadtxt(file_path, delimiter=',')

def calculate_statistics(data):
    """Calculate basic statistics"""
    stats_dict = {
        'count': len(data),
        'mean': np.mean(data),
        'median': np.median(data),
        'std': np.std(data),
        'min': np.min(data),
        'max': np.max(data),
        'q1': np.percentile(data, 25),
        'q3': np.percentile(data, 75),
        'skewness': stats.skew(data),
        'kurtosis': stats.kurtosis(data)
    }
    return stats_dict

def print_statistics(stats_dict):
    """Print statistical results"""
    print("Data Analysis Results:")
    print(f"Number of data points: {stats_dict['count']}")
    print(f"Mean: {stats_dict['mean']:.2f}")
    print(f"Median: {stats_dict['median']:.2f}")
    print(f"Standard deviation: {stats_dict['std']:.2f}")
    print(f"Minimum: {stats_dict['min']:.2f}")
    print(f"Maximum: {stats_dict['max']:.2f}")
    print(f"First quartile (25%): {stats_dict['q1']:.2f}")
    print(f"Third quartile (75%): {stats_dict['q3']:.2f}")
    print(f"Skewness: {stats_dict['skewness']:.2f}")
    print(f"Kurtosis: {stats_dict['kurtosis']:.2f}")

def create_histogram(data, stats_dict, bins=30):
    """Create histogram"""
    plt.figure(figsize=(12, 8))
    
    # First subplot - Basic histogram
    plt.subplot(2, 2, 1)
    n, bins_edges, patches = plt.hist(data, bins=bins, alpha=0.7, color='skyblue', edgecolor='black')
    plt.title('Data Distribution Histogram')
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    
    # Second subplot - Histogram with statistical information
    plt.subplot(2, 2, 2)
    plt.hist(data, bins=bins, alpha=0.7, color='lightgreen', edgecolor='black')
    plt.axvline(stats_dict['mean'], color='red', linestyle='dashed', linewidth=2, 
                label=f'Mean: {stats_dict["mean"]:.2f}')
    plt.axvline(stats_dict['median'], color='blue', linestyle='dashed', linewidth=2, 
                label=f'Median: {stats_dict["median"]:.2f}')
    plt.axvline(stats_dict['q1'], color='orange', linestyle='dotted', linewidth=2, 
                label=f'Q1: {stats_dict["q1"]:.2f}')
    plt.axvline(stats_dict['q3'], color='purple', linestyle='dotted', linewidth=2, 
                label=f'Q3: {stats_dict["q3"]:.2f}')
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
    plt.subplot(2, 2, 4)
    stats.probplot(data, dist="norm", plot=plt)
    plt.title('Q-Q Plot (Normality Test)')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return plt

def main():
    """Main function"""
    try:
        # Load data
        data = load_data()
        
        # Calculate statistics
        stats_dict = calculate_statistics(data)
        
        # Print statistical results
        print_statistics(stats_dict)
        
        # Create and save plots
        plt = create_histogram(data, stats_dict)
        plt.savefig('improved_analysis_plots.png', dpi=300, bbox_inches='tight')
        print("Analysis plots have been saved to improved_analysis_plots.png")
        plt.show()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
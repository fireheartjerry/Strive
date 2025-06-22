import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Benchmark constraints
BENCHMARKS = {
    'ear_neck_hip': {'min': 110, 'max': 180},
    'neck_hip_knee': {'min': 40, 'max': 160},
    'hip_knee_ankle': {'min': 150, 'max': 200},
}

# Sample data
DATA = [
    {'subject': 'Alex',        'trial': 1, 'ear_neck_hip': 141.3, 'neck_hip_knee': 131.9, 'hip_knee_ankle': 178.5, 'global_angle': 165.0},
    {'subject': 'Alex',        'trial': 2, 'ear_neck_hip': 123.9, 'neck_hip_knee': 124.6, 'hip_knee_ankle': 173.7, 'global_angle': 160.2},
    {'subject': 'Alex',        'trial': 3, 'ear_neck_hip': 145.3, 'neck_hip_knee': 134.5, 'hip_knee_ankle': 168.9, 'global_angle': 162.7}
]


def ingest_data(data_list):
    """Convert raw data list into pandas DataFrame."""
    df = pd.DataFrame(data_list)
    return df


def compute_statistics(df):
    """Compute mean, median, min, max, std, variance for each metric."""
    stats = df[['ear_neck_hip', 'neck_hip_knee', 'hip_knee_ankle']].agg(
        ['mean', 'median', 'min', 'max', 'std', 'var']
    ).transpose()
    return stats


def compute_compliance(df, benchmarks):
    """Calculate compliance percentage within benchmark ranges for each metric."""
    compliance = {}
    total = len(df)
    for metric, limits in benchmarks.items():
        col = df[metric]
        within = col.between(limits['min'], limits['max'])
        compliance[metric] = within.sum() / total * 100
    return compliance


def generate_report(df, stats, compliance):
    """Print a comprehensive report to console."""
    print("=== Plank Pose Analysis Report ===")
    print("\nDescriptive Statistics:")
    print(stats.to_string(), "\n")
    print("Compliance with Benchmarks (% of frames within range):")
    for metric, pct in compliance.items():
        print(f"- {metric}: {pct:.1f}%")
    print("\nSummary Insights:")
    for metric, pct in compliance.items():
        if pct > 90:
            print(f"{metric} met benchmark in {pct:.1f}% of frames — excellent consistency.")
        elif pct > 70:
            print(f"{metric} met benchmark in {pct:.1f}% of frames — acceptable but room for improvement.")
        else:
            print(f"{metric} met benchmark in only {pct:.1f}% of frames — suggests form issues.")


def visualize_data(df):
    """Optional: create line charts and histograms for each metric."""
    metrics = ['ear_neck_hip', 'hip_ankle_slope', 'global_angle', 'arm_angle']
    fig, axes = plt.subplots(len(metrics), 2, figsize=(10, 8))
    for i, metric in enumerate(metrics):
        # time series
        df[metric].plot(ax=axes[i,0], title=f"{metric} over Trials")
        # histogram
        df[metric].hist(ax=axes[i,1], bins=10)
        axes[i,0].axhline(BENCHMARKS[metric.upper()]['min'], color='r', linestyle='--')
        axes[i,0].axhline(BENCHMARKS[metric.upper()]['max'], color='r', linestyle='--')
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    df = ingest_data(DATA)
    stats = compute_statistics(df)
    compliance = compute_compliance(df, BENCHMARKS)
    generate_report(df, stats, compliance)
    # To visualize uncomment:
    # visualize_data(df)

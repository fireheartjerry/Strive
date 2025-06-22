import argparse
import json
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, classification_report, accuracy_score
from sklearn.ensemble import RandomForestClassifier
import joblib

def load_reps_from_directory(directory):
    """
    Load all JSON files in the directory and extract 'reps' entries.
    Returns a list of rep dicts with added 'source_file' field.
    """
    all_reps = []
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Input directory {directory} does not exist")
    for file in directory.glob("*.json"):
        try:
            with open(file, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Warning: Skipping file {file} due to read/JSON error: {e}")
            continue
        reps = data.get("reps", [])
        if not isinstance(reps, list):
            print(f"Warning: 'reps' not list in file {file}, skipping")
            continue
        for rep in reps:
            rep['source_file'] = file.name
            all_reps.append(rep)
    return all_reps

def flatten_reps(reps):
    """
    Flatten nested rep structure into a DataFrame row per rep.
    """
    flat_data = []
    for rep in reps:
        row = {
            "source_file": rep.get("source_file"),
            "rep_number": rep.get("rep_number"),
            "duration_sec": rep.get("duration_sec"),
            "valid_rep": rep.get("valid_rep")
        }
        # down/up metrics
        for phase in ["down", "up"]:
            phase_data = rep.get(phase, {})
            if isinstance(phase_data, dict):
                for key, value in phase_data.items():
                    if key == "frame":
                        continue
                    # prefix with phase name
                    row[f"{phase}_{key}"] = value
        # range_of_motion metrics
        rom = rep.get("range_of_motion", {})
        if isinstance(rom, dict):
            for key, value in rom.items():
                row[f"rom_{key}"] = value
        # timestamp fields: convert if present (ms since epoch or ISO)
        ts_start = rep.get("timestamp_start")
        ts_end = rep.get("timestamp_end")
        for ts_label, ts in [("timestamp_start", ts_start), ("timestamp_end", ts_end)]:
            if ts is None:
                row[ts_label] = np.nan
            else:
                # if numeric epoch in ms
                if isinstance(ts, (int, float)):
                    try:
                        dt = datetime.fromtimestamp(ts / 1000.0)
                        row[ts_label] = dt
                    except:
                        row[ts_label] = np.nan
                else:
                    # try parse ISO string
                    try:
                        row[ts_label] = pd.to_datetime(ts)
                    except:
                        row[ts_label] = np.nan
        flat_data.append(row)
    df = pd.DataFrame(flat_data)
    return df

def feature_engineering(df):
    """
    Ensure necessary features exist; compute derived features if missing.
    """
    # Example: if rom_elbow_delta missing, compute from up/down angles if present
    if "rom_elbow_delta" not in df.columns and {"down_elbow_angle", "up_elbow_angle"}.issubset(df.columns):
        df["rom_elbow_delta"] = df["up_elbow_angle"] - df["down_elbow_angle"]
    if "rom_shoulder_delta" not in df.columns and {"down_shoulder_angle", "up_shoulder_angle"}.issubset(df.columns):
        df["rom_shoulder_delta"] = df["up_shoulder_angle"] - df["down_shoulder_angle"]
    if "rom_hip_delta" not in df.columns and {"down_hip_angle", "up_hip_angle"}.issubset(df.columns):
        df["rom_hip_delta"] = df["up_hip_angle"] - df["down_hip_angle"]
    if "rom_chest_displacement" not in df.columns and {"down_chest_y", "up_chest_y"}.issubset(df.columns):
        df["rom_chest_displacement"] = df["down_chest_y"] - df["up_chest_y"]
    # Additional derived: speed: rep duration is available; rate: ROM/duration
    if "duration_sec" in df.columns:
        for rom_col in ["rom_elbow_delta", "rom_shoulder_delta", "rom_hip_delta", "rom_chest_displacement"]:
            if rom_col in df.columns:
                df[f"{rom_col}_rate"] = df[rom_col] / df["duration_sec"].replace({0: np.nan})
    return df

def train_clustering(df, features, output_dir, k_range=(2,5)):
    """
    Perform KMeans clustering on valid reps, choose best k by silhouette score.
    Save cluster centers as benchmarks.
    """
    X = df[features].dropna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    best_k = None
    best_score = -1
    best_model = None
    for k in range(k_range[0], k_range[1]+1):
        model = KMeans(n_clusters=k, random_state=42)
        labels = model.fit_predict(X_scaled)
        if len(set(labels)) > 1:
            score = silhouette_score(X_scaled, labels)
            print(f"KMeans with k={k}, silhouette={score:.3f}")
            if score > best_score:
                best_score = score
                best_k = k
                best_model = model
    if best_model is None:
        print("Clustering: no valid clustering found.")
        return None, None, None
    # Save scaler and model
    scaler_path = Path(output_dir) / "scaler_clustering.joblib"
    model_path = Path(output_dir) / "kmeans_model.joblib"
    joblib.dump(scaler, scaler_path)
    joblib.dump(best_model, model_path)
    # Extract cluster centers in original feature space
    centers_scaled = best_model.cluster_centers_
    centers = scaler.inverse_transform(centers_scaled)
    benchmarks_df = pd.DataFrame(centers, columns=features)
    benchmarks_df["cluster_id"] = range(len(centers))
    benchmarks_path = Path(output_dir) / "pushup_cluster_benchmarks.csv"
    benchmarks_df.to_csv(benchmarks_path, index=False)
    print(f"Saved clustering scaler to {scaler_path}") 
    print(f"Saved KMeans model to {model_path}") 
    print(f"Saved cluster benchmarks to {benchmarks_path}") 
    return scaler, best_model, benchmarks_df

def train_classifier(df, features, output_dir):
    """
    Train a classifier to predict valid_rep if labels exist.
    Use RandomForestClassifier. Save model and scaler.
    """
    if "valid_rep" not in df.columns:
        print("No 'valid_rep' column; skipping classifier training.")
        return None, None
    df_label = df.dropna(subset=["valid_rep"])
    if df_label["valid_rep"].nunique() < 2:
        print("valid_rep has only one class; skipping classifier training.")
        return None, None
    X = df_label[features].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    y = df_label["valid_rep"].astype(int)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_scaled, y)
    y_pred = clf.predict(X_scaled)
    print("Classifier training results:") 
    print(classification_report(y, y_pred))
    # Save scaler and model
    scaler_path = Path(output_dir) / "scaler_classifier.joblib"
    model_path = Path(output_dir) / "rf_classifier.joblib"
    joblib.dump(scaler, scaler_path)
    joblib.dump(clf, model_path)
    print(f"Saved classifier scaler to {scaler_path}") 
    print(f"Saved classifier model to {model_path}") 
    return scaler, clf

def main():
    parser = argparse.ArgumentParser(description="Push-Up Data Analysis and Model Training")
    parser.add_argument("--input_dir", type=str, required=True, help="Directory with pushup JSON files")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save analysis outputs and models")
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Load and flatten data
    reps = load_reps_from_directory(input_dir)
    if not reps:
        print("No reps found in input directory.")
        return
    df = flatten_reps(reps)
    df = feature_engineering(df)

    # Inspect numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    print("Numeric columns available for analysis:", numeric_cols)

    # Select features: ROM, angles, slopes, rates if available
    features = [col for col in numeric_cols if col.startswith("rom_") or col.endswith("_angle") or col.endswith("_slope") or col.endswith("_rate")]
    print("Selected features for modeling:", features)
    if not features:
        print("No suitable numeric features found; aborting.")
        return

    # Clustering on valid reps only
    df_valid = df[df.get("valid_rep", True) == True]
    if df_valid.empty:
        print("No valid reps to cluster; skipping clustering.")
    else:
        print("Training clustering on valid reps...")
        train_clustering(df_valid, features, output_dir)

    # Classifier training if valid_rep labels exist
    print("Training classifier if possible...")
    train_classifier(df, features, output_dir)

    # Save flattened DataFrame to CSV for inspection
    csv_path = Path(output_dir) / "pushup_flattened_data.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved flattened data to {csv_path}")

if __name__ == "__main__":
    main()


import pandas as pd
from pathlib import Path
from .classifier import classify_pipeline

def main():
    """
    Evaluate the classifier against a labeled 'golden set'
    and compute accuracy.

    This script expects a CSV file shaped like:

        description,true_category

    Example row:
        "uber trip to airport",Travel
    """
    df = pd.read_csv(Path(__file__).resolve().parents[1] / "data" / "golden_set.csv")
    correct = 0
    total = 0
    for _, row in df.iterrows():
        res, _, _, _, _ = classify_pipeline(row["description"])
        total += 1
        if res["category"] == row["true_category"]:
            correct += 1
    print("Accuracy:", correct/total if total else 0)

if __name__ == "__main__":
    main()

"""
To avoid shipping un-validated changes, I built an evaluation script that runs the full production pipeline against a labeled golden dataset. I trigger it manually during development to measure accuracy and detect regressions before deployment.
"""
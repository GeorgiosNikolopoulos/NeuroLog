from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import argparse


def main():
    
    pd.set_option('display.max_columns', None)
    df = pd.read_csv(file, sep="\t", dtype={
        "project" : "string",
        "severity": "string",
        "msg": "string"
    }, na_filter=False)
    #print(df.info())
    df["msgLength"] = df.apply(lambda row : len(row.msg), axis=1)
    
    print(f"Total Number of logs: {len(df)}")
    print(f"Average msg length: {df['msgLength'].mean().round(2)}")
    print(f"Min msg length: {df['msgLength'].min()}")
    print(f"Max msg length: {df['msgLength'].max()}")
    
    print("Severity levels follow")
    print(orderDataFrameBySeverity(df.groupby(["severity"]).count()["msg"]).to_string())

    ax = df[df["msgLength"] <= 200].hist(column="msgLength",grid=False, bins=12, zorder=2, rwidth=0.9)[0][0]

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.set_title("")
    ax.set_xlabel("Message length (chars)", labelpad=20, weight='bold', size=10)
    ax.set_ylabel("Logs", labelpad=20, weight="bold", size=10)

    vals = ax.get_yticks()
    for tick in vals:
        ax.axhline(y=tick, linestyle='dashed', alpha=0.4, color='#eeeeee', zorder=1)

    plt.show()

    containMethod = df[df["msg"].str.contains("\..*\(.*\)",regex=True)]
    print(f"Number of logs that contain methods: {len(containMethod)}")

    containTextOnly = df[df["msg"].str.contains('"[a-z:=()\- ,A-Z]+"' ,regex=True)]
    print(f"Number of logs that contain text only: {len(containTextOnly)}")

    print("Msg average length per severity follows")
    print(df.groupby(["severity"])["msgLength"].mean().round(2).to_string())
    
    print("Logs per project follow")
    print(df.groupby(["project"])["msg"].count().to_string())

    print("Breakdown of project log severity follow")
    print(df.groupby(["project", "severity"])["msg"].count().to_string())

def orderDataFrameBySeverity(df):
    return df[["trace", "debug", "info", "warn", "error", "fatal"]]

if __name__ == "__main__":
    # use argparser to set up all argument parsing
    parser = argparse.ArgumentParser(description="Analyze a generated TSV file to display statistics ")
    parser.add_argument("input_tsv", help="TSV input (tab-seperated csv)",
                        type=str)
    args = parser.parse_args()
    file = Path(args.input_tsv)
    main()
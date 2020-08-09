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
    severityFrame = orderDataFrameBySeverity(df.groupby(["severity"]).count()["msg"])
    print(severityFrame.to_string())
    
    ax = severityFrame.plot(kind="bar")
    ax.set_xlabel("Severity")
    ax.set_ylabel("Logs")
    
    df[df["msgLength"] <= 200].plot.hist(by="msgLength")
    plt.show()
    
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
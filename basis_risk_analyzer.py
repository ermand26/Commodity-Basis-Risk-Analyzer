import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

def fetch_real_commodity_data(ticker_front, ticker_back, period="1y"):
    """
    Fetches real historical closing prices for front-month and back-month futures.
    Front-month acts as our 'Spot' proxy, and back-month acts as our 'Futures' hedge contract.
    """
    print(f"[Data Retrieval] Downloading data for {ticker_front} and {ticker_back} via yfinance...")
    
    # Download data from Yahoo Finance API
    data_front = yf.download(ticker_front, period=period)
    data_back = yf.download(ticker_back, period=period)
    
    # Handle multi-index columns if returned by modern yfinance versions
    if isinstance(data_front.columns, pd.MultiIndex):
        front_series = data_front['Close'][ticker_front]
        back_series = data_back['Close'][ticker_back]
    else:
        front_series = data_front['Close']
        back_series = data_back['Close']
        
    # Standardize dataframes to remove timezone structures
    front_series.index = front_series.index.tz_localize(None)
    back_series.index = back_series.index.tz_localize(None)

    # Merge datasets to align trading dates perfectly
    df = pd.DataFrame({
        "Spot_Proxy": front_series,
        "Futures_Hedge": back_series
    }).dropna() # Dropping non-overlapping market holidays
    
    return df

def analyze_basis_risk(df, commodity_name):
    """
    Calculates operational basis metrics based on real aligned data.
    """
    # Calculate Basis: Spot Proxy minus Futures Hedge
    df["Basis"] = df["Spot_Proxy"] - df["Futures_Hedge"]
    
    # Core Risk Aggregations
    mean_basis = df["Basis"].mean()
    basis_risk = df["Basis"].std() # Volatility of the spread represents basis risk
    
    print("=" * 60)
    print(f"    COMMODITY BASIS RISK ANALYTICS: {commodity_name.upper()}   ")
    print("=" * 60)
    print(f"Data Window Tracked: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"Average Spread Basis: ${mean_basis:.4f}")
    print(f"Basis Risk Volatility: ${basis_risk:.4f}")
    print(f"Max Contango Depth:    ${df['Basis'].min():.4f}")
    print(f"Max Backwardation Peak: ${df['Basis'].max():.4f}")
    print("=" * 60)
    
    return df, basis_risk

def plot_basis_analysis(df, commodity_name):
    """
    Generates an updated vector visual plot.
    """
    plt.figure(figsize=(12, 8))
    
    # Subplot 1: Price Tracking
    plt.subplot(2, 1, 1)
    plt.plot(df.index, df["Spot_Proxy"], label="Front Month (Spot Proxy)", color="darkblue", lw=1.5)
    plt.plot(df.index, df["Futures_Hedge"], label="Back Month (Hedge Contract)", color="crimson", linestyle="--", lw=1.5)
    plt.title(f"Real Market Trends: {commodity_name} Curve Structure")
    plt.ylabel("Price ($)")
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.5)
    
    # Subplot 2: Basis Spread Risk Zone
    plt.subplot(2, 1, 2)
    plt.plot(df.index, df["Basis"], label="Historical Spread (Basis)", color="forestgreen", lw=1.8)
    plt.axhline(df["Basis"].mean(), color="black", linestyle="-.", label=f"Mean Basis (${df['Basis'].mean():.2f})")
    
    # Compute standard deviation bands for structural risk
    plt.fill_between(df.index, df["Basis"].mean() - df["Basis"].std(), df["Basis"].mean() + df["Basis"].std(), 
                     color="forestgreen", alpha=0.15, label="Basis Risk Envelope (1-Sigma)")
    
    plt.title("Basis Evolution & Risk Volatility Envelope")
    plt.xlabel("Timeline Date")
    plt.ylabel("Basis Value ($)")
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.5)
    
    plt.tight_layout()
    plt.savefig("basis_risk_chart.png", dpi=300)
    print("[System] Production visualization successfully rendered to 'basis_risk_chart.png'")
    plt.show()

if __name__ == "__main__":
    # Choose your commodity. Example: US Crude Oil Futures (CL=F vs CL=F's back months)
    # For global portfolios: Front-Month vs Next-Quarter Contracts
    
    COMMODITY_LABEL = "Crude Oil (WTI)"
    FRONT_MONTH_TICKER = "CL=F"   # Front month contract
    BACK_MONTH_TICKER = "QM=F"    # E-mini Crude or back-month derivative asset tracking
    
    # Run pipeline
    market_data = fetch_real_commodity_data(FRONT_MONTH_TICKER, BACK_MONTH_TICKER, period="1y")
    analyzed_data, historical_risk = analyze_basis_risk(market_data, COMMODITY_LABEL)
    plot_basis_analysis(analyzed_data, COMMODITY_LABEL)

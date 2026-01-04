import os

def load_watchlist(file_path='watchlist.txt'):
    """
    Load tickers from a text file.
    Expected format: One ticker per line.
    """
    if not os.path.exists(file_path):
        # Default fallback if file missing
        return ['AAPL', 'NVDA', 'TSLA']
    
    with open(file_path, 'r') as f:
        tickers = [line.strip().upper() for line in f if line.strip()]
    
    return list(dict.fromkeys(tickers)) # Remove duplicates while preserving order

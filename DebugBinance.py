import ccxt

class DebugBinance(ccxt.binance):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_count = 0  # Initialize counter

    def request(self, path, api='public', method='GET', params={}, headers=None, body=None, **kwargs):
        self.request_count += 1
        print(f"[{self.request_count}] {method} {path} {params}")  # Short log
        return super().request(path, api, method, params, headers, body)

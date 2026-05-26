
import requests

class Palantir:
    
    def __init__(self, uri):
        self.uri = uri
        
    def get_scores(self):
        url = f"{self.uri}/predictions"
        response = requests.post(url, json={"model_name": "tmw_score_fiel"})
        return response.json()
        
        
    def get_features(self):
        url = f"{self.uri}/features"
        response = requests.post(url, json={"model_name": "tmw_score_fiel"})
        return response.json()
    
class Points:
    
    def __init__(self, uri):
        self.uri = uri
        
    def get_customers(self):
        url = f"{self.uri}/customers"
        response = requests.get(url)
        return response.json()
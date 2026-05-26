import copy
import json

class StockCache:
    def __init__(self, chemin_stock_json):
        self.chemin_stock_json = chemin_stock_json
        self._stock_original = self._charger_stock()
        self._stock_cache = copy.deepcopy(self._stock_original)

    def _charger_stock(self):
        with open(self.chemin_stock_json, encoding="utf-8") as f:
            return json.load(f)

    def reset_cache(self):
        self._stock_cache = copy.deepcopy(self._stock_original)

    def save(self):
        with open(self.chemin_stock_json, "w", encoding="utf-8") as f:
            json.dump(self._stock_cache, f, indent=2, ensure_ascii=False)
        self._stock_original = copy.deepcopy(self._stock_cache)

    def get_quantite(self, chemin):
        """chemin = liste de clés pour accéder à l'élément (ex: ['Plats', 'Pizza', 'Pâte à pizza'])"""
        ref = self._stock_cache
        for key in chemin:
            ref = ref[key]
        return ref.get("Quantité", None)

    def decrementer(self, chemin, n=1):
        ref = self._stock_cache
        for key in chemin[:-1]:
            ref = ref[key]
        elem = ref[chemin[-1]]
        if "Quantité" in elem and elem["Quantité"] >= n:
            elem["Quantité"] -= n
            if elem["Quantité"] == 0:
                elem["OutOfStock"] = True
            return True
        return False

    def incrementer(self, chemin, n=1):
        ref = self._stock_cache
        for key in chemin[:-1]:
            ref = ref[key]
        elem = ref[chemin[-1]]
        if "Quantité" in elem:
            elem["Quantité"] += n
            if elem["Quantité"] > 0:
                elem["OutOfStock"] = False
            return True
        return False

    def is_out_of_stock(self, chemin):
        ref = self._stock_cache
        for key in chemin:
            ref = ref[key]
        return ref.get("OutOfStock", False)
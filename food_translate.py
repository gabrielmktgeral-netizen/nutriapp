"""Tradução PT -> EN para os nomes de alimentos mais comuns, usada só para
pesquisar na API pública de receitas (TheMealDB), que funciona em inglês."""

PT_TO_EN = {
    "frango": "chicken", "peito de frango": "chicken breast", "carne de vaca": "beef",
    "bife": "beef", "porco": "pork", "lombo de porco": "pork loin", "peixe": "fish",
    "salmao": "salmon", "salmão": "salmon", "atum": "tuna", "bacalhau": "cod",
    "pescada": "hake", "ovo": "egg", "ovos": "egg", "arroz": "rice",
    "arroz integral": "brown rice", "massa": "pasta", "esparguete": "spaghetti",
    "batata": "potato", "batata doce": "sweet potato", "pao": "bread", "pão": "bread",
    "aveia": "oats", "feijao": "beans", "feijão": "beans", "grao": "chickpeas",
    "grão": "chickpeas", "lentilhas": "lentils", "banana": "banana", "maca": "apple",
    "maçã": "apple", "iogurte": "yogurt", "iogurte grego": "greek yogurt",
    "leite": "milk", "queijo": "cheese", "queijo fresco": "cottage cheese",
    "azeite": "olive oil", "manteiga": "butter", "brocolos": "broccoli",
    "brócolos": "broccoli", "espinafres": "spinach", "cenoura": "carrot",
    "tomate": "tomato", "alface": "lettuce", "cebola": "onion", "legumes": "vegetables",
    "amendoas": "almond", "amêndoas": "almond", "nozes": "walnut", "amendoim": "peanut",
    "camarao": "shrimp", "camarão": "shrimp", "peru": "turkey",
}


def to_english(nome_pt: str):
    key = nome_pt.strip().lower()
    if key in PT_TO_EN:
        return PT_TO_EN[key]
    for pt, en in PT_TO_EN.items():
        if pt in key or key in pt:
            return en
    return None

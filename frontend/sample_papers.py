"""
sample_papers.py
----------------
TEMPORARY local test data for the favourites feature, used until the real
search page and backend (which call an external REST service) are ready.

Each paper is a plain dict with the same fields the real API should return:
    id, title, authors, year, citations

The citation counts here are rough illustrative numbers, NOT live figures.
"""

SAMPLE_PAPERS: list[dict] = [
    {"id": "p01", "title": "Attention Is All You Need",
     "authors": "A. Vaswani, N. Shazeer, N. Parmar, et al.", "year": 2017, "citations": 150000},
    {"id": "p02", "title": "Deep Residual Learning for Image Recognition",
     "authors": "K. He, X. Zhang, S. Ren, J. Sun", "year": 2016, "citations": 220000},
    {"id": "p03", "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
     "authors": "J. Devlin, M. Chang, K. Lee, K. Toutanova", "year": 2019, "citations": 110000},
    {"id": "p04", "title": "ImageNet Classification with Deep Convolutional Neural Networks",
     "authors": "A. Krizhevsky, I. Sutskever, G. Hinton", "year": 2012, "citations": 130000},
    {"id": "p05", "title": "MapReduce: Simplified Data Processing on Large Clusters",
     "authors": "J. Dean, S. Ghemawat", "year": 2008, "citations": 25000},
    {"id": "p06", "title": "The Google File System",
     "authors": "S. Ghemawat, H. Gobioff, S. Leung", "year": 2003, "citations": 11000},
    {"id": "p07", "title": "Bigtable: A Distributed Storage System for Structured Data",
     "authors": "F. Chang, J. Dean, S. Ghemawat, et al.", "year": 2008, "citations": 8000},
    {"id": "p08", "title": "Dynamo: Amazon's Highly Available Key-value Store",
     "authors": "G. DeCandia, D. Hastorun, M. Jampani, et al.", "year": 2007, "citations": 7000},
    {"id": "p09", "title": "Borg, Omega, and Kubernetes",
     "authors": "B. Burns, B. Grant, D. Oppenheimer, E. Brewer, J. Wilkes", "year": 2016, "citations": 1500},
    {"id": "p10", "title": "Generative Adversarial Nets",
     "authors": "I. Goodfellow, J. Pouget-Abadie, M. Mirza, et al.", "year": 2014, "citations": 75000},
    {"id": "p11", "title": "Adam: A Method for Stochastic Optimization",
     "authors": "D. Kingma, J. Ba", "year": 2015, "citations": 190000},
    {"id": "p12", "title": "Highly Accurate Protein Structure Prediction with AlphaFold",
     "authors": "J. Jumper, R. Evans, A. Pritzel, et al.", "year": 2021, "citations": 30000},
]


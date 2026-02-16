# Welcome to My Vivino
A scalable machine learning recommendation system designed to replace rule-based wine suggestions with personalized predictions.

## Task
My Vivino is transitioning from a rules-based system to a data-driven recommendation engine.
The goal is to recommend wines that users are most likely to enjoy based on historical user ratings, improving personalization and customer experience.

## Description
This project implements a production-oriented recommender system that combines behavioral learning with contextual filtering:

- Collaborative Filtering (SVD) trained on historical user ratings (primary signal)

- Optional food pairing filter leveraging the wine Harmonize metadata (secondary signal)

- Popularity-based fallback to ensure recommendations remain available during cold-start scenarios

The system is designed to be modular, interpretable, and easily deployable.

**Data Source**:
de Azambuja, R. X., Morais, A. J., & Filipe, V. (2023).
X-Wines: A Wine Dataset for Recommender Systems and Machine Learning.
Big Data and Cognitive Computing, 7(1), 20.
https://github.com/rogerioxavier/X-Wines
 

## Installation
Install the following libraries if not already available:
```
pip install pandas numpy scipy scikit-learn matplotlib
```
## Usage
Run the Jupyter notebook:
```
my_vivino.ipynb
```
Or execute the Python script:
```
pyton my_vivino.py
```

### The Core Team
- Sinchana Rai
- Khagendra Adhikari


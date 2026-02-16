#!/usr/bin/env python
# coding: utf-8

# # My Vivino — Data-Driven Wine Recommendation System
# 
# **Core Team:** Sinchana Rai, Khagendra Adhikari
# 
# ### Executive Summary
# My Vivino currently relies on a rules-based recommendation engine. This limits personalization and scalability across a large wine catalog.
# 
# In this notebook, we build a production-oriented recommendation system using:
# - **Collaborative Filtering (SVD)** as the primary personalized recommender
# - **Optional food pairing filter** using wine metadata (`Harmonize`) as a contextual constraint
# - **Popularity fallback** (train-only) for cold-start users or missing signals
# 
# We evaluate model quality using **RMSE** and demonstrate example recommendations for:
# - Personalized (CF-only)
# - Personalized + Food context (e.g., "beef")
# 

# ### Business Problem
# My Vivino is an online marketplace with millions of users and a large wine catalog.  
# The existing rules-based system cannot reliably personalize recommendations across diverse preferences.
# 
# ### Project Objective
# Design and implement a scalable, machine learning–based wine recommendation system using historical user ratings.
# 
# 
# ### Hypotheses
# - **H1:** Collaborative filtering will outperform popularity-based recommendations by learning latent user preferences.
# - **H2:** Adding food pairing as context will improve relevance in meal-planning scenarios.
# 
# ### Success Criteria (Offline)
# - **RMSE** on rating prediction (for known users/items)
# - Demonstrable recommendation quality via example outputs
# - **Production readiness**: deterministic pipeline, no data leakage, clear fallbacks
# 
# > Online KPIs (future): CTR, conversion rate, retention, revenue lift (A/B testing).
# 

# ### Import required Libraries

# In[ ]:


import pandas as pd
import numpy as np
import re
import ast

from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import mean_squared_error

import matplotlib.pyplot as plt


# ## Data Source
# 
# This project utilizes the X-Wines dataset (specifically the "Slim" version), a curated, large-scale wine dataset designed for developing and testing recommender systems. Due to technical loading issues encountered with the full training dataset, the slimmed version (150K ratings/1K wines) is used as a functional alternative, ensuring efficiency in preprocessing and model evaluation.
# 
# - ~1,000 wines  
# - ~150k real user ratings  
# - Ratings collected between 2012–2021  
# - Wines from 60+ countries  
# 
# **Repository:**  
# https://github.com/rogerioxavier/X-Wines  
# 
# **Citation:**  
# de Azambuja, R. X., Morais, A. J., & Filipe, V. (2023).  
# *X-Wines: A Wine Dataset for Recommender Systems and Machine Learning.*  
# Big Data and Cognitive Computing, 7(1), 20.  
# https://doi.org/10.3390/bdcc7010020
# 

# In[ ]:


def gdrive_csv(file_id: str) -> pd.DataFrame:
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    return pd.read_csv(url, low_memory=False)

def load_data():
    wines = gdrive_csv("1z-TrJSjGx5a4E4k_xn-sZDeeBmQhwgfl")
    ratings_train = gdrive_csv("1Ac34SJfq5vqIENcLX6wFY4Ub3ZGfMDln")
    ratings_test = gdrive_csv("1LhzeXTkD2TFGmE4tDESuJ_GUreEYv_zE")
    return wines, ratings_train, ratings_test

wines, train, test = load_data()

print("Wines:", wines.shape)
print("Train ratings:", train.shape)
print("Test ratings:", test.shape)
print("Train users:", train["UserID"].nunique(), "| Train wines rated:", train["WineID"].nunique())


# ## Data Preparation
# We prepare data for modeling by:
# 1. Normalizing food pairing metadata (`Harmonize`) into a clean list of tokens.
# 2. Computing **train-only** wine statistics:
#    - `avg_rating` and `num_ratings` used for fallback ranking and display.
# 3. Building an interaction matrix for collaborative filtering:
#    - map sparse `UserID` and `WineID` into dense indices for matrix factorization.
# 

# In[ ]:


def normalize(text: str) -> str:
    """Lowercase + trim + collapse whitespace for reliable matching."""
    return re.sub(r"\s+", " ", str(text).strip().lower())

def parse_list(value):
    """
    Harmonize can be stored as:
    - "['beef', 'lamb']"
    - "beef, lamb"
    - NaN
    Returns a list[str] in all cases.
    """
    if pd.isna(value):
        return []
    s = str(value).strip()
    if not s:
        return []
    try:
        y = ast.literal_eval(s)
        if isinstance(y, list):
            return y
        if isinstance(y, str):
            return [y]
    except Exception:
        pass
    return [v.strip() for v in s.split(",") if v.strip()]

def prepare_wines(wines_df: pd.DataFrame, ratings_train: pd.DataFrame) -> pd.DataFrame:
    wines_df = wines_df.copy()

    # Food pairing tokens
    wines_df["harmonize_norm"] = (
        wines_df.get("Harmonize", "")
        .apply(parse_list)
        .apply(lambda xs: [normalize(x) for x in xs])
    )

    # Train-only popularity stats (prevents leakage)
    stats = (ratings_train.groupby("WineID")["Rating"]
             .agg(num_ratings="count", avg_rating="mean")
             .reset_index())

    global_avg = float(ratings_train["Rating"].mean())
    wines_df = wines_df.merge(stats, on="WineID", how="left")
    wines_df["num_ratings"] = wines_df["num_ratings"].fillna(0).astype(int)
    wines_df["avg_rating"] = wines_df["avg_rating"].fillna(global_avg)

    return wines_df

wines = prepare_wines(wines, train)
wines[["WineID", "WineName", "avg_rating", "num_ratings"]].head()


# ### Exploratory Data Analysis (EDA)
# We run lightweight EDA to understand:
# - Rating behavior (distribution)
# - Interaction sparsity (ratings per user)
# 
# These insights motivate collaborative filtering (sparse interactions + preference diversity).
# 

# In[ ]:


# 1) Rating distribution (train)
plt.figure(figsize=(8, 4))
plt.hist(train["Rating"].dropna(), bins=30)
plt.title("Ratings Distribution (Train)")
plt.xlabel("Rating")
plt.ylabel("Count")
plt.savefig("Figures/Ratings_distribution.png")
plt.show()

# 2) Ratings per user (train) -> sparsity signal
ratings_per_user = train.groupby("UserID").size()
plt.figure(figsize=(8, 4))
plt.hist(ratings_per_user, bins=50)
plt.title("Ratings per User (Train)")
plt.xlabel("#Ratings")
plt.ylabel("#Users")
plt.savefig("Figures/Numer_of_ratings_per_user_distribution.png")
plt.show()

print(f"Mean ratings per user: {ratings_per_user.mean():.4f}")
print(f"Median ratings per user: {ratings_per_user.median():.4f}")


# ## Modeling Approach
# We implement a hybrid recommender:
# 
# #### Baseline: Popularity Fallback
# If personalization is not available (cold start), recommend wines with high `avg_rating` and `num_ratings` computed from training data only.
# 
# #### Primary Model: Collaborative Filtering (SVD)
# We factorize the sparse user–wine rating matrix to learn latent embeddings for users and wines.
# 
# #### Contextual Constraint: Food Pairing (Optional)
# If the user provides a food context (e.g., "beef"), we filter the CF candidate list to wines whose `Harmonize` metadata includes that food.
# If filtering yields too few results, we backfill using the remaining CF-ranked items.
# 

# In[ ]:


def build_seen_items(ratings_train: pd.DataFrame) -> dict:
    """User -> set of wines already rated (prevents recommending already-seen items)."""
    return ratings_train.groupby("UserID")["WineID"].apply(set).to_dict()

class RecommenderCF:
    def __init__(self, n_factors=50, random_state=42):
        self.svd = TruncatedSVD(n_components=n_factors, random_state=random_state)

    def fit(self, ratings_train: pd.DataFrame):
        self.user_map = {u: i for i, u in enumerate(ratings_train["UserID"].unique())}
        self.wine_map = {w: i for i, w in enumerate(ratings_train["WineID"].unique())}
        self.inv_wine_map = {i: w for w, i in self.wine_map.items()}
        self.seen = build_seen_items(ratings_train)
        self.global_mean = train["Rating"].mean()

        rows = ratings_train["UserID"].map(self.user_map).values
        cols = ratings_train["WineID"].map(self.wine_map).values
        data = ratings_train["Rating"].astype(float).values - self.global_mean

        mat = csr_matrix((data, (rows, cols)), shape=(len(self.user_map), len(self.wine_map)))
        self.user_emb = self.svd.fit_transform(mat)
        self.item_emb = self.svd.components_.T

    def recommend_ids(self, user_id: int, top_n: int = 200):
        """Return a ranked list of WineIDs (candidates) based on predicted preference."""
        if user_id not in self.user_map:
            return []

        u = self.user_map[user_id]
        scores = self.user_emb[u] @ self.item_emb.T
        ranked = np.argsort(scores)[::-1]

        out = []
        seen = self.seen.get(user_id, set())
        for idx in ranked:
            wid = self.inv_wine_map[int(idx)]
            if wid in seen:
                continue
            out.append(wid)
            if len(out) >= top_n:
                break
        return out


# ## Recommendation Policy (Orchestration)
# We combine signals using a simple policy:
# 
# 1. Generate a ranked candidate list from **Collaborative Filtering**.
# 2. If food context is provided, filter candidates by `harmonize_norm`.
# 3. If the filtered list is too short, backfill with remaining CF candidates.
# 4. If the user is unknown (cold start), return **most popular wines** (train-only).
# 

# In[ ]:


def recommend(wines_df: pd.DataFrame, model: RecommenderCF, user_id: int, food: str = None, k: int = 10):
    # CF candidate pool
    candidates = model.recommend_ids(user_id, top_n=200)

    # Cold start -> popularity fallback
    if not candidates:
        df = wines_df.sort_values(["avg_rating", "num_ratings"], ascending=False)
        if food:
            f = normalize(food)
            df = df[df["harmonize_norm"].apply(lambda xs: f in xs)]
        return df.head(k).reset_index(drop=True)

    # Materialize candidates and preserve CF order
    df = wines_df[wines_df["WineID"].isin(candidates)].copy()
    order = {wid: i for i, wid in enumerate(candidates)}
    df["rank"] = df["WineID"].map(order)
    df = df.sort_values("rank")

    # Optional: food filter + backfill
    if food:
        f = normalize(food)
        df_food = df[df["harmonize_norm"].apply(lambda xs: f in xs)]
        if len(df_food) >= k:
            return df_food.head(k).drop(columns="rank").reset_index(drop=True)
        df = pd.concat([df_food, df[~df.index.isin(df_food.index)]], axis=0)

    return df.head(k).drop(columns="rank").reset_index(drop=True)


# ### Evaluation (Offline)
# We evaluate rating prediction accuracy using **RMSE** for user–wine pairs present in both train and test mappings. Ratings were mean-centered prior to matrix factorization to ensure predicted scores aligned with the observed rating scale.
# 
# 
# RMSE is not a perfect recommender metric, but it provides a quick sanity check for the collaborative filtering model.
# (Online success will ultimately be measured via A/B testing: CTR, conversion, retention.)
# 

# In[ ]:


def rmse(model: RecommenderCF, ratings_test: pd.DataFrame) -> float:
    preds, actuals = [], []

    for r in ratings_test.itertuples(index=False):
        if r.UserID in model.user_map and r.WineID in model.wine_map:
            u = model.user_map[r.UserID]
            i = model.wine_map[r.WineID]
            pred = model.global_mean + (model.user_emb[u] @ model.item_emb[i])
            pred = float(np.clip(pred, 1, 5))  
            preds.append(pred)
            actuals.append(float(r.Rating))
    return float(np.sqrt(mean_squared_error(actuals, preds))) if preds else float("inf")


# ## Training & Results
# We train the collaborative filtering model on the training ratings data and report:
# - RMSE on the test set
# - Example recommendations (CF-only)
# - Example recommendations with food context ("beef")
# 

# In[ ]:


model = RecommenderCF(n_factors=50, random_state=42)
model.fit(train)

print(f"RMSE (CF): {rmse(model, test):.4f}")

sample_user = int(test["UserID"].iloc[0])

cols = ["WineID", "WineName", "Type", "Country", "avg_rating", "num_ratings", "harmonize_norm"]
cols = [c for c in cols if c in wines.columns]

print(f"\nCF recommendations for UserID={sample_user}")
display(recommend(wines, model, sample_user, k=5)[cols])

print(f"\nCF + Food='beef' recommendations for UserID={sample_user}")
display(recommend(wines, model, sample_user, food="beef", k=5)[cols])


# ## Production Considerations
# This notebook is designed to be production-friendly:
# 
# - **Deterministic training** via fixed random seed
# - **No data leakage**: popularity stats computed from training data only
# - **Robust fallbacks** for cold-start users and missing food matches
# - Clear separation between:
#   - data preparation
#   - modeling
#   - recommendation policy
#   - evaluation
# 

# ## Conclusion
# We replaced a rules-based approach with a ML-based recommender system.
# - Collaborative Filtering provides personalization from historical ratings.
# - Food context acts as a lightweight constraint to improve situational relevance.
# - Popularity fallback ensures reliability for cold-start cases.
# 
# This establishes a scalable foundation for a production recommendation service.
# 

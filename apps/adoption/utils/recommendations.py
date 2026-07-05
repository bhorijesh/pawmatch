"""Content-based pet recommendation utilities."""


def extract_pet_features(pets):
    """One-hot encode species, size, age_group, temperament into feature vectors."""
    species_list = ['Dog', 'Cat', 'Rabbit', 'Bird', 'Other']
    size_list = ['Small', 'Medium', 'Large']
    age_list = ['Baby', 'Young', 'Adult', 'Senior']
    temperament_list = ['Calm', 'Energetic', 'Friendly', 'Shy']

    features = []
    for pet in pets:
        species_vec = [1 if pet['species'] == s else 0 for s in species_list]
        size_vec = [1 if pet['size'] == s else 0 for s in size_list]
        age_vec = [1 if pet['age_group'] == a else 0 for a in age_list]
        temp_vec = [1 if pet['temperament'] == t else 0 for t in temperament_list]
        features.append(species_vec + size_vec + age_vec + temp_vec)
    return features


def cosine_similarity(vec1, vec2):
    dot = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
    mag1 = sum(v ** 2 for v in vec1) ** 0.5
    mag2 = sum(v ** 2 for v in vec2) ** 0.5
    if mag1 == 0 or mag2 == 0:
        return 0
    return dot / (mag1 * mag2)


def get_species_frequencies(adopted_pets):
    freq = {}
    for pet in adopted_pets:
        freq[pet['species']] = freq.get(pet['species'], 0) + 1
    return freq


def content_based_recommendation(user_pets, all_pets, top_n=10):
    """Recommend pets using cosine similarity on adoption history."""
    if not user_pets or not all_pets:
        return []

    user_features = extract_pet_features(user_pets)
    all_features = extract_pet_features(all_pets)
    species_freq = get_species_frequencies(user_pets)

    scores = []
    for i, pet_feat in enumerate(all_features):
        pet = all_pets[i]
        avg_sim = sum(
            cosine_similarity(uf, pet_feat) for uf in user_features
        ) / len(user_features)
        if pet['species'] in species_freq:
            avg_sim *= (1 + species_freq[pet['species']] * 0.2)
        scores.append((i, avg_sim))

    scores.sort(key=lambda x: x[1], reverse=True)
    return [all_pets[i] for i, _ in scores[:top_n]]

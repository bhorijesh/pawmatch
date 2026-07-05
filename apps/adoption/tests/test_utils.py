from django.test import TestCase

from apps.adoption.utils import haversine, cosine_similarity, content_based_recommendation, extract_pet_features


class HaversineTests(TestCase):
    def test_same_point_is_zero(self):
        self.assertEqual(haversine(27.7172, 85.3240, 27.7172, 85.3240), 0)

    def test_known_distance_is_positive(self):
        dist = haversine(27.7172, 85.3240, 27.7200, 85.3300)
        self.assertGreater(dist, 0)
        self.assertLess(dist, 5)


class CosineSimilarityTests(TestCase):
    def test_identical_vectors(self):
        vec = [1, 0, 1, 0]
        self.assertAlmostEqual(cosine_similarity(vec, vec), 1.0)

    def test_orthogonal_vectors(self):
        self.assertEqual(cosine_similarity([1, 0], [0, 1]), 0)


class RecommendationTests(TestCase):
    def test_recommends_similar_pets(self):
        user_pets = [{'species': 'Dog', 'size': 'Large', 'age_group': 'Adult', 'temperament': 'Friendly'}]
        all_pets = [
            {'id': 1, 'species': 'Dog', 'size': 'Large', 'age_group': 'Adult', 'temperament': 'Friendly'},
            {'id': 2, 'species': 'Cat', 'size': 'Small', 'age_group': 'Baby', 'temperament': 'Shy'},
        ]
        result = content_based_recommendation(user_pets, all_pets, top_n=1)
        self.assertEqual(result[0]['id'], 1)

    def test_empty_input_returns_empty(self):
        self.assertEqual(content_based_recommendation([], []), [])

    def test_feature_vector_length(self):
        pets = [{'species': 'Dog', 'size': 'Medium', 'age_group': 'Young', 'temperament': 'Calm'}]
        features = extract_pet_features(pets)
        self.assertEqual(len(features[0]), 16)

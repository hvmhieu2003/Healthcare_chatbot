from rest_framework.views import APIView
from rest_framework.response import Response
import numpy as np
import tensorflow as tf

class PredictDisease(APIView):
    def post(self, request):
        symptoms = request.data.get('symptoms')  # Expecting list like [1, 1, 0, 1, 0, 0]
        model = tf.keras.models.load_model('healthcare_model.h5')
        input_array = np.array([symptoms], dtype=np.float32)
        
        # Dự đoán với tính bất định
        n_iter = 100
        preds = np.array([model(input_array, training=True).numpy() for _ in range(n_iter)])
        mean_probs = preds.mean(axis=0)
        std_probs = preds.std(axis=0)
        most_likely = np.argmax(mean_probs)
        diseases = ["Flu", "Cold", "COVID-19", "Allergy"]

        response = {
            'diagnosis': diseases[most_likely],
            'probabilities': mean_probs[0].tolist(),
            'uncertainty': std_probs[0].tolist(),
        }
        return Response(response)
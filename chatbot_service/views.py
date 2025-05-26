from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from user_service.models import UserProfile
from django.utils import timezone

class Chatbot(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if user_id:
            try:
                user = UserProfile.objects.get(user_id=user_id)
                return Response({
                    'user_id': user.user_id,
                    'name': user.name,
                    'medical_history': user.medical_history
                })
            except UserProfile.DoesNotExist:
                return Response({"detail": "User not found."}, status=404)
        return Response({"detail": "This endpoint requires a POST request with symptoms data or user_id for history."})

    def post(self, request):
        user_id = request.data.get('user_id')
        symptoms_text = request.data.get('symptoms_text')  # Văn bản triệu chứng
        symptoms_array = request.data.get('symptoms')     # Mảng triệu chứng (tùy chọn)

        if not user_id:
            return Response({"detail": "user_id is required."}, status=400)

        # Chuyển đổi văn bản thành mảng triệu chứng nếu có
        symptoms = [0, 0, 0, 0, 0, 0, 0, 0]  # Mở rộng mảng với 8 phần tử (thêm Chóng mặt, Buồn nôn)
        symptom_keywords = {
            'fever': 0, 'sốt': 0,
            'cough': 1, 'ho': 1,
            'sneezing': 2, 'hắt hơi': 2,
            'fatigue': 3, 'mệt mỏi': 3,
            'loss of taste': 4, 'mất vị giác': 4,
            'itchy eyes': 5, 'ngứa mắt': 5,
            'dizziness': 6, 'chóng mặt': 6,
            'nausea': 7, 'buồn nôn': 7
        }
        if symptoms_text:
            text = symptoms_text.lower()
            for keyword, index in symptom_keywords.items():
                if keyword in text or (len(keyword.split()) > 1 and all(word in text for word in keyword.split())):
                    symptoms[index] = 1

        # Nếu có mảng symptoms, ưu tiên dùng mảng
        if symptoms_array and isinstance(symptoms_array, list):
            symptoms = [1 if i < len(symptoms_array) and symptoms_array[i] else 0 for i in range(len(symptoms))]

        # Gọi model_service
        model_response = requests.post('http://localhost:8001/model/predict/', json={'symptoms': symptoms})
        model_data = model_response.json()

        diagnosis = model_data['diagnosis']
        probabilities = model_data['probabilities']
        uncertainty = model_data['uncertainty']

        test_map = {
            "Flu": "Influenza A/B test",
            "Cold": "Nasal swab",
            "COVID-19": "PCR test",
            "Allergy": "Allergy skin test",
            "Dizziness": "Blood pressure test",
            "Nausea": "Gastrointestinal test"
        }
        medicine_map = {
            "Flu": "Oseltamivir (Tamiflu)",
            "Cold": "Rest, fluids, antihistamines",
            "COVID-19": "Isolation + Paracetamol",
            "Allergy": "Loratadine or Cetirizine",
            "Dizziness": "Rest and hydration",
            "Nausea": "Antiemetics (e.g., Ondansetron)"
        }

        response = {
            'diagnosis': diagnosis,
            'test': test_map.get(diagnosis, "No specific test"),
            'medicine': medicine_map.get(diagnosis, "No specific medicine"),
            'probabilities': probabilities,
            'uncertainty': uncertainty,
        }

        try:
            user, created = UserProfile.objects.get_or_create(
                user_id=user_id,
                defaults={'name': 'Unknown'}
            )
            user.medical_history.setdefault('diagnoses', []).append({
                'symptoms': symptoms,
                'diagnosis': diagnosis,
                'probabilities': probabilities,
                'uncertainty': uncertainty,
                'test': test_map.get(diagnosis, "No specific test"),
                'medicine': medicine_map.get(diagnosis, "No specific medicine"),
                'timestamp': str(timezone.now())
            })
            user.save()
        except Exception as e:
            response['warning'] = f"Could not save to medical history: {str(e)}"

        return Response(response)

class MedicalHistory(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"detail": "user_id is required."}, status=400)
        try:
            user = UserProfile.objects.get(user_id=user_id)
            return Response({
                'user_id': user.user_id,
                'name': user.name,
                'medical_history': user.medical_history
            })
        except UserProfile.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

    def post(self, request):
        user_id = request.data.get('user_id')
        index = request.data.get('index')
        if not user_id or index is None:
            return Response({"detail": "user_id and index are required."}, status=400)
        try:
            user = UserProfile.objects.get(user_id=user_id)
            diagnoses = user.medical_history.get('diagnoses', [])
            if index < 0 or index >= len(diagnoses):
                return Response({"detail": "Invalid index."}, status=400)
            diagnoses.pop(index)
            user.medical_history['diagnoses'] = diagnoses
            user.save()
            return Response({"detail": "Diagnosis deleted successfully."})
        except UserProfile.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)
        except Exception as e:
            return Response({"detail": f"Error deleting diagnosis: {str(e)}"}, status=500)

def chatbot_page(request):
    return render(request, 'chatbot.html')
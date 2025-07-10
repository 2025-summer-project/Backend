from django.http import JsonResponse

def test_api(request):
    return JsonResponse({'message': '테스트 API 응답'})

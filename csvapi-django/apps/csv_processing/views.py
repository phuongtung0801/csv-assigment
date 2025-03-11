from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import CSVFile, CSVTask
from .serializers import CSVFileSerializer, CSVTaskSerializer
from .tasks import process_csv_task

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_csv(request):
    file_obj = request.FILES.get('file')
    if file_obj is None or file_obj.content_type != 'text/csv':
        return Response({"error": "Invalid file format. Only CSV files are allowed."}, status=status.HTTP_400_BAD_REQUEST)
    # Nếu người dùng đã đăng nhập, lưu owner; nếu không, để null
    owner = request.user if request.user.is_authenticated else None
    csv_file = CSVFile.objects.create(file=file_obj, owner=owner)
    serializer = CSVFileSerializer(csv_file)
    return Response({"message": "File uploaded successfully", "file_id": serializer.data['id']}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def perform_operation(request):
    file_id = request.data.get('file_id')
    operation = request.data.get('operation')
    if not file_id or not operation:
        return Response({"error": "Missing file_id or operation"}, status=status.HTTP_400_BAD_REQUEST)
    csv_file = get_object_or_404(CSVFile, id=file_id)
    task_obj = CSVTask.objects.create(file=csv_file, operation=operation)
    # Enqueue task bất đồng bộ qua Celery
    process_csv_task.delay(task_obj.id)
    return Response({"message": "Operation started", "task_id": task_obj.id}, status=status.HTTP_200_OK)

@api_view(['GET'])
def task_status(request):
    task_id = request.query_params.get('task_id')
    if not task_id:
        return Response({"error": "Missing task_id"}, status=status.HTTP_400_BAD_REQUEST)
    task_obj = get_object_or_404(CSVTask, id=task_id)
    serializer = CSVTaskSerializer(task_obj)
    return Response(serializer.data, status=status.HTTP_200_OK)

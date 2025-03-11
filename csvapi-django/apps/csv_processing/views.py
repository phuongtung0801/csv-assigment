from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import CSVFile, CSVTask
from .serializers import CSVFileSerializer, CSVTaskSerializer
from .tasks import process_csv_task
import pandas as pd
import numpy as np

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
    operation_details = request.data.get('operation_details', {})  # Get additional details

    if not file_id or not operation:
        return Response({"error": "Missing file_id or operation"}, status=status.HTTP_400_BAD_REQUEST)

    if operation not in ["dedup", "unique", "filter"]:
        return Response({"error": "Invalid operation. Allowed operations are: dedup, unique, filter"}, status=status.HTTP_400_BAD_REQUEST)

    csv_file = get_object_or_404(CSVFile, id=file_id)

    # Operation-specific validation
    if operation == "unique":
        column_name = operation_details.get('column_name')
        if not column_name:
            return Response({"error": "Missing column_name for unique operation"}, status=status.HTTP_400_BAD_REQUEST)
        operation_string = f"unique:{column_name}" # Reconstruct operation string for task
    elif operation == "filter":
        column = operation_details.get('column')
        value = operation_details.get('value')
        if not column or not value:
            return Response({"error": "Missing column and value for filter operation"}, status=status.HTTP_400_BAD_REQUEST)
        operation_string = f"filter:{column}={value}" # Reconstruct operation string for task
    elif operation == "dedup":
        operation_string = "dedup" # No additional details needed

    task_obj = CSVTask.objects.create(file=csv_file, operation=operation_string) # Use the constructed operation string
    process_csv_task.delay(task_obj.id)
    return Response({"message": "Operation started", "task_id": task_obj.id}, status=status.HTTP_200_OK)

@api_view(['GET'])
def task_status(request):
    task_id = request.query_params.get('task_id')
    n = request.query_params.get('n', 100)
    try:
        n = int(n)
    except ValueError:
        n = 100

    if not task_id:
        return Response({"error": "Missing task_id"}, status=status.HTTP_400_BAD_REQUEST)

    task_obj = get_object_or_404(CSVTask, id=task_id)

    # Nếu task đang chờ (PENDING)
    if task_obj.status == "PENDING":
        return Response({"task_id": task_id, "status": "PENDING"}, status=status.HTTP_200_OK)

    # Nếu task thất bại (FAILURE)
    elif task_obj.status == "FAILURE":
        return Response({
            "task_id": task_id,
            "status": "FAILURE",
            "error": task_obj.error_message or "Task failed without error description."
        }, status=status.HTTP_200_OK)

    # Nếu task thành công (SUCCESS)
    elif task_obj.status == "SUCCESS":
        try:
            df = pd.read_csv(task_obj.result_file.path)
            # Thay thế các giá trị không JSON compliant (NaN, inf, -inf) thành None
            df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
            data = df.head(n).to_dict(orient='records')
        except Exception as e:
            return Response({
                "task_id": task_id,
                "status": "FAILURE",
                "error": f"Error reading processed CSV file: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        file_link = request._request.build_absolute_uri(task_obj.result_file.url)
        result = {
            "data": data,
            "file_link": file_link
        }
        return Response({
            "task_id": task_id,
            "status": "SUCCESS",
            "result": result
        }, status=status.HTTP_200_OK)

    return Response({
        "task_id": task_id,
        "status": task_obj.status,
        "error": "Unknown task status."
    }, status=status.HTTP_200_OK)



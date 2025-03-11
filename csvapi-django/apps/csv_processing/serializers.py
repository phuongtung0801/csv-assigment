from rest_framework import serializers
from .models import CSVFile, CSVTask

class CSVFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVFile
        fields = ['id', 'file', 'uploaded_at']

class CSVTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVTask
        fields = ['id', 'file', 'operation', 'created_at', 'status', 'result_file', 'error_message']

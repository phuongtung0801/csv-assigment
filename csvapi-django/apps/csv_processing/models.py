from django.db import models
from django.contrib.auth.models import User

class CSVFile(models.Model):
    file = models.FileField(upload_to='csv_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="csv_files", null=True, blank=True)

    def __str__(self):
        return f"CSVFile {self.id} - {self.file.name}"

class CSVTask(models.Model):
    file = models.ForeignKey(CSVFile, on_delete=models.CASCADE)
    operation = models.CharField(max_length=50)  # ví dụ: "dedup", "unique:column_name", "filter:column=value"
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='PENDING')
    result_file = models.FileField(upload_to='processed_csv/', null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Task {self.id} - {self.operation} ({self.status})"

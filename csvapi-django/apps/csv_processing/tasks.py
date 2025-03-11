from celery import shared_task
from .models import CSVTask
import pandas as pd
import os
from django.conf import settings

@shared_task
def process_csv_task(task_id):
    try:
        task_obj = CSVTask.objects.get(id=task_id)
        csv_path = task_obj.file.file.path
        df = pd.read_csv(csv_path)

        # Xử lý các thao tác dựa trên operation
        if task_obj.operation == "dedup":
            df_processed = df.drop_duplicates()
        elif task_obj.operation.startswith("unique"):
            # Định dạng: "unique:column_name"
            try:
                _, column = task_obj.operation.split(':')
                df_processed = df.drop_duplicates(subset=[column])
            except Exception as e:
                task_obj.status = 'FAILURE'
                task_obj.error_message = f"Invalid unique operation: {str(e)}"
                task_obj.save()
                return
        elif task_obj.operation.startswith("filter"):
            # Định dạng: "filter:column=value"
            try:
                _, condition = task_obj.operation.split(':')
                column, value = condition.split('=')
                df_processed = df[df[column] == value]
            except Exception as e:
                task_obj.status = 'FAILURE'
                task_obj.error_message = f"Invalid filter operation: {str(e)}"
                task_obj.save()
                return
        else:
            task_obj.status = 'FAILURE'
            task_obj.error_message = "Unsupported operation"
            task_obj.save()
            return

        # Lưu file CSV kết quả
        output_filename = f"processed_{os.path.basename(task_obj.file.file.name)}"
        output_dir = os.path.join(settings.MEDIA_ROOT, 'processed_csv')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)
        df_processed.to_csv(output_path, index=False)

        task_obj.result_file.name = os.path.join('processed_csv', output_filename)
        task_obj.status = 'SUCCESS'
        task_obj.save()
    except Exception as e:
        task_obj.status = 'FAILURE'
        task_obj.error_message = str(e)
        task_obj.save()

from celery import shared_task
from .models import CSVTask
import pandas as pd
import os
from django.conf import settings

@shared_task()
def process_csv_task(task_id):
    try:
        print(f"Starting task with task_id: {task_id}")
        task_obj = CSVTask.objects.get(id=task_id)
        print(f"Task object is: {task_obj}")
        csv_path = task_obj.file.file.path
        print(f"CSV path: {csv_path}")
        df = pd.read_csv(csv_path)
        print(f"DataFrame loaded. shape: {df.shape}")

        if task_obj.operation == "dedup":
            df_processed = df.drop_duplicates()
            print("Dedup operation performed")
        elif task_obj.operation.startswith("unique"):
            try:
                _, column = task_obj.operation.split(':')
                df_processed = df.drop_duplicates(subset=[column])
                print(f"Unique operation performed on column: {column}")
            except Exception as e:
                task_obj.status = 'FAILURE'
                task_obj.error_message = f"Invalid unique operation: {str(e)}"
                task_obj.save()
                print(f"Error in unique operation: {str(e)}")
                return
        elif task_obj.operation.startswith("filter"):
            try:
                _, condition = task_obj.operation.split(':')
                column, value = condition.split('=')
                # --- Thử chuyển đổi 'value' sang kiểu số ---
                try:
                    value = int(value) # Thử chuyển sang integer trước
                except ValueError:
                    try:
                        value = float(value) # Nếu không được integer, thử float
                    except ValueError:
                        pass # Nếu vẫn không được, để nguyên là string (hoặc xử lý khác nếu cần)
                # --- Kết thúc chuyển đổi ---
                df_processed = df[df[column] == value]
                print(f"Filter operation performed: column={column}, value={value}")
                print("df_processed")
                print(df_processed) # Thêm dòng này để in ra DataFrame đã lọc để debug
            except Exception as e:
                task_obj.status = 'FAILURE'
                task_obj.error_message = f"Invalid filter operation: {str(e)}"
                task_obj.save()
                print(f"Error in filter operation: {str(e)}")
                return
        else:
            task_obj.status = 'FAILURE'
            task_obj.error_message = "Unsupported operation"
            task_obj.save()
            print("Unsupported operation")
            return

        output_filename = f"processed_{os.path.basename(task_obj.file.file.name)}"
        output_dir = os.path.join(settings.MEDIA_ROOT, 'processed_csv')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)
        df_processed.to_csv(output_path, index=False)
        print(f"Output file saved to: {output_path}")

        task_obj.result_file.name = os.path.join('processed_csv', output_filename)
        task_obj.status = 'SUCCESS'
        task_obj.save()
        print("Task completed successfully")
    except Exception as e:
        task_obj.status = 'FAILURE'
        task_obj.error_message = str(e)
        task_obj.save()
        print(f"Task failed with error: {str(e)}")
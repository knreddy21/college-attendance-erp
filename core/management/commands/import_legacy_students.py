import json
from pathlib import Path
from django.core.management.base import BaseCommand
from core.models import Student
class Command(BaseCommand):
    help='Import the original students.json records into the Django Student table.'
    def add_arguments(self,parser): parser.add_argument('--file',default='students.json')
    def handle(self,*args,**opts):
        path=Path(opts['file'])
        if not path.exists(): self.stderr.write(f'File not found: {path}'); return
        records=json.loads(path.read_text(encoding='utf-8'))
        created=0
        for item in records:
            sid=str(item['student_id']).upper()
            obj,was_created=Student.objects.get_or_create(student_id=sid,defaults={
              'roll_number':sid,'full_name':item['name'],'email':item.get('email',''),
              'course':item.get('course',''),
            })
            created+=int(was_created)
        self.stdout.write(self.style.SUCCESS(f'Imported {created} new students; existing IDs were skipped.'))

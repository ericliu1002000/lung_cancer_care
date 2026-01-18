
import json
from datetime import date

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

from core.models import CheckupLibrary
from health_data.models import ReportUpload, ReportImage, UploadSource
from users.models import DoctorProfile, PatientProfile
from users import choices
from web_doctor.views.reports_history_data import batch_archive_images

User = get_user_model()

class ImageArchiveTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create a doctor user
        self.user = User.objects.create_user(
            username='doctor', 
            password='password',
            user_type=choices.UserType.DOCTOR,
            phone="13800000000"
        )
        self.doctor_profile = DoctorProfile.objects.create(user=self.user, name='Test Doctor')
        
        # Create a patient
        self.patient_user = User.objects.create_user(
            username='patient', 
            user_type=choices.UserType.PATIENT,
            wx_openid="test_openid"
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user, name='Test Patient')
        self.checkup_item = CheckupLibrary.objects.create(name="CT")
        
    def test_batch_archive_images_group_edit(self):
        upload = ReportUpload.objects.create(patient=self.patient, upload_source=UploadSource.PERSONAL_CENTER)
        img1 = ReportImage.objects.create(upload=upload, image_url="http://test.com/1.jpg")
        img2 = ReportImage.objects.create(upload=upload, image_url="http://test.com/2.jpg")

        updates = [
            {
                "image_id": img1.id,
                "category": "门诊",
                "report_date": "2023-01-01"
            }
        ]
        updates.append({
            "image_id": img2.id,
            "category": "复查-CT",
            "report_date": "2023-01-02"
        })
            
        payload = {"updates": updates}
        
        request = self.factory.post(
            f'/doctor/workspace/patient/{self.patient.id}/reports/archive/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        request.user = self.user
        
        response = batch_archive_images(request, self.patient.id)
        
        self.assertEqual(response.status_code, 200)
        
        img1.refresh_from_db()
        img2.refresh_from_db()

        self.assertEqual(img1.record_type, ReportImage.RecordType.OUTPATIENT)
        self.assertEqual(img1.report_date, date(2023, 1, 1))
        self.assertIsNotNone(img1.clinical_event)

        self.assertEqual(img2.record_type, ReportImage.RecordType.CHECKUP)
        self.assertEqual(img2.report_date, date(2023, 1, 2))
        self.assertIsNotNone(img2.checkup_item)
        self.assertEqual(img2.checkup_item.name, "CT")
        self.assertIsNotNone(img2.clinical_event)

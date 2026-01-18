from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.urls import reverse

from users import choices
from users.models import DoctorProfile, PatientProfile
from web_doctor.views.workspace import patient_workspace_section


User = get_user_model()


class ConsultationRecordsResetButtonTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="doctor_reset_btn",
            password="password",
            user_type=choices.UserType.DOCTOR,
            phone="13800000099",
        )
        self.doctor_profile = DoctorProfile.objects.create(user=self.user, name="Test Doctor")

        self.patient_user = User.objects.create_user(
            username="patient_reset_btn",
            user_type=choices.UserType.PATIENT,
            wx_openid="openid_reset_btn",
        )
        self.patient = PatientProfile.objects.create(
            user=self.patient_user,
            name="Test Patient",
            doctor=self.doctor_profile,
        )

    def test_reset_button_present_in_records_tab(self):
        url = reverse("web_doctor:patient_workspace_section", args=[self.patient.id, "reports"])
        request = self.factory.get(url, {"tab": "records"})
        request.user = self.user
        response = patient_workspace_section(request, self.patient.id, "reports")

        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8", errors="ignore")
        self.assertTrue("重置" in html)
        self.assertTrue("resetFilters()" in html)
        self.assertTrue("filters.recordType" in html or "recordType" in html)

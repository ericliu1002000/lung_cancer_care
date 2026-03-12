from django.test import TestCase
from django.urls import reverse

from users import choices
from users.models import CustomUser, PatientProfile, PatientRelation


class FamilyBindingFlowTests(TestCase):
    def setUp(self):
        self.patient_user = CustomUser.objects.create_user(
            username="patient_family_bind",
            password="password",
            user_type=choices.UserType.PATIENT,
            wx_openid="openid_patient_family_bind",
        )
        self.patient = PatientProfile.objects.create(
            user=self.patient_user,
            name="患者甲",
            phone="13800001001",
        )
        self.family_user = CustomUser.objects.create_user(
            username="family_member_bind",
            password="password",
            user_type=choices.UserType.PATIENT,
            wx_openid="openid_family_member_bind",
        )

    def test_bind_landing_shows_family_only_form(self):
        response = self.client.get(
            reverse("web_patient:bind_landing", args=[self.patient.id])
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("我是家属/监护人", content)
        self.assertIn("选择与患者的关系", content)
        self.assertNotIn("我是患者本人", content)

    def test_bind_submit_creates_family_relation(self):
        self.client.force_login(self.family_user)

        response = self.client.post(
            reverse("web_patient:bind_submit", args=[self.patient.id]),
            {
                "relation_type": choices.RelationType.CHILD,
                "relation_name": "大女儿",
                "receive_notification": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        relation = PatientRelation.objects.get(
            patient=self.patient,
            user=self.family_user,
        )
        self.assertEqual(relation.relation_type, choices.RelationType.CHILD)
        self.assertEqual(relation.relation_name, "大女儿")
        self.assertTrue(relation.receive_alert_msg)

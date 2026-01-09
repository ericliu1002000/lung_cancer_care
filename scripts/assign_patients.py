from users.models import PatientProfile, DoctorStudio
from chat.models import PatientStudioAssignment
from django.utils import timezone

def run():
    studio = DoctorStudio.objects.first()
    if not studio:
        print("No studios found!")
        return

    patients = PatientProfile.objects.all()
    count = 0
    for patient in patients:
        # Check if active assignment exists
        active = PatientStudioAssignment.objects.filter(patient=patient, end_at__isnull=True).first()
        if not active:
            PatientStudioAssignment.objects.create(
                patient=patient,
                studio=studio,
                start_at=timezone.now(),
                reason="Auto-assigned by script"
            )
            print(f"Assigned {patient.name} to {studio.name}")
            count += 1
    print(f"Total assigned: {count}")
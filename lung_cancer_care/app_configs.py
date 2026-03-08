from django_changelog.apps import ChangelogConfig as DjangoChangelogConfig


class PatchedDjangoChangelogConfig(DjangoChangelogConfig):
    # django-changelog 0.1.2 ships with name='changelog', which breaks app loading.
    name = "django_changelog"
    label = "django_changelog"

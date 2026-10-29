import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0032_limit_default_interleave_delta"),
    ]

    operations = [
        migrations.AddField(
            model_name="outputprofile",
            name="xc_path",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Xtream Codes URL ending (http://host:port/<xc_path>). Empty = off.",
                max_length=64,
                validators=[
                    django.core.validators.RegexValidator(
                        "^[A-Za-z0-9_-]+$", "Letters, digits, - and _ only."
                    )
                ],
            ),
        ),
        migrations.AddConstraint(
            model_name="outputprofile",
            constraint=models.UniqueConstraint(
                condition=models.Q(("xc_path", ""), _negated=True),
                fields=("xc_path",),
                name="unique_output_profile_xc_path",
            ),
        ),
    ]

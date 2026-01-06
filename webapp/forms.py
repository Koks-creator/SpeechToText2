import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField
from wtforms.validators import DataRequired, ValidationError
from flask_wtf.file import MultipleFileField, FileAllowed

from config import Config


def max_files_count(max_count):
    def _max_files_count(form, field):
        # field.data - list of FileStorage objects
        if len(field.data) > max_count:
            raise ValidationError(f"You can only upload max {max_count} files.")
    return _max_files_count

def min_files_count(min_count):
    def _min_files_count(form, field):
        real_files = [f for f in field.data if f and f.filename] # not empty files
        if len(real_files) < min_count:
            raise ValidationError(f"Required at least {min_count} files.")
    return _min_files_count

class MainForm(FlaskForm):
    normalize_list_field = BooleanField("Normalize", default=False)
    images_field = MultipleFileField(
        "Upload files",
        validators=[
            DataRequired(),
            FileAllowed(list(Config.API_ALLOWED_EXTENSIONS), f"Not allowed file extension. Allowed ones: {', '.join(list(Config.API_ALLOWED_EXTENSIONS))}"),
            min_files_count(1),
            max_files_count(Config.MAX_IMAGE_FILES)
        ]
                                )
    submit_field = SubmitField("Submit")
from pydantic import BaseModel, ValidationError, field_validator


VALID_GENDERS = {'male', 'female', 'other'}
BLOCKED_PHONE_NUMBERS = {'0000000000', '1234567890'}


def clean_text(value: str):
    if value is None:
        return ''

    return str(value).strip()


def first_validation_error(error):
    message = error.errors()[0]['msg']
    return message.replace('Value error, ', '')


class SignupData(BaseModel):
    fullname: str
    email: str
    gender: str
    phoneNumber: str
    password: str

    @field_validator('fullname', mode='before')
    @classmethod
    def prepare_fullname(cls, value):
        return clean_text(value)

    @field_validator('email', mode='before')
    @classmethod
    def prepare_email(cls, value):
        return clean_text(value).lower()

    @field_validator('gender', mode='before')
    @classmethod
    def prepare_gender(cls, value):
        return clean_text(value).lower()

    @field_validator('phoneNumber', mode='before')
    @classmethod
    def prepare_phone_number(cls, value):
        return clean_text(value)

    @field_validator('password', mode='before')
    @classmethod
    def prepare_password(cls, value):
        if value is None:
            return ''

        return str(value)

    @field_validator('fullname')
    @classmethod
    def validate_fullname(cls, value):
        if len(value) < 3:
            raise ValueError('Full name must be at least 3 characters.')

        return value

    @field_validator('email')
    @classmethod
    def validate_email(cls, value):
        if len(value) < 6:
            raise ValueError('Email must be at least 6 characters.')

        if '@' not in value or '.' not in value:
            raise ValueError('Please enter a valid email address.')

        return value

    @field_validator('phoneNumber')
    @classmethod
    def validate_phone_number(cls, value):
        if len(value) < 7 or value in BLOCKED_PHONE_NUMBERS:
            raise ValueError('Please enter a valid phone number.')

        if not value.isdigit():
            raise ValueError('Phone number must contain only digits.')

        if len(value) > 15:
            raise ValueError('Phone number must be less than 15 digits.')

        return value

    @field_validator('gender')
    @classmethod
    def validate_gender(cls, value):
        if value not in VALID_GENDERS:
            raise ValueError('Please select a valid gender.')

        return value

    @field_validator('password')
    @classmethod
    def validate_password(cls, value):
        if len(value) < 6:
            raise ValueError('Password must be at least 6 characters.')

        return value


class LoginData(BaseModel):
    email: str
    password: str

    @field_validator('email', mode='before')
    @classmethod
    def prepare_email(cls, value):
        return clean_text(value).lower()

    @field_validator('password', mode='before')
    @classmethod
    def prepare_password(cls, value):
        if value is None:
            return ''

        return str(value)

    @field_validator('email')
    @classmethod
    def validate_email(cls, value):
        if len(value) < 4 or '@' not in value or '.' not in value:
            raise ValueError('Please enter a valid email address.')

        return value

    @field_validator('password')
    @classmethod
    def validate_password(cls, value):
        if not value:
            raise ValueError("You didn't enter any password.")

        return value

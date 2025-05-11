import json
import base64
import hashlib
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet, InvalidToken

# It's good practice to have a dedicated logger for your custom fields or app utilities
import logging
logger = logging.getLogger(__name__)

class EncryptionService:
    """
    A simple service to encapsulate Fernet key generation and encryption/decryption.
    """
    _fernet_instance = None

    @classmethod
    def _get_key(cls):
        """
        Derives a 32-byte key suitable for Fernet from Django's SECRET_KEY.
        Uses SHA256 hash of the SECRET_KEY.
        """
        # SECRET_KEY should be bytes or a string that can be encoded
        secret_key_bytes = getattr(settings, 'SECRET_KEY', '').encode('utf-8')
        # Use SHA256 to get a 32-byte hash
        hashed_key = hashlib.sha256(secret_key_bytes).digest()
        return base64.urlsafe_b64encode(hashed_key) # Fernet keys must be url-safe base64 encoded

    @classmethod
    def get_fernet(cls):
        if cls._fernet_instance is None:
            key = cls._get_key()
            if not key:
                raise ValueError("Encryption key could not be derived. Is SECRET_KEY set?")
            cls._fernet_instance = Fernet(key)
        return cls._fernet_instance

    @classmethod
    def encrypt(cls, data_bytes: bytes) -> bytes:
        return cls.get_fernet().encrypt(data_bytes)

    @classmethod
    def decrypt(cls, encrypted_bytes: bytes) -> bytes:
        return cls.get_fernet().decrypt(encrypted_bytes)


class EncryptedJSONField(models.TextField):
    """
    A custom Django model field that stores JSON data encrypted as text in the database.
    It handles serialization/deserialization of Python dicts to/from JSON strings,
    and encrypts/decrypts the JSON string.
    """
    description = "JSON object, stored as encrypted text"

    def __init__(self, *args, **kwargs):
        # `default` should be a callable (like `dict`) or an actual dict for JSONField behavior.
        # For our TextField base, if a default is dict, we'll handle it in to_python.
        self.default_value = kwargs.get('default', dict) 
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        """
        Converts data from the database format (encrypted string) to Python format (dict).
        """
        if value is None:
            # If default is callable (like dict), call it. Otherwise, return as is.
            return self.default_value() if callable(self.default_value) else self.default_value

        if not isinstance(value, str): # Should be a string from TextField
            logger.warning(f"EncryptedJSONField received non-string from DB: {type(value)}")
            # Fallback to default or raise error, depending on desired strictness
            return self.default_value() if callable(self.default_value) else self.default_value


        try:
            # The value from DB is a string, needs to be encoded to bytes for Fernet
            encrypted_bytes = value.encode('utf-8')
            decrypted_bytes = EncryptionService.decrypt(encrypted_bytes)
            decrypted_string = decrypted_bytes.decode('utf-8')
            return json.loads(decrypted_string)
        except InvalidToken:
            logger.error(f"EncryptedJSONField: InvalidToken during decryption. Data may be corrupted or not encrypted. Value: {value[:50]}...")
            # Fallback to default or raise error. For safety, return default.
            # This could happen if data was written before encryption was active.
            # Or if the SECRET_KEY changed without a data migration strategy.
            return self.default_value() if callable(self.default_value) else self.default_value
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"EncryptedJSONField: Error decoding/deserializing data: {e}. Value: {value[:50]}...")
            return self.default_value() if callable(self.default_value) else self.default_value
        except Exception as e: # Catch any other unexpected errors during decryption
            logger.error(f"EncryptedJSONField: Unexpected error in from_db_value: {e}. Value: {value[:50]}...")
            return self.default_value() if callable(self.default_value) else self.default_value


    def to_python(self, value):
        """
        Converts value to a Python dictionary. This is called during deserialization
        (e.g. by forms) and when the field is accessed.
        """
        if isinstance(value, dict):
            return value
        if value is None:
            return self.default_value() if callable(self.default_value) else self.default_value
        
        # If from_db_value has already processed it, it might be a dict.
        # If it's a string (e.g. from a form or direct assignment of JSON string),
        # we might try to parse it, but get_prep_value is primary for saving.
        # For simplicity, if it's not a dict here, we assume it's already processed
        # by from_db_value or will be handled by get_prep_value.
        # Or, if it's a string, it might be an encrypted string or a raw JSON string.
        # This method's role can be tricky with custom fields.
        # Let's assume if it's a string, it's likely the DB representation or similar.
        # from_db_value is more critical for DB -> Python.
        if isinstance(value, str):
            # This could be an encrypted string or a raw JSON string.
            # Attempting decryption here could be redundant if from_db_value handles it.
            # For now, let's assume if it's a string, it's the DB form.
            # This part might need refinement based on how Django calls to_python vs from_db_value.
            # Let's try to decrypt if it looks like it might be an encrypted string.
            # This is a bit heuristic.
            try:
                # This is a simplified attempt; robustly distinguishing JSON string vs encrypted string is hard.
                # Relying on from_db_value for DB load is safer.
                # If direct assignment of an encrypted string happens, this might be an issue.
                return json.loads(value) # If it's a plain JSON string
            except json.JSONDecodeError:
                # If it's not plain JSON, it might be encrypted or garbage.
                # Let from_db_value handle the encrypted case from DB.
                # If it's assigned directly as an already encrypted string, that's an edge case.
                pass # Fall through, or could try decrypting as in from_db_value

        # If we haven't returned a dict, return the default.
        if isinstance(value, dict): # Re-check after potential parse
            return value
        return self.default_value() if callable(self.default_value) else self.default_value


    def get_prep_value(self, value):
        """
        Converts Python dictionary to database format (encrypted string).
        """
        if value is None:
            # Respect `null=True` if set on the field instance in the model
            if self.null:
                return None
            # Otherwise, encrypt the JSON representation of an empty dict or default
            py_value = self.default_value() if callable(self.default_value) else self.default_value
        elif not isinstance(value, dict):
            # If a non-dict is passed, try to make it a dict or use default
            # This could be stricter (e.g., raise ValidationError)
            logger.warning(f"EncryptedJSONField received non-dict for prep_value: {type(value)}. Using default.")
            py_value = self.default_value() if callable(self.default_value) else self.default_value
        else:
            py_value = value

        try:
            json_string = json.dumps(py_value)
            json_bytes = json_string.encode('utf-8')
            encrypted_bytes = EncryptionService.encrypt(json_bytes)
            # Store as a string in the TextField
            return encrypted_bytes.decode('utf-8')
        except Exception as e: # Catch any unexpected errors during encryption/serialization
            logger.error(f"EncryptedJSONField: Unexpected error in get_prep_value: {e}. Value: {str(py_value)[:50]}...")
            # Depending on desired behavior, could raise error or return encrypted default
            # For safety, returning encrypted empty dict string if possible
            empty_dict_json = json.dumps({})
            return EncryptionService.encrypt(empty_dict_json.encode('utf-8')).decode('utf-8')

    def value_to_string(self, obj):
        """
        Used for serialization, e.g. by dumpdata.
        We want to dump the encrypted string.
        """
        value = self.value_from_object(obj)
        return self.get_prep_value(value) # This will return the encrypted string

    # If you want it to behave more like JSONField in forms and validation:
    # def formfield(self, **kwargs):
    #     from django.forms import fields
    #     defaults = {'form_class': fields.JSONField} # Or a custom widget
    #     defaults.update(kwargs)
    #     return super().formfield(**defaults)

    # For Django's type system / deconstruction
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.default_value is not dict: # Only add default if it's not the standard `dict`
             if callable(self.default_value) and hasattr(self.default_value, '__name__'):
                 # Heuristic for callables like `dict` itself vs. lambdas or complex objects
                 if self.default_value.__name__ == 'dict' and self.default_value.__module__ == 'builtins':
                     pass # Standard dict, no need to serialize
                 else:
                     kwargs['default'] = self.default_value 
             elif not callable(self.default_value):
                 kwargs['default'] = self.default_value
        return name, path, args, kwargs

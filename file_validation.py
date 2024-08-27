import os
import re

def validate_filename(filename):
    """Validate the filename based on expected naming conventions."""
    if not re.match(r'^[\w\-]+\.txt$', filename):
        return f"Filename '{filename}' does not match the expected pattern."
    return None

def validate_file_size(filename, max_size_mb=5):
    """Validate the file size is within the specified limit (in MB)."""
    file_size = os.path.getsize(filename) / (1024 * 1024)
    if file_size > max_size_mb:
        return f"File size {file_size:.2f} MB exceeds the maximum allowed size of {max_size_mb} MB."
    return None

def validate_encoding(filename, expected_encoding='utf-8'):
    """Validate that the file is encoded in the expected format."""
    try:
        with open(filename, 'r', encoding=expected_encoding) as file:
            file.read()  # Try reading the file to check encoding
    except UnicodeDecodeError:
        return f"File '{filename}' is not encoded in {expected_encoding}."
    return None

def convert_to_utf8(filename, new_filename):
    """Convert the file encoding to UTF-8 if it's not already."""
    try:
        with open(filename, 'r', encoding='ISO-8859-1') as file:
            content = file.read()
        with open(new_filename, 'w', encoding='utf-8') as file:
            file.write(content)
    except (UnicodeDecodeError, IOError) as e:
        raise RuntimeError(f"Failed to convert file encoding: {e}")

def validate_record_length(filename, expected_length, delimiter='|'):
    """Validate that each record has the expected number of fields."""
    with open(filename, 'r') as file:
        for i, line in enumerate(file, start=1):
            fields = line.strip().split(delimiter)
            if len(fields) != expected_length:
                return f"Record {i} has an incorrect number of fields. Expected {expected_length}, found {len(fields)}."
    return None

def validate_field_lengths(filename, max_lengths, delimiter='|'):
    """Validate that each field in the records does not exceed its maximum length."""
    with open(filename, 'r') as file:
        for i, line in enumerate(file, start=1):
            fields = line.strip().split(delimiter)
            for j, field in enumerate(fields):
                if len(field) > max_lengths[j]:
                    return f"Record {i}, Field {j+1} exceeds the maximum length of {max_lengths[j]} characters."
    return None

def validate_datatypes(filename, datatype_checks, delimiter='|'):
    """Validate that each field in the records matches the expected datatype."""
    with open(filename, 'r') as file:
        for i, line in enumerate(file, start=1):
            fields = line.strip().split(delimiter)
            for j, field in enumerate(fields):
                if not datatype_checks[j](field):
                    return f"Record {i}, Field {j+1} does not match the expected datatype."
    return None

def validate_mandatory_fields(filename, mandatory_fields, delimiter='|'):
    """Validate that mandatory fields are not null or empty."""
    with open(filename, 'r') as file:
        for i, line in enumerate(file, start=1):
            fields = line.strip().split(delimiter)
            for field_index in mandatory_fields:
                if not fields[field_index].strip():
                    return f"Record {i}, Field {field_index+1} is mandatory and cannot be empty."
    return None

def check_for_duplicates(filename, delimiter='|'):
    """Check for duplicate records based on the 'id' field."""
    seen_ids = set()
    duplicates = []
    with open(filename, 'r') as file:
        for i, line in enumerate(file, start=1):
            fields = line.strip().split(delimiter)
            record_id = fields[0]
            if record_id in seen_ids:
                duplicates.append(f"Duplicate record found at line {i}: {line.strip()}")
            else:
                seen_ids.add(record_id)
    return duplicates

def run_all_validations(filename, delimiter='|', expected_encoding='utf-8'):
    """Run all validations on the file and return a list of errors."""
    errors = []

    # Check encoding and convert if necessary
    encoding_error = validate_encoding(filename, expected_encoding)
    if encoding_error:
        errors.append(encoding_error)
        temp_filename = 'temp_converted_file.txt'
        try:
            convert_to_utf8(filename, temp_filename)
            filename = temp_filename  # Update filename to the converted file
        except RuntimeError as e:
            errors.append(str(e))
            return errors

    # Run each validation function
    result = validate_filename(filename)
    if result: errors.append(result)

    result = validate_file_size(filename)
    if result: errors.append(result)

    result = validate_record_length(filename, expected_length=3, delimiter=delimiter)
    if result: errors.append(result)

    max_lengths = [20, 10, 255]  # Example: max lengths for 'id', 'code', 'text' fields
    result = validate_field_lengths(filename, max_lengths, delimiter)
    if result: errors.append(result)

    datatype_checks = [
        lambda x: bool(re.match(r'^[a-zA-Z0-9\-]+$', x)),  # id: alphanumeric
        lambda x: x.isdigit(),  # code: numeric
        lambda x: bool(re.match(r'^[a-zA-Z0-9\s\-]+$', x))  # text: alphanumeric with spaces and hyphens
    ]
    result = validate_datatypes(filename, datatype_checks, delimiter)
    if result: errors.append(result)

    # Check mandatory fields: 'id' (index 0) and 'cd' (index 1)
    mandatory_fields = [0, 1]
    result = validate_mandatory_fields(filename, mandatory_fields, delimiter)
    if result: errors.append(result)

    duplicates = check_for_duplicates(filename, delimiter)
    if duplicates: errors.extend(duplicates)

    return errors

def generate_report(errors, report_file):
    """Generate a validation report."""
    with open(report_file, 'w') as file:
        if not errors:
            file.write("File validation successful. No errors found.\n")
        else:
            file.write("File validation failed. Errors:\n")
            for error in errors:
                file.write(f"{error}\n")

# Example usage
if __name__ == "__main__":
    filename = "mainframe_dataset.txt"
    delimiter = '|'  # Specify the delimiter used in your txt file

    errors = run_all_validations(filename, delimiter)

    if not errors:
        print("File passed all validations.")
    else:
        print("File validation failed.")
    
    generate_report(errors, "validation_report.txt")

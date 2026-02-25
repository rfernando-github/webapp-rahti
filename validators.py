"""Input Validator Module for CardioRisk Predictor."""


def validate_input(data):
    """Validate user input and return a list of error messages (empty if valid)."""
    errors = []

    # --- Numeric field parsing ---
    numeric_fields = {
        'age': ('Age', int),
        'height': ('Height', float),
        'weight': ('Weight', float),
        'ap_hi': ('Systolic BP', int),
        'ap_lo': ('Diastolic BP', int),
    }
    parsed = {}
    for field, (label, typ) in numeric_fields.items():
        val = data.get(field, '').strip()
        if not val:
            errors.append(f'{label} is required.')
            continue
        try:
            parsed[field] = typ(val)
        except (ValueError, TypeError):
            errors.append(f'{label} must be a valid number.')

    # If basic parsing failed, return early
    if errors:
        return errors

    # --- Range checks ---
    age = parsed['age']
    if not (1 <= age <= 120):
        errors.append('Age must be between 1 and 120 years.')

    height = parsed['height']
    if not (100 <= height <= 220):
        errors.append('Height must be between 100 and 220 cm.')

    weight = parsed['weight']
    if not (30 <= weight <= 200):
        errors.append('Weight must be between 30 and 200 kg.')

    ap_hi = parsed['ap_hi']
    if not (90 <= ap_hi <= 250):
        errors.append('Systolic BP must be between 90 and 250 mmHg.')

    ap_lo = parsed['ap_lo']
    if not (40 <= ap_lo <= 150):
        errors.append('Diastolic BP must be between 40 and 150 mmHg.')

    if ap_hi <= ap_lo:
        errors.append('Systolic BP must be greater than Diastolic BP.')

    # --- Categorical fields ---
    for field, label in [('cholesterol', 'Cholesterol'), ('gluc', 'Glucose')]:
        val = data.get(field, '').strip()
        if val not in ('1', '2', '3'):
            errors.append(f'{label} must be 1 (Normal), 2 (Above Normal), or 3 (High).')

    for field, label in [('gender', 'Gender'), ('smoke', 'Smoking'),
                         ('alco', 'Alcohol'), ('active', 'Physical Activity')]:
        val = data.get(field, '').strip()
        if val not in ('0', '1'):
            errors.append(f'{label} must be 0 or 1.')

    return errors

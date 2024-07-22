import numpy as np

delay_list = np.linspace(0, 200, num=10, endpoint=False)

def generate_sin_with_error(numbers):
    # Calculate the sine of each number
    sine_values = np.sin(numbers)
    # Generate random errors between -0.2 and 0.2
    errors = np.random.uniform(-0.2, 0.2, size=len(numbers))
    # Add the sine values and the errors
    result = sine_values + errors
    return result
sine=generate_sin_with_error(delay_list)
print(delay_list.tolist())
print(sine.tolist())

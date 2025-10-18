# Unit Tests

This directory contains unit tests for the NBA Player Performance Predictor.

## Running Tests

### Run all tests:
```bash
python run_tests.py
```

### Run specific test file:
```bash
python -m unittest tests.test_models
python -m unittest tests.test_statistics
```

### Run specific test class:
```bash
python -m unittest tests.test_models.TestInverseFrequencyModel
```

### Run specific test method:
```bash
python -m unittest tests.test_models.TestInverseFrequencyModel.test_inverse_frequency_basic
```

## Test Coverage

### `test_models.py`
Tests for the `InverseFrequencyModel` class:
- Recency weight calculation
- Inverse frequency probability calculations
- Confidence intervals
- Bayesian smoothing
- Fatigue analysis
- Minutes trend detection
- Non-stationarity detection
- Edge cases (empty data, missing columns)

### `test_statistics.py`
Tests for the `StatisticsEngine` class:
- Z-score normalization
- League averages caching
- Minutes format parsing
- Career phase weight calculation
- Consistency metrics
- Momentum indicators
- Outlier detection (IQR, z-score methods)
- Seasonal normalization

## Adding New Tests

1. Create a new test file in the `tests/` directory with prefix `test_`
2. Import `unittest` and the module you want to test
3. Create test classes inheriting from `unittest.TestCase`
4. Write test methods with prefix `test_`
5. Use assertions like `self.assertEqual()`, `self.assertAlmostEqual()`, etc.

Example:
```python
import unittest
from my_module import MyClass

class TestMyClass(unittest.TestCase):
    def setUp(self):
        self.obj = MyClass()
    
    def test_my_method(self):
        result = self.obj.my_method(5)
        self.assertEqual(result, 10)
```

## Test Requirements

All tests should:
- Be independent (not rely on other tests)
- Use setUp() for test fixtures
- Test both normal cases and edge cases
- Have descriptive names
- Include docstrings explaining what they test


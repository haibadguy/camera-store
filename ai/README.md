# AI Recommendation

This folder contains the Python recommendation component described by the project specification.

## Structure

- `recommendation/train.py`: model training entry point
- `recommendation/predict.py`: inference entry point
- `recommendation/requirements.txt`: Python dependencies
- `recommendation/models/`: generated model artifacts

The first supported algorithm is content-based recommendation. Collaborative and hybrid
experiments can be added without coupling the Spring Boot modules to training code.


"""IncidentMind backend application package.

Deliberately does not import ``app.main`` here: doing so would make the package
initialiser import its own subpackage graph, which is a circular-import hazard
for no benefit. Import the app explicitly as ``app.main:app`` (uvicorn) or
``from app.main import app`` (tests).
"""

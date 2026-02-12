
import sys
import os

print("Python Executable:", sys.executable)
print("Sys Path:")
for p in sys.path:
    print(p)

try:
    import rest_framework
    print("rest_framework imported successfully:", rest_framework.__file__)
except ImportError as e:
    print("Failed to import rest_framework:", e)

try:
    import dj_database_url
    print("dj_database_url imported successfully:", dj_database_url.__file__)
except ImportError as e:
    print("Failed to import dj_database_url:", e)

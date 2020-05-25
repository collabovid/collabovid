import os.path

DB_EXPORT_STORE_LOCALLY = True
DB_EXPORT_LOCAL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'resources', 'export')

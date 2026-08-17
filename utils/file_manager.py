import os
import time
import shutil
import logging

logger = logging.getLogger(__name__)

# Base folder jahan saari ZIP aur PDFs rakhi jayengi
TEMP_UPLOAD_DIR = "./temp_resumes_data"

# Ensure folder exists
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

def save_uploaded_zip(bulk_id: str, file_bytes: bytes) -> str:
    """ZIP file ko temp folder me save karta hai aur path return karta hai."""
    job_folder = os.path.join(TEMP_UPLOAD_DIR, bulk_id)
    os.makedirs(job_folder, exist_ok=True)
    
    zip_path = os.path.join(job_folder, "uploaded_resumes.zip")
    with open(zip_path, "wb") as f:
        f.write(file_bytes)
        
    return job_folder, zip_path

def cleanup_old_folders(hours: int = 24):
    """
    Yeh function check karega ki kaunsa folder 24 ghante se zyada purana hai 
    aur usko hamesha ke liye delete kar dega.
    """
    now = time.time()
    cutoff_time = now - (hours * 3600)  # 24 hours in seconds
    
    deleted_count = 0
    for folder_name in os.listdir(TEMP_UPLOAD_DIR):
        folder_path = os.path.join(TEMP_UPLOAD_DIR, folder_name)
        
        # Check if it's a directory
        if os.path.isdir(folder_path):
            folder_creation_time = os.path.getmtime(folder_path)
            
            # Agar 24 ghante se purana hai, toh uda do!
            if folder_creation_time < cutoff_time:
                try:
                    shutil.rmtree(folder_path)
                    deleted_count += 1
                    print(f" [CLEANUP] Deleted old folder: {folder_name}")
                except Exception as e:
                    logger.error(f"Failed to delete {folder_name}: {e}")
                    
    if deleted_count > 0:
        print(f" [CLEANUP SUCCESS] Cleared {deleted_count} old resume batches.")
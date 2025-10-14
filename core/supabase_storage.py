import os
from supabase import create_client, Client
from django.conf import settings
import uuid

class SupabaseStorage:
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.bucket_name = os.getenv('SUPABASE_BUCKET', 'profile-pictures')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    def upload_profile_picture(self, file, user_id):
        try:
            # Generate unique filename
            file_ext = file.name.split('.')[-1]
            filename = f"user_{user_id}_{uuid.uuid4().hex[:8]}.{file_ext}"
            filepath = f"avatars/{filename}"
            
            # Read file content
            file_content = file.read()
            
            # Upload to Supabase Storage
            response = self.client.storage.from_(self.bucket_name).upload(
                path=filepath,
                file=file_content,
                file_options={
                    "content-type": file.content_type,
                    "upsert": "true"
                }
            )
            
            # Get public URL
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(filepath)
            
            return public_url
            
        except Exception as e:
            raise Exception(f"Failed to upload to Supabase: {str(e)}")
    
    def delete_profile_picture(self, file_path):
        try:
            # Extract path from URL if full URL is provided
            if file_path.startswith('http'):
                path = file_path.split(f'{self.bucket_name}/')[-1]
            else:
                path = file_path
            
            # Delete from Supabase Storage
            self.client.storage.from_(self.bucket_name).remove([path])
            
        except Exception as e:
            print(f"Failed to delete from Supabase: {str(e)}")
    
    def get_public_url(self, filepath):
        return self.client.storage.from_(self.bucket_name).get_public_url(filepath)

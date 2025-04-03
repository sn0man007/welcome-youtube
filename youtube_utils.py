"""
YouTube Utility Functions

This module provides a set of utility functions for interacting with the YouTube API.
It includes functionality for video upload, metadata management, and analytics.
"""

from typing import Dict, List, Optional
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubeAPI:
    """A class to handle YouTube API operations."""
    
    def __init__(self, client_secrets_file: str):
        """
        Initialize the YouTube API client.
        
        Args:
            client_secrets_file (str): Path to the client secrets file from Google Cloud Console
        """
        self.SCOPES = [
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube.readonly'
        ]
        self.client_secrets_file = client_secrets_file
        self.credentials = None
        self.youtube = None
        
    def authenticate(self) -> None:
        """Authenticate with the YouTube API using OAuth 2.0."""
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_file, self.SCOPES)
        self.credentials = flow.run_local_server(port=0)
        self.youtube = build('youtube', 'v3', credentials=self.credentials)
        
    def upload_video(self, 
                    file_path: str, 
                    title: str, 
                    description: str, 
                    privacy_status: str = 'private',
                    tags: Optional[List[str]] = None) -> Dict:
        """
        Upload a video to YouTube.
        
        Args:
            file_path (str): Path to the video file
            title (str): Video title
            description (str): Video description
            privacy_status (str): Privacy status ('private', 'unlisted', or 'public')
            tags (List[str], optional): List of video tags
            
        Returns:
            Dict: Response from the YouTube API containing video details
        """
        if not self.youtube:
            raise ValueError("YouTube API client not authenticated. Call authenticate() first.")
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")
            
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags or [],
                'categoryId': '22'  # Default to 'People & Blogs'
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(
            file_path, 
            mimetype='video/*',
            resumable=True
        )
        
        request = self.youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")
                
        return response
        
    def get_channel_stats(self) -> Dict:
        """
        Get statistics for the authenticated user's channel.
        
        Returns:
            Dict: Channel statistics including view count, subscriber count, and video count
        """
        if not self.youtube:
            raise ValueError("YouTube API client not authenticated. Call authenticate() first.")
            
        request = self.youtube.channels().list(
            part="statistics",
            mine=True
        )
        response = request.execute()
        
        if 'items' in response and response['items']:
            return response['items'][0]['statistics']
        return {}
        
    def list_videos(self, max_results: int = 50) -> List[Dict]:
        """
        List videos from the authenticated user's channel.
        
        Args:
            max_results (int): Maximum number of videos to retrieve
            
        Returns:
            List[Dict]: List of video details
        """
        if not self.youtube:
            raise ValueError("YouTube API client not authenticated. Call authenticate() first.")
            
        request = self.youtube.search().list(
            part="snippet",
            forMine=True,
            type="video",
            maxResults=max_results
        )
        response = request.execute()
        
        return response.get('items', [])

def main():
    """Example usage of the YouTubeAPI class."""
    # Replace with your client secrets file path
    client_secrets_file = "path/to/your/client_secrets.json"
    
    try:
        # Initialize and authenticate
        yt = YouTubeAPI(client_secrets_file)
        yt.authenticate()
        
        # Get channel statistics
        stats = yt.get_channel_stats()
        print("Channel Statistics:", stats)
        
        # List videos
        videos = yt.list_videos(max_results=5)
        print("\nRecent Videos:")
        for video in videos:
            print(f"- {video['snippet']['title']}")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
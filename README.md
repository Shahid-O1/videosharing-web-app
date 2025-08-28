# Video Sharing Web App

A scalable, cloud-native video sharing platform built with Flask, supporting both creator and consumer roles, secure user authentication, video uploads, metadata, commenting, rating, and search functionality.

## Features

- Creator and Consumer user roles
- Secure registration and login with password hashing
- Video upload restricted to creators, with metadata (Title, Publisher, Producer, Genre, Age rating)
- Dashboard displaying latest videos with search functionality
- Commenting and rating on videos by consumers
- REST API endpoint for listing videos

## Getting Started

### Prerequisites

- Python 3.x
- pip

### Installation

1. Clone the repository:
    ```
    git clone https://github.com/Shahid-O1/videosharing-web-app.git
    cd videosharing-web-app
    ```
2. Install dependencies:
    ```
    pip install -r requirements.txt
    ```

3. Run the application:
    ```
    python app.py
    ```
   The app will start at `http://127.0.0.1:5000/`

### Folder Structure

```
videosharing-web-app/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── upload_video.html
│   └── video_detail.html
├── static/
│   └── style.css (optional)
└── uploads/
```

### Usage

- Register as a consumer to view, search, comment on, and rate videos.
- Creators (added manually or via admin) can upload new videos with metadata.
- Consumers can view video details, post comments, and rate videos.

## Deployment (Azure)

- Push your repository to GitHub.
- Connect Azure App Service to your GitHub repo for automatic deployment.
- Ensure `uploads/` is created for storing uploaded videos (not tracked by Git).
- For production, use environment variables for secrets.
- Consider using Azure SQL Database and Blob Storage for scalable storage in production.

## Notes

- The app uses SQLite for demonstration purposes; swap for Azure SQL or another cloud DB for scalability.
- Video files are stored locally in the `uploads/` directory; move to cloud storage in production.
- All templates are found in the `/templates` folder.

## License

MIT

## Author

Shahid-O1

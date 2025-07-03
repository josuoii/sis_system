# PDIE System - Personal Development and Intervention Education System

A comprehensive Django-based web application designed for managing student interventions, academic records, and personal development tracking in educational institutions.

## 🎯 Project Overview

The PDIE System is a sophisticated Student Information System (SIS) that provides tools for:
- Student intervention management and tracking
- Academic record maintenance
- Personal development assessment
- Document management and progress evidence
- Multi-user role-based access control
- Real-time communication features

## 🚀 Features

### Core Functionality
- **Student Management**: Complete student profile management with academic records
- **Intervention Tracking**: Systematic approach to student intervention planning and monitoring
- **Document Management**: Upload and organize intervention documents and progress evidence
- **Academic Records**: Comprehensive academic performance tracking
- **User Authentication**: Secure login system with role-based permissions
- **Dashboard Analytics**: Visual representation of student progress and intervention outcomes

### Technical Features
- **Django Framework**: Built with Django 4.2.11 for robust backend functionality
- **Real-time Communication**: WebSocket support via Django Channels
- **File Management**: Secure file upload and storage system
- **PDF Generation**: Automated report generation using xhtml2pdf
- **Responsive Design**: Modern, mobile-friendly user interface
- **Database**: SQLite database for data persistence

## 📋 Prerequisites

Before running this project, ensure you have:
- Python 3.10 or higher
- pip (Python package installer)
- Git (for version control)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pdie_system_sis
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:8000/`

## 📁 Project Structure

```
pdie_system_sis/
├── intervention/           # Main Django app
│   ├── migrations/        # Database migrations
│   ├── scripts/          # Utility scripts
│   ├── templates/        # HTML templates
│   └── static/           # Static files (CSS, JS, images)
├── pdie_system/          # Django project settings
├── media/                # User-uploaded files
├── static/               # Static assets
├── templates/            # Base templates
├── logs/                 # Application logs
├── requirements.txt      # Python dependencies
└── manage.py            # Django management script
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory with the following variables:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
```

### Database Configuration
The system uses SQLite by default. For production, consider using PostgreSQL or MySQL.

## 👥 User Roles

The system supports multiple user roles:
- **Administrators**: Full system access and user management
- **Teachers/Staff**: Student intervention management and academic record access
- **Students**: View their own records and progress

## 📊 Key Modules

### Intervention Management
- Create and track student interventions
- Document intervention strategies and outcomes
- Monitor progress over time
- Generate intervention reports

### Academic Records
- Maintain comprehensive student academic history
- Track grades, attendance, and performance metrics
- Generate academic transcripts and reports

### Document Management
- Upload and organize intervention documents
- Store progress evidence and supporting materials
- Secure file access with role-based permissions

## 🔒 Security Features

- **Authentication**: Secure login system with password protection
- **Authorization**: Role-based access control
- **File Security**: Protected file uploads and downloads
- **Session Management**: Secure session handling
- **Input Validation**: Comprehensive form validation

## 📝 API Documentation

The system provides RESTful API endpoints for:
- Student data management
- Intervention tracking
- Document upload/download
- User authentication

## 🧪 Testing

Run the test suite:
```bash
python manage.py test
```

## 🚀 Deployment

### Production Setup
1. Set `DEBUG=False` in settings
2. Configure a production database
3. Set up static file serving
4. Configure web server (nginx, Apache)
5. Set up SSL certificates

### Docker Deployment (Optional)
```bash
# Build and run with Docker
docker build -t pdie-system .
docker run -p 8000:8000 pdie-system
```

## 📈 Monitoring and Logging

- Application logs are stored in `logs/django.log`
- Monitor system performance and user activity
- Track intervention outcomes and student progress

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation in the `docs/` folder

## 🔄 Version History

- **v1.0.0**: Initial release with core intervention management features
- **v1.1.0**: Added document management and progress tracking
- **v1.2.0**: Enhanced user interface and reporting capabilities

## 📞 Contact

- **Project Maintainer**: [Your Name]
- **Email**: [your.email@example.com]
- **Project Link**: [https://github.com/yourusername/pdie_system_sis]

---

**Note**: This is a Django-based educational management system designed to streamline student intervention processes and academic record management. 